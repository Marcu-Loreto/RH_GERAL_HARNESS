# Documento de Requisitos — Assistente Conversacional de RH

## Introdução

Transformação do harness de avaliação de IA de RH existente em um assistente conversacional funcional com interface separada por perfil de usuário (colaborador, RH, admin), arquitetura multiagente com escalonamento de modelos LLM por dificuldade da pergunta, e dashboards de gestão.

## Glossário

- **Sistema**: O assistente conversacional de RH como um todo (backend + frontend)
- **Agente_Recepção**: Agente responsável pela saudação inicial e triagem social do usuário
- **Agente_Orquestrador**: Agente que captura a intenção do usuário e roteia para o agente especialista correto
- **Agente_Especialista**: Agente de domínio que responde perguntas de RH usando a base de conhecimento
- **Classificador_Dificuldade**: Módulo baseado em dicionário que classifica a dificuldade da pergunta em 3 níveis (fácil, intermediário, difícil)
- **Model_Router**: Componente que seleciona o modelo LLM adequado com base no nível de dificuldade
- **Base_Conhecimento**: Corpus de documentos de RH (corpus_rh.json + documentos ingeridos)
- **Transbordo**: Escalonamento para RH humano via link JIRA quando o sistema não consegue responder
- **Colaborador**: Perfil de usuário comum (funcionário) com acesso apenas ao chat
- **Perfil_RH**: Perfil de profissional de RH com acesso a gestão de documentos e dashboard (exceto custos)
- **Perfil_Admin**: Perfil administrativo com acesso total ao sistema incluindo custos

## Requisitos

### Requisito 1: Agente de Recepção

**User Story:** Como colaborador, quero ser recebido por um agente acolhedor ao iniciar uma conversa, para que eu me sinta orientado sobre como usar o assistente.

#### Critérios de Aceitação

1. WHEN um usuário inicia uma nova sessão de chat, THE Agente_Recepção SHALL responder com uma saudação acolhedora e orientação sobre os temas disponíveis
2. WHEN o usuário envia uma mensagem social (saudação, agradecimento, despedida), THE Agente_Recepção SHALL responder de forma contextual sem acionar o pipeline de retrieval
3. WHEN o usuário envia uma mensagem com sinal de domínio de RH, THE Agente_Recepção SHALL encaminhar a mensagem ao Agente_Orquestrador sem interceptá-la
4. THE Agente_Recepção SHALL utilizar o modelo econômico (MiniMax M2.5) para todas as interações

### Requisito 2: Orquestração e Roteamento de Intenção

**User Story:** Como colaborador, quero que minha pergunta seja automaticamente direcionada ao especialista correto, para que eu receba uma resposta precisa do domínio adequado.

#### Critérios de Aceitação

1. WHEN o Agente_Orquestrador recebe uma pergunta, THE Agente_Orquestrador SHALL classificar o domínio de RH usando a Query Intelligence Layer existente
2. WHEN o domínio é identificado com confiança acima do limiar configurado, THE Agente_Orquestrador SHALL rotear a pergunta ao Agente_Especialista correspondente
3. WHEN a confiança de classificação fica abaixo do limiar, THE Agente_Orquestrador SHALL realizar uma busca ampla (fallback) sem filtro de domínio
4. WHEN nenhuma evidência é encontrada após fallback, THE Sistema SHALL acionar o mecanismo de transbordo

### Requisito 3: Classificação de Dificuldade por Dicionário

**User Story:** Como arquiteto do sistema, quero que a dificuldade das perguntas seja classificada por um filtro baseado em dicionário, para que o modelo LLM adequado seja selecionado sem custos extras de classificação.

#### Critérios de Aceitação

1. THE Classificador_Dificuldade SHALL categorizar cada pergunta em exatamente um dos três níveis: fácil, intermediário ou difícil
2. WHEN uma pergunta contém apenas termos presentes no dicionário de termos simples (ex.: "quantos dias de férias", "qual o vale refeição"), THE Classificador_Dificuldade SHALL classificá-la como fácil
3. WHEN uma pergunta contém termos do dicionário de complexidade média (ex.: "como funciona promoção", "regras de banco de horas"), THE Classificador_Dificuldade SHALL classificá-la como intermediário
4. WHEN uma pergunta contém termos sensíveis ou de alta complexidade (ex.: "assédio", "demissão por justa causa", "processo disciplinar"), THE Classificador_Dificuldade SHALL classificá-la como difícil
5. WHEN nenhum termo do dicionário é encontrado na pergunta, THE Classificador_Dificuldade SHALL classificá-la como intermediário por padrão

### Requisito 4: Escalonamento de Modelos LLM

**User Story:** Como arquiteto do sistema, quero que o modelo LLM seja selecionado com base na dificuldade da pergunta, para otimizar custo e qualidade de resposta.

#### Critérios de Aceitação

1. WHEN a pergunta é classificada como fácil, THE Model_Router SHALL selecionar o modelo econômico (MiniMax M2.5)
2. WHEN a pergunta é classificada como intermediário, THE Model_Router SHALL selecionar o modelo intermediário (GPT-4o-mini)
3. WHEN a pergunta é classificada como difícil, THE Model_Router SHALL selecionar o modelo robusto (GPT-4o)
4. IF o modelo selecionado estiver indisponível, THEN THE Model_Router SHALL realizar fallback para o próximo modelo disponível
5. THE Model_Router SHALL registrar em log o modelo selecionado, o nível de dificuldade e o custo estimado para cada interação

### Requisito 5: Geração de Resposta com Base de Conhecimento

**User Story:** Como colaborador, quero receber respostas fundamentadas nos documentos oficiais de RH, para que eu tenha informações confiáveis.

#### Critérios de Aceitação

1. WHEN o Agente_Especialista recebe uma pergunta roteada, THE Agente_Especialista SHALL buscar evidências relevantes na Base_Conhecimento
2. WHEN evidências são encontradas, THE Agente_Especialista SHALL gerar uma resposta baseada exclusivamente nos trechos recuperados
3. WHEN nenhuma evidência suficiente é encontrada, THE Agente_Especialista SHALL informar a limitação e sugerir transbordo para RH humano
4. THE Agente_Especialista SHALL citar as fontes (título do documento e versão) em cada resposta

### Requisito 6: Mecanismo de Transbordo

**User Story:** Como colaborador, quero ser encaminhado para o RH humano quando o sistema não puder responder, para que eu não fique sem atendimento.

#### Critérios de Aceitação

1. WHEN o sistema não encontra evidência suficiente para responder, THE Sistema SHALL gerar um link JIRA de escalonamento para a equipe de RH
2. WHEN um transbordo é acionado, THE Sistema SHALL registrar o motivo do escalonamento no trace da interação
3. WHEN um transbordo é acionado, THE Sistema SHALL informar ao usuário que sua dúvida foi encaminhada e fornecer o link de acompanhamento
4. THE Sistema SHALL contabilizar cada transbordo no dashboard de métricas

### Requisito 7: Interface do Colaborador (Tela de Chat)

**User Story:** Como colaborador, quero uma interface de chat simples e dedicada, para que eu possa fazer perguntas e receber respostas sem distrações.

#### Critérios de Aceitação

1. WHEN um colaborador acessa o sistema, THE Sistema SHALL exibir apenas a interface de chat conversacional
2. THE Sistema SHALL exibir o histórico de mensagens da sessão atual de forma cronológica
3. WHEN o colaborador envia uma mensagem, THE Sistema SHALL exibir indicador de carregamento até a resposta ser recebida
4. THE Sistema SHALL ocultar todas as funcionalidades administrativas (gestão de documentos, dashboards) para o perfil colaborador
5. WHEN a resposta contém fontes, THE Sistema SHALL exibir as referências de forma acessível abaixo da resposta

### Requisito 8: Interface do Administrador (Dashboard Completo)

**User Story:** Como administrador, quero acesso a todos os dashboards e funcionalidades de gestão, para que eu possa monitorar e controlar o sistema.

#### Critérios de Aceitação

1. WHEN um admin acessa o sistema, THE Sistema SHALL exibir o painel com todas as seções: chat, gestão de documentos e dashboards
2. THE Sistema SHALL exibir o dashboard de uso de tokens (total consumido por período)
3. THE Sistema SHALL exibir o dashboard de custos (custo por modelo, custo total por período)
4. THE Sistema SHALL exibir a contagem de sessões ativas e históricas
5. THE Sistema SHALL exibir a contagem de perguntas respondidas
6. THE Sistema SHALL exibir o total de transbordos realizados
7. WHEN o admin adiciona um documento à base de conhecimento, THE Sistema SHALL ingerir, chunkar e indexar o documento

### Requisito 9: Interface do RH (Dashboard Parcial)

**User Story:** Como profissional de RH, quero gerenciar a base de conhecimento e ver métricas de uso, para que eu possa manter o conteúdo atualizado e acompanhar a utilização.

#### Critérios de Aceitação

1. WHEN um profissional de RH acessa o sistema, THE Sistema SHALL exibir o painel com chat, gestão de documentos e dashboards (exceto custos)
2. WHEN o profissional de RH adiciona um documento, THE Sistema SHALL ingerir e indexar o documento na base de conhecimento
3. THE Sistema SHALL exibir para o Perfil_RH o dashboard de tokens, sessões, perguntas respondidas e transbordos
4. THE Sistema SHALL ocultar o dashboard de custos para o Perfil_RH
5. WHEN o profissional de RH edita ou remove um documento, THE Sistema SHALL atualizar a base de conhecimento e invalidar o cache relacionado

### Requisito 10: Gestão da Base de Conhecimento

**User Story:** Como administrador ou profissional de RH, quero adicionar, editar e remover documentos da base de conhecimento, para que o assistente sempre tenha informações atualizadas.

#### Critérios de Aceitação

1. WHEN um documento é adicionado, THE Sistema SHALL realizar parsing, chunking e indexação no vector store
2. WHEN um documento é editado, THE Sistema SHALL re-processar o documento e atualizar os chunks correspondentes
3. WHEN um documento é removido, THE Sistema SHALL excluir os chunks associados do vector store e invalidar entradas de cache relacionadas
4. THE Sistema SHALL manter versionamento dos documentos (histórico de alterações)
5. IF um documento inválido ou vazio é submetido, THEN THE Sistema SHALL rejeitar a submissão com mensagem de erro descritiva

### Requisito 11: Controle de Acesso por Perfil

**User Story:** Como arquiteto do sistema, quero que o acesso seja controlado por perfil de usuário, para que cada tipo de usuário veja apenas as funcionalidades permitidas.

#### Critérios de Aceitação

1. THE Sistema SHALL autenticar o usuário e determinar o perfil (colaborador, rh, admin) antes de servir qualquer conteúdo
2. WHEN um colaborador tenta acessar rotas administrativas, THE Sistema SHALL retornar erro 403 (acesso negado)
3. WHEN um profissional de RH tenta acessar a rota de custos, THE Sistema SHALL retornar erro 403
4. THE Sistema SHALL propagar o perfil do usuário em todas as requisições ao backend via contexto autenticado
