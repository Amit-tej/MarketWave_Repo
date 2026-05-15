import React from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppProvider } from './contexts/AppContext'
import Dashboard from './pages/Dashboard'
import PredictionPage from './pages/Prediction'
import Compare from './pages/Compare'
import Analysis from './pages/Analysis'
import Insights from './pages/Insights'
import Resources from './pages/Resources'
import Layout from './components/Layout'
import './index.css'

const qc = new QueryClient()

function App(){
  return (
    <QueryClientProvider client={qc}>
      <AppProvider>
        <HashRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard/>} />
              <Route path="/predict" element={<PredictionPage/>} />
              <Route path="/compare" element={<Compare/>} />
              <Route path="/analysis" element={<Analysis/>} />
              <Route path="/insights" element={<Insights/>} />
              <Route path="/resources" element={<Resources/>} />
            </Routes>
          </Layout>
        </HashRouter>
      </AppProvider>
    </QueryClientProvider>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
