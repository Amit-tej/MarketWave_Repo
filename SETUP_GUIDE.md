# 🌾 MarketWave - Complete Setup & User Guide

## Quick Start (30 seconds)

```powershell
.\START_MARKETWAVE.ps1
```

Then open **http://localhost:5173** in your browser.

---

## 📋 What is MarketWave?

MarketWave is an **AI-powered agricultural intelligence platform** that helps farmers make better decisions about crop pricing and market selection using machine learning predictions.

### Key Features:
- **🎯 Price Forecasting**: 30-day ahead price predictions using ensemble ML models
- **📊 Market Comparison**: Find markets with the best prices for your crops
- **📈 Volatility Analysis**: Understand price stability and market trends
- **🔍 AI Explainability**: See which factors influence price predictions
- **💡 Farming Insights**: Get practical tips for better returns

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────┐
│   Web Browser (React + TypeScript)      │
│   • Prediction Dashboard                │
│   • Market Comparison                   │
│   • Volatility Analysis                 │
│   • Insights & Resources                │
└────────────┬────────────────────────────┘
             │ HTTP/REST API (Port 5173)
             ↓
┌─────────────────────────────────────────┐
│   FastAPI Backend (Python)              │
│   • Price predictions                   │
│   • Model management                    │
│   • Feature explainability              │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│   ML Ensemble Models                    │
│   • XGBoost                             │
│   • Prophet (Time Series)               │
│   • LSTM (Deep Learning)                │
└─────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│   Agricultural Price Datasets           │
│   • Brinjal, Onion, Potato              │
│   • Tomato, Green Chilli                │
│   • 5 Markets (Hyderabad region)        │
│   • 2021-2024 Historical Data           │
└─────────────────────────────────────────┘
```

---

## 💻 Prerequisites

- **Windows 10/11**
- **Python 3.9+** (pre-installed at `C:\Users\HP\AppData\Local\Programs\Python\Python39\`)
- **Node.js 20+** & **npm 10+**

### Verify Installation:
```powershell
python --version    # Should show Python 3.9.x
npm --version       # Should show npm 10.x or higher
```

---

## 🚀 Installation & Setup

### Option 1: Automated (Recommended)
```powershell
.\START_MARKETWAVE.ps1
```

### Option 2: Manual Startup

**Terminal 1 - Start API Server:**
```powershell
python api_server.py
```
Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Start Frontend:**
```powershell
cd frontend
npm run dev
```
Expected output:
```
  ➜  Local:   http://localhost:5173/
```

### Option 3: Docker (Coming Soon)

---

## 📱 Application Pages

### 1. **Prediction Dashboard** (Home)
- Select market and commodity
- Adjust forecast horizon (1-60 days)
- Generate AI price predictions
- View forecast chart with confidence intervals
- Understand price drivers via feature importance

### 2. **Market Comparison**
- Compare prices across 5 different markets
- Identify best-price markets for your crop
- 7-day average price analysis
- Strategic selling location recommendations

### 3. **Volatility Analysis**
- Price stability insights for each commodity
- Volatility indicators (🟢 Stable, 🟡 Moderate, 🔴 Volatile)
- Risk assessment for crop selection
- Insights for farming decisions

### 4. **Insights & Trends**
- Market trends and patterns
- Optimal timing for harvest/sales
- Price forecasting summaries
- Market comparison highlights

### 5. **Resources & Help**
- Comprehensive FAQ
- Technical explanations
- Links to government data portals
- Best practices for farmers

---

## 🎯 How to Use

### Step 1: Generate a Price Prediction
1. Open http://localhost:5173
2. Select a **Market** (e.g., "Bowenpally")
3. Select a **Commodity** (e.g., "Onion")
4. Adjust **Forecast Days** (default: 30)
5. Click **"✨ Generate Prediction"**

### Step 2: Interpret Results
- **📈 Forecast Chart**: Historical prices + predicted future prices
- **🔍 Feature Importance**: Which factors drive price changes?
- **💰 Price Card**: Current trend and confidence level
- **📊 Volatility**: How stable/risky this commodity is

### Step 3: Compare Markets
1. Go to **"Market Comparison"**
2. Select your commodity
3. Click **"Compare"**
4. See which markets offer the best prices

### Step 4: Understand Volatility
1. Go to **"Analysis"**
2. Check stability indicators for each commodity
3. Green = Stable (predictable income)
4. Red = Volatile (higher risk, potentially higher profit)

---

## 📊 Supported Markets & Commodities

### Markets (Hyderabad Region)
- Bowenpally
- Erragadda (Rythu Bazar)
- Gudimalkapur
- L.B. Nagar
- Mahboob Mansion

### Commodities
- 🥕 Brinjal
- 🌶️ Green Chilli
- 🧅 Onion
- 🥔 Potato
- 🍅 Tomato

---

## 🔧 Troubleshooting

### Issue: "Port 8000 already in use"
```powershell
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: "Cannot find npm"
```powershell
# Reinstall Node.js from nodejs.org
# Or add to PATH: C:\Program Files\nodejs\
```

### Issue: "Module not found" (Python)
```powershell
pip install -r requirements.txt
```

### Issue: "Blank page on localhost:5173"
1. Check browser console (F12) for errors
2. Verify API is running on http://localhost:8000/health
3. Refresh page (Ctrl+R)
4. Clear browser cache (Ctrl+Shift+Delete)

---

## 📈 Model Performance

Our ensemble models achieve:
- **7-day forecast**: 75-85% accuracy
- **14-day forecast**: 65-75% accuracy
- **30-day forecast**: 55-65% accuracy

Accuracy varies by:
- Commodity type
- Market conditions
- Seasonal factors
- Data availability

**Always verify predictions with official sources before major decisions.**

---

## 🔐 Data & Privacy

- **Data Source**: Public agricultural market data
- **Your Data**: Not stored or tracked
- **Updates**: Daily automatic refresh
- **Latency**: 24-hour official data lag (normal)

---

## 🎓 Technical Details

### Backend Stack
- **Framework**: FastAPI (Python)
- **Models**: XGBoost, Prophet, LSTM
- **Data**: Pandas, NumPy
- **Server**: Uvicorn (ASGI)

### Frontend Stack
- **Framework**: React 18.2
- **Language**: TypeScript 5.5
- **Build**: Vite 5.4
- **State**: React Query v5
- **Charts**: Recharts 2.6
- **Styling**: Tailwind CSS 3.4
- **Routing**: React Router 6.11

### API Endpoints
```
GET  /health                           - Health check
GET  /markets                          - List all markets
GET  /markets/{market}/commodities    - List commodities in market
POST /predict                          - Generate price prediction
GET  /predictions/{id}/explain        - Get feature importance
```

---

## 📚 API Documentation

Full interactive API docs available at:
```
http://localhost:8000/docs
```

Swagger UI provides:
- Endpoint specifications
- Request/response examples
- Try-it-out functionality
- Model schemas

---

## 🚀 Next Steps

1. ✅ Run `.\START_MARKETWAVE.ps1`
2. ✅ Open http://localhost:5173
3. ✅ Generate a prediction
4. ✅ Compare markets
5. ✅ Make better farming decisions!

---

## 📞 Support & Feedback

For issues or suggestions:
1. Check the **Resources** page in the app
2. Review this guide
3. Check `/docs` API documentation
4. Verify all prerequisites are installed

---

## 📝 Version Info

- **MarketWave**: v2.0
- **Frontend**: 0.1.0
- **Backend**: 0.1
- **Last Updated**: November 2025

---

**Happy farming with MarketWave! 🌾**
