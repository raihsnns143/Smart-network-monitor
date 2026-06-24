/**
 * dashboard.js
 * ============
 * Fetches chart data from /api/chart-data and renders four
 * Chart.js visualisations on the dashboard page.
 */

// ── Shared Chart.js defaults ──────────────────────────────────────────────────
Chart.defaults.color             = "#8b949e";
Chart.defaults.borderColor       = "rgba(255,255,255,0.06)";
Chart.defaults.font.family       = "'Inter', sans-serif";
Chart.defaults.plugins.legend.labels.boxWidth = 12;

// ── Colour palette ────────────────────────────────────────────────────────────
const COLORS = {
  primary:  "#4361ee",
  accent:   "#f72585",
  success:  "#2dc653",
  warning:  "#fca311",
  danger:   "#ef233c",
  info:     "#4cc9f0",
  purple:   "#7209b7",
  muted:    "#8b949e",
};

const PIE_PALETTE = [
  "#4361ee","#f72585","#4cc9f0","#2dc653",
  "#fca311","#ef233c","#7209b7","#43aa8b",
];

function hexAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── Fetch data & build charts ────────────────────────────────────────────────
async function loadCharts() {
  try {
    const resp = await fetch("/api/chart-data");
    if (!resp.ok) throw new Error("API error");
    const data = await resp.json();

    buildActivityChart(data.daily);
    buildTypeChart(data.device_types);
    buildAlertChart(data.alerts);
    buildTrafficChart(data.traffic);
  } catch (err) {
    console.error("Chart load failed:", err);
    buildDemoCharts();   // fallback with synthetic data
  }
}

// ── 1. Activity Line Chart ────────────────────────────────────────────────────
function buildActivityChart(daily) {
  const ctx = document.getElementById("activityChart");
  if (!ctx) return;
  new Chart(ctx, {
    type: "line",
    data: {
      labels: daily.labels,
      datasets: [
        {
          label: "Online",
          data: daily.online,
          borderColor: COLORS.success,
          backgroundColor: hexAlpha(COLORS.success, 0.12),
          borderWidth: 2.5,
          pointRadius: 4,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.4,
        },
        {
          label: "Offline",
          data: daily.offline,
          borderColor: COLORS.muted,
          backgroundColor: hexAlpha(COLORS.muted, 0.06),
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top" },
        tooltip: { cornerRadius: 8 },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { stepSize: 1 },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

// ── 2. Device Type Pie ────────────────────────────────────────────────────────
function buildTypeChart(types) {
  const ctx = document.getElementById("typeChart");
  if (!ctx) return;
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: types.labels.length ? types.labels : ["No Data"],
      datasets: [{
        data: types.data.length ? types.data : [1],
        backgroundColor: PIE_PALETTE,
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      cutout: "65%",
      plugins: {
        legend: { position: "bottom" },
        tooltip: { cornerRadius: 8 },
      },
    },
  });
}

// ── 3. Alert Severity Doughnut ─────────────────────────────────────────────────
function buildAlertChart(alerts) {
  const ctx = document.getElementById("alertChart");
  if (!ctx) return;
  const colorMap = {
    "Critical": COLORS.danger,
    "High":     COLORS.warning,
    "Medium":   COLORS.info,
    "Low":      COLORS.success,
  };
  const bgColors = (alerts.labels.length ? alerts.labels : ["No Alerts"])
    .map(l => colorMap[l] || COLORS.muted);

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: alerts.labels.length ? alerts.labels : ["No Alerts"],
      datasets: [{
        data: alerts.data.length ? alerts.data : [1],
        backgroundColor: bgColors,
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      cutout: "60%",
      plugins: {
        legend: { position: "bottom" },
      },
    },
  });
}

// ── 4. Traffic Bar Chart ──────────────────────────────────────────────────────
function buildTrafficChart(traffic) {
  const ctx = document.getElementById("trafficChart");
  if (!ctx) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: traffic.labels,
      datasets: [
        {
          label: "Sent (MB)",
          data: traffic.sent,
          backgroundColor: hexAlpha(COLORS.primary, 0.75),
          borderColor: COLORS.primary,
          borderWidth: 1,
          borderRadius: 6,
        },
        {
          label: "Received (MB)",
          data: traffic.recv,
          backgroundColor: hexAlpha(COLORS.info, 0.75),
          borderColor: COLORS.info,
          borderWidth: 1,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.raw.toFixed(1)} MB`,
          },
          cornerRadius: 8,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

// ── Fallback demo charts (when no DB data) ───────────────────────────────────
function buildDemoCharts() {
  const days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  buildActivityChart({
    labels: days,
    online:  [4,5,5,6,5,4,5],
    offline: [3,2,3,2,3,4,3],
  });
  buildTypeChart({
    labels: ["PC","Mobile","Router","IoT","Printer"],
    data:   [4,2,1,1,1],
  });
  buildAlertChart({
    labels: ["High","Medium","Low"],
    data:   [2,3,1],
  });
  buildTrafficChart({
    labels: days,
    sent:   [45,60,55,80,70,50,65],
    recv:   [180,220,200,310,260,190,240],
  });
}

// ── Initialise ────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", loadCharts);
