"""Pipeline RAG multiagente (Fase 1 + Fase 2 + Fase 3) — orquestração completa.

Fluxo:
    entrada → guardrail de entrada → orquestrador (classificação + seleção de
    agente + retrieval por domínio + vigência) → model router → cache semântico
    seguro → geração → guardrail de saída → FinOps (custo) → human-in-the-loop →
    resposta com evidência → trace observável (via TraceSink plugável).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.agents.answer_generator import AnswerGenerator, ExtractiveAnswerGenerator
from app.agents.llm_answer_generator import LLMAnswerGenerator
from app.agents.orchestrator import OrchestrationDecision, Orchestrator
from app.agents.reception_agent import ReceptionAgent
from app.cache.semantic_cache import SemanticCache, cache_bypass_reason
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.model_router import BudgetStatus, ModelTier, RoutingDecision, select_model
from app.core.models import Answer, Confidence, Confidentiality, Trace, UserRole
from app.core.tracing import generate_trace_id, get_session_id, get_trace_id
from app.escalation.human_review import evaluate_escalation
from app.finops.cost import CostRecord, FinOpsTracker, classify_budget, estimate_cost
from app.governance.policy_registry import PolicyRegistry, get_policy_registry
from app.guardrails.input_guardrail import check_input
from app.guardrails.output_guardrail import check_output
from app.guardrails.pii import detect_pii
from app.guardrails.policies import (
    FORBIDDEN_REQUEST_RESPONSE,
    BlockReason,
    no_evidence_response,
    restricted_data_response,
)
from app.observability.sinks import TraceSink, get_trace_sink
from app.observability.trace import build_answer_trace, estimate_tokens, record_trace
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import ScoredChunk

logger = get_logger(__name__)


def allowed_confidentiality_for(role: UserRole) -> list[Confidentiality]:
    """Atalho de compatibilidade: delega ao policy registry padrão (RF3.8)."""
    return get_policy_registry().allowed_confidentiality_for(role)


@dataclass
class RagResponse:
    """Resultado completo de uma consulta: resposta + trace."""

    answer: Answer
    trace: Trace
    blocked: bool = False
    guardrails_triggered: list[str] = field(default_factory=list)
    agent: str | None = None
    domain: str | None = None
    cache_hit: bool = False
    model: str | None = None
    estimated_cost: float = 0.0
    cache_bypass_reason: str | None = None
    budget_status: str | None = None
    budget_action: str | None = None
    screening_decision: str | None = None


class RagPipeline:
    """Orquestra guardrails, roteamento, geração, observabilidade e FinOps."""

    def __init__(
        self,
        retriever: Retriever,
        generator: AnswerGenerator | None = None,
        *,
        cache: SemanticCache | None = None,
        finops: FinOpsTracker | None = None,
        policy_registry: PolicyRegistry | None = None,
        embedder: EmbeddingProvider | None = None,
        prompt_version: str | None = None,
        sink: TraceSink | None = None,
        cost_budget_per_answer: float | None = None,
    ) -> None:
        settings = get_settings()
        self._orchestrator = Orchestrator(retriever)
        self._reception = ReceptionAgent()
        # Seleciona o gerador: LLM (se habilitado) ou extrativo
        if generator is not None:
            self._generator = generator
        elif settings.use_llm_generator:
            self._generator = LLMAnswerGenerator()
        else:
            self._generator = ExtractiveAnswerGenerator()
        self._policies = policy_registry or get_policy_registry()
        self._embedder = embedder or get_embedding_provider()
        self._finops = finops or FinOpsTracker()
        self._prompt_version = prompt_version
        self._sink = sink or get_trace_sink()
        self._budget = (
            cost_budget_per_answer
            if cost_budget_per_answer is not None
            else settings.cost_budget_per_answer
        )
        self._cache = cache or (
            SemanticCache(similarity_threshold=settings.cache_similarity_threshold)
            if settings.cache_enabled
            else None
        )

    @property
    def finops(self) -> FinOpsTracker:
        """Expõe o tracker de custo (relatório FinOps)."""
        return self._finops

    def _get_model_for_tier(self, tier: ModelTier) -> str:
        """Retorna o modelo configurado para o tier especificado (via .env)."""
        settings = get_settings()
        tier_map = {
            "economico": settings.model_economico,
            "intermediario": settings.model_intermediario,
            "robusto": settings.model_robusto,
        }
        return tier_map.get(tier.value, settings.model_economico)

    def run(
        self,
        query: str,
        *,
        role: UserRole = UserRole.COLABORADOR,
        area_rh: str | None = None,
        user_id: str | None = None,
        channel: str = "api",
    ) -> RagResponse:
        """Executa o fluxo RAG multiagente completo para uma pergunta."""
        start = time.perf_counter()
        trace_id = get_trace_id() or generate_trace_id()
        session_id = get_session_id() or trace_id
        settings = get_settings()

        self._sink.event(
            "interaction_start", trace_id=trace_id, session_id=session_id, channel=channel
        )

        # 1. Guardrail de entrada
        input_check = check_input(query)
        if input_check.blocked:
            triggered = [r.value for r in input_check.reasons]
            self._sink.event(
                "guardrail_triggered", trace_id=trace_id, stage="input", reasons=triggered
            )
            # Diferencia recusa de segurança (injeção/entrada inválida — sem
            # incentivo a chamado) de pedido legítimo porém restrito (dado
            # pessoal — encaminha ao RH/chamado).
            security_block = {
                BlockReason.PROMPT_INJECTION,
                BlockReason.INVALID_INPUT,
            }
            if security_block.intersection(input_check.reasons):
                blocked_message = FORBIDDEN_REQUEST_RESPONSE
            else:
                blocked_message = restricted_data_response()
            answer = Answer(
                answer=blocked_message,
                evidence=[],
                confidence=Confidence.BAIXA,
                limitations="Solicitação bloqueada pelo guardrail de entrada.",
                requires_human_review=False,
            )
            return self._finalize(
                start=start,
                trace_id=trace_id,
                session_id=session_id,
                user_id=user_id,
                channel=channel,
                original_query=query,
                canonical_query=input_check.sanitized_query,
                domain=None,
                agent="input_guardrail",
                answer=answer,
                chunk_ids=[],
                triggered=triggered,
                routing_confidence=None,
                routing_reason="bloqueado na entrada",
                agents_invoked=[],
                routing=None,
                cache_hit=False,
                escalation_reason=None,
                cache_bypass=None,
                blocked=True,
            )

        canonical = input_check.sanitized_query
        allowed = self._policies.allowed_confidentiality_for(role)

        # 1.5 Agente de Recepção (front door): acolhe saudações, agradecimentos,
        #     despedidas e pedidos de ajuda antes de acionar os especialistas.
        reception_answer = self._reception.try_handle(canonical)
        if reception_answer is not None:
            self._sink.event("reception_handled", trace_id=trace_id)
            return self._finalize(
                start=start,
                trace_id=trace_id,
                session_id=session_id,
                user_id=user_id,
                channel=channel,
                original_query=query,
                canonical_query=canonical,
                domain=None,
                agent=self._reception.name,
                answer=reception_answer,
                chunk_ids=[],
                triggered=[],
                routing_confidence=None,
                routing_reason="recepção: acolhimento do usuário",
                agents_invoked=[self._reception.name],
                routing=None,
                cache_hit=False,
                escalation_reason=None,
                cache_bypass=None,
                blocked=False,
                budget_status=None,
                budget_action=None,
                screening_decision=None,
            )

        # 2. Orquestrador: classifica domínio, seleciona agente e recupera evidências
        decision: OrchestrationDecision = self._orchestrator.route(
            canonical, allowed, forced_area=area_rh
        )
        chunks = decision.chunks
        chunk_ids = [s.chunk.chunk_id for s in chunks]
        domain = decision.intel.domain.value
        triggered = []
        self._sink.event(
            "retrieval_completed",
            trace_id=trace_id,
            domain=domain,
            agent=decision.agent_used,
            relevant=len(chunks),
        )

        # 3. Triagem de risco do agente (RF2.6): a decisão de screening governa a
        #    resposta — bloqueio impede a geração normal; revisão humana é propagada.
        screening = decision.screening
        screening_requires_review = bool(screening and screening.requires_human_review)
        if screening is not None and screening.blocked:
            self._sink.event(
                "agent_screening_block",
                trace_id=trace_id,
                agent=decision.agent_used,
                reason=screening.reason,
            )
            triggered.append(BlockReason.PII_REQUEST.value)
            answer = Answer(
                answer=restricted_data_response(),
                evidence=[],
                confidence=Confidence.BAIXA,
                limitations="Solicitação bloqueada pela triagem do agente especialista.",
                requires_human_review=True,
                screening_decision="blocked",
                escalation_reason=screening.reason or None,
            )
            return self._finalize(
                start=start,
                trace_id=trace_id,
                session_id=session_id,
                user_id=user_id,
                channel=channel,
                original_query=query,
                canonical_query=canonical,
                domain=domain,
                agent=decision.agent_used,
                answer=answer,
                chunk_ids=[],
                triggered=triggered,
                routing_confidence=decision.intel.confidence,
                routing_reason=decision.reason,
                agents_invoked=decision.agents_invoked,
                routing=None,
                cache_hit=False,
                escalation_reason=screening.reason or None,
                cache_bypass=None,
                blocked=True,
                budget_status=None,
                budget_action=None,
                screening_decision="blocked",
            )

        # 4. Model router (RF3.3) + enforcement de orçamento (RF3.5).
        input_tokens_est = estimate_tokens(canonical)
        output_tokens_est = self._estimate_output_tokens(chunks)
        routing = select_model(
            decision.intel.risk_level,
            decision.intel.confidence,
            strategy=settings.model_selection_strategy,
            min_confidence=settings.human_review_min_confidence,
            estimated_input_tokens=input_tokens_est,
            estimated_output_tokens=output_tokens_est,
        )
        budget_status = classify_budget(routing.estimated_cost, self._budget)
        budget_action: str | None = None
        if budget_status != BudgetStatus.NORMAL:
            chunks, budget_action = self._enforce_budget(budget_status, chunks)
            chunk_ids = [s.chunk.chunk_id for s in chunks]
            output_tokens_est = self._estimate_output_tokens(chunks)
            routing = select_model(
                decision.intel.risk_level,
                decision.intel.confidence,
                strategy=settings.model_selection_strategy,
                min_confidence=settings.human_review_min_confidence,
                budget_status=budget_status,
                estimated_input_tokens=input_tokens_est,
                estimated_output_tokens=output_tokens_est,
            )
            self._sink.event(
                "finops_budget_enforced",
                trace_id=trace_id,
                budget_status=budget_status.value,
                action=budget_action,
                budget=self._budget,
                estimated_cost=routing.estimated_cost,
            )

        # 5. Cache semântico seguro (RF3.4): bypass em contexto sensível
        bypass = cache_bypass_reason(
            has_pii=detect_pii(canonical).has_pii,
            risk_level=decision.intel.risk_level,
            requires_human_review=screening_requires_review,
        )
        query_vector = self._embedder.embed(canonical)
        current_versions = {s.chunk.source_id: s.chunk.version for s in chunks}
        cache_hit = False
        cached = None
        if self._cache is not None and bypass is None:
            cached = self._cache.lookup(
                query_vector,
                domain=domain,
                allowed_confidentiality=allowed,
                current_versions=current_versions,
            )

        if cached and cached.hit and cached.answer is not None:
            answer = cached.answer
            cache_hit = True
        else:
            # 6. Geração fundamentada
            # Determina o modelo baseado no tier selecionado pelo model_router
            model_name = None
            if settings.use_llm_generator and routing is not None:
                model_name = self._get_model_for_tier(routing.model.tier)
            answer = self._generator.generate(canonical, chunks, model_name)

            # 7. Guardrail de saída
            output_check = check_output(answer)
            if not output_check.approved:
                triggered.extend(r.value for r in output_check.reasons)
                self._sink.event(
                    "guardrail_triggered", trace_id=trace_id, stage="output", reasons=triggered
                )
                answer = Answer(
                    answer=no_evidence_response(),
                    evidence=[],
                    confidence=Confidence.BAIXA,
                    limitations="Resposta reprovada pelo guardrail de saída (sem fonte/evidência).",
                    requires_human_review=True,
                )
                chunk_ids = []

        # 8. Human-in-the-loop (RF3.6): reconcilia escalonamento, screening do
        #    agente e exigência de revisão do model router.
        escalation = evaluate_escalation(
            risk=decision.intel.risk_level,
            confidence=Confidence(answer.confidence),
            has_evidence=bool(answer.evidence),
            routing_confidence=decision.intel.confidence,
            min_routing_confidence=settings.human_review_min_confidence,
        )
        reasons: list[str] = []
        if screening_requires_review and screening and screening.reason:
            reasons.append(screening.reason)
        if escalation.reason:
            reasons.append(escalation.reason)
        if routing.requires_human_review:
            reasons.append("model router: exige revisão humana")
        combined_reason = "; ".join(reasons) or None

        requires_review = (
            escalation.escalate
            or routing.requires_human_review
            or screening_requires_review
            or answer.requires_human_review
        )
        screening_decision = "human_review" if screening_requires_review else None
        answer = answer.model_copy(
            update={
                "requires_human_review": requires_review,
                "screening_decision": screening_decision,
                "escalation_reason": combined_reason,
            }
        )

        # 9. Armazena no cache somente quando seguro (sem bypass, com evidência,
        #    aprovado e sem revisão humana).
        effective_bypass = bypass
        if not cache_hit and self._cache is not None:
            if bypass is None and answer.requires_human_review:
                effective_bypass = "revisao_humana_obrigatoria"
            if effective_bypass is None and answer.evidence:
                self._store_in_cache(canonical, query_vector, answer, domain, chunks)

        return self._finalize(
            start=start,
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            original_query=query,
            canonical_query=canonical,
            domain=domain,
            agent=decision.agent_used,
            answer=answer,
            chunk_ids=chunk_ids,
            triggered=triggered,
            routing_confidence=decision.intel.confidence,
            routing_reason=decision.reason,
            agents_invoked=decision.agents_invoked,
            routing=routing,
            cache_hit=cache_hit,
            escalation_reason=combined_reason,
            cache_bypass=effective_bypass,
            blocked=False,
            budget_status=budget_status.value,
            budget_action=budget_action,
            screening_decision=screening_decision,
        )

    def _estimate_output_tokens(self, chunks: list[ScoredChunk]) -> int:
        """Estima tokens de saída do gerador extrativo (para custo/orçamento)."""
        if not chunks:
            return estimate_tokens(no_evidence_response())
        total = 10
        for item in chunks:
            total += min(len(item.chunk.text.split()), 55)
        return total

    def _enforce_budget(
        self, status: BudgetStatus, chunks: list[ScoredChunk]
    ) -> tuple[list[ScoredChunk], str]:
        """Aplica a redução de contexto correspondente à situação de orçamento."""
        if status == BudgetStatus.EXCEEDED:
            # Reduz agressivamente o contexto e força o modelo econômico.
            return chunks[:1], "contexto_reduzido_e_modelo_economico"
        # NEAR_LIMIT: reduz o contexto pela metade para conter custo.
        keep = max(1, len(chunks) // 2)
        return chunks[:keep], "contexto_reduzido"

    def _store_in_cache(
        self,
        canonical: str,
        query_vector: list[float],
        answer: Answer,
        domain: str,
        chunks: list[ScoredChunk],
    ) -> None:
        """Armazena a resposta no cache com restrições de domínio, permissão e versão."""
        if self._cache is None:
            return
        required = frozenset(str(s.chunk.confidentiality) for s in chunks)
        versions = {s.chunk.source_id: s.chunk.version for s in chunks}
        self._cache.store(
            canonical,
            query_vector,
            answer,
            domain=domain,
            required_confidentiality=required,
            document_versions=versions,
        )

    def _finalize(
        self,
        *,
        start: float,
        trace_id: str,
        session_id: str,
        user_id: str | None,
        channel: str,
        original_query: str,
        canonical_query: str,
        domain: str | None,
        agent: str,
        answer: Answer,
        chunk_ids: list[str],
        triggered: list[str],
        routing_confidence: float | None,
        routing_reason: str,
        agents_invoked: list[str],
        routing: RoutingDecision | None,
        cache_hit: bool,
        escalation_reason: str | None,
        cache_bypass: str | None,
        blocked: bool,
        budget_status: str | None = None,
        budget_action: str | None = None,
        screening_decision: str | None = None,
    ) -> RagResponse:
        latency_ms = (time.perf_counter() - start) * 1000

        input_tokens = estimate_tokens(original_query)
        output_tokens = estimate_tokens(answer.answer)

        # FinOps: cache hit não consome o modelo; custo zero.
        if cache_hit or routing is None:
            model_name = "cache" if cache_hit else (routing.model.name if routing else "n/a")
            model_tier = None
            cost = 0.0
        else:
            model_name = routing.model.name
            model_tier = routing.model.tier.value
            cost = estimate_cost(routing.model, input_tokens, output_tokens)
            settings = get_settings()
            if cost > settings.cost_budget_per_answer:
                logger.warning(
                    "finops_budget_exceeded",
                    cost=cost,
                    budget=settings.cost_budget_per_answer,
                    model=model_name,
                )

        self._finops.record(
            CostRecord(
                trace_id=trace_id,
                agent=agent,
                model=model_name,
                channel=channel,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
            )
        )

        trace = build_answer_trace(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            original_query=original_query,
            canonical_query=canonical_query,
            domain=domain,
            agent=agent,
            model=model_name,
            answer=answer,
            retrieved_chunk_ids=chunk_ids,
            guardrails_triggered=triggered,
            latency_ms=latency_ms,
            estimated_cost=cost,
            output_tokens=output_tokens,
            routing_confidence=routing_confidence,
            routing_reason=routing_reason,
            agents_invoked=agents_invoked,
            model_tier=model_tier,
            cache_hit=cache_hit,
            prompt_version=self._prompt_version,
            escalation_reason=escalation_reason,
            cache_bypass_reason=cache_bypass,
            budget_status=budget_status,
            budget_action=budget_action,
            screening_decision=screening_decision,
        )
        record_trace(trace)
        return RagResponse(
            answer=answer,
            trace=trace,
            blocked=blocked,
            guardrails_triggered=triggered,
            agent=agent,
            domain=domain,
            cache_hit=cache_hit,
            model=model_name,
            estimated_cost=cost,
            cache_bypass_reason=cache_bypass,
            budget_status=budget_status,
            budget_action=budget_action,
            screening_decision=screening_decision,
        )
