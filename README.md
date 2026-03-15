# ♻️ ReCraft AI

> **GenAI Genesis 2026 — Google Best Sustainability AI Hack Submission**  
> Turn trash into treasure with multimodal AI — upload a photo, get DIY upcycling ideas, AI-generated product visualisations, market price estimates, and publish to a community marketplace.

---

## 🌱 Inspiration

Over **2 billion tonnes of waste** are generated globally each year, with less than 20% recycled. ReCraft AI bridges the gap between discarded materials and the circular economy by making upcycling **accessible, visual, and economically rewarding** using generative AI.

## ✨ What It Does

1. **Upload** a photo of any household waste (plastic bottle, cardboard box, glass jar…)
2. **AI identifies** the material using Qwen2.5-VL multimodal vision (via HuggingFace)
3. **Generates** a 5-step DIY upcycling project tailored to that material using gpt-oss-120b
4. **Visualises** the finished product using Flux-1 photorealistic image generation
5. **Estimates** the resale price with a gpt-oss-120b pricing agent (structured JSON)
6. **Publishes** the creation to a shared Community Marketplace wall

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI (Python) |
| Hosting | Replit |
| AI Orchestration | Custom pipeline (Railtracks-inspired) |
| Material ID | Qwen2.5-VL-72B-Instruct (HuggingFace) |
| DIY Generation | gpt-oss-120b (HuggingFace vLLM) |
| Image Generation | Flux-1 Pro (Black Forest Labs) |
| Image Editing | Flux-2 Kontext Pro |
| Pricing Agent | gpt-oss-120b (HuggingFace vLLM) |
| Language | Python 3.11 |

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- API keys: HuggingFace, Flux (Black Forest Labs) — OpenAI key optional (only needed if using OpenAI directly)

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

Open [http://localhost:8501](http://localhost:8501)

### Replit Deployment

1. Import this repo into Replit
2. Add secrets in **Replit Secrets** (Tools → Secrets):
   - `HUGGINGFACE_API_KEY`
   - `FLUX_API_KEY`
   - `GPT_OSS_BASE_URL`
3. Click **Run** — FastAPI starts automatically via `.replit` config
4. Deploy Streamlit separately (Streamlit Community Cloud) pointing `API_BASE_URL` to your Replit URL

### Environment Variables

| Variable | Description | Where to get |
|----------|-------------|-------------|
| `HUGGINGFACE_API_KEY` | HuggingFace API key (for Qwen-VL + gpt-oss) | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| `GPT_OSS_BASE_URL` | HuggingFace vLLM endpoint for gpt-oss-120b | Your HuggingFace Inference Endpoint URL |
| `FLUX_API_KEY` | Flux image generation key | [api.bfl.ml](https://api.bfl.ml) |
| `FLUX_API_URL` | Flux base URL (default set) | `https://api.bfl.ml/v1` |
| `API_BASE_URL` | FastAPI backend URL | Your Replit URL |

## 📁 Project Structure

```
recraft-ai/
├── frontend/
│   └── app.py                  # Streamlit UI
├── backend/
│   └── main.py                 # FastAPI routes + CORS + marketplace state
├── agents/
│   ├── upcycle_agent.py        # Qwen2.5-VL + gpt-oss-120b: identify + DIY pipeline
│   ├── pricing_agent.py        # gpt-oss-120b: structured JSON price estimate
│   └── image_agent.py          # Flux-1/Flux-2: image generation + editing
├── .env.example                # Environment variable template
├── .replit                     # Replit deployment config
├── requirements.txt
└── README.md
```

## 👥 Team

| Member | Role |
|--------|------|
| Member 1 | PM & Pitch Lead |
| Member 2 | Frontend UI (Streamlit) |
| Member 3 | Backend & Cloud (FastAPI + Replit) |
| Member 4 | AI Orchestrator (Agents + Prompts) |

## 🤖 AI Use Declaration

> More than **70%** of this project's code was generated with the assistance of AI tools (Google Gemini, GitHub Copilot). All prompts, agent logic, and UI code were AI-assisted as part of the hackathon's AI-first development philosophy.

## 📄 License

MIT License — See [LICENSE](LICENSE)
