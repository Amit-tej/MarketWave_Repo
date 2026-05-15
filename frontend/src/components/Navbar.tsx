import React from 'react'

export default function Navbar() {
  return (
    <nav className="bg-white/90 px-6 py-4 fixed top-0 left-0 right-0 z-50 backdrop-blur-xl">
      <div className="flex justify-between items-center">
        <div className="flex items-center">
          {/* Logo removed as requested */}
          <h1 className="text-2xl font-bold text-gray-900">Agricultural Intelligence</h1>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Live • Connected</span>
          </div>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200">
            Get Started
          </button>
        </div>
      </div>
    </nav>
  )
}
