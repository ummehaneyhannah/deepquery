# DeepQuery

An AI-powered research agent that answers questions by searching the web,
reading sources in full, and citing where each claim comes from. Supports
multi-turn conversations, so you can ask follow-up questions naturally.

**Live app:** https://deepquery-mu.vercel.app

## How it works

1. You ask a question through the web UI.
2. The agent (backend) plans what to search for.
3. It searches the web (Tavily API) and reads the most promising source in full.
4. It writes a concise answer with an inline citation to the source URL.
5. Follow-up questions reuse the same conversation, so the agent remembers
   earlier context.

## Tech stack

- **Backend:** Python, FastAPI, Groq (Llama 3.3) for reasoning + tool-calling
- **Frontend:** React, Vite, Tailwind CSS
- **Search:** Tavily API
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
- Graceful error handling (network failures, rate limits, malformed
  model output all degrade gracefully instead of crashing)

## Known limitations

- Conversation history is stored in-memory on the backend, so it resets
  if the server restarts (e.g. Render's free tier spinning down from
  inactivity). A persistent database would fix this.
- Running on free-tier APIs (Groq, Tavily), so there are daily rate limits.
- No image generation yet.
- No user accounts — anyone with the link can use it.

## Status

Working product with multi-turn conversations, deployed publicly.
Core research loop (search, fetch, cite) is functional and tested.