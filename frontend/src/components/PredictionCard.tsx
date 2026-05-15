import React from 'react'
import { PredictionResponse, ExplainResponse, HistoricalData } from '../types'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchComparisonForecast } from '../utils/api'

export default function PredictionCard({
  historical,
  predictionId,
  explain,
  selectedCommodity,
  selectedMarket
}:{
  historical?: HistoricalData
  predictionId?: string
  explain?: ExplainResponse
  selectedCommodity?: string
  selectedMarket?: string
}){
  const queryClient = useQueryClient()

  // Get prediction data from cache (set by usePredict mutation)
  const predictionData = predictionId ? queryClient.getQueryData<PredictionResponse>(['prediction', predictionId]) : null

  // Use actual prediction data or fall back to historical calculations
  const lastPrice = historical?.prices?.[historical.prices.length - 1] || 0
  const historicalLength = historical?.prices?.length || 0
  const predictedPrices = predictionData?.yhat?.slice(historicalLength) || []
  const averagePredictedPrice = predictedPrices.length > 0 ? predictedPrices.reduce((sum, price) => (sum || 0) + (price || 0), 0) / predictedPrices.length : lastPrice
  const finalPredictedPrice = predictionData?.yhat?.[predictionData.yhat.length - 1] || lastPrice

  // Calculate confidence interval for the final predicted price (traditional MarketWave style)
  const confidenceIntervals = predictionData?.intervals?.['80%']?.slice(historicalLength) || []
  const finalInterval = confidenceIntervals[confidenceIntervals.length - 1] || [finalPredictedPrice * 0.9, finalPredictedPrice * 1.1]

  // Use confidence interval for the final prediction
  const priceRange = {
    min: Math.round(finalInterval[0] || finalPredictedPrice * 0.9),
    max: Math.round(finalInterval[1] || finalPredictedPrice * 1.1)
  }

  // Calculate accurate confidence interval price based on forecast
  const accuratePrice = Math.round(finalPredictedPrice)

  // Determine trend from prediction data - use the final predicted price for overall trend
  const trendChange = finalPredictedPrice - lastPrice
  const trendThreshold = 0.5 // Consider stable if change is less than 0.5 rupees

  let trend: 'Increasing' | 'Decreasing' | 'Stable'
  if (Math.abs(trendChange) < trendThreshold) {
    trend = 'Stable'
  } else {
    trend = trendChange > 0 ? 'Increasing' : 'Decreasing'
  }

  // Fetch top market recommendation based on forecast horizon
  const { data: comparisonData } = useQuery({
    queryKey: ['comparison', selectedCommodity, 'forecast'],
    queryFn: () => selectedCommodity ? fetchComparisonForecast(selectedCommodity, true) : null,
    enabled: !!selectedCommodity
  })

  const topMarket = comparisonData?.best_market

  // Only show recommendation if forecast price is higher than current market price
  const shouldShowRecommendation = topMarket && selectedMarket !== topMarket.market && averagePredictedPrice > topMarket.price

  return (
    <div className="space-y-6">
      {/* Main Summary Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          Forecast Summary
        </h3>

        <div className="text-3xl font-bold text-blue-600 mb-6">
          ₹{priceRange.min}-{priceRange.max}/kg
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-500 mb-1">Trend</div>
            <div className={`font-semibold ${trend === 'Increasing' ? 'text-green-600' : trend === 'Decreasing' ? 'text-red-600' : 'text-gray-600'}`}>
              {trend === 'Increasing' ? 'Increasing' : trend === 'Decreasing' ? 'Decreasing' : 'Stable'}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-500 mb-1">Expected Price</div>
            <div className="font-semibold text-orange-600">₹{Math.round(averagePredictedPrice)}/kg</div>
          </div>
        </div>

        {/* Top Market Recommendation */}
        {shouldShowRecommendation && topMarket && (
          <div className="bg-green-50 p-4 rounded-lg border border-green-200 mb-6">
            <div className="text-sm text-gray-600 mb-1 flex items-center">
              Less Prefered Market
            </div>
            <div className="font-semibold text-green-700">
              {topMarket.market}: ₹{topMarket.price}/kg
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Expected forecast price: ₹{Math.round(averagePredictedPrice)}/kg
            </div>
          </div>
        )}

        {lastPrice > 0 && (
          <div className="text-sm text-gray-600 mb-6">
            <span className="font-medium">Last Price:</span> ₹{Math.round(lastPrice)}/kg •
            <span className="ml-3 font-medium">Change:</span> <span className={trendChange >= 0 ? 'text-green-600' : 'text-red-600'}>
              {trendChange >= 0 ? '+' : ''}{Math.round(trendChange * 10) / 10}₹/forecast
            </span>
          </div>
        )}

        <div className="border-t border-gray-200 pt-4 space-y-3">
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center">
            Export CSV
          </button>
          <button className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center">
            Download Explain
          </button>
        </div>
      </div>

      {/* Explainability Summary */}
      {explain && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            AI Explainability
          </h4>
          {explain.global_importance && explain.global_importance.length > 0 ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-600 mb-4">Top Features Influencing Price:</p>
              {explain.global_importance.slice(0, 3).map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-900">{item.feature}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${item.importance * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500 w-8 text-right">{Math.round(item.importance * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-500 text-center py-4">Loading explainability...</div>
          )}
        </div>
      )}
    </div>
  )
}
