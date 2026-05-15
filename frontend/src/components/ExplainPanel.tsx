import React from 'react'
import { ExplainResponse } from '../types'

export default function ExplainPanel({data}:{data?: ExplainResponse}){
  const global = data?.global_importance || []
  const local = data?.local || []
  const metadata = data?.model_metadata

  if(!data){
    return (
      <div style={{textAlign: 'center', padding: 32, color: '#111827'}}>
        Run a prediction to see explainability insights
      </div>
    )
  }

  return (
    <div>
      <h3 style={{marginTop: 0, color: '#111827'}}>🧠 Explainability Analysis</h3>

      {/* Model Metadata */}
      {metadata && (
        <div style={{marginBottom: 16, padding: 12, background: 'rgba(59, 130, 246, 0.1)', borderRadius: 8, border: '1px solid rgba(59, 130, 246, 0.3)'}}>
          <div style={{fontSize: 12, color: '#111827'}}>Model Source</div>
          <div style={{fontSize: 14, fontWeight: 500, color: '#111827'}}>
            {metadata.source || metadata.model_name || 'Ensemble Model'}
          </div>
        </div>
      )}

      {/* Global Feature Importance */}
      <div style={{marginBottom: 16}}>
        <h4 style={{margin: '0 0 12px 0', fontSize: 14, color: '#111827'}}>📈 Global Feature Importance</h4>
        {global.length === 0 ? (
          <div style={{fontSize: 12, color: '#111827', padding: 12, textAlign: 'center'}}>
            No feature importance data available
          </div>
        ) : (
          <div style={{display: 'grid', gap: 8}}>
            {global.map((item, i) => (
              <div key={i}>
                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 4}}>
                  <span style={{fontSize: 13, color: '#111827'}}>{item.feature}</span>
                  <span style={{fontSize: 12, color: '#111827'}}>{Math.round(item.importance * 100)}%</span>
                </div>
                <div style={{background: 'rgba(59, 130, 246, 0.2)', height: 6, borderRadius: 3, overflow: 'hidden'}}>
                  <div 
                    style={{
                      height: '100%',
                      background: 'linear-gradient(90deg, #3b82f6, #10b981)',
                      width: `${item.importance * 100}%`,
                      borderRadius: 3,
                      transition: 'width 0.3s ease'
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Local Contributions */}
      {local && local.length > 0 && (
        <div>
          <h4 style={{margin: '0 0 12px 0', fontSize: 14, color: '#111827'}}>🎯 Local Contributions</h4>
          <div style={{display: 'grid', gap: 8}}>
            {local.map((item, i) => (
              <div key={i} style={{padding: 10, background: 'rgba(16, 185, 129, 0.1)', borderRadius: 6, border: '1px solid rgba(16, 185, 129, 0.3)'}}>
                <div style={{display: 'flex', justifyContent: 'space-between'}}>
                  <span style={{fontSize: 13, color: '#111827'}}>{item.feature}</span>
                  <span style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: item.contribution >= 0 ? '#10b981' : '#ef4444'
                  }}>
                    {item.contribution >= 0 ? '+' : ''}{Math.round(item.contribution * 100) / 100}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Note */}
      <div style={{marginTop: 16, padding: 12, background: 'rgba(249, 115, 22, 0.1)', borderRadius: 8, border: '1px solid rgba(249, 115, 22, 0.3)', fontSize: 12, color: '#111827'}}>
        ℹ️ These insights help you understand which factors most influence the predicted price
      </div>
    </div>
  )
}
