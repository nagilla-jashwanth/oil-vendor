# 🛢️ OIL Vendor Risk Management

AI-powered third-party vendor risk assessment platform built with **LangGraph**, **FastAPI**, and a clean HTML/CSS/JS frontend — optimised for AMD ROCm + vLLM cloud instances.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
│                                                         │
│  POST /api/assess                                       │
│       │                                                 │
│       ▼                                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │           LangGraph Pipeline (risk_graph)        │   │
│  │                                                  │   │
│  │  START                                           │   │
│  │    │                                             │   │
│  │    ▼                                             │   │
│  │  [intelligence_node]  ← ReAct agent              │   │
│  │    │  calls 7 tools:                             │   │
│  │    │  • web_search                               │   │
│  │    │  • financial_news_search                    │   │
│  │    │  • compliance_search                        │   │
│  │    │  • social_media_search                      │   │
│  │    │  • video_intelligence_search                │   │
│  │    │  • geopolitical_risk_search                 │   │
│  │    │  • operational_incident_search              │   │
│  │    │                                             │   │
│  │    ▼                                             │   │
│  │  [scoring_node]   ← LLM → structured JSON scores │   │
│  │    │                                             │   │
│  │    ▼                                             │   │
│  │  [mitigation_node] ← LLM → mitigation actions   │   │
│  │    │                                             │   │
│  │  END → RiskAssessment                           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Pre-configured Real Vendors

| Vendor | Ticker | Why Interesting for Risk |
|--------|--------|--------------------------|
| **ExxonMobil** | XOM | Largest US oil major; climate litigation exposure, Guyana expansion risk |
| **Shell plc** | SHEL | Anglo-Dutch; Dutch court climate ruling, LNG transition complexity |
| **Rosneft** | ROSN | Russian state-controlled; heavy sanctions exposure since 2022, OFAC risk |

---

## Step-by-Step Setup on AMD ROCm vLLM Notebook

### Prerequisites
- AMD ROCm virtual cloud notebook (MI250/MI300 GPU)
- Python 3.10+
- Internet access from the notebook

---

### Step 1 — Clone / Upload the project

In your notebook terminal:
```bash
# If using git:
git clone <your-repo-url> oil-vendor-risk
cd oil-vendor-risk

# Or upload the zip and extract:
unzip oil-vendor-risk.zip
cd oil-vendor-risk
```

---

### Step 2 — Run the setup script

```bash
bash setup.sh
```

This will:
- Create a Python virtual environment (`venv/`)
- Install all dependencies from `requirements.txt`
- Verify your `.env` file exists

---

### Step 3 — Configure your `.env`

Open `.env` in any text editor:

```bash
nano .env
```

**Option A — Use your local vLLM (recommended for AMD ROCm):**
```
USE_AZURE=false
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.3
```

**Option B — Use Azure OpenAI (if vLLM is not running):**
```
USE_AZURE=true
AZURE_OPENAI_API_KEY=sk-...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
```

---

### Step 4 — Start vLLM (if using local model)

**Open a NEW terminal tab** and run:

```bash
cd oil-vendor-risk
bash start_vllm.sh
```

Wait until you see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

This takes 1–3 minutes to download/load the model weights.

**Verify it's working:**
```bash
curl http://localhost:8000/v1/models
```

---

### Step 5 — Start the FastAPI application

**In your original terminal:**
```bash
source venv/bin/activate
bash run.sh
```

You'll see:
```
══════════════════════════════════════════════════════
  OIL Vendor Risk Management
  http://0.0.0.0:7860
══════════════════════════════════════════════════════
```

---

### Step 6 — Open the UI

In your browser navigate to:
```
http://localhost:7860
```

If using a cloud notebook with port forwarding, use the forwarded URL for port **7860**.

---

## How to Use

1. **Quick Select**: Click one of the three preset vendors (ExxonMobil, Shell, Rosneft)
2. **Custom Vendor**: Type any oil company name in the input field
3. **Click "Assess Risk"** — the pipeline runs for ~60–90 seconds
4. Review the **Risk Score**, **Category Scores**, **Findings**, **Radar Chart**, **Mitigations**, and **Sources**

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: langchain` | Run `pip install -r requirements.txt` inside `venv` |
| `Connection refused localhost:8000` | Start vLLM first: `bash start_vllm.sh` |
| Assessment returns error | Check the FastAPI terminal for full traceback |
| vLLM OOM (out of memory) | Lower `--gpu-memory-utilization 0.75` in `start_vllm.sh` |
| Slow responses | Expected — 7B model + 7 tool calls ≈ 60–120s |
| Azure 401 Unauthorized | Double-check `AZURE_OPENAI_API_KEY` and endpoint in `.env` |

---

## File Structure

```
oil-vendor-risk/
├── main.py                          # FastAPI app entry point
├── requirements.txt
├── .env                             # Your config (do not commit)
├── setup.sh                         # One-shot setup
├── start_vllm.sh                    # Start vLLM server
├── run.sh                           # Start FastAPI
├── backend/
│   ├── agents/
│   │   ├── llm_factory.py           # vLLM / Azure LLM selector
│   │   └── risk_graph.py            # LangGraph pipeline (3 nodes)
│   ├── tools/
│   │   └── search_tools.py          # 7 @tool-decorated LangChain tools
│   └── models/
│       └── schemas.py               # Pydantic models
└── frontend/
    ├── templates/index.html         # Main UI
    └── static/
        ├── css/app.css
        └── js/app.js
```
