import React, { useState } from 'react'
import { useMarkets } from '../hooks/useMarkets'
import { useAppContext } from '../contexts/AppContext'
import { fetchComparison } from '../utils/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts'

const COMMODITIES = ['Brinjal', 'Green Chilli', 'Onion', 'Potato', 'Tomato']

export default function Compare() {
  const { data: mdata } = useMarkets()
  const markets = mdata?.markets || []
  const {
    compareCommodity, setCompareCommodity,
    compareTop5, setCompareTop5,
    compareBest, setCompareBest,
    horizon
  } = useAppContext()
  const [isComparing, setIsComparing] = useState(false)
  const [error, setError] = useState('')

  const handleCompare = async () => {
    setIsComparing(true)
    setError('')
    setCompareTop5([])
    setCompareBest(null)

    try {
      const comparisonData = await fetchComparison(compareCommodity)
      const rows = comparisonData.markets.map(m => ({
        market: m.market,
        price: m.price
      }))

      if (rows.length === 0) {
        setError(`No market data found for ${compareCommodity}`)
        setIsComparing(false)
        return
      }

      rows.sort((a, b) => b.price - a.price)
      setCompareTop5(rows.slice(0, 5))
      setCompareBest({ market: comparisonData.best_market.market, price: comparisonData.best_market.price })
    } catch (e) {
      setError(`Failed to fetch comparison data for ${compareCommodity}`)
    } finally {
      setIsComparing(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center">
          Market Comparison
        </h1>
        <p className="text-lg text-gray-600">Compare prices across different markets to find the best selling opportunities</p>
      </div>

      {/* Selection Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          Compare Prices Across Markets
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Commodity
            </label>
            <select
              value={compareCommodity}
              onChange={e => setCompareCommodity(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 transition-colors"
            >
              {COMMODITIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="md:col-span-2 flex justify-end">
            <button
              onClick={handleCompare}
              disabled={isComparing || !compareCommodity}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors duration-200 flex items-center"
            >
              {isComparing ? (
                <>
                  <span className="mr-2">🔄</span> Comparing...
                </>
              ) : (
                <>
                  <span className="mr-2">🔍</span> Compare
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <span className="text-red-500 mr-2">⚠️</span>
              <span className="text-red-700 text-sm">{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Best Market Card */}
      {compareBest && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
                Highest Price Market
              </h3>
              <div className="text-2xl font-bold text-green-700 mb-1">{compareBest.market}</div>
              <div className="text-sm text-gray-600">Average 7-day price for {compareCommodity}</div>
            </div>
            <div className="text-4xl font-bold text-green-600">₹{compareBest.price}</div>
          </div>
        </div>
      )}

      {/* Top 5 Markets Chart */}
      {compareTop5.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            Top 5 Markets by Price
          </h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compareTop5} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="market"
                  stroke="#6b7280"
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis
                  stroke="#6b7280"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(value) => [`₹${value}`, 'Price']}
                />
                <Bar
                  dataKey="price"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                  name="Price (₹/kg)"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-center text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
            💡 Farmers typically sell to markets with higher prices for better returns
          </div>
        </div>
      )}

      {!compareTop5.length && !isComparing && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <div className="text-gray-400 mb-2">
            <span className="text-4xl">📈</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Compare</h3>
          <p className="text-gray-600">Select a commodity and click "Compare" to analyze prices across different markets</p>
        </div>
      )}
    </div>
  )
}
