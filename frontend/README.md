# MarketWave Frontend (minimal scaffold)

This is a minimal React + Vite frontend scaffold that calls the MarketWave HTTP adapter (`api_server.py`). It is intentionally small to show the end-to-end flow using real data from the local adapter.

Prerequisites
- Node 18+ and npm/yarn/pnpm
- Python environment with dependencies for running `api_server.py` (FastAPI, uvicorn, joblib, pandas)

Quick start
1. Run the backend adapter:

```powershell
python api_server.py
```

2. In `frontend/`, install dependencies and run dev server:

```powershell
cd frontend
npm ci
copy .env.example .env
npm run dev
```

3. Open http://localhost:5173 and use the UI to pick a market and commodity and run a prediction.

Notes
- The frontend expects the adapter at `VITE_API_BASE` (default http://localhost:8000). Update `.env` if your API runs elsewhere.
- This scaffold is intentionally minimal. For production, add auth, i18n, accessibility improvements, testing and CI.
