# OIL VRM — Oil Vendor Risk Management System

AI-powered multi-agent platform that assesses third-party risk for oil vendors using
LangGraph, FastAPI, and a local vLLM inference server (AMD ROCm).

---

## Architecture Overview

```
Browser (React + Vite)
       │  SSE stream  │  REST
       ▼              ▼
   FastAPI (port 8080)
       │
   LangGraph State Machine
       │
   ┌───┴─────────────────────────────────┐
   │ financial_agent → operational_agent  │
   │ → compliance_agent → social_agent    │
   │ → aggregator_node → END              │
   └──────────────────────────────────────┘
       │
   Tool calls (7 tools)
   • WebSearchTool        – DuckDuckGo web search
   • NewsSearchTool       – DuckDuckGo news
   • SocialMediaSearchTool– X / Reddit via DDG
   • YouTubeSearchTool    – YouTube via DDG
   • RegulatorySearchTool – SEC / EPA / OSHA
   • FinancialDataTool    – Credit, earnings, debt
   • OperationalRiskTool  – Incidents, spills
       │
   vLLM (port 8000, AMD GPU / ROCm)
   Model: mistralai/Mistral-7B-Instruct-v0.3
```

Real-world oil vendors included by default:
- **Valero Energy Corporation** (USA, Refining & Marketing)
- **Suncor Energy** (Canada, Integrated Oil & Gas)
- **Petrobras** (Brazil, National Oil Company)

---

## Step-by-Step Setup on AMD GPU Cloud Notebook

> These instructions assume you are on the default AMD ROCm + vLLM notebook
> instance. You will need 3 terminals (or 3 tmux panes).

---

### Step 1 — Verify your environment

Open a terminal and run:

```bash
# Check ROCm
rocm-smi

# Check Python version (needs 3.10+)
python3 --version

# Check if vLLM is already installed
python3 -c "import vllm; print(vllm.__version__)"
```

If vLLM is not installed:

```bash
pip install vllm --extra-index-url https://download.pytorch.org/whl/rocm6.0
```

---

### Step 2 — Upload the project

If you are using Jupyter or a file manager, upload the entire `oil-vendor-risk/`
folder to your home directory, e.g. `/home/user/oil-vendor-risk/`.

Or clone/copy it via the terminal.

---

### Step 3 — Set up the Python backend

```bash
cd ~/oil-vendor-risk/backend

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up .env
cp .env.example .env
```

Open `.env` and verify/edit:

```
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL=mistralai/Mistral-7B-Instruct-v0.3
BACKEND_PORT=8080
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

### Step 4 — Install Node.js (if not already available)

```bash
# Check if node is installed
node --version   # needs v18+

# If not installed:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

---

### Step 5 — Start vLLM (Terminal 1)

```bash
cd ~/oil-vendor-risk
bash start_vllm.sh
```

Wait until you see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

This downloads the model on first run (~14 GB). Subsequent starts are fast.

**Low VRAM alternative** (if you have < 16 GB GPU VRAM):
```bash
bash start_vllm.sh TinyLlama/TinyLlama-1.1B-Chat-v1.0
# Then edit .env: VLLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

---

### Step 6 — Start the FastAPI backend (Terminal 2)

```bash
cd ~/oil-vendor-risk/backend
source .venv/bin/activate
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```

Test it:
```bash
curl http://localhost:8080/health
```

---

### Step 7 — Start the React frontend (Terminal 3)

```bash
cd ~/oil-vendor-risk/frontend
npm install          # first time only, downloads packages
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in 800ms
  ➜  Local:   http://localhost:5173/
```

---

### Step 8 — Open the application

In your browser (or Jupyter Lab's built-in browser), navigate to:

```
http://localhost:5173
```

You will see the OIL VRM dashboard.

**To run an assessment:**
1. Click one of the pre-loaded vendors (Valero, Suncor, or Petrobras), or type a custom vendor name.
2. Click **Start Risk Assessment**.
3. Watch the live Agent Activity Feed as each specialist agent runs.
4. The full risk report appears once all agents complete (typically 2–5 minutes).

---

## Accessing from outside the notebook

If your AMD cloud notebook exposes a public URL (e.g. through a proxy or tunnel),
you may need to:

```bash
# Option A: Use SSH port forwarding from your local machine
ssh -L 5173:localhost:5173 -L 8080:localhost:8080 user@your-amd-instance

# Option B: Use a cloudflare tunnel (no auth needed)
pip install cloudflared
cloudflared tunnel --url http://localhost:5173
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: langchain` | Run `pip install -r requirements.txt` inside the venv |
| `Connection refused 8000` | vLLM hasn't finished starting yet; wait ~60s |
| `CUDA out of memory` on AMD | Add `--quantization awq` to start_vllm.sh or use a smaller model |
| Empty agent response (JSON parse error) | The model produced malformed JSON; try a larger model |
| `CORS error` in browser | Make sure `CORS_ORIGINS` in `.env` matches your frontend URL |
| `duckduckgo_search` rate limit | Add `time.sleep(2)` between tool calls or reduce `max_results` |
| Frontend shows white page | Run `npm install` in the `frontend/` folder |

---

## Project structure

```
oil-vendor-risk/
├── backend/
│   ├── agents/
│   │   └── risk_graph.py      ← LangGraph state machine + all agent nodes
│   ├── tools/
│   │   └── search_tools.py    ← 7 LangChain BaseTool subclasses
│   ├── models/
│   │   └── schemas.py         ← Pydantic models + vendor list
│   ├── main.py                ← FastAPI app + SSE streaming endpoint
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── VendorSelector.jsx
│   │   │   ├── AgentFeed.jsx        ← Live SSE event feed
│   │   │   ├── RiskScoreCard.jsx    ← Gauge + category bars
│   │   │   ├── RiskSignalsTable.jsx ← Filterable signals table
│   │   │   ├── MitigationPanel.jsx  ← Expandable action cards
│   │   │   └── ExecutiveSummary.jsx ← Text + radar chart
│   │   ├── utils/api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── start_vllm.sh
├── start_backend.sh
├── start_frontend.sh
└── README.md
```

---

## Customisation

**Add a new vendor to the quick-pick list:**
Edit `backend/models/schemas.py` → `KNOWN_OIL_VENDORS`.

**Change the LLM model:**
Edit `VLLM_MODEL` in `backend/.env` and restart both vLLM and the backend.

**Add a new tool:**
1. Create a new `BaseTool` subclass in `backend/tools/search_tools.py`.
2. Add it to the appropriate specialist agent's tool list in `backend/agents/risk_graph.py`.

**Tune risk scoring:**
Edit the `AGGREGATOR_SYSTEM_PROMPT` in `backend/agents/risk_graph.py` to adjust
category weightings.
