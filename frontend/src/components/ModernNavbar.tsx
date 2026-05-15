import React from 'react'
import { NavLink } from 'react-router-dom'

export default function ModernNavbar() {
  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/predict', label: 'Predict' },
    { path: '/compare', label: 'Compare' },
    { path: '/analysis', label: 'Analysis' },
    { path: '/insights', label: 'Insights' },
    { path: '/resources', label: 'Resources' }
  ]

  return (
    <nav className="relative bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 shadow-2xl border-b border-slate-700/50 backdrop-blur-md">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-purple-600/5 to-green-600/10 animate-pulse" />

      {/* Glass effect overlay */}
      <div className="absolute inset-0 bg-white/5 backdrop-blur-sm" />

      <div className="relative max-w-7xl mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center">
            {/* Logo removed as requested */}
          </div>

          {/* Navigation Items */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-4 py-2 rounded-lg transition-all duration-300 ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-200 border border-blue-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                  }`
                }
              >
                <span className="font-medium">{item.label}</span>
              </NavLink>
            ))}
          </div>

          {/* Status and Actions */}
          <div className="flex items-center space-x-6">
            {/* Live Status */}
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full backdrop-blur-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50" />
              <span className="text-sm text-green-400 font-medium">Live • Connected</span>
            </div>

            {/* CTA Button */}
            <button className="relative group px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/40 transition-all duration-300 hover:scale-105 overflow-hidden">
              {/* Button shine effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
              <span className="relative z-10">Get Started</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden mt-4 pb-2">
          <div className="flex items-center space-x-1 overflow-x-auto">
            {navItems.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg transition-all duration-300 whitespace-nowrap ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-200 border border-blue-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                  }`
                }
              >
                <span className="font-medium text-sm">{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom gradient line */}
      <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
    </nav>
  )
}
