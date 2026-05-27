// ── Charts ──────────────────────────────────────────
const CHART_CONFIG = (label, color) => ({
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label,
        data: [],
        borderColor: color,
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.4,
        fill: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { display: false },
      y: {
        ticks: { color: "#6b6b80", font: { size: 10 } },
        grid: { color: "#2a2a35" },
      },
    },
  },
});

const chartTemp = new Chart(
  document.getElementById("chart-temp"),
  CHART_CONFIG("Temperature", "#ff6b35"),
);
const chartHum = new Chart(
  document.getElementById("chart-hum"),
  CHART_CONFIG("Humidity", "#00d4aa"),
);
const chartPress = new Chart(
  document.getElementById("chart-press"),
  CHART_CONFIG("Pressure", "#7b8cff"),
);

// ── Thresholds ───────────────────────────────────────
let thresholds = null;

async function loadThresholds() {
  const response = await fetch("http://127.0.0.1:8000/telemetry/thresholds");
  thresholds = await response.json();
}

loadThresholds();

function checkAlerts(data) {
  if (!thresholds) return;

  const alerts = [];

  const statusTemp = document.getElementById("status-temp");
  if (
    data.temperature_c < thresholds.temperature_c.min ||
    data.temperature_c > thresholds.temperature_c.max
  ) {
    alerts.push(`Temperature ${data.temperature_c}°C out of range`);
    statusTemp.textContent = "ALERT";
    statusTemp.className = "metric-status alert";
  } else {
    statusTemp.textContent = "NOMINAL";
    statusTemp.className = "metric-status ok";
  }

  const statusHum = document.getElementById("status-hum");
  if (
    data.humidity_pct < thresholds.humidity_pct.min ||
    data.humidity_pct > thresholds.humidity_pct.max
  ) {
    alerts.push(`Humidity ${data.humidity_pct}% out of range`);
    statusHum.textContent = "ALERT";
    statusHum.className = "metric-status alert";
  } else {
    statusHum.textContent = "NOMINAL";
    statusHum.className = "metric-status ok";
  }

  const statusPress = document.getElementById("status-press");
  if (
    data.pressure_hpa < thresholds.pressure_hpa.min ||
    data.pressure_hpa > thresholds.pressure_hpa.max
  ) {
    alerts.push(`Pressure ${data.pressure_hpa}hPa out of range`);
    statusPress.textContent = "ALERT";
    statusPress.className = "metric-status alert";
  } else {
    statusPress.textContent = "NOMINAL";
    statusPress.className = "metric-status ok";
  }

  const list = document.getElementById("alerts-list");
  if (alerts.length === 0) {
    list.innerHTML =
      '<div class="no-alerts">✓ All parameters within range</div>';
  } else {
    list.innerHTML = alerts
      .map(
        (a) =>
          `<div class="alert-item"><span class="alert-icon">⚠</span>${a}</div>`,
      )
      .join("");
  }
}

// ── SSE Connection ───────────────────────────────────
const MAX_POINTS = 30; // сколько точек показываем на графике

const source = new EventSource("http://127.0.0.1:8000/stream/telemetry");

source.onmessage = function (event) {
  const data = JSON.parse(event.data);

  // 1. Обновляем текущие значения
  document.getElementById("val-temp").innerHTML =
    data.temperature_c + '<span class="metric-unit">°C</span>';
  document.getElementById("val-hum").innerHTML =
    data.humidity_pct + '<span class="metric-unit">%</span>';
  document.getElementById("val-press").innerHTML =
    data.pressure_hpa + '<span class="metric-unit">hPa</span>';

  // 2. Метка времени
  document.getElementById("last-update").textContent =
    "Last update: " + new Date(data.ts).toLocaleString("en-GB");

  // 3. Добавляем точку на графики
  const label = new Date(data.ts).toLocaleTimeString();
  addPoint(chartTemp, label, data.temperature_c);
  addPoint(chartHum, label, data.humidity_pct);
  addPoint(chartPress, label, data.pressure_hpa);

  checkAlerts(data);
};

function addPoint(chart, label, value) {
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  if (chart.data.labels.length > MAX_POINTS) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update();
}

// ── Stats ────────────────────────────────────────────
async function updateStats() {
  const response = await fetch("http://127.0.0.1:8000/telemetry/stats");
  const stats = await response.json();

  document.getElementById("stats-temp").innerHTML =
    `<span>MIN <b>${stats.temperature.min}</b></span>
     <span>MAX <b>${stats.temperature.max}</b></span>
     <span>AVG <b>${stats.temperature.avg}</b></span>`;

  document.getElementById("stats-hum").innerHTML =
    `<span>MIN <b>${stats.humidity.min}</b></span>
     <span>MAX <b>${stats.humidity.max}</b></span>
     <span>AVG <b>${stats.humidity.avg}</b></span>`;

  document.getElementById("stats-press").innerHTML =
    `<span>MIN <b>${stats.pressure.min}</b></span>
     <span>MAX <b>${stats.pressure.max}</b></span>
     <span>AVG <b>${stats.pressure.avg}</b></span>`;
}

updateStats();
setInterval(updateStats, 30000); // обновляем каждые 30 секунд

// ── Clock ────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById("current-time").textContent =
    now.toLocaleTimeString("en-GB");
  document.getElementById("current-date").textContent = now
    .toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
    .toUpperCase();
}

updateClock();
setInterval(updateClock, 1000);
