import React from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import { FileText, Database } from 'lucide-react'

export default function ExecutiveSummary({ report }) {
  const { executive_summary, risk_score, data_sources_used = [] } = report

  const radarData = [
    { subject: 'Financial',    score: risk_score.financial    },
    { subject: 'Operational',  score: risk_score.operational  },
    { subject: 'Compliance',   score: risk_score.compliance   },
    { subject: 'Reputational', score: risk_score.reputational },
    { subject: 'Geopolitical', score: risk_score.geopolitical },
  ]

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)',
      overflow: 'hidden',
      boxShadow: 'var(--shadow-sm)',
    }}>
      <div style={{
        padding: '14px 20px',
        borderBottom: '1px solid var(--border-soft)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <FileText size={15} color="var(--navy)" />
        <h3 style={{ fontSize: 14, fontWeight: 600 }}>Executive Summary</h3>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: 0 }}>
        {/* Left: text */}
        <div style={{ padding: '20px 24px', borderRight: '1px solid var(--border-soft)' }}>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.75, marginBottom: 'var(--sp-5)' }}>
            {executive_summary}
          </p>

          {data_sources_used.length > 0 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <Database size={12} color="var(--text-muted)" />
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Data Sources
                </span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {data_sources_used.map((src, i) => (
                  <span key={i} style={{
                    padding: '3px 10px',
                    borderRadius: 99,
                    background: 'var(--surface-2)',
                    border: '1px solid var(--border)',
                    fontSize: 11,
                    color: 'var(--text-secondary)',
                  }}>
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: radar */}
        <div style={{ padding: '12px 8px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Risk Profile
          </p>
          <ResponsiveContainer width="100%" height={190}>
            <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
              />
              <Radar
                dataKey="score"
                stroke="var(--navy)"
                fill="var(--navy)"
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <Tooltip
                formatter={(v) => [`${Math.round(v)}/100`, 'Score']}
                contentStyle={{
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
