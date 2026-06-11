/* ─────────────────────────────────────────────────────────────────────────────
   Oil Vendor Risk Management – app.js
───────────────────────────────────────────────────────────────────────────── */

"use strict";

// ── State ────────────────────────────────────────────────────────────────────

const state = {
  loading: false,
  history: [],        // array of RiskAssessment objects
  currentResult: null,
};

// ── DOM refs ─────────────────────────────────────────────────────────────────

const $ = id => document.getElementById(id);

// ── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", async () => {
  await loadPresets();
  bindEvents();
  renderEmptyState();
});

// ── Presets ──────────────────────────────────────────────────────────────────

async function loadPresets() {
  try {
    const res = await fetch("/api/vendors/presets");
    const data = await res.json();
    renderPresets(data.vendors);
  } catch (e) {
    console.warn("Could not load presets", e);
  }
}

function renderPresets(vendors) {
  const container = $("presetCards");
  container.innerHTML = "";
  vendors.forEach(v => {
    const card = document.createElement("div");
    card.className = "preset-card";
    card.innerHTML = `
      <div class="preset-ticker">${v.ticker}</div>
      <div class="preset-name">${v.name}</div>
      <div class="preset-desc">${v.description}</div>
    `;
    card.addEventListener("click", () => {
      document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      $("vendorName").value = v.name;
      $("vendorTicker").value = v.ticker;
    });
    container.appendChild(card);
  });
}

// ── Events ───────────────────────────────────────────────────────────────────

function bindEvents() {
  $("assessBtn").addEventListener("click", runAssessment);
  $("vendorName").addEventListener("keydown", e => {
    if (e.key === "Enter") runAssessment();
  });
}

// ── Assessment ───────────────────────────────────────────────────────────────

async function runAssessment() {
  const vendorName = $("vendorName").value.trim();
  const ticker = $("vendorTicker").value.trim();

  if (!vendorName) {
    $("vendorName").focus();
    $("vendorName").style.borderColor = "var(--risk-critical)";
    setTimeout(() => $("vendorName").style.borderColor = "", 1500);
    return;
  }

  state.loading = true;
  renderLoadingState(vendorName);
  $("assessBtn").disabled = true;

  try {
    const res = await fetch("/api/assess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vendor_name: vendorName, ticker: ticker || null }),
    });

    const data = await res.json();

    if (data.status === "success" && data.data) {
      state.currentResult = data.data;
      state.history.unshift(data.data);
      renderResult(data.data);
      renderHistory();
    } else {
      renderErrorState(data.error || "Unknown error occurred.");
    }
  } catch (err) {
    renderErrorState(`Network error: ${err.message}`);
  } finally {
    state.loading = false;
    $("assessBtn").disabled = false;
  }
}

// ── Loading state ─────────────────────────────────────────────────────────────

const STEPS = [
  { key: "intel",    label: "Gathering web & news intelligence…" },
  { key: "social",   label: "Scanning social media signals…" },
  { key: "video",    label: "Analysing video intelligence…" },
  { key: "geo",      label: "Assessing geopolitical exposure…" },
  { key: "scoring",  label: "Computing risk scores…" },
  { key: "mitigate", label: "Generating mitigation actions…" },
];

let stepInterval = null;

function renderLoadingState(vendorName) {
  clearInterval(stepInterval);
  $("contentArea").innerHTML = `
    <div class="state-panel">
      <div class="spinner"></div>
      <div class="state-title">Assessing ${escHtml(vendorName)}</div>
      <div class="state-desc">Running multi-source intelligence pipeline. This takes 45–90 seconds.</div>
      <div class="progress-steps" id="progressSteps">
        ${STEPS.map((s, i) => `
          <div class="progress-step" id="step-${s.key}">
            <div class="step-dot"></div>
            <span>${s.label}</span>
          </div>
        `).join("")}
      </div>
    </div>
  `;

  let currentStep = 0;
  const activateStep = () => {
    if (currentStep > 0) {
      const prev = $(`step-${STEPS[currentStep - 1].key}`);
      if (prev) { prev.classList.remove("active"); prev.classList.add("done"); }
    }
    if (currentStep < STEPS.length) {
      const cur = $(`step-${STEPS[currentStep].key}`);
      if (cur) cur.classList.add("active");
      currentStep++;
    }
  };
  activateStep();
  stepInterval = setInterval(() => {
    if (currentStep < STEPS.length) activateStep();
  }, 10000);
}

// ── Empty state ───────────────────────────────────────────────────────────────

function renderEmptyState() {
  $("contentArea").innerHTML = `
    <div class="state-panel">
      <div class="state-icon">🛢️</div>
      <div class="state-title">Vendor Risk Intelligence</div>
      <div class="state-desc">
        Select a pre-configured oil vendor or enter any company name to launch a
        full AI-powered risk assessment across financial, operational, compliance,
        reputational, and geopolitical dimensions.
      </div>
    </div>
  `;
}

// ── Error state ───────────────────────────────────────────────────────────────

function renderErrorState(msg) {
  $("contentArea").innerHTML = `
    <div class="error-panel">
      <div class="error-icon">⚠️</div>
      <div>
        <div class="error-title">Assessment Failed</div>
        <div class="error-msg">${escHtml(msg)}</div>
      </div>
    </div>
  `;
}

// ── Result renderer ───────────────────────────────────────────────────────────

function renderResult(a) {
  clearInterval(stepInterval);

  const scoreColor = getScoreColor(a.overall_score);
  const riskClass = a.risk_level;

  $("contentArea").innerHTML = `

    <!-- Header -->
    <div class="result-header">
      <div>
        <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.5);margin-bottom:6px;">
          Risk Assessment Report
        </div>
        <div class="result-vendor-name">${escHtml(a.vendor_name)}</div>
        <div style="margin:8px 0;">
          <div class="risk-meter" title="Risk Score: ${a.overall_score}">
            <div class="risk-meter-needle" id="riskNeedle"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:rgba(255,255,255,0.4);margin-top:2px;">
            <span>Low</span><span>Medium</span><span>High</span><span>Critical</span>
          </div>
        </div>
        <div class="result-summary">${escHtml(a.summary)}</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:0;">
        <div class="score-circle" style="border-color:${scoreColor}40;">
          <div class="score-number" style="color:${scoreColor}">${Math.round(a.overall_score)}</div>
          <div class="score-label">Risk Score</div>
        </div>
        <div class="score-level badge-${riskClass}" style="margin-top:8px;">${a.risk_level.toUpperCase()}</div>
      </div>
    </div>

    <!-- Category Scores -->
    <div class="score-grid">
      ${renderScoreCard("Financial",    a.financial_score)}
      ${renderScoreCard("Operational",  a.operational_score)}
      ${renderScoreCard("Compliance",   a.compliance_score)}
      ${renderScoreCard("Reputational", a.reputational_score)}
      ${renderScoreCard("Geopolitical", a.geopolitical_score)}
    </div>

    <!-- Tabs: Findings | Radar | Mitigations | Sources -->
    <div class="section-card">
      <div class="tabs">
        <button class="tab-btn active" data-tab="findings">⚠️ Risk Findings (${a.findings.length})</button>
        <button class="tab-btn" data-tab="radar">📊 Risk Radar</button>
        <button class="tab-btn" data-tab="mitigations">🛡️ Mitigations (${a.mitigations.length})</button>
        <button class="tab-btn" data-tab="sources">🔗 Sources</button>
      </div>

      <!-- Findings -->
      <div class="tab-panel active" id="tab-findings">
        <div class="findings-list">
          ${a.findings.length
            ? a.findings.map(renderFinding).join("")
            : "<p style='color:#9B9589;font-size:0.85rem;'>No specific findings identified.</p>"
          }
        </div>
      </div>

      <!-- Radar -->
      <div class="tab-panel" id="tab-radar">
        <div class="chart-wrap">
          <canvas id="radarChart" width="380" height="340"></canvas>
        </div>
      </div>

      <!-- Mitigations -->
      <div class="tab-panel" id="tab-mitigations">
        <div class="mitigation-list">
          ${a.mitigations.length
            ? a.mitigations.map(renderMitigation).join("")
            : "<p style='color:#9B9589;font-size:0.85rem;'>No mitigation actions generated.</p>"
          }
        </div>
      </div>

      <!-- Sources -->
      <div class="tab-panel" id="tab-sources">
        <div class="sources-list">
          ${a.sources_consulted.length
            ? a.sources_consulted.map(s =>
                `<a class="source-chip" href="${escHtml(s)}" target="_blank" title="${escHtml(s)}">${escHtml(s)}</a>`
              ).join("")
            : "<p style='color:#9B9589;font-size:0.85rem;'>No sources recorded.</p>"
          }
        </div>
      </div>
    </div>

  `;

  // Animate needle
  setTimeout(() => {
    const needle = $("riskNeedle");
    if (needle) needle.style.left = `${Math.min(Math.max(a.overall_score, 2), 98)}%`;
  }, 100);

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      $(`tab-${btn.dataset.tab}`).classList.add("active");
      if (btn.dataset.tab === "radar") drawRadar(a);
    });
  });
}

// ── Sub-renderers ─────────────────────────────────────────────────────────────

function renderScoreCard(label, score) {
  const color = getScoreColor(score);
  return `
    <div class="score-card">
      <div class="score-card-label">${label}</div>
      <div class="score-card-value" style="color:${color}">${Math.round(score)}</div>
      <div class="score-bar-wrap">
        <div class="score-bar" style="width:${score}%;background:${color};"></div>
      </div>
    </div>
  `;
}

function renderFinding(f) {
  const icons = {
    financial: "💰", operational: "⚙️", compliance: "📋",
    reputational: "📢", geopolitical: "🌍",
  };
  return `
    <div class="finding-item ${f.severity}">
      <div class="finding-icon">${icons[f.category] || "⚠️"}</div>
      <div>
        <div class="finding-title">${escHtml(f.title)}</div>
        <div class="finding-detail">${escHtml(f.detail)}</div>
        ${f.source ? `<div class="finding-source">📎 ${escHtml(f.source)}</div>` : ""}
      </div>
      <div class="finding-severity sev-${f.severity}">${f.severity}</div>
    </div>
  `;
}

function renderMitigation(m) {
  const labels = { immediate: "Now", short_term: "6mo", long_term: "Long" };
  return `
    <div class="mitigation-item">
      <div class="mitigation-priority-dot prio-${m.priority}">${labels[m.priority] || "?"}</div>
      <div>
        <div class="mitigation-action">${escHtml(m.action)}</div>
        <div class="mitigation-rationale">${escHtml(m.rationale)}</div>
      </div>
    </div>
  `;
}

// ── Radar Chart (pure Canvas, no lib needed) ──────────────────────────────────

function drawRadar(a) {
  const canvas = $("radarChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const maxR = Math.min(cx, cy) - 50;
  const labels = ["Financial", "Operational", "Compliance", "Reputational", "Geopolitical"];
  const scores = [a.financial_score, a.operational_score, a.compliance_score, a.reputational_score, a.geopolitical_score];
  const N = labels.length;
  const angleStep = (2 * Math.PI) / N;
  const startAngle = -Math.PI / 2;

  ctx.clearRect(0, 0, W, H);

  // Background rings
  for (let ring = 1; ring <= 5; ring++) {
    const r = (ring / 5) * maxR;
    ctx.beginPath();
    for (let i = 0; i < N; i++) {
      const angle = startAngle + i * angleStep;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = "#E2E0D8";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Ring label
    ctx.fillStyle = "#9B9589";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(ring * 20, cx + 4, cy - r + 4);
  }

  // Spokes
  for (let i = 0; i < N; i++) {
    const angle = startAngle + i * angleStep;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + maxR * Math.cos(angle), cy + maxR * Math.sin(angle));
    ctx.strokeStyle = "#E2E0D8";
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Data polygon
  ctx.beginPath();
  for (let i = 0; i < N; i++) {
    const angle = startAngle + i * angleStep;
    const r = (scores[i] / 100) * maxR;
    const x = cx + r * Math.cos(angle);
    const y = cy + r * Math.sin(angle);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = "rgba(26,39,68,0.12)";
  ctx.fill();
  ctx.strokeStyle = "#1A2744";
  ctx.lineWidth = 2;
  ctx.stroke();

  // Data points
  for (let i = 0; i < N; i++) {
    const angle = startAngle + i * angleStep;
    const r = (scores[i] / 100) * maxR;
    const x = cx + r * Math.cos(angle);
    const y = cy + r * Math.sin(angle);
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fillStyle = getScoreColor(scores[i]);
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // Labels
  ctx.fillStyle = "#1A2744";
  ctx.font = "bold 11px Inter, sans-serif";
  ctx.textAlign = "center";
  for (let i = 0; i < N; i++) {
    const angle = startAngle + i * angleStep;
    const r = maxR + 26;
    const x = cx + r * Math.cos(angle);
    const y = cy + r * Math.sin(angle) + 4;
    ctx.fillText(labels[i], x, y);
    ctx.fillStyle = "#9B9589";
    ctx.font = "10px Inter, sans-serif";
    ctx.fillText(Math.round(scores[i]), x, y + 13);
    ctx.fillStyle = "#1A2744";
    ctx.font = "bold 11px Inter, sans-serif";
  }
}

// ── History ───────────────────────────────────────────────────────────────────

function renderHistory() {
  const list = $("historyList");
  if (!list) return;
  list.innerHTML = state.history.slice(0, 8).map(a => `
    <div class="history-item" data-vendor="${escHtml(a.vendor_name)}">
      <span class="history-vendor">${escHtml(a.vendor_name)}</span>
      <span class="history-badge badge-${a.risk_level}">${a.risk_level}</span>
    </div>
  `).join("");

  list.querySelectorAll(".history-item").forEach((el, i) => {
    el.addEventListener("click", () => renderResult(state.history[i]));
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getScoreColor(score) {
  if (score >= 76) return "#C0392B";
  if (score >= 51) return "#E67E22";
  if (score >= 26) return "#c9a800";
  return "#27AE60";
}

function escHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
