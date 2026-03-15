# ♻️ ReCraft AI

> **GenAI Genesis 2026 — Google Best Sustainability AI Hack Submission**  
> Turn trash into treasure with multimodal AI — upload a photo, get DIY upcycling ideas, AI-generated product visualisations, market price estimates, and publish to a community marketplace.

---

## 1. Project Overview

Over **2 billion tonnes of waste** are generated globally each year, with less than 20% recycled. ReCraft AI bridges the gap between discarded materials and the circular economy by making upcycling **accessible, visual, and economically rewarding** using generative AI.

### What It Does
1. **Upload** a photo of any household waste (plastic bottle, cardboard box, glass jar...)
2. **AI identifies** the material using Qwen2.5-VL-72B-Instruct multimodal vision.
3. **Generates** a 5-step DIY upcycling project tailored to that material using gpt-oss-120b.
4. **Visualises** the finished product using Flux / Hugging Face photorealistic image generation.
5. **Estimates** the resale price with a gpt-oss-120b pricing agent (structured JSON) to incentivize the circular economy.
6. **Publishes** the creation to a shared Community Marketplace wall.

---

## 2. Setup Instructions

### Prerequisites
- Python 3.11+
- API keys & Endpoints: 
  - Hugging Face API Key (for Qwen-VL router & custom Endpoints)
  - Hugging Face Inference Endpoint URL (for `gpt-oss-120b`)
  - Hugging Face Image Generation Endpoint URL (custom FLUX endpoint)
  - *Note: Direct OpenAI API keys are not required as the OpenAI SDK is only used as a client for Hugging Face endpoints.*

### Local Development

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_ORG/recraft-ai.git
cd recraft-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and fill in your API keys

# 4. Start the FastAPI backend (Terminal 1)
cd backend
uvicorn main:app --reload --port 8000

# 5. Start the Streamlit frontend (Terminal 2)
cd frontend
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Replit Deployment

1. Import this repo into Replit.
2. Add secrets in **Replit Secrets** (Tools → Secrets):
   - `HUGGINGFACE_API_KEY`
   - `FLUX_API_KEY`
   - `GPT_OSS_BASE_URL`
3. Click **Run** — FastAPI starts automatically via `.replit` config.
4. Deploy Streamlit separately (Streamlit Community Cloud) pointing `API_BASE_URL` to your Replit URL.

### Environment Variables

| Variable | Description | Where to get |
|----------|-------------|-------------|
| `HUGGINGFACE_API_KEY` | Hugging Face API key (for models/endpoints) | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| `GPT_OSS_BASE_URL` | Hugging Face Inference Endpoint URL (gpt-oss-120b) | Your Hugging Face Inference Endpoint |
| `API_BASE_URL` | FastAPI backend URL | Your Replit URL / Localhost |

---

## 3. Project Structure & Functionality

ReCraft AI is built with a **FastAPI** backend handling state and AI orchestration, and a **Streamlit** frontend providing an interactive user interface. Data is persisted using an embedded **SQLite** database.

### Core Technologies
- **Backend:** FastAPI, SQLite, Pydantic, Uvicorn
- **Frontend:** Streamlit
- **AI Models:** Qwen2.5-VL-72B-Instruct, gpt-oss-120b, Hugging Face Image Generation
- **Cloud/Hosting:** Replit (Backend), Streamlit Community Cloud (Frontend)

### Directory Structure & Functional Modules

```text
recraft-ai/
├── frontend/                   # Streamlit Frontend Setup
│   ├── app.py                  # Main UI entry point & routing
│   └── pages/                  # Streamlit multi-page routing (Login, DIY Studio, Marketplace, Profile)
├── backend/                    # FastAPI Server & DB Setup
│   ├── main.py                 # Core API routing (auth, marketplace, generation API) 
│   ├── database.py             # Embedded SQLite integration, persistence queries, and seeding
│   └── auth.py                 # Basic JWT authentication, session modeling, and user management
├── agents/                     # Custom AI Orchestration Pipeline
│   ├── analyze_agent.py        # Object & material detection logic using Qwen2.5-VL
│   ├── upcycle_agent.py        # Uses gpt-oss-120b to create step-by-step DIY plans
│   ├── image_agent.py          # Post-requests to Hugging Face endpoint to generate images
│   └── pricing_agent.py        # Generates structured JSON market price estimates
├── .env.example                # Templates for local API keys
├── .replit                     # Config needed strictly for Replit host deployment
└── requirements.txt            # Specifies exact library dependencies (Python 3.11)
```

---

*👥 **AI Use Declaration:** More than 70% of this project's code was generated with the assistance of AI tools (Google Antigravity, Google Gemini, GitHub Copilot).
