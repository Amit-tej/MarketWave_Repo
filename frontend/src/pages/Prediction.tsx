import React, { useState, useEffect, useCallback } from 'react'
import { useMarkets, useCommodities } from '../hooks/useMarkets'
import { useHistorical, usePredict, useExplain } from '../hooks/usePrediction'
import { useAppContext } from '../contexts/AppContext'
import PredictionCard from '../components/PredictionCard'
import ForecastChart from '../components/ForecastChart'
import ExplainPanel from '../components/ExplainPanel'

export default function PredictionPage() {
  const { data: mdata, isLoading: marketsLoading, error: marketsError } = useMarkets()
  const markets = mdata?.markets || []
  const {
    selectedMarket, setSelectedMarket,
    selectedCommodity, setSelectedCommodity,
    horizon, setHorizon,
    predictionId, setPredictionId,
    predictionData, setPredictionData,
    explainData, setExplainData
  } = useAppContext()

  const { data: cdata, isLoading: commLoading } = useCommodities(selectedMarket)
  const commodities = cdata?.commodities || []

  const { data: historical, isLoading: histLoading } = useHistorical(selectedMarket, selectedCommodity, 30)
  const predictMut = usePredict()
  const { data: explainDataHook } = useExplain(predictionId)

  // Update context with hook data
  useEffect(() => {
    if (explainDataHook) {
      setExplainData(explainDataHook)
    }
  }, [explainDataHook, setExplainData])

  useEffect(() => {
    if (markets.length > 0 && !selectedMarket) setSelectedMarket(markets[0])
  }, [markets, selectedMarket, setSelectedMarket])

  useEffect(() => {
    if (commodities.length > 0 && !selectedCommodity) setSelectedCommodity(commodities[0])
  }, [commodities, selectedCommodity, setSelectedCommodity])

  const handlePredict = useCallback(async () => {
    if (!selectedMarket || !selectedCommodity) return
    try {
      const resp = await predictMut.mutateAsync({ market: selectedMarket, commodity: selectedCommodity, horizon })
      setPredictionId(resp.prediction_id)
      setPredictionData(resp)
    } catch (err) {
      console.error('Prediction error:', err)
    }
  }, [selectedMarket, selectedCommodity, horizon, predictMut, setPredictionId, setPredictionData])

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center">
          Price Prediction
        </h1>
        <p className="text-lg text-gray-600">Get AI-powered price forecasts for agricultural commodities</p>
      </div>

      {/* Selection Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          Configure Prediction Parameters
        </h2>

        {marketsError && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <span className="text-red-500 mr-2">⚠️</span>
              <span className="text-red-700 text-sm">Error loading markets</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2 flex items-center">
              Market
            </label>
            <select
              value={selectedMarket}
              onChange={e => setSelectedMarket(e.target.value)}
              disabled={marketsLoading}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select market...</option>
              {markets.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2 flex items-center">
              Commodity
            </label>
            <select
              value={selectedCommodity}
              onChange={e => setSelectedCommodity(e.target.value)}
              disabled={commLoading}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select commodity...</option>
              {commodities.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2 flex items-center">
              Forecast Horizon
            </label>
            <div className="space-y-3">
              <input
                type="range"
                min={1}
                max={30}
                value={horizon}
                onChange={e => setHorizon(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                title={`${horizon} days`}
              />
              <div className="flex justify-between text-sm text-gray-600">
                <span>1 day</span>
                <span className="font-medium text-blue-600">{horizon} days</span>
                <span>30 days</span>
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={handlePredict}
          disabled={predictMut.isPending || !selectedMarket || !selectedCommodity}
          className="w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors duration-200 flex items-center justify-center"
        >
          {predictMut.isPending ? (
            <>
              <span className="mr-2">⏳</span> Generating Prediction...
            </>
          ) : (
            <>
              <span className="mr-2">✨</span> Generate Prediction
            </>
          )}
        </button>
      </div>

      <div className={`grid gap-8 ${selectedCommodity ? 'lg:grid-cols-3' : 'grid-cols-1'}`}>
        <div className="space-y-8 lg:col-span-2">
          {selectedCommodity && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              {histLoading ? (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-4">
                    <span className="text-4xl">⏳</span>
                  </div>
                  <p className="text-gray-600">Loading historical data...</p>
                </div>
              ) : (
                <ForecastChart historical={historical} predictionId={predictionId} horizon={horizon} />
              )}
            </div>
          )}

          {predictionId && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                Feature Importance Analysis
              </h3>
              <ExplainPanel data={explainData || undefined} />
            </div>
          )}
        </div>

        {selectedCommodity && (
          <div className="lg:col-span-1">
            {predictionId ? (
              <PredictionCard historical={historical} predictionId={predictionId} explain={explainData || undefined} selectedCommodity={selectedCommodity} selectedMarket={selectedMarket} />
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
                <div className="text-gray-400 mb-4">
                  <span className="text-4xl">📈</span>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Predict</h3>
                <p className="text-gray-600 text-sm">Configure your parameters and generate a prediction to see detailed insights</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
