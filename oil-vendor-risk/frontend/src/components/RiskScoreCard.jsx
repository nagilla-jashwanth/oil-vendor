import React from 'react'
import { getRiskColor, getRiskBg } from '../utils/api'

function ScoreGauge({ score, size = 80 }) {
  const r = size * 0.38
  const cx = size / 2
  const cy = size / 2
  const circumference = Math.PI * r  // half circle

  // Score 0-100 maps to arc
  const filled = (score / 100) * circumference

  const color = score >= 76 ? 'var(--risk-critical)'
    : score >= 56 ? 'var(--risk-high)'
    : score >= 31 ? 'var(--risk-medium)'
    : 'var(--risk-low)'

  return (
    <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
      {/* Track */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none"
        stroke="var(--border)"
        strokeWidth={size * 0.08}
        strokeLinecap="round"
      />
      {/* Fill */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none"
        stroke={color}
        strokeWidth={size * 0.08}
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circumference}`}
        style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1)' }}
      />
      {/* Score text */}
      <text
        x={cx}
        y={cy * 0.95}
        textAnchor="middle"
        fill={color}
        fontSize={size * 0.22}
        fontWeight="700"
        fontFamily="Inter, sans-serif"
      >
        {Math.round(score)}
      </text>
    </svg>
  )
}

function CategoryBar({ label, score, color }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 600, color }}>{Math.round(score)}</span>
      </div>
      <div style={{ height: 6, background: 'var(--border)', borderRadius: 99, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${score}%`,
          background: color,
          borderRadius: 99,
          transition: 'width 1.2s cubic-bezier(0.4,0,0.2,1)',
        }} />
      </div>
    </div>
  )
}

const CAT_COLORS = {
  financial:    'var(--cat-financial)',
  operational:  'var(--cat-operational)',
  compliance:   'var(--cat-compliance)',
  reputational: 'var(--cat-reputational)',
  geopolitical: 'var(--cat-geopolitical)',
}

export default function RiskScoreCard({ report }) {
  const { risk_score, risk_level, vendor_name } = report

  const levelColor = getRiskColor(risk_level)
  const levelBg    = getRiskBg(risk_level)

  return (
    <div className="animate-fadeUp" style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)',
      padding: 'var(--sp-6)',
      boxShadow: 'var(--shadow-sm)',
    }}>
      {/* Vendor name + level badge */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 'var(--sp-4)' }}>
        <div>
          <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
            Risk Assessment
          </p>
          <h2 style={{ fontSize: 18, fontFamily: 'DM Serif Display, serif', color: 'var(--text-primary)' }}>
            {vendor_name}
          </h2>
        </div>
        <span style={{
          padding: '4px 12px',
          borderRadius: 999,
          background: levelBg,
          color: levelColor,
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          border: `1.5px solid ${levelColor}30`,
        }}>
          {risk_level}
        </span>
      </div>

      {/* Gauge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-6)', marginBottom: 'var(--sp-6)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <ScoreGauge score={risk_score.overall} size={100} />
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Overall Score</p>
        </div>
        <div style={{ flex: 1 }}>
          {['financial','operational','compliance','reputational','geopolitical'].map(cat => (
            <CategoryBar
              key={cat}
              label={cat}
              score={risk_score[cat] ?? 0}
              color={CAT_COLORS[cat]}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
