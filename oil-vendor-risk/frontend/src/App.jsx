import React, { useState, useCallback } from 'react'
import { RotateCcw, ShieldAlert } from 'lucide-react'
import Header from './components/Header'
import VendorSelector from './components/VendorSelector'
import AgentFeed from './components/AgentFeed'
import RiskScoreCard from './components/RiskScoreCard'
import RiskSignalsTable from './components/RiskSignalsTable'
import MitigationPanel from './components/MitigationPanel'
import ExecutiveSummary from './components/ExecutiveSummary'
import { streamAssessment } from './utils/api'

export default function App() {
  const [phase, setPhase] = useState('idle')         // idle | assessing | done | error
  const [currentVendor, setCurrentVendor] = useState(null)
  const [agentMessages, setAgentMessages] = useState([])
  const [report, setReport] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [cleanup, setCleanup] = useState(null)

  const startAssessment = useCallback((vendorName) => {
    // Reset state
    setCurrentVendor(vendorName)
    setAgentMessages([])
    setReport(null)
    setErrorMsg('')
    setPhase('assessing')

    const stopFn = streamAssessment({
      vendorName,
      onStatus: (msg) => setAgentMessages(prev => [...prev, msg]),
      onReport: (r) => {
        setReport(r)
        setPhase('done')
      },
      onError: (msg) => {
        setErrorMsg(msg)
        setPhase('error')
      },
      onDone: () => {
        setPhase(p => p === 'assessing' ? 'error' : p)
      },
    })
    setCleanup(() => stopFn)
  }, [])

  const reset = () => {
    cleanup?.()
    setPhase('idle')
    setCurrentVendor(null)
    setAgentMessages([])
    setReport(null)
    setErrorMsg('')
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <Header />

      <main style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: 'var(--sp-8) var(--sp-6)',
      }}>

        {/* ── IDLE: Vendor selection ── */}
        {phase === 'idle' && (
          <div className="animate-fadeUp" style={{
            display: 'grid',
            gridTemplateColumns: '1fr 340px',
            gap: 'var(--sp-8)',
            alignItems: 'flex-start',
          }}>
            {/* Selector card */}
            <div style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-xl)',
              padding: 'var(--sp-8)',
              boxShadow: 'var(--shadow-md)',
            }}>
              <div style={{ marginBottom: 'var(--sp-6)' }}>
                <h1 style={{ fontSize: 28, marginBottom: 8 }}>Vendor Risk Assessment</h1>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  Select an oil vendor to run an AI-powered multi-agent risk assessment across
                  financial, operational, compliance, and reputational dimensions.
                </p>
              </div>
              <VendorSelector onSelect={startAssessment} disabled={phase === 'assessing'} />
            </div>

            {/* Info sidebar */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
              <InfoCard
                title="4 Specialist Agents"
                body="Financial, Operational, Compliance, and Social/Reputational agents run simultaneously using real web data."
                accent="var(--navy)"
              />
              <InfoCard
                title="7 Live Data Tools"
                body="Web search, news, social media (X/Reddit), YouTube, regulatory filings, financial data, and operational incident feeds."
                accent="var(--amber)"
              />
              <InfoCard
                title="Actionable Output"
                body="Risk scores across 5 categories, prioritised mitigation actions, and an executive summary ready for procurement leadership."
                accent="var(--risk-low)"
              />
            </div>
          </div>
        )}

        {/* ── ASSESSING: Live feed ── */}
        {(phase === 'assessing' || (phase === 'done' && agentMessages.length > 0)) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-6)' }}>

            {phase === 'assessing' && (
              <div className="animate-fadeUp" style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '16px 24px',
                background: 'var(--navy)',
                borderRadius: 'var(--r-lg)',
                color: '#fff',
              }}>
                <div style={{
                  width: 10, height: 10, borderRadius: '50%', background: 'var(--amber-2)',
                  flexShrink: 0, position: 'relative',
                }}>
                  <div style={{
                    position: 'absolute', inset: -3, borderRadius: '50%',
                    background: 'var(--amber-2)', animation: 'pulse-ring 1.2s ease-out infinite',
                  }} />
                </div>
                <div>
                  <p style={{ fontWeight: 600, marginBottom: 2 }}>
                    Assessing {currentVendor}
                  </p>
                  <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>
                    AI agents are gathering data from multiple sources. This may take 1–3 minutes.
                  </p>
                </div>
              </div>
            )}

            <AgentFeed messages={agentMessages} vendorName={currentVendor} />
          </div>
        )}

        {/* ── DONE: Full report ── */}
        {phase === 'done' && report && (
          <div className="animate-fadeUp" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-6)' }}>

            {/* Report header bar */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 'var(--sp-4)', flexWrap: 'wrap',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <ShieldAlert size={20} color="var(--navy)" />
                <h2 style={{ fontSize: 20 }}>
                  Risk Report — {report.vendor_name}
                </h2>
              </div>
              <button
                onClick={reset}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '8px 16px',
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--r-md)',
                  fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all var(--t-fast)',
                }}
              >
                <RotateCcw size={14} />
                New Assessment
              </button>
            </div>

            {/* Top row: score + summary */}
            <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 'var(--sp-5)', alignItems: 'flex-start' }}>
              <RiskScoreCard report={report} />
              <ExecutiveSummary report={report} />
            </div>

            {/* Agent feed (collapsed) */}
            <AgentFeed messages={agentMessages} vendorName={currentVendor} />

            {/* Signals + Mitigations */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--sp-5)' }}>
              <RiskSignalsTable signals={report.signals || []} />
              <MitigationPanel actions={report.mitigation_actions || []} />
            </div>

            {/* Timestamp */}
            <p style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'right' }}>
              Assessment generated: {new Date(report.assessment_timestamp).toLocaleString()}
            </p>
          </div>
        )}

        {/* ── ERROR ── */}
        {phase === 'error' && (
          <div className="animate-fadeUp" style={{
            background: 'var(--risk-high-bg)',
            border: '1px solid var(--risk-high)',
            borderRadius: 'var(--r-lg)',
            padding: 'var(--sp-8)',
            textAlign: 'center',
          }}>
            <ShieldAlert size={32} color="var(--risk-high)" style={{ marginBottom: 12 }} />
            <h3 style={{ marginBottom: 8, color: 'var(--risk-high)' }}>Assessment Failed</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 20, fontSize: 13 }}>{errorMsg}</p>
            <button
              onClick={reset}
              style={{
                padding: '10px 24px',
                background: 'var(--navy)',
                color: '#fff',
                borderRadius: 'var(--r-md)',
                fontWeight: 600, fontSize: 14, cursor: 'pointer',
              }}
            >
              Try Again
            </button>
          </div>
        )}

      </main>
    </div>
  )
}

function InfoCard({ title, body, accent }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderLeft: `3px solid ${accent}`,
      borderRadius: 'var(--r-md)',
      padding: 'var(--sp-4) var(--sp-5)',
      boxShadow: 'var(--shadow-sm)',
    }}>
      <p style={{ fontWeight: 600, fontSize: 13, marginBottom: 6, color: 'var(--text-primary)' }}>{title}</p>
      <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{body}</p>
    </div>
  )
}
