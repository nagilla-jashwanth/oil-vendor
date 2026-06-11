import React, { useState } from 'react'
import { CheckSquare, Clock, Calendar, CalendarDays, ChevronDown, ChevronUp } from 'lucide-react'
import { getCategoryColor } from '../utils/api'

const PRIORITY_META = {
  immediate:   { label: 'Immediate',   color: 'var(--risk-critical)', icon: Clock },
  'short-term':{ label: 'Short-term',  color: 'var(--risk-high)',     icon: Calendar },
  'long-term': { label: 'Long-term',   color: 'var(--risk-medium)',   icon: CalendarDays },
}

function ActionCard({ action, index }) {
  const [expanded, setExpanded] = useState(false)
  const meta = PRIORITY_META[action.priority] || PRIORITY_META['short-term']
  const Icon = meta.icon
  const catColor = getCategoryColor(action.category)

  return (
    <div
      className="animate-fadeUp"
      style={{
        animationDelay: `${index * 60}ms`,
        border: '1px solid var(--border)',
        borderLeft: `3px solid ${meta.color}`,
        borderRadius: 'var(--r-md)',
        overflow: 'hidden',
        background: 'var(--surface)',
        transition: 'box-shadow var(--t-fast)',
      }}
    >
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          width: '100%',
          padding: '12px 14px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 10,
          background: 'none',
          textAlign: 'left',
          cursor: 'pointer',
        }}
      >
        <div style={{
          width: 28, height: 28,
          borderRadius: 6,
          background: meta.color + '15',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
          marginTop: 1,
        }}>
          <Icon size={13} color={meta.color} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 4 }}>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.05em',
              color: meta.color, textTransform: 'uppercase',
            }}>
              {meta.label}
            </span>
            <span style={{
              fontSize: 10, padding: '1px 7px', borderRadius: 99,
              background: catColor + '15', color: catColor, fontWeight: 600,
              textTransform: 'capitalize',
            }}>
              {action.category}
            </span>
          </div>
          <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.4 }}>
            {action.action}
          </p>
        </div>
        <div style={{ flexShrink: 0, color: 'var(--text-muted)', marginTop: 4 }}>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {expanded && (
        <div style={{
          padding: '0 14px 12px 52px',
          fontSize: 12,
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
          borderTop: '1px solid var(--border-soft)',
          paddingTop: 10,
        }}>
          <strong style={{ display: 'block', marginBottom: 4, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            Rationale
          </strong>
          {action.rationale}
        </div>
      )}
    </div>
  )
}

export default function MitigationPanel({ actions = [] }) {
  const [filter, setFilter] = useState('all')

  const priorities = ['all', 'immediate', 'short-term', 'long-term']
  const filtered = filter === 'all' ? actions : actions.filter(a => a.priority === filter)

  const counts = {
    immediate:    actions.filter(a => a.priority === 'immediate').length,
    'short-term': actions.filter(a => a.priority === 'short-term').length,
    'long-term':  actions.filter(a => a.priority === 'long-term').length,
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
          <CheckSquare size={15} color="var(--risk-low)" />
          <h3 style={{ fontSize: 14, fontWeight: 600 }}>Mitigation Actions</h3>
          <span style={{
            padding: '1px 8px', borderRadius: 99,
            background: 'var(--surface-2)',
            fontSize: 11, color: 'var(--text-muted)',
          }}>
            {actions.length}
          </span>
        </div>

        {/* Priority summary chips */}
        <div style={{ display: 'flex', gap: 4 }}>
          {priorities.map(p => {
            const meta = PRIORITY_META[p]
            const count = p === 'all' ? actions.length : counts[p]
            return (
              <button
                key={p}
                onClick={() => setFilter(p)}
                style={{
                  padding: '3px 10px',
                  borderRadius: 99,
                  fontSize: 11,
                  fontWeight: 500,
                  border: `1px solid ${filter === p ? (meta?.color || 'var(--navy)') : 'var(--border)'}`,
                  background: filter === p ? (meta?.color || 'var(--navy)') + '15' : 'transparent',
                  color: filter === p ? (meta?.color || 'var(--navy)') : 'var(--text-secondary)',
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  transition: 'all var(--t-fast)',
                }}
              >
                {p === 'all' ? 'All' : p} {count > 0 ? `(${count})` : ''}
              </button>
            )
          })}
        </div>
      </div>

      {/* Actions list */}
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.length === 0 ? (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, padding: 24 }}>
            No actions for this filter
          </p>
        ) : (
          filtered.map((a, i) => <ActionCard key={i} action={a} index={i} />)
        )}
      </div>
    </div>
  )
}
