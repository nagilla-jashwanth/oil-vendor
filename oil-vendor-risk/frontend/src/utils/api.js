/**
 * API utilities for the Oil Vendor Risk Management frontend.
 */

const BASE = '/api'

export async function fetchVendors() {
  const res = await fetch(`${BASE}/vendors`)
  if (!res.ok) throw new Error('Failed to fetch vendors')
  return res.json()
}

/**
 * Run a streaming assessment via SSE.
 * Calls onStatus(msg) for each progress event and
 * onReport(report) once the final report arrives.
 */
export function streamAssessment({ vendorName, context = '', onStatus, onReport, onError, onDone }) {
  const params = new URLSearchParams({
    vendor_name: vendorName,
    additional_context: context,
  })
  const url = `${BASE}/assess/stream?${params.toString()}`
  const es = new EventSource(url)

  es.addEventListener('status', (e) => {
    try {
      const data = JSON.parse(e.data)
      onStatus?.(data)
    } catch (_) {}
  })

  es.addEventListener('report', (e) => {
    try {
      const data = JSON.parse(e.data)
      onReport?.(data)
      es.close()
      onDone?.()
    } catch (_) {}
  })

  es.addEventListener('error', (e) => {
    try {
      const data = JSON.parse(e.data)
      onError?.(data.message || 'Unknown error')
    } catch (_) {
      onError?.('Connection error')
    }
    es.close()
    onDone?.()
  })

  es.onerror = () => {
    onError?.('Stream connection lost')
    es.close()
    onDone?.()
  }

  return () => es.close()  // cleanup fn
}

export function getRiskColor(level) {
  const map = {
    low: 'var(--risk-low)',
    medium: 'var(--risk-medium)',
    high: 'var(--risk-high)',
    critical: 'var(--risk-critical)',
  }
  return map[level] || 'var(--text-secondary)'
}

export function getRiskBg(level) {
  const map = {
    low: 'var(--risk-low-bg)',
    medium: 'var(--risk-medium-bg)',
    high: 'var(--risk-high-bg)',
    critical: 'var(--risk-critical-bg)',
  }
  return map[level] || 'var(--surface-2)'
}

export function getCategoryColor(cat) {
  const map = {
    financial:    'var(--cat-financial)',
    operational:  'var(--cat-operational)',
    compliance:   'var(--cat-compliance)',
    reputational: 'var(--cat-reputational)',
    geopolitical: 'var(--cat-geopolitical)',
  }
  return map[cat] || 'var(--text-secondary)'
}

export function getSeverityLabel(score) {
  if (score >= 8) return 'Critical'
  if (score >= 6) return 'High'
  if (score >= 4) return 'Medium'
  return 'Low'
}

export function getSeverityColor(score) {
  if (score >= 8) return 'var(--risk-critical)'
  if (score >= 6) return 'var(--risk-high)'
  if (score >= 4) return 'var(--risk-medium)'
  return 'var(--risk-low)'
}
