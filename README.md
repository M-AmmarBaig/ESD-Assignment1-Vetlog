# Vetlog AI

Veterinary clinic AI assistant. Queries clinic WhatsApp data via natural language.

---

## Overview & Features

Vetlog AI is a comprehensive assistant designed to ingest, process, and query WhatsApp messages from veterinary clinics. 
- **AI Agentic Workflow:** Uses LangGraph to dynamically call tools (SQL queries, report generation) based on user intent.
- **WhatsApp Ingestion:** Custom Chrome extension to scrape and batch messages to the backend.
- **Multi-LLM Support:** Seamlessly switch between OpenAI, Gemini, Ollama, Groq, and more.
- **Enterprise Observability:** Fully containerized ELK stack (Elasticsearch, Loguru, Filebeat, Kibana) and Prometheus/Grafana integration for live monitoring.

---

## Setup & Configuration

### 1. Environment Variables

Create a `.env` file in the project root directory. You must configure your API keys and the database route here.
```env
# Example .env configuration
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./data/vetlog.db
```
*(Ensure the `data/` folder exists so the SQLite database can be created).*

### 2. Database

The database lives at `data/vetlog.db`. If it's empty, use the WhatsApp Chrome extension to populate it.

---

## Running the System

The entire ecosystem is containerized using Docker Compose.

### Starting the Stack
1. Open Docker Desktop.
2. Open your terminal in the project root.
3. Run the following command:
```bash
docker compose up -d
```
*(This spins up 8 containers: FastAPI, React, Prometheus, Node Exporter, Grafana, Elasticsearch, Kibana, and Filebeat).*

### Stopping the Stack
To safely shut down the system and preserve data:
```bash
docker compose down
```

---

## Accessing the Applications

| Service | URL | Notes |
|---|---|---|
| **Frontend (React)** | [http://localhost:5173](http://localhost:5173) | The main chat interface |
| **Backend (FastAPI)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation |
| **Grafana** | [http://localhost:3000](http://localhost:3000) | Hardware & metrics (Login: `admin` / `admin`) |
| **Kibana** | [http://localhost:5601](http://localhost:5601) | Log streaming and tracing |

---

## Observability & Tracing

The system is heavily instrumented to track every step of the AI's reasoning.

### Hardware & Latency (Grafana)
Grafana scrapes the `/metrics` endpoint via Prometheus and visualizes hardware utilization (Node Exporter) and request latencies. 

### Structured Logging (Kibana)
All backend logs, LLM token usages, and frontend React crashes are shipped to Elasticsearch via Filebeat in structured JSON.

**First-Time Kibana Setup:**
1. Go to `http://localhost:5601` > **Stack Management** > **Data Views**.
2. Click **Create data view**.
3. Name it `filebeat-*` and set the timestamp field to `@timestamp`.

**How to get a Clean Log UI in Kibana:**
By default, Kibana's Discover tab shows raw JSON documents. To make it readable:
1. Go to the **Discover** tab.
2. In the left sidebar, find and click the `+` icon next to **`record.level.name`**, **`record.module`**, and **`record.message`**.
3. Kibana will now look like a clean, professional logging table.

**How to Trace a Chat Request:**
1. Because `record.message` is mapped as a strict "Keyword", do not use the search bar. 
2. Instead, click **`+ Add filter`** (under the search bar).
3. Set Field to `record.message`, Operator to `is`, and Value to `Incoming request: POST /chat/stream/`.
4. Find your request, click to expand it, and scroll to `record.extra.request_id`.
5. Click the **`+` magnifying glass** next to the UUID.
6. Remove the `record.message` filter to see the exact chronological trace of that single AI request!

---

## Backend Routes (for reference)

| Route | Purpose |
|---|---|
| `/` | Health check |
| `/chat/` | Send a message (POST) |
| `/chat/stream/` | Send a message, stream response (SSE) |
| `/logs/client` | Ingest React frontend crashes |
| `/usage/` | Token/cost stats |
| `/api/config/llm` | Get/set AI provider (GET/POST) |
| `/reports/{filename}` | View or export a report |
| `/webhook/extension/batch/` | Ingest WhatsApp messages |

---

## Chrome Extension

The `whatsapp_extension/` folder is a Chrome extension that scrapes WhatsApp Web messages. To install:
1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select `whatsapp_extension/`
4. Open `https://web.whatsapp.com`, pin the extension, and scrape

---

## Testing & Load Testing

**Load Testing (Locust):**
```bash
source .venv/bin/activate
locust -f locustfile.py
```
Open `http://localhost:8089` to swarm the API.

**Unit Testing (DeepEval):**
```bash
deepeval test run tests/test_agent.py -v
```

---

## Tech Stack

- **Backend:** Python, FastAPI, LangGraph, SQLAlchemy, SQLite
- **Frontend:** React 18, Vite, Framer Motion, React Markdown
- **Observability:** Elasticsearch, Kibana, Filebeat, Loguru, Prometheus, Grafana
- **LLM providers:** Ollama, Gemini, Groq, Mistral, Cerebras, OpenRouter, OpenAI
