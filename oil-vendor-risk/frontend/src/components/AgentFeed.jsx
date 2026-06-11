import React, { useEffect, useRef } from 'react'
import {
  DollarSign, Cog, FileText, MessageSquare, BarChart2,
  CheckCircle, Loader, AlertCircle, Wrench
} from 'lucide-react'

const AGENT_META = {
  financial:    { label: 'Financial Agent',    icon: DollarSign,    color: 'var(--cat-financial)' },
  operational:  { label: 'Operational Agent',  icon: Cog,           color: 'var(--cat-operational)' },
  compliance:   { label: 'Compliance Agent',   icon: FileText,      color: 'var(--cat-compliance)' },
  social:       { label: 'Social Agent',       icon: MessageSquare, color: 'var(--cat-reputational)' },
  aggregator:   { label: 'Aggregator',         icon: BarChart2,     color: 'var(--navy)' },
  tool:         { label: 'Tool Call',          icon: Wrench,        color: 'var(--text-muted)' },
  orchestrator: { label: 'Orchestrator',       icon: BarChart2,     color: 'var(--navy)' },
}

function StatusDot({ status }) {
  if (status === 'done') return <CheckCircle size={14} color="var(--risk-low)" />
  if (status === 'error') return <AlertCircle size={14} color="var(--risk-high)" />
  return (
    <span style={{
      width: 14, height: 14,
      border: '2px solid var(--amber)',
      borderTopColor: 'transparent',
      borderRadius: '50%',
      display: 'inline-block',
      animation: 'spin 0.8s linear infinite',
      flexShrink: 0,
    }} />
  )
}

function AgentRow({ msg, index }) {
  const meta = AGENT_META[msg.agent] || AGENT_META.orchestrator
  const Icon = meta.icon

  return (
    <div
      className="animate-fadeUp"
      style={{
        animationDelay: `${index * 30}ms`,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10,
        padding: '8px 12px',
        borderRadius: 'var(--r-sm)',
        background: msg.status === 'done' ? 'rgba(5,150,105,0.04)' : 'transparent',
        transition: 'background var(--t-med)',
      }}
    >
      <div style={{
        width: 28, height: 28,
        borderRadius: 6,
        background: meta.color + '18',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Icon size={13} color={meta.color} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: meta.color }}>{meta.label}</span>
          <StatusDot status={msg.status} />
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4, wordBreak: 'break-word' }}>
          {msg.message}
        </p>
        {msg.data?.tool && (
          <span style={{
            display: 'inline-block',
            marginTop: 4,
            padding: '2px 8px',
            background: 'var(--surface-2)',
            borderRadius: 99,
            fontSize: 10,
            color: 'var(--text-muted)',
            fontFamily: 'monospace',
          }}>
            {msg.data.tool}
          </span>
        )}
      </div>
    </div>
  )
}

export default function AgentFeed({ messages, vendorName }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-soft)',
        background: 'var(--navy)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: 'var(--amber-2)',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute', inset: -2,
            borderRadius: '50%',
            background: 'var(--amber-2)',
            animation: 'pulse-ring 1.2s ease-out infinite',
            opacity: 0.5,
          }} />
        </div>
        <span style={{ fontSize: 12, fontWeight: 600, color: '#fff' }}>
          Live Agent Activity — {vendorName}
        </span>
        <span style={{
          marginLeft: 'auto',
          fontSize: 10,
          color: 'rgba(255,255,255,0.4)',
          background: 'rgba(255,255,255,0.08)',
          padding: '2px 8px',
          borderRadius: 99,
        }}>
          {messages.length} events
        </span>
      </div>

      {/* Feed */}
      <div style={{
        maxHeight: 380,
        overflowY: 'auto',
        padding: '8px 4px',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}>
        {messages.length === 0 ? (
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            Starting agents...
          </div>
        ) : (
          messages.map((msg, i) => <AgentRow key={i} msg={msg} index={i} />)
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
