# SimIoT

Plataforma web educacional para laboratórios de IoT. Ver [proposta.md](proposta.md) para a descrição conceitual completa.

## Stack

- **Backend**: Python 3.11+ · FastAPI · Docker SDK
- **Frontend**: Vue 3 · TypeScript · Vite
- **Orquestração**: Docker socket (execução local)
- **Mensageria**: Eclipse Mosquitto
- **Processamento**: Node-RED
- **Firmware**: `espressif/idf` (build) + QEMU ESP32 (emulação)

## Estrutura do repositório

```
backend/       API FastAPI que orquestra containers via Docker SDK
frontend/      SPA Vue 3 + TS (editor, canvas, dashboards)
containers/    Dockerfiles e configs dos serviços auxiliares
```

## Rodando em desenvolvimento

Pré-requisitos: Python 3.11+, Node 20+, Docker Desktop.

### 1. Serviços auxiliares (Mosquitto + Node-RED)

```bash
docker compose -f docker-compose.dev.yml up -d
```

- MQTT TCP: `localhost:1883`
- MQTT WebSocket: `localhost:9001`
- Node-RED: http://localhost:1880

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs OpenAPI: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

### 4. Imagem ESP-IDF (pré-pull recomendado)

O build do firmware usa `espressif/idf:release-v5.4`. A imagem tem ~3 GB — o primeiro build vai baixar isso, então é útil puxar antes para separar "download lento" de "compilação":

```bash
docker pull espressif/idf:release-v5.4
```

Depois disso, um build típico de `hello-world` leva ~2–4 min na primeira vez (configuração do CMake) e alguns segundos nas seguintes. Os artefatos ficam em `backend/.simiot-work/builds/<build_id>/` para serem reusados pela execução em QEMU.

### 5. Imagem QEMU ESP32 (build local)

A execução dos nós usa uma imagem customizada que estende `espressif/idf:release-v5.4` e instala o fork QEMU Xtensa via `idf_tools`:

```bash
docker build -t simiot/esp32-qemu:latest containers/esp32-qemu/
```

O build leva alguns minutos na primeira vez (download do binário do QEMU). Depois disso, clicar "executar" no frontend sobe um container desse tipo montando o workdir do último build bem-sucedido e expõe o serial da ESP32 emulada via `docker logs`.

> **Nota**: esta etapa (2A) só cobre serial log. A rede QEMU → Mosquitto entra na próxima etapa.

## Roadmap

Ver [proposta.md](proposta.md) para o detalhamento. Em alto nível:

- **Fase 1 (atual)**: CRUD de projetos, editor de firmware, build ESP-IDF, um nó QEMU, Mosquitto, Node-RED, logs
- **Fase 2**: canvas visual de topologia, múltiplos nós, templates, viewer de tópicos MQTT
- **Fase 3**: persistência temporal, dashboards avançados, clonagem de experimentos
- **Fase 4**: integração com hardware físico (flash/monitor)
