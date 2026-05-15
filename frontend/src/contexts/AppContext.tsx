import React, { createContext, useContext, useState, ReactNode } from 'react'
import { PredictionResponse, ExplainResponse } from '../types'
import { ComparisonResponse, TopSummaryResponse, InsightsDataResponse } from '../types_new'

interface AppContextType {
  // User selections
  selectedMarket: string
  selectedCommodity: string
  horizon: number
  setSelectedMarket: (market: string) => void
  setSelectedCommodity: (commodity: string) => void
  setHorizon: (horizon: number) => void

  // Prediction state
  predictionId: string | undefined
  predictionData: PredictionResponse | null
  explainData: ExplainResponse | null
  setPredictionId: (id: string | undefined) => void
  setPredictionData: (data: PredictionResponse | null) => void
  setExplainData: (data: ExplainResponse | null) => void

  // Compare state
  compareCommodity: string
  compareTop5: any[]
  compareBest: { market: string, price: number } | null
  setCompareCommodity: (commodity: string) => void
  setCompareTop5: (data: any[]) => void
  setCompareBest: (data: { market: string, price: number } | null) => void

  // Analysis state
  analysisSummaryData: any[]
  setAnalysisSummaryData: (data: any[]) => void

  // Insights state
  insightsData: InsightsDataResponse | null
  setInsightsData: (data: InsightsDataResponse | null) => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export const useAppContext = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider')
  }
  return context
}

interface AppProviderProps {
  children: ReactNode
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  // User selections
  const [selectedMarket, setSelectedMarket] = useState<string>('')
  const [selectedCommodity, setSelectedCommodity] = useState<string>('')
  const [horizon, setHorizon] = useState<number>(30)

  // Prediction state
  const [predictionId, setPredictionId] = useState<string | undefined>(undefined)
  const [predictionData, setPredictionData] = useState<PredictionResponse | null>(null)
  const [explainData, setExplainData] = useState<ExplainResponse | null>(null)

  // Compare state
  const [compareCommodity, setCompareCommodity] = useState<string>('Onion')
  const [compareTop5, setCompareTop5] = useState<any[]>([])
  const [compareBest, setCompareBest] = useState<{ market: string, price: number } | null>(null)

  // Analysis state
  const [analysisSummaryData, setAnalysisSummaryData] = useState<any[]>([])

  // Insights state
  const [insightsData, setInsightsData] = useState<InsightsDataResponse | null>(null)

  const value: AppContextType = {
    // User selections
    selectedMarket,
    selectedCommodity,
    horizon,
    setSelectedMarket,
    setSelectedCommodity,
    setHorizon,

    // Prediction state
    predictionId,
    predictionData,
    explainData,
    setPredictionId,
    setPredictionData,
    setExplainData,

    // Compare state
    compareCommodity,
    compareTop5,
    compareBest,
    setCompareCommodity,
    setCompareTop5,
    setCompareBest,

    // Analysis state
    analysisSummaryData,
    setAnalysisSummaryData,

    // Insights state
    insightsData,
    setInsightsData,
  }

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  )
}
