# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aruba Wireless AI Analyzer** — an AI-powered wireless troubleshooting web app that connects to Aruba Wireless Controllers (ArubaOS 8.x / AOS 10.x) for real-time monitoring, visual analytics, AI-driven diagnosis, and one-click automated remediation via the Hermes AI Agent.

## Tech Stack

- **Backend**: Python 3.10+ / FastAPI / Uvicorn
- **Frontend**: Node.js 18+ / React (JSX) with polling-based data fetching
- **AI Agent**: Hermes Agent (self-hosted) with OpenRouter or Ollama as LLM backend
- **Infrastructure**: Docker Compose (backend on :8000, frontend on :3000, Hermes on :8080)

## Development Commands

### Docker (recommended)
```bash
docker-compose up -d                    # Start all services
docker-compose logs -f backend          # View backend logs
curl http://localhost:8080/health       # Check Hermes Agent health
```

### Backend (manual)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Swagger docs at http://localhost:8000/docs
```

### Frontend (manual)
```bash
cd frontend
npm install
npm run dev
```

## Architecture

### Three-service architecture
```
Frontend (React) ←→ Backend (FastAPI) ←→ Aruba Controller REST API
                        ↕
                   Hermes AI Agent ←→ LLM (OpenRouter/Ollama)
```

The frontend polls the backend for controller data and sends remediation requests. The backend wraps Aruba Controller REST API calls and delegates AI analysis/execution to Hermes. Hermes tools execute SSH or REST commands back to the controller.

### Backend structure (`backend/app/`)
- **`main.py`** — FastAPI entrypoint
- **`config.py`** — Loads all settings from environment variables
- **`routers/`** — API endpoints: `clients.py`, `access_points.py`, `events.py`, `remediation.py`
- **`services/`** — Core logic: `aruba_client.py` (REST API wrapper), `hermes_agent.py` (AI interface), `analyzer.py` (rule-based pre-analysis)
- **`models/`** — Data models: `client.py`, `ap.py`, `issue.py`

### Frontend structure (`frontend/src/`)
- **`pages/`** — `Dashboard.jsx` (main), `ClientDetail.jsx` (drill-down), `AuditLog.jsx` (history)
- **`components/`** — Charts (`RSSIChart.jsx`, `ChannelHeatmap.jsx`), data views (`ClientTable.jsx`, `APHealthCard.jsx`), AI panels (`AIInsightPanel.jsx`, `AlertPanel.jsx`, `ResolveButton.jsx`)
- **`hooks/`** — `useAruba.js` (controller polling), `useHermes.js` (AI interaction)

### Hermes Agent (`hermes/`)
- **`agent_config.yaml`** — Tool and LLM configuration
- **`tools/`** — `aruba_ssh.py` (SSH executor), `aruba_rest_action.py` (REST config push), `log_analyzer.py` (log parsing)
- **`prompts/`** — System persona and remediation template prompts

## Key Integration Details

### Aruba Controller REST API
- Login: `POST /v1/api/login` (returns session ID)
- Monitoring: `/v1/monitoring/clients`, `/v1/monitoring/aps`, `/v1/monitoring/ap_rf_summary`, `/v1/monitoring/events`
- Configuration: `/v1/configuration/object/wlan_ssid_profile`
- Port 4343 HTTPS, SSL verification optional for lab environments

### Alert Thresholds (configurable via `.env`)
- `ALERT_RSSI_THRESHOLD` (default -75 dBm) — triggers low RSSI alerts
- `ALERT_CHANNEL_UTIL_THRESHOLD` (default 80%) — triggers high channel utilization alerts
- `POLL_INTERVAL_SECONDS` (default 30) — controller data polling rate

### Hermes Agent
- Configured via `hermes/agent_config.yaml` with tool definitions pointing to Python modules in `hermes/tools/`
- LLM settings: temperature 0.2 (low, for consistent technical output), max_tokens 2048
- Tools: `aruba_rest_action` (config push), `aruba_ssh_command` (show/debug), `analyze_event_log` (log parsing), `get_client_details` (client stats)

## Environment Variables

All configuration lives in `.env` (copy from `.env.example`). Critical groups:
- **Aruba Controller**: `ARUBA_CONTROLLER_HOST`, `ARUBA_CONTROLLER_PORT`, `ARUBA_USERNAME`, `ARUBA_PASSWORD`, `ARUBA_API_VERSION` (v1 or v8)
- **Hermes**: `HERMES_AGENT_URL`, `HERMES_API_KEY`
- **LLM**: `LLM_PROVIDER` (openrouter/ollama), provider-specific keys and model names
- **App**: `POLL_INTERVAL_SECONDS`, `ALERT_RSSI_THRESHOLD`, `ALERT_CHANNEL_UTIL_THRESHOLD`, `LOG_LEVEL`
