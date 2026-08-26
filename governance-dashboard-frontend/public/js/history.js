// history.js — Prompt history page logic.
// Depends on: api.js (api, ApiError), auth.js (guardProtectedPage, initLogoutButton)
//
// Endpoint: GET /prompts/history
// Returns:  [{ id, prompt, response, model, status, timestamp }, ...]
//
// CSV export is 100% client-side — mirrors History.py which uses
// pandas df.to_csv().  No backend export endpoint exists.
// Filtering is also 100% client-side on the in-memory array.

guardProtectedPage();
initLogoutButton();

// ── DOM refs ──────────────────────────────────────────────────────────────────
const loadingEl    = document.getElementById('history-loading');
const errorEl      = document.getElementById('history-error');
const contentEl    = document.getElementById('history-content');
const tableBody    = document.getElementById('history-tbody');
const filterCount  = document.getElementById('filter-count');

// Filters
const filterStart  = document.getElementById('filter-start');
const filterEnd    = document.getElementById('filter-end');
const filterSearch = document.getElementById('filter-search');
const downloadBtn  = document.getElementById('download-csv');

// Modal
const modal        = document.getElementById('detail-modal');
const modalClose   = document.getElementById('modal-close');
const modalPrompt  = document.getElementById('modal-prompt');
const modalResp    = document.getElementById('modal-response');
const modalModel   = document.getElementById('modal-model');
const modalStatus  = document.getElementById('modal-status');
const modalTs      = document.getElementById('modal-timestamp');
const modalId      = document.getElementById('modal-id');

// ── State ─────────────────────────────────────────────────────────────────────
let allRecords  = [];   // full dataset, never mutated after load
let filteredRec = [];   // result of applyFilters(), used for CSV + table

// ── Helpers ───────────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function truncate(str, max = 80) {
  const s = String(str ?? '');
  return s.length > max ? s.slice(0, max) + '…' : s;
}

function badgeHtml(status) {
  const s = String(status ?? '').toUpperCase();
  const cls = s === 'SUCCESS' ? 'badge--success'
            : s === 'FAILED'  ? 'badge--failed'
            : 'badge--unknown';
  return `<span class="badge ${cls}">${escHtml(s || '—')}</span>`;
}

// normaliseTs — the backend (SQLite/SQLAlchemy) returns naive UTC timestamps
// like "2026-08-26T04:02:51.360837" with NO timezone suffix.  JS treats these
// as **local** time rather than UTC, so the displayed time is wrong by the
// machine's UTC offset.  Appending "Z" forces unambiguous UTC interpretation
// so new Date() converts it correctly to local time for display.
function normaliseTs(ts) {
  if (!ts) return ts;
  const s = String(ts);
  // Already has an offset (+HH:MM, -HH:MM) or ends with Z — leave it alone.
  if (/Z$|[+-]\d{2}:\d{2}$/.test(s)) return s;
  return s + 'Z';
}

// fmtTimestamp — combined, used in the modal detail view.
function fmtTimestamp(ts) {
  if (!ts) return '—';
  try {
    return new Date(normaliseTs(ts)).toLocaleString();
  } catch {
    return String(ts);
  }
}

// fmtDate / fmtTime — split display used in the table columns.
function fmtDate(ts) {
  if (!ts) return '—';
  try {
    return new Date(normaliseTs(ts)).toLocaleDateString();
  } catch {
    return String(ts);
  }
}

function fmtTime(ts) {
  if (!ts) return '—';
  try {
    return new Date(normaliseTs(ts)).toLocaleTimeString();
  } catch {
    return String(ts);
  }
}

function responseLength(rec) {
  return rec.response ? String(rec.response).length : 0;
}

// ── Render table from filtered array ─────────────────────────────────────────
function renderTable(records) {
  filteredRec = records;
  filterCount.textContent = `Showing ${records.length} of ${allRecords.length} record${allRecords.length !== 1 ? 's' : ''}`;

  if (records.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="8" class="empty-state">No records match the current filters.</td>
      </tr>`;
    return;
  }

  tableBody.innerHTML = records.map(rec => `
    <tr>
      <td>${rec.id}</td>
      <td><span class="truncate" title="${escHtml(rec.prompt)}">${escHtml(truncate(rec.prompt))}</span></td>
      <td>${escHtml(rec.model ?? '—')}</td>
      <td>${badgeHtml(rec.status)}</td>
      <td>${responseLength(rec)}</td>
      <td>${escHtml(fmtDate(rec.timestamp))}</td>
      <td>${escHtml(fmtTime(rec.timestamp))}</td>
      <td><button class="btn-view" data-id="${rec.id}">View</button></td>
    </tr>
  `).join('');

  // Wire up View buttons (event delegation would also work for large tables)
  tableBody.querySelectorAll('.btn-view').forEach(btn => {
    btn.addEventListener('click', () => openModal(Number(btn.dataset.id)));
  });
}

// ── Client-side filtering ─────────────────────────────────────────────────────
//
// Bug 1 fix — root cause:
//   `new Date("YYYY-MM-DD")` (the value returned by <input type="date">)
//   is parsed as **UTC midnight**, not local midnight.  In UTC+5:30 that
//   means "2026-08-26" becomes 2026-08-26T00:00:00Z = 2026-08-26T05:30 IST.
//   `end.setHours(23,59,59,999)` then works in local time, but `start` is
//   still UTC midnight, creating an asymmetric boundary.  When start===end
//   the "end" boundary (local EOD) is correct but any record timestamped
//   in UTC before 05:30 IST would fall before the UTC-midnight `start`.
//
//   Fix: use `parseDateInputAsLocal()` which splits the YYYY-MM-DD string
//   and calls `new Date(y, m-1, d)` — always local midnight, on all
//   platforms, regardless of timezone offset.

function parseDateInputAsLocal(dateStr) {
  // dateStr from <input type="date"> is always "YYYY-MM-DD" or empty.
  if (!dateStr) return null;
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d); // local midnight
}

function applyFilters() {
  const start  = parseDateInputAsLocal(filterStart.value);  // local 00:00:00.000
  const end    = parseDateInputAsLocal(filterEnd.value);    // local 00:00:00.000 → extended below
  const search = filterSearch.value.trim().toLowerCase();

  // Extend end to local end-of-day so the filter is fully inclusive of the
  // selected date.  This correctly handles start === end (same-day filter)
  // and is not a special case — it applies to every end-date selection.
  if (end) end.setHours(23, 59, 59, 999);

  const result = allRecords.filter(rec => {
    const ts = rec.timestamp ? new Date(rec.timestamp) : null;

    if (start && ts && ts < start) return false;
    if (end   && ts && ts > end)   return false;
    if (search && !String(rec.prompt ?? '').toLowerCase().includes(search)) return false;

    return true;
  });

  renderTable(result);
}

// Wire filter inputs to applyFilters — live, no re-fetch
filterStart.addEventListener('change', applyFilters);
filterEnd.addEventListener('change', applyFilters);
filterSearch.addEventListener('input', applyFilters);

// ── Modal ─────────────────────────────────────────────────────────────────────
function openModal(id) {
  // Look up from the FULL dataset (not filtered) so detail view always works
  const rec = allRecords.find(r => r.id === id);
  if (!rec) return;

  modalId.textContent        = rec.id;
  modalModel.textContent     = rec.model ?? 'N/A';
  modalStatus.innerHTML      = badgeHtml(rec.status);
  modalTs.textContent        = fmtTimestamp(rec.timestamp);
  modalPrompt.textContent    = rec.prompt ?? '—';
  modalResp.textContent      = rec.response ?? 'No AI response available.';

  modal.classList.add('visible');
}

function closeModal() {
  modal.classList.remove('visible');
}

modalClose.addEventListener('click', closeModal);

// Close on backdrop click (but not on card click)
modal.addEventListener('click', (e) => {
  if (e.target === modal) closeModal();
});

// Close on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});

// ── CSV download — currently-filtered data only ───────────────────────────────
downloadBtn.addEventListener('click', () => {
  if (filteredRec.length === 0) return;

  const cols = ['id', 'prompt', 'model', 'status', 'response_length', 'timestamp', 'response'];

  function csvCell(val) {
    const s = String(val ?? '');
    // Quote cells that contain commas, quotes, or newlines
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  }

  const header = cols.map(csvCell).join(',');
  const rows   = filteredRec.map(rec => [
    rec.id,
    rec.prompt,
    rec.model ?? '',
    rec.status ?? '',
    responseLength(rec),
    rec.timestamp ?? '',
    rec.response ?? '',
  ].map(csvCell).join(','));

  const csv  = [header, ...rows].join('\r\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'prompt_history.csv';
  a.click();
  URL.revokeObjectURL(url);
});

// ── Initial data load ─────────────────────────────────────────────────────────
async function loadHistory() {
  try {
    const data = await api.get('/prompts/history');

    allRecords = Array.isArray(data) ? data : [];

    loadingEl.classList.add('hidden');
    contentEl.classList.remove('hidden');

    if (allRecords.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="8" class="empty-state">No prompt history available yet.</td></tr>`;
      filterCount.textContent = 'No records found.';
      return;
    }

    renderTable(allRecords);

  } catch (err) {
    loadingEl.classList.add('hidden');
    errorEl.textContent = err.message || 'Failed to load history. Is the backend running?';
    errorEl.classList.remove('hidden');
  }
}

loadHistory();
