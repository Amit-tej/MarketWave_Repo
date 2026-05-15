import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const farmerImages = [
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1594736797933-d0401ba2fe65?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400&h=300&fit=crop'
]

export default function Dashboard() {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)

  useEffect(() => {
    if (!isAutoPlaying) return

    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % farmerImages.length)
    }, 3000)
    return () => clearInterval(timer)
  }, [isAutoPlaying])

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % farmerImages.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + farmerImages.length) % farmerImages.length)
  }

  const handleImageClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const halfWidth = rect.width / 2

    if (clickX > halfWidth) {
      nextSlide()
    } else {
      prevSlide()
    }
  }

  const handleDoubleClick = () => {
    setIsAutoPlaying(!isAutoPlaying)
  }

  const features = [
    {
      title: 'AI Price Prediction',
      description: 'Get accurate price forecasts for agricultural commodities using advanced machine learning models.',
      link: '/predict'
    },
    {
      title: 'Market Comparison',
      description: 'Compare prices across different markets to find the best selling opportunities.',
      link: '/compare'
    },
    {
      title: 'Market Analysis',
      description: 'Deep dive into market trends and patterns with comprehensive analytics.',
      link: '/analysis'
    },
    {
      title: 'Smart Insights',
      description: 'Get actionable insights and recommendations for better farming decisions.',
      link: '/insights'
    }
  ]

  const stats = [
    { label: 'Markets Covered', value: '500+' },
    { label: 'Commodities Tracked', value: '50+' },
    { label: 'Daily Predictions', value: '10K+' },
    { label: 'Farmers Helped', value: '25K+' }
  ]

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center">
          Dashboard
        </h1>
        <p className="text-lg text-gray-600">Overview of market data and key insights</p>
      </div>

      {/* Hero Section with Slider */}
      <div className="relative bg-gradient-to-r from-green-600 to-blue-600 rounded-2xl overflow-hidden shadow-2xl">
        <div className="relative h-96 flex items-center justify-center text-white">
          <div className="absolute inset-0">
            <div
              className="w-full h-full bg-cover bg-center opacity-30 cursor-pointer"
              style={{ backgroundImage: `url(${farmerImages[currentSlide]})` }}
              onClick={handleImageClick}
              onDoubleClick={handleDoubleClick}
            />
            <div className="absolute inset-0 bg-gradient-to-r from-green-600/80 to-blue-600/80"></div>
          </div>



          {/* Hero Content */}
          <div className="relative z-10 text-center px-8">
            <h1 className="text-5xl font-bold mb-4 text-white">Welcome to Agricultural Intelligence</h1>
            <p className="text-xl mb-8 max-w-2xl mx-auto text-white">
              Empowering farmers with AI-driven price predictions and market insights for better agricultural decisions
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/predict"
                className="bg-white text-green-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors duration-200"
              >
                Start Predicting
              </Link>
              <Link
                to="/resources"
                className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors duration-200"
              >
                Learn More
              </Link>
            </div>
          </div>

          {/* Slide Indicators */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-2">
            {farmerImages.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                  index === currentSlide ? 'bg-white' : 'bg-white/50'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
            <div className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</div>
            <div className="text-sm text-gray-600">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature, index) => (
          <Link
            key={index}
            to={feature.link}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow duration-200 group"
          >
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors duration-200">
                {feature.title}
              </h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
            <svg className="w-6 h-6 text-gray-400 group-hover:text-blue-600 transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/predict"
            className="flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors duration-200"
          >
            <span>Make Prediction</span>
          </Link>
          <Link
            to="/compare"
            className="flex items-center justify-center bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors duration-200"
          >
            <span>Compare Markets</span>
          </Link>
          <Link
            to="/analysis"
            className="flex items-center justify-center bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition-colors duration-200"
          >
            <span>View Analysis</span>
          </Link>
          <Link
            to="/insights"
            className="flex items-center justify-center bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg transition-colors duration-200"
          >
            <span>Get Insights</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
