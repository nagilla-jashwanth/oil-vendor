import React from 'react'
import { Shield, Activity } from 'lucide-react'

export default function Header() {
  return (
    <header style={{
      background: 'var(--navy)',
      borderBottom: '1px solid rgba(255,255,255,0.08)',
      padding: '0 var(--sp-8)',
      height: 64,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)' }}>
        <div style={{
          width: 36, height: 36,
          background: 'var(--amber)',
          borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Shield size={18} color="#fff" strokeWidth={2.5} />
        </div>
        <div>
          <div style={{
            fontFamily: 'DM Serif Display, serif',
            fontSize: 20,
            color: '#fff',
            letterSpacing: '-0.01em',
          }}>
            OIL<span style={{ color: 'var(--amber-2)', marginLeft: 6 }}>VRM</span>
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Vendor Risk Management
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.1)',
          padding: '6px 12px',
          borderRadius: 999,
          fontSize: 12,
          color: 'rgba(255,255,255,0.6)',
        }}>
          <Activity size={13} />
          AI-Powered Assessment
        </div>
      </div>
    </header>
  )
}
