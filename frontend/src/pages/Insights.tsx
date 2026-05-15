import Rteact, { useState, useEffect } from 'react'
import { useMarkets } from '../hooks/useMarkets'
import { fetchInsightsData } from '../utils/api'

export default function Insights(){
  const { data: mdata } = useMarkets()
  const markets = mdata?.markets || []
  const [insightsData, setInsightsData] = useState<any>({})

  useEffect(() => {
    const loadInsights = async () => {
      try {
        const data = await fetchInsightsData()
        setInsightsData(data)
      } catch (e) {
        // Fallback to static data
        setInsightsData({
          total_markets: markets.length,
          total_commodities: 5,
          avg_volatility: 15.2,
          top_performing: 'Tomato',
          market_insights: [
            'Price volatility is highest for Green Chilli',
            'Onion shows most stable pricing',
            'Tomato prices are trending upward'
          ]
        })
      }
    }

    if (markets.length > 0) loadInsights()
  }, [markets])

  const insights = [
    {
      icon: '📈',
      title: 'Market Trends',
      description: 'Track price movements and seasonal patterns',
      color: '#3b82f6'
    },
    {
      icon: '🎯',
      title: 'Best Timing',
      description: 'Identify optimal selling periods for higher profits',
      color: '#10b981'
    },
    {
      icon: '💰',
      title: 'Price Forecast',
      description: 'AI-powered predictions for next 30 days',
      color: '#f97316'
    },
    {
      icon: '🤝',
      title: 'Market Comparison',
      description: 'Find markets with best prices for your crop',
      color: '#8b5cf6'
    }
  ]

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center">
          Insights
        </h1>
        <p className="text-lg text-gray-600">Get actionable insights and recommendations for better farming decisions</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {insights.map((item, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200" style={{borderLeft: `4px solid ${item.color}`}}>
            <div className="text-3xl mb-3">{item.icon}</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
            <p className="text-gray-600 text-sm leading-relaxed">{item.description}</p>
          </div>
        ))}
      </div>

      {/* Market Overview */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          Active Markets
        </h2>
        <p className="text-gray-600 mb-6">Currently tracking {markets.length} markets with real-time data</p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {markets.slice(0, 6).map((m, i) => (
            <div key={i} className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center hover:bg-blue-100 transition-colors duration-200">
              <div className="text-blue-600 mb-1">📍</div>
              <div className="text-sm font-medium text-gray-900">{m}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tips Section */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
          Quick Tips for Better Returns
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-green-100">
            <div className="flex items-start">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3 mt-1">
                <span className="text-green-600 font-bold">1</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Monitor Predictions</h4>
                <p className="text-gray-600 text-sm">Check 30-day price forecasts regularly to plan harvest timing</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-green-100">
            <div className="flex items-start">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3 mt-1">
                <span className="text-green-600 font-bold">2</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Compare Markets</h4>
                <p className="text-gray-600 text-sm">Different markets offer different prices - transport to higher-priced markets when economical</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-green-100">
            <div className="flex items-start">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3 mt-1">
                <span className="text-green-600 font-bold">3</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Diversify Crops</h4>
                <p className="text-gray-600 text-sm">Don't depend on a single commodity - spread risk across multiple crops</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-green-100">
            <div className="flex items-start">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3 mt-1">
                <span className="text-green-600 font-bold">4</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Watch Volatility</h4>
                <p className="text-gray-600 text-sm">High volatility crops have greater risk but also greater profit potential</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
