import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts'
import { HistoricalData, PredictionResponse } from '../types'
import { useQueryClient } from '@tanstack/react-query'
import { fetchPriceComparison } from '../services/client'

export default function ForecastChart({
  historical,
  predictionId,
  horizon = 7,
  useMistral = false,
  commodity
}:{
  historical?: HistoricalData
  predictionId?: string
  horizon?: number
  useMistral?: boolean
  commodity?: string
}){
  const queryClient = useQueryClient()
  const data: any[] = []
  const [priceComparison, setPriceComparison] = useState<any>(null)

  // Get actual prediction data from cache
  const predictionData = predictionId ? queryClient.getQueryData<PredictionResponse>(['prediction', predictionId]) : null

  // Fetch price comparison data when commodity changes
  useEffect(() => {
    if (commodity) {
      fetchPriceComparison(commodity)
        .then(data => {
          setPriceComparison(data)
        })
        .catch(error => {
          console.error('Failed to fetch price comparison:', error)
          setPriceComparison(null)
        })
    } else {
      setPriceComparison(null)
    }
  }, [commodity])

  // Add historical data
  if(historical && historical.dates && historical.prices){
    for(let i = 0; i < historical.dates.length; i++){
      data.push({
        date: historical.dates[i],
        actual: historical.prices[i],
        type: 'historical'
      })
    }
  }

  // Add predicted data using actual prediction data
  let forecastDays = 0
  if(predictionData && predictionData.yhat && data.length > 0){
    // Use the last historical date as the base for forecast dates
    const lastHistoricalDate = new Date(data[data.length - 1].date)

    let added = 0
    for(let i = 0; i < Math.min(horizon, predictionData.yhat.length); i++){
      const forecastDate = new Date(lastHistoricalDate)
      forecastDate.setDate(forecastDate.getDate() + (i + 1))
      const forecastItem: any = {
        date: forecastDate.toISOString().split('T')[0],
        predicted: Math.round(predictionData.yhat[i] || 0),
        type: 'predicted'
      }

      // Add confidence bands for Mistral predictions
      if(useMistral && predictionData.intervals && predictionData.intervals['80'] && predictionData.intervals['80'][i]){
        const [lower, upper] = predictionData.intervals['80'][i]
        forecastItem.upper_80 = Math.round(upper || 0)
        forecastItem.lower_80 = Math.round(lower || 0)
      }

      data.push(forecastItem)
      added++
    }
    forecastDays = added
  }

  if(data.length === 0){
    return (
      <div style={{width: '100%', height: 360, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9fb1d4'}}>
        <div>No data available. Select market and commodity to load historical data.</div>
      </div>
    )
  }

  // Separate data for historical and forecast
  const historicalData = data.filter(d => d.type === 'historical')
  const forecastData = data.filter(d => d.type === 'predicted')

  // Calculate date ranges
  const historicalDays = historicalData.length
  const historicalStartDate = historicalData.length > 0 ? new Date(historicalData[0].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : ''
  const historicalEndDate = historicalData.length > 0 ? new Date(historicalData[historicalData.length - 1].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : ''
  const historicalRange = historicalStartDate && historicalEndDate ? `${historicalStartDate} - ${historicalEndDate}` : ''

  const forecastStartDate = forecastData.length > 0 ? new Date(forecastData[0].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : ''
  const forecastEndDate = forecastData.length > 0 ? new Date(forecastData[forecastData.length - 1].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : ''
  const forecastRange = forecastStartDate && forecastEndDate ? `${forecastStartDate} - ${forecastEndDate}` : ''

  return (
    <div style={{width: '100%'}}>
      {/* Historical Chart */}
      <div style={{marginBottom: predictionId ? '24px' : '0'}}>
        <h4 style={{margin: '0 0 12px 0', fontSize: '14px', color: '#60a5fa'}}>Historical Price Trend ({historicalDays} days: {historicalRange})</h4>
        <div style={{width: '100%', height: 300}}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historicalData} margin={{top: 5, right: 30, left: 0, bottom: 5}}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
              <XAxis
                dataKey="date"
                stroke="#9fb1d4"
                style={{fontSize: 12}}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
                }}
              />
              <YAxis
                stroke="#9fb1d4"
                style={{fontSize: 12}}
              />
              <Tooltip
                contentStyle={{background: '#0f1724', border: '1px solid #374151', borderRadius: 8}}
                labelStyle={{color: '#e6eef8'}}
                formatter={(value: any) => [`₹${Math.round(Number(value))}/kg`, 'Historical Price']}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#60a5fa"
                dot={false}
                strokeWidth={2}
                name="Historical Price"
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Forecast Chart */}
      {predictionId && forecastData.length > 0 && (
        <div>
          <h4 style={{margin: '0 0 12px 0', fontSize: '14px', color: useMistral ? '#a855f7' : '#34d399'}}>
            {useMistral ? 'Mistral AI Price Forecast' : 'Price Forecast'} ({forecastDays} days: {forecastRange})
          </h4>
          <div style={{width: '100%', height: 300}}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastData} margin={{top: 5, right: 30, left: 0, bottom: 5}}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                <XAxis
                  dataKey="date"
                  stroke="#9fb1d4"
                  style={{fontSize: 12}}
                  tickFormatter={(value) => {
                    const date = new Date(value)
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
                  }}
                />
                <YAxis
                  stroke="#9fb1d4"
                  style={{fontSize: 12}}
                />
                <Tooltip
                  contentStyle={{background: '#0f1724', border: '1px solid #374151', borderRadius: 8}}
                  labelStyle={{color: '#e6eef8'}}
                  formatter={(value: any) => [`₹${Math.round(Number(value))}/kg`, 'Forecast Price']}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#34d399"
                  strokeDasharray="5 5"
                  dot={{r: 3, fill: '#34d399'}}
                  strokeWidth={2}
                  name="Forecast Price"
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Price Comparison */}
      {priceComparison && (
        <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #374151', borderRadius: '8px', background: '#0f1724' }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#f59e0b' }}>Price Comparison Across Markets</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
            <div><strong>Lowest Price:</strong> ₹{priceComparison.lowest_price} ({priceComparison.lowest_market})</div>
            <div><strong>Highest Price:</strong> ₹{priceComparison.highest_price} ({priceComparison.highest_market})</div>
            <div><strong>Average Price:</strong> ₹{priceComparison.average_price}</div>
            <div><strong>Price Range:</strong> ₹{priceComparison.price_range?.min} - ₹{priceComparison.price_range?.max} (Spread: ₹{priceComparison.price_range?.spread})</div>
            <div><strong>Volatility:</strong> {priceComparison.price_volatility}</div>
            <div><strong>Markets Searched:</strong> {priceComparison.markets_searched}, <strong>Successful Fetches:</strong> {priceComparison.successful_fetches}</div>
          </div>
        </div>
      )}
    </div>
  )
}
