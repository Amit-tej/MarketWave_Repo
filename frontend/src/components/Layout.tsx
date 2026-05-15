import React from 'react'
import ModernNavbar from './ModernNavbar'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <ModernNavbar />
      <main className="w-full p-8" style={{ marginTop: '80px' }}>
        {children}
      </main>
    </div>
  )
}
