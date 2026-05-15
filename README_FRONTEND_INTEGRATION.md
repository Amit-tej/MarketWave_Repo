How to integrate the built frontend into MarketWave backend

1. Build frontend

```powershell
cd frontend
npm ci
npm run build
```

2. Copy built files to backend static folder

This project currently does not include a dedicated static-serving path. A recommended location is `backend/static/frontend` or `public/frontend` depending on how you choose to serve static files.

Example (copy to `backend_static` folder in repo root):

```powershell
mkdir backend_static
cp -r frontend/dist/* backend_static/
```

3. Serve static files

If you later add a simple Flask/FastAPI wrapper to serve static files, configure it like this (example snippet):

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
app = FastAPI()
app.mount('/', StaticFiles(directory='backend_static', html=True), name='frontend')
```

4. Deploy
- If the backend will run on a server, make sure the server route and static paths are configured so the frontend can reach the API at `/predict` etc.

Notes
- The frontend communicates to `http://localhost:8000` by default. If you deploy the backend under a different base URL, change the `VITE_API_BASE` env variable before building.
- For production, prefer serving static files via a CDN or the application server with caching headers.
