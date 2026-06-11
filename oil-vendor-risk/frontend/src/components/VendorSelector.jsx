import React, { useEffect, useState } from 'react'
import { Search, ChevronRight, Building2, Globe, TrendingUp } from 'lucide-react'
import { fetchVendors } from '../utils/api'

const segmentIcons = {
  'Refining & Marketing': '🏭',
  'Integrated Oil & Gas': '🛢️',
  'National Oil Company': '🏛️',
}

export default function VendorSelector({ onSelect, disabled }) {
  const [vendors, setVendors] = useState([])
  const [custom, setCustom] = useState('')
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVendors()
      .then(d => setVendors(d.vendors || []))
      .catch(() => setVendors([]))
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = (name) => {
    setSelected(name)
    setCustom('')
  }

  const handleCustom = (e) => {
    setCustom(e.target.value)
    setSelected(null)
  }

  const activeName = custom.trim() || selected
  const canAssess = !!activeName && !disabled

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-6)' }}>

      {/* Pre-built vendor cards */}
      <div>
        <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 'var(--sp-3)' }}>
          Real-world oil vendors
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--sp-3)' }}>
          {loading
            ? [1,2,3].map(i => (
                <div key={i} className="skeleton" style={{ height: 96, borderRadius: 'var(--r-md)' }} />
              ))
            : vendors.map(v => (
                <button
                  key={v.name}
                  onClick={() => handleSelect(v.name)}
                  disabled={disabled}
                  style={{
                    background: selected === v.name ? 'var(--navy)' : 'var(--surface)',
                    border: `1.5px solid ${selected === v.name ? 'var(--navy)' : 'var(--border)'}`,
                    borderRadius: 'var(--r-md)',
                    padding: 'var(--sp-4)',
                    textAlign: 'left',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    transition: 'all var(--t-fast) var(--ease)',
                    opacity: disabled ? 0.6 : 1,
                    boxShadow: selected === v.name ? 'var(--shadow-md)' : 'var(--shadow-sm)',
                  }}
                >
                  <div style={{ fontSize: 22, marginBottom: 6 }}>
                    {segmentIcons[v.segment] || '🔷'}
                  </div>
                  <div style={{
                    fontWeight: 600,
                    fontSize: 13,
                    color: selected === v.name ? '#fff' : 'var(--text-primary)',
                    marginBottom: 3,
                    lineHeight: 1.3,
                  }}>
                    {v.name}
                  </div>
                  <div style={{
                    fontSize: 11,
                    color: selected === v.name ? 'rgba(255,255,255,0.6)' : 'var(--text-muted)',
                  }}>
                    {v.country} · {v.segment}
                  </div>
                </button>
              ))
          }
        </div>
      </div>

      {/* Divider */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)' }}>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500 }}>or enter custom vendor</span>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
      </div>

      {/* Custom input */}
      <div style={{ display: 'flex', gap: 'var(--sp-3)', alignItems: 'center' }}>
        <div style={{
          flex: 1,
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
        }}>
          <Search size={15} color="var(--text-muted)" style={{ position: 'absolute', left: 12, pointerEvents: 'none' }} />
          <input
            type="text"
            placeholder="e.g. Chevron Corporation, BP, Shell..."
            value={custom}
            onChange={handleCustom}
            disabled={disabled}
            style={{
              width: '100%',
              padding: '10px 12px 10px 36px',
              background: 'var(--surface)',
              border: `1.5px solid ${custom ? 'var(--navy)' : 'var(--border)'}`,
              borderRadius: 'var(--r-md)',
              fontSize: 14,
              color: 'var(--text-primary)',
              transition: 'border-color var(--t-fast) var(--ease)',
            }}
          />
        </div>
      </div>

      {/* Assess button */}
      <button
        onClick={() => canAssess && onSelect(activeName)}
        disabled={!canAssess}
        style={{
          background: canAssess ? 'var(--navy)' : 'var(--surface-2)',
          color: canAssess ? '#fff' : 'var(--text-muted)',
          padding: '12px 24px',
          borderRadius: 'var(--r-md)',
          fontWeight: 600,
          fontSize: 14,
          cursor: canAssess ? 'pointer' : 'not-allowed',
          transition: 'all var(--t-fast) var(--ease)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          boxShadow: canAssess ? 'var(--shadow-md)' : 'none',
          border: 'none',
        }}
      >
        {disabled ? (
          <>
            <span style={{
              width: 16, height: 16,
              border: '2px solid rgba(255,255,255,0.3)',
              borderTopColor: '#fff',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
              display: 'inline-block',
            }} />
            Assessing...
          </>
        ) : (
          <>
            Start Risk Assessment
            <ChevronRight size={16} />
          </>
        )}
      </button>

    </div>
  )
}
