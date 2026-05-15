# MarketWave - Complete Application Setup & Testing Guide

## ✅ System Status

### Backend API Server
- **Status**: ✓ Running on `http://localhost:8000`
- **Framework**: FastAPI + Uvicorn
- **Process**: Python api_server.py
- **Health Check**: `GET http://localhost:8000/health` → `{"status": "ok"}`

### Frontend Dev Server
- **Status**: ✓ Running on `http://localhost:5173`
- **Framework**: React 18 + TypeScript + Vite
- **Build Tool**: Vite 5.4.21
- **Hot Reload**: Enabled

---

## 🚀 Quick Start

### Automated Startup (Recommended)
```powershell
cd "c:\Users\HP\OneDrive\Desktop\marketwave 2.0"
.\START_MARKETWAVE.ps1
```

### Manual Startup

**Terminal 1 - API Server:**
```powershell
cd "c:\Users\HP\OneDrive\Desktop\marketwave 2.0"
python api_server.py
```

**Terminal 2 - Frontend:**
```powershell
cd "c:\Users\HP\OneDrive\Desktop\marketwave 2.0\frontend"
npm run dev
```

---

## 📋 API Endpoints

### Health Check
```
GET /health
Response: {"status": "ok"}
```

### List Markets
```
GET /markets
Response: {"markets": ["Bowenpally", "Erragadda(Rythu_Bazar)", "Gudimalkapur", ...]}
```

### List Commodities by Market
```
GET /markets/{market}/commodities
Response: {"commodities": ["Brinjal", "Green Chilli", "Onion", "Potato", "Tomato"]}
```

### Create Prediction
```
POST /predict
Request Body:
{
  "market": "Bowenpally",
  "commodity": "Brinjal",
  "horizon": 30,
  "force_simple": false
}

Response:
{
  "prediction_id": "ensemble_Brinjal_Bowenpally.joblib_1731310234",
  "yhat": [45.2, 46.1, 45.8, ...],
  "intervals": {
    "lower": [[42.1, 43.2, ...], ...],
    "upper": [[48.3, 49.0, ...], ...]
  },
  "base_preds": {
    "xgb": [45.0, 45.9, ...],
    "prophet": [45.5, 46.2, ...],
    ...
  }
}
```

### Get Explainability
```
GET /predictions/{prediction_id}/explain
Response:
{
  "model_metadata": {"model_name": "xgboost", "path": "..."},
  "global_importance": [
    {"feature": "lag_7", "importance": 0.35},
    {"feature": "rolling_30", "importance": 0.28},
    ...
  ],
  "local": []
}
```

---

## 🧪 Frontend Testing Checklist

### 1. Navigation & Layout
- [ ] Sidebar appears with all navigation links (Predict, Compare, Analysis, Insights, Resources)
- [ ] Navbar shows title and status indicator
- [ ] Layout is responsive and clean

### 2. Predict Page
- [ ] Market dropdown populates with real markets
- [ ] Commodity dropdown updates when market changes
- [ ] Horizon input accepts numbers (default 30)
- [ ] "Predict" button triggers prediction
- [ ] Loading state shows while prediction is in progress
- [ ] Forecast chart displays with actual (blue) and predicted (green) lines
- [ ] Confidence intervals shown correctly
- [ ] Explainability panel shows feature importance

### 3. Compare Page
- [ ] Market comparison loads data
- [ ] Bar chart displays top commodities/markets
- [ ] Sorting works correctly

### 4. Analysis Page
- [ ] Commodity analysis displays grid
- [ ] Charts render without errors

### 5. Insights Page
- [ ] Trend insights load
- [ ] Summary cards display correctly

### 6. Resources Page
- [ ] Help content displays
- [ ] External links work

---

## 🔍 Debugging Commands

### Check API Server Health
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

### Check Available Markets
```powershell
$markets = Invoke-WebRequest -Uri "http://localhost:8000/markets" -UseBasicParsing | ConvertFrom-Json
$markets
```

### Check Commodities for a Market
```powershell
$commodities = Invoke-WebRequest -Uri "http://localhost:8000/markets/Bowenpally/commodities" -UseBasicParsing | ConvertFrom-Json
$commodities
```

### Create Test Prediction
```powershell
$body = @{
  market = "Bowenpally"
  commodity = "Brinjal"
  horizon = 30
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/predict" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body -UseBasicParsing | ConvertFrom-Json
```

### View API Documentation
Open browser: `http://localhost:8000/docs`

---

## 📦 Environment Variables

### Frontend (.env)
```
VITE_API_BASE=http://localhost:8000
```

### Backend (api_server.py)
- `ROOT`: Project root directory
- `MODELS_DIR`: `./models`
- `DATASET_DIR`: `./dataset`

---

## 🛠️ Troubleshooting

### Issue: API Server won't start
**Solution**: 
```powershell
# Check Python environment
python --version

# Verify FastAPI is installed
python -c "import fastapi; print(fastapi.__version__)"

# Run environment fix
python fix_environment.py
```

### Issue: Frontend won't start
**Solution**:
```powershell
cd frontend
npm install
npm run dev
```

### Issue: CORS errors
**Solution**: API server is running on port 8000, frontend on 5173. FastAPI should accept requests automatically.

### Issue: Models not found
**Solution**: Ensure `models/` directory exists with market subdirectories:
```
models/
  ├── Bowenpally/
  ├── Erragadda(Rythu_Bazar)/
  ├── Gudimalkapur/
  └── ...
```

### Issue: Dataset not found
**Solution**: Ensure `dataset/` directory contains CSV files with price/quantity data.

---

## 📊 Project Structure

```
marketwave 2.0/
├── api_server.py              # FastAPI adapter
├── prediction_engine.py       # Core prediction logic
├── requirements.txt           # Python dependencies
├── models/                    # Trained ensemble models
├── dataset/                   # Price & quantity CSV files
├── frontend/                  # React TypeScript application
│   ├── src/
│   │   ├── pages/            # Page components (Predict, Compare, etc.)
│   │   ├── components/       # UI components
│   │   ├── hooks/            # React Query hooks
│   │   ├── utils/            # API client & utilities
│   │   ├── types.ts          # TypeScript interfaces
│   │   ├── main.tsx          # Entry point
│   │   └── index.css         # Tailwind styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.cjs
│   └── tsconfig.json
└── START_MARKETWAVE.ps1       # One-click startup script
```

---

## 📈 Next Steps

1. **Open Frontend**: Go to `http://localhost:5173` in your browser
2. **Select Market**: Choose a market from the dropdown
3. **Select Commodity**: Choose a commodity
4. **Set Horizon**: Enter prediction horizon (days)
5. **Click Predict**: Generate forecast
6. **View Results**: See chart, confidence intervals, and explainability

---

## ✨ Features

- ✓ Real-time market and commodity selection
- ✓ 30-day price forecasting with confidence intervals
- ✓ Explainable AI with feature importance
- ✓ Multi-page dashboard with comparison tools
- ✓ Auto-refresh every 5 minutes
- ✓ Dark mode support
- ✓ Responsive design

---

## 📝 Notes

- API server runs on `http://0.0.0.0:8000` (accessible from any interface)
- Frontend dev server runs on `http://localhost:5173` (local only)
- Hot module replacement (HMR) enabled for frontend
- All predictions are ensemble-based (XGBoost + Prophet + LSTM)
- Models are pre-trained and stored in `models/` directory

---

**Status**: ✅ **READY TO USE**

Last Updated: 2025-11-11
