# Analise do Repositorio SimIoT

Data da analise: 2026-04-21

## Visao geral

O repositorio ja materializa um MVP da Fase 1 proposta em `README.md` e `proposta.md`:

- backend em FastAPI para CRUD de projetos, edicao de firmware, build e execucao
- frontend em Vue 3 + TypeScript com tela unica para listar projetos, editar firmware, acompanhar builds e rodar QEMU
- infraestrutura auxiliar com Mosquitto e Node-RED via Docker Compose
- imagem Docker dedicada para execucao de firmware ESP32 emulado via QEMU

O projeto esta coerente com a proposta conceitual e ja demonstra o fluxo principal:

1. criar projeto
2. carregar firmware default
3. salvar firmware
4. compilar em container `espressif/idf`
5. executar em container `simiot/esp32-qemu`
6. acompanhar logs no frontend

## Estrutura atual

### Backend

- `backend/app/main.py`: sobe a API, CORS e registra rotas
- `backend/app/api/projects.py`: CRUD basico de projetos
- `backend/app/api/firmware.py`: firmware por projeto e historico de builds
- `backend/app/api/run.py`: execucao e parada do no QEMU
- `backend/app/services/builder.py`: escrita dos arquivos e build em container ESP-IDF
- `backend/app/services/runner.py`: start/stop do container QEMU e stream de logs
- `backend/app/services/templates.py`: firmware seed default

### Frontend

- `frontend/src/App.vue`: shell principal com status do backend e alternancia entre lista e detalhe
- `frontend/src/components/ProjectList.vue`: criacao, listagem e remocao de projetos
- `frontend/src/components/ProjectDetail.vue`: editor de arquivos, build, historico e execucao
- `frontend/src/api.ts`: cliente HTTP tipado para a API

### Infraestrutura

- `docker-compose.dev.yml`: Mosquitto + Node-RED na rede `simiot-net`
- `containers/mosquitto/mosquitto.conf`: broker aberto para dev, com listener TCP e WebSocket
- `containers/esp32-qemu/Dockerfile`: imagem de execucao baseada em `espressif/idf:release-v5.4`

## O que ja funciona bem

- A divisao backend/frontend/containers esta limpa e facil de evoluir.
- O frontend compila em producao com sucesso via `npm run build`.
- A ideia do firmware seed default e boa para onboarding e demos.
- O uso de workdir persistido para reaproveitar artefatos de build facilita a execucao posterior em QEMU.
- A composicao Mosquitto + Node-RED + QEMU atende bem ao objetivo didatico do projeto.

## Pontos de atencao

### 1. Estado totalmente em memoria

Projetos, firmware, builds, runs e referencias a containers ficam em dicionarios globais Python. Isso torna o MVP simples, mas cria limites imediatos:

- tudo se perde quando o backend reinicia
- multiplos workers/processos quebram consistencia
- nao ha trilha de auditoria nem reprodutibilidade real entre sessoes

Arquivos envolvidos:

- `backend/app/api/projects.py`
- `backend/app/api/firmware.py`
- `backend/app/api/run.py`

### 2. Falta de limpeza de recursos ao remover projeto

Ao excluir um projeto, apenas `_projects` e limpo. Builds, firmware, execucoes, containers em memoria e artefatos em disco podem ficar orfaos.

Impacto:

- crescimento de lixo em `.simiot-work`
- possibilidade de container continuar existindo sem projeto correspondente
- divergencia entre estado visivel na UI e estado real do backend/docker

### 3. Escrita de arquivos sem validacao de caminho

Os caminhos recebidos do frontend sao gravados diretamente no filesystem de build. Sem sanitizacao, um caminho malformado pode escapar do diretorio de build usando `..`.

Impacto:

- risco de sobrescrita de arquivos fora do projeto de firmware
- superficie de ataque desnecessaria mesmo em ambiente local

Arquivos envolvidos:

- `backend/app/api/firmware.py`
- `backend/app/services/builder.py`

### 4. Concorrencia sem controle explicito

Builds usam `BackgroundTasks` e runs usam `threading.Thread`, ambos atualizando objetos compartilhados em memoria e acumulando logs por concatenacao de string.

Impacto:

- risco de race condition
- logs inconsistentes em cenarios paralelos
- dificuldade de evoluir para varias execucoes simultaneas ou SSE/WebSocket

### 5. Acoplamento alto entre rotas

As rotas compartilham estado importando estruturas privadas de outros modulos (`_projects`, `_builds`, `_project_builds`). Isso funciona no MVP, mas mistura camada HTTP com armazenamento e orquestracao.

Impacto:

- testes mais dificeis
- manutencao mais sensivel
- refatoracoes futuras com maior custo

### 6. Ambiente backend nao esta pronto localmente

O ambiente virtual existente em `backend/.venv` tem apenas o pacote local instalado. Dependencias como `fastapi`, `docker`, `pytest` e `ruff` nao estao disponiveis no momento da analise.

Impacto:

- backend nao sobe imediatamente nesse ambiente
- nao foi possivel executar `pytest` nem `ruff`

### 7. Ausencia de testes automatizados

Nao ha suite de testes no repositorio para garantir:

- CRUD de projetos
- validacao de firmware
- fluxo de build
- regras de execucao/parada
- comportamento basico do frontend

Para a proxima fase, isso vira risco de regressao rapido.

### 8. Indicio de problema de encoding

A leitura de arquivos no terminal mostrou varios textos com caracteres corrompidos em docs e strings de UI. Isso pode ser apenas efeito do ambiente de leitura, mas vale confirmar antes de ampliar a interface.

Observacao: esta e uma inferencia a partir da saida do terminal, nao uma confirmacao definitiva do conteudo salvo em disco.

### 9. Observacao de ambiente Git

`git status` falhou por `dubious ownership` no diretorio do repositorio. Nao e problema do codigo, mas pode atrapalhar fluxos de revisao e versionamento ate ajustar `safe.directory`.

## Maturidade por area

- Arquitetura do MVP: boa
- Fluxo principal demonstravel: bom
- Persistencia: inexistente
- Seguranca local de arquivos: fraca
- Testabilidade: baixa
- Prontidao para multiusuario: baixa
- Prontidao para evolucao de produto: media, desde que o proximo passo seja consolidacao tecnica

## Sequencia recomendada para continuar o desenvolvimento

### Etapa 1. Consolidar backend

- extrair estado em memoria para camada de repositorio/servico
- introduzir persistencia inicial para projetos, firmware e builds
- validar caminhos de arquivos de firmware
- limpar artefatos e execucoes ao excluir projeto

### Etapa 2. Melhorar observabilidade e contratos

- padronizar erros da API
- separar logs/estado de build e run em modelos mais robustos
- considerar SSE ou WebSocket para logs em vez de polling

### Etapa 3. Criar base de testes

- testes de API com FastAPI TestClient
- testes de servicos com mocks do Docker SDK
- pelo menos um teste de smoke do frontend

### Etapa 4. Evoluir UX do frontend

- metadados do projeto no detalhe
- feedback melhor para estados de salvamento/build/run
- organizacao do editor para multiplos arquivos e templates

## Sugestao objetiva de foco imediato

Se formos seguir de forma segura e com bom ritmo, eu recomendaria a seguinte prioridade:

1. persistencia minima para projetos/firmware/builds
2. saneamento de paths de firmware
3. limpeza de recursos ao remover projeto
4. testes de backend antes de expandir funcionalidades da Fase 2

## Validacoes realizadas nesta analise

- leitura da documentacao principal e da proposta
- inspecao dos principais arquivos do backend, frontend e containers
- build do frontend com sucesso via `npm run build`
- tentativa de validacao do backend bloqueada por ambiente Python sem dependencias instaladas

