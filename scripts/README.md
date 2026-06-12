# Scripts

Utilitários operacionais e de manutenção do harness (ingestão em lote, execução
do Evaluation Harness, exportação de relatórios FinOps, etc.).

Convenções:

- Scripts em Python devem reutilizar os serviços de `app/` (sem duplicar lógica).
- Configuração sempre via `app.core.config.get_settings()` (nunca ler env direto).
- Cada script deve ser idempotente e logar de forma estruturada (`get_logger`).

Exemplos de scripts previstos para a Fase 4:

- `ingest_corpus.py` — ingere o corpus de `datasets/` na base de conhecimento.
- `run_evaluation.py` — roda o golden dataset e imprime o relatório agregado.
