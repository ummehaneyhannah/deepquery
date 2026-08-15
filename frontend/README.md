# DeepQuery

An AI-powered research agent that answers questions by searching the web,
reading sources in full, and citing where each claim comes from. Supports
multi-turn conversations, image generation, and RAG-based Q&A over
uploaded PDFs — so you can ask follow-up questions naturally, generate
visuals, and discuss documents in depth.

**Live app:** https://deepquery-mu.vercel.app

## How it works

1. You ask a question through the web UI (or attach a PDF first).
2. The agent plans what to search for, or — for PDFs — retrieves the
   most relevant excerpts using TF-IDF-based retrieval (RAG) rather than
   stuffing the whole document into context.
3. It searches the web and reads the most promising source in full.
4. It writes a concise answer with an inline citation to the source
   (URL, or page/section for PDFs).
5. Follow-up questions reuse the same conversation, so the agent
   remembers earlier context.
6. If asked to generate an image, it uses a dedicated image-generation
   tool instead of researching.
7. If the primary LLM hits a rate limit, the backend automatically
   falls back to a secondary model to keep answering.

## Tech stack

- **Backend:** Python, FastAPI, Groq (Llama 3.3, with automatic fallback)
- **Frontend:** React, Vite, Tailwind CSS
- **Search:** Tavily API
- **Image generation:** Pollinations.ai
- **PDF Q&A:** pypdf (extraction) + scikit-learn TF-IDF (lightweight RAG retrieval)
- **PDF export:** reportlab
- **Database:** Supabase (Postgres) — persistent conversation history and PDF chunks
- **Deployment:** Render (backend), Vercel (frontend)
## Project structure
## Running locally

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
# Add your API keys to a .env file (see .env.example)
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Then open the frontend's local URL in your browser (usually `http://localhost:5173`).

Note: the frontend's `API_URL` in `src/App.jsx` points to the deployed
backend by default. Change it to `http://127.0.0.1:8000` to test against a
local backend instead.

## Environment variables

See `backend/.env.example` for the required keys (Groq API key, Tavily API key).

## Features

- Web search + full-page source reading (not just snippets)
- Inline citations for every non-obvious claim
- Multi-turn conversations (follow-up questions keep context)
- Image generation from text prompts
- PDF upload with RAG-based retrieval — ask multiple questions about a
  document, each one retrieves only the most relevant excerpts instead
  of re-sending the whole file
- Export any answer as a downloadable PDF report
- Automatic LLM fallback to a secondary model when the primary model
  hits a rate limit
- Graceful error handling throughout (network failures, rate limits,
  malformed model output, corrupt/encrypted PDFs all degrade gracefully
  instead of crashing)

## Known limitations

- Retrieval uses TF-IDF (sparse, keyword-based) rather than neural
  embeddings — a deliberate tradeoff to stay within free-tier hosting
  memory limits (loading an embedding model risks exceeding Render's
  512MB free-instance RAM). Works well for keyword-heavy queries; a
  future upgrade path would add dense vector embeddings for better
  semantic matching.
- Running on free-tier APIs (Groq, Tavily), so there are daily/per-minute
  rate limits — mitigated by automatic model fallback, but not eliminated.
- No per-user accounts or API key isolation — all users currently share
  the same backend quota and database rows are keyed only by
  conversation ID, not by user.
- Retrieval uses TF-IDF (sparse, keyword-based) rather than neural
  embeddings — a deliberate tradeoff to stay within free-tier hosting
  memory limits (loading an embedding model risks exceeding Render's
  512MB free-instance RAM). Works well for keyword-heavy queries; a
  future upgrade path would add dense vector embeddings for better
  semantic matching.
- Running on free-tier APIs (Groq, Tavily), so there are daily/per-minute
  rate limits — mitigated by automatic model fallback, but not eliminated.
- No per-user accounts or API key isolation — all users currently share
  the same backend quota.

## Status

Working product with persistent multi-turn conversation (backed by a
real database), image generation, and RAG-based PDF Q&A, deployed
publicly. Core features are functional and tested end-to-end.