# Job Aggregator (Streamlit)

Lightweight job-aggregator that queries SerpAPI (Google Jobs), normalizes results, and displays them in a Streamlit UI. Optional local Ollama LLM can summarize descriptions and extract skills.

Quickstart

1. Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set `SERPAPI_API_KEY` and `OLLAMA_HOST` if using LLM.

3. Run the app:

```bash
streamlit run app.py
```

Notes
- The app calls SerpAPI (`engine=google_jobs`) — ensure your key has access.
- Ollama integration is optional; if the local server is unavailable, the app falls back to raw text.

Project layout

- `app.py` — Streamlit UI
- `services/serpapi_client.py` — SerpAPI wrapper
- `services/llm_service.py` — Ollama wrapper with graceful fallback
- `services/job_normalizer.py` — Normalize raw results into `Job` model
- `models/job.py` — `@dataclass` for normalized job
- `utils/validators.py` — simple input validators
