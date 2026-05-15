import React from 'react'

interface ModernCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  gradient?: boolean
}

export default function ModernCard({
  children,
  className = '',
  hover = true,
  gradient = false
}: ModernCardProps) {
  const baseClasses = 'relative overflow-hidden rounded-2xl border border-gray-200/50 backdrop-blur-sm transition-all duration-300'

  const gradientClasses = gradient
    ? 'bg-gradient-to-br from-white via-gray-50/80 to-white shadow-xl shadow-gray-200/20'
    : 'bg-white/80 shadow-lg shadow-gray-100/50'

  const hoverClasses = hover
    ? 'hover:shadow-2xl hover:shadow-gray-200/30 hover:-translate-y-1 hover:border-gray-300/50'
    : ''

  return (
    <div className={`${baseClasses} ${gradientClasses} ${hoverClasses} ${className}`}>
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-[0.02]">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(0,0,0,0.15) 1px, transparent 0)`,
          backgroundSize: '20px 20px'
        }} />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  )
}
