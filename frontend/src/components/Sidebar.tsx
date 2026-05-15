import React from 'react'
import { NavLink } from 'react-router-dom'

export default function Sidebar() {
  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/predict', label: 'Predict' },
    { path: '/compare', label: 'Compare' },
    { path: '/analysis', label: 'Analysis' },
    { path: '/insights', label: 'Insights' },
    { path: '/resources', label: 'Resources' }
  ]

  return (
    <aside className="w-64 bg-white shadow-lg border-r border-gray-200">
      <div className="p-6">
        <nav>
          <ul className="space-y-2">
            {navItems.map(item => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center px-4 py-3 rounded-lg transition-colors duration-200 ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border-r-4 border-blue-500'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`
                  }
                >
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </aside>
  )
}
