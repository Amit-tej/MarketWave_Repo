import React from 'react'

interface StatItem {
  label: string
  value: string | number
  icon: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
}

interface ModernStatsProps {
  stats: StatItem[]
  className?: string
}

export default function ModernStats({ stats, className = '' }: ModernStatsProps) {
  return (
    <div className={`grid grid-cols-2 md:grid-cols-4 gap-6 ${className}`}>
      {stats.map((stat, index) => (
        <div
          key={index}
          className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-white via-gray-50/80 to-white p-6 shadow-lg shadow-gray-200/20 border border-gray-200/50 backdrop-blur-sm transition-all duration-300 hover:shadow-2xl hover:shadow-gray-200/30 hover:-translate-y-1"
        >
          {/* Animated background gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50/0 via-transparent to-green-50/0 group-hover:from-blue-50/30 group-hover:to-green-50/30 transition-all duration-500" />

          {/* Subtle pattern overlay */}
          <div className="absolute inset-0 opacity-[0.03]">
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: `radial-gradient(circle at 1px 1px, rgba(0,0,0,0.15) 1px, transparent 0)`,
                backgroundSize: '16px 16px'
              }}
            />
          </div>

          <div className="relative z-10">
            {/* Icon with glow effect */}
            <div className="mb-4 flex items-center justify-between">
              <div className="text-3xl group-hover:scale-110 transition-transform duration-300">
                {stat.icon}
              </div>
              {stat.trend && (
                <div className={`text-sm font-medium ${
                  stat.trend === 'up' ? 'text-green-600' :
                  stat.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {stat.trend === 'up' ? '↗' : stat.trend === 'down' ? '↘' : '→'}
                  {stat.trendValue && <span className="ml-1">{stat.trendValue}</span>}
                </div>
              )}
            </div>

            {/* Value with animation */}
            <div className="text-3xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors duration-300">
              {stat.value}
            </div>

            {/* Label */}
            <div className="text-sm text-gray-600 font-medium">
              {stat.label}
            </div>
          </div>

          {/* Hover effect line */}
          <div className="absolute bottom-0 left-0 w-0 h-1 bg-gradient-to-r from-blue-500 to-green-500 group-hover:w-full transition-all duration-500" />
        </div>
      ))}
    </div>
  )
}
