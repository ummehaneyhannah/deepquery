# DeepQuery

An AI-powered research agent that answers questions by searching the web,
reading sources in full, and citing where each claim comes from.

## How it works

1. You ask a question through the web UI.
2. The agent (backend) plans what to search for.
3. It searches the web (Tavily API) and reads the most promising source in full.
4. It writes a concise answer with an inline citation to the source URL.

## Tech stack

- **Backend:** Python, FastAPI, Groq (Llama 3.3) for reasoning + tool-calling
- **Frontend:** React, Vite, Tailwind CSS
- **Search:** Tavily API

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

## Environment variables

See `backend/.env.example` for the required keys (Groq API key, Tavily API key).

## Status

Working MVP — core research loop (search, fetch, cite) is functional.
Not yet deployed publicly; runs locally.