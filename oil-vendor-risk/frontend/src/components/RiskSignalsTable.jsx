import React, { useState } from 'react'
import { ExternalLink, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'
import { getCategoryColor, getSeverityColor, getSeverityLabel } from '../utils/api'

function SeverityBadge({ severity }) {
  const color = getSeverityColor(severity)
  const label = getSeverityLabel(severity)
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: 99,
      fontSize: 10,
      fontWeight: 700,
      letterSpacing: '0.04em',
      color,
      background: color + '18',
      border: `1px solid ${color}30`,
    }}>
      {label}
    </span>
  )
}

function CategoryChip({ category }) {
  const color = getCategoryColor(category)
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: 99,
      fontSize: 10,
      fontWeight: 600,
      color,
      background: color + '12',
      textTransform: 'capitalize',
    }}>
      {category}
    </span>
  )
}

export default function RiskSignalsTable({ signals = [] }) {
  const [filter, setFilter] = useState('all')
  const [sortBy, setSortBy] = useState('severity')
  const [sortDir, setSortDir] = useState('desc')

  const categories = ['all', ...new Set(signals.map(s => s.category))]

  const filtered = signals
    .filter(s => filter === 'all' || s.category === filter)
    .sort((a, b) => {
      const dir = sortDir === 'desc' ? -1 : 1
      if (sortBy === 'severity') return dir * (a.severity - b.severity)
      if (sortBy === 'category') return dir * a.category.localeCompare(b.category)
      return 0
    })

  const toggleSort = (col) => {
    if (sortBy === col) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortBy(col); setSortDir('desc') }
  }

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)',
      overflow: 'hidden',
      boxShadow: 'var(--shadow-sm)',
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 20px',
        borderBottom: '1px solid var(--border-soft)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertTriangle size={15} color="var(--amber)" />
          <h3 style={{ fontSize: 14, fontWeight: 600 }}>Risk Signals</h3>
          <span style={{
            padding: '1px 8px', borderRadius: 99,
            background: 'var(--surface-2)',
            fontSize: 11, color: 'var(--text-muted)',
          }}>
            {filtered.length}
          </span>
        </div>

        {/* Category filter tabs */}
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {categories.map(c => (
            <button
              key={c}
              onClick={() => setFilter(c)}
              style={{
                padding: '4px 10px',
                borderRadius: 99,
                fontSize: 11,
                fontWeight: 500,
                border: `1px solid ${filter === c ? getCategoryColor(c) : 'var(--border)'}`,
                background: filter === c ? getCategoryColor(c) + '15' : 'transparent',
                color: filter === c ? getCategoryColor(c) : 'var(--text-secondary)',
                cursor: 'pointer',
                textTransform: 'capitalize',
                transition: 'all var(--t-fast)',
              }}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--surface-2)' }}>
              {[
                { key: 'signal', label: 'Signal' },
                { key: 'category', label: 'Category', sortable: true },
                { key: 'severity', label: 'Severity', sortable: true },
                { key: 'source', label: 'Source' },
              ].map(col => (
                <th
                  key={col.key}
                  onClick={() => col.sortable && toggleSort(col.key)}
                  style={{
                    padding: '8px 16px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                    cursor: col.sortable ? 'pointer' : 'default',
                    userSelect: 'none',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    {col.label}
                    {col.sortable && sortBy === col.key && (
                      sortDir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                  No signals found
                </td>
              </tr>
            ) : (
              filtered.map((sig, i) => (
                <tr
                  key={i}
                  style={{
                    borderTop: '1px solid var(--border-soft)',
                    transition: 'background var(--t-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-2)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--text-primary)', maxWidth: 320 }}>
                    <div style={{ lineHeight: 1.4 }}>{sig.signal}</div>
                  </td>
                  <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                    <CategoryChip category={sig.category} />
                  </td>
                  <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{
                        width: 32, height: 4, borderRadius: 99,
                        background: 'var(--border)',
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${sig.severity * 10}%`,
                          background: getSeverityColor(sig.severity),
                        }} />
                      </div>
                      <SeverityBadge severity={sig.severity} />
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', display: 'inline-block' }}>
                        {sig.source}
                      </span>
                      {sig.url && (
                        <a
                          href={sig.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: 'var(--cat-financial)', flexShrink: 0 }}
                        >
                          <ExternalLink size={12} />
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
