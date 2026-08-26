// dashboard.js — AI Governance Dashboard main page logic.
// Depends on: api.js (api, ApiError), auth.js (guardProtectedPage, initLogoutButton)

guardProtectedPage();
initLogoutButton();

// ── DOM refs ──────────────────────────────────────────────────────────────────
const loadingEl  = document.getElementById('dashboard-loading');
const errorEl    = document.getElementById('dashboard-error');
const contentEl  = document.getElementById('dashboard-content');

// KPI cards — Core
const totalEl    = document.getElementById('kpi-total');
const aiEl       = document.getElementById('kpi-ai');
const manualEl   = document.getElementById('kpi-manual');

// KPI cards — Performance
const successRateEl     = document.getElementById('kpi-success-rate');
const failedEl          = document.getElementById('kpi-failed');
const longestEl         = document.getElementById('kpi-longest');

// Info boxes
const mostUsedModelEl   = document.getElementById('info-most-used-model');
const systemHealthEl    = document.getElementById('info-system-health');

// Latest prompt
const latestPromptEl    = document.getElementById('latest-prompt');

// Chart canvases
const distChartEl       = document.getElementById('chart-distribution');
const modelChartEl      = document.getElementById('chart-model-usage');

// Model usage table
const modelTableBody    = document.getElementById('model-table-body');

// ── Helpers ───────────────────────────────────────────────────────────────────
function showError(msg) {
  loadingEl.classList.add('hidden');
  contentEl.classList.add('hidden');
  errorEl.textContent = msg;
  errorEl.classList.remove('hidden');
}

function fmt(val, fallback = '—') {
  if (val === null || val === undefined) return fallback;
  return val;
}

// ── Chart.js helpers ──────────────────────────────────────────────────────────
function buildBarChart(canvas, labels, values, label, color) {
  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data: values,
        backgroundColor: color || 'rgba(37, 99, 235, 0.7)',
        borderRadius: 4,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0 },
          grid: { color: '#e5e7eb' },
        },
        x: {
          grid: { display: false },
        },
      },
    },
  });
}

// ── Main data fetch & render ──────────────────────────────────────────────────
async function loadDashboard() {
  try {
    // Fire all three requests in parallel
    const [analytics, kpis, modelUsage] = await Promise.all([
      api.get('/analytics/'),
      api.get('/analytics/dashboard-kpis'),
      api.get('/analytics/model-usage'),
    ]);

    // ── Section 1: Core KPIs (/analytics/)
    totalEl.textContent  = fmt(analytics.total_requests, 0);
    aiEl.textContent     = fmt(analytics.ai_requests, 0);
    manualEl.textContent = fmt(analytics.manual_requests, 0);

    // ── Section 2: Performance (/analytics/dashboard-kpis)
    successRateEl.textContent = `${fmt(kpis.success_rate, 0)}%`;
    failedEl.textContent      = fmt(kpis.failed_requests, 0);
    longestEl.textContent     = fmt(kpis.longest_response, 0);

    // ── Section 3: Request Distribution chart
    buildBarChart(
      distChartEl,
      ['AI Requests', 'Manual Requests'],
      [analytics.ai_requests, analytics.manual_requests],
      'Requests',
      ['rgba(37, 99, 235, 0.75)', 'rgba(107, 114, 128, 0.65)']
    );

    // ── Section 4: Model Insights
    if (modelUsage && modelUsage.length > 0) {
      // Chart
      buildBarChart(
        modelChartEl,
        modelUsage.map(r => r.model || 'Unknown'),
        modelUsage.map(r => r.count),
        'Usage',
        'rgba(37, 99, 235, 0.7)'
      );

      // Table
      modelTableBody.innerHTML = modelUsage.map(row => `
        <tr>
          <td>${escHtml(row.model || 'Unknown')}</td>
          <td>${row.count}</td>
        </tr>
      `).join('');
    } else {
      document.getElementById('model-insights-section').innerHTML =
        '<p style="color:var(--text-muted);font-size:0.875rem;">No model usage data available.</p>';
    }

    // ── Section 5: System Health + Most Used Model
    mostUsedModelEl.textContent = fmt(kpis.most_used_model, 'N/A');
    systemHealthEl.textContent  = `${fmt(kpis.success_rate, 0)}% success rate`;

    // ── Section 6: Latest Prompt
    latestPromptEl.textContent = fmt(kpis.latest_prompt, 'No prompts yet.');

    // Show content
    loadingEl.classList.add('hidden');
    contentEl.classList.remove('hidden');

  } catch (err) {
    showError(err.message || 'Failed to load dashboard data. Is the backend running?');
  }
}

// ── XSS guard ─────────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

loadDashboard();
