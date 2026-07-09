/* ============================================================
   RetailIQ Dashboard — app.js
   Consumes the FastAPI backend (api/main.py) and renders KPIs,
   charts, and tables. No frontend build step required — plain
   fetch() + Chart.js.
   ============================================================ */

const API_BASE = "http://localhost:8000";

const fmtCurrency = (n) => {
  if (n === null || n === undefined) return "—";
  if (n >= 1e7) return "₹" + (n / 1e7).toFixed(2) + "Cr";
  if (n >= 1e5) return "₹" + (n / 1e5).toFixed(2) + "L";
  return "₹" + Number(n).toLocaleString("en-IN");
};

const chartColors = {
  accent: "#f5a524",
  accent2: "#35d0ba",
  grid: "#232e47",
  text: "#8b96b3",
};

Chart.defaults.color = chartColors.text;
Chart.defaults.borderColor = chartColors.grid;
Chart.defaults.font.family = "Inter, sans-serif";

let charts = {};

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

function setApiStatus(online) {
  const dot = document.getElementById("apiDot");
  const text = document.getElementById("apiStatusText");
  dot.className = "dot " + (online ? "online" : "offline");
  text.textContent = online ? "API connected" : "API unreachable — start uvicorn";
}

function updateClock() {
  const el = document.getElementById("clock");
  el.textContent = new Date().toLocaleString("en-IN", { hour12: true });
}
setInterval(updateClock, 1000);
updateClock();

async function loadDashboardKPIs() {
  const data = await apiGet("/dashboard");
  document.getElementById("kpiRevenue").textContent = fmtCurrency(data.total_revenue);
  document.getElementById("kpiProfit").textContent = fmtCurrency(data.total_profit);
  document.getElementById("kpiOrders").textContent = Number(data.total_orders).toLocaleString("en-IN");
  document.getElementById("kpiAOV").textContent = fmtCurrency(data.average_order_value);
  const margin = data.total_revenue ? ((data.total_profit / data.total_revenue) * 100).toFixed(1) : 0;
  document.getElementById("kpiMargin").textContent = `${margin}% margin`;
}

async function loadMonthlyChart() {
  const data = await apiGet("/sales/monthly");
  const labels = data.map((d) => d.order_date);
  const revenue = data.map((d) => d.sales_amount);
  const profit = data.map((d) => d.profit_amount);

  const ctx = document.getElementById("monthlyChart");
  if (charts.monthly) charts.monthly.destroy();
  charts.monthly = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Revenue",
          data: revenue,
          borderColor: chartColors.accent,
          backgroundColor: "rgba(245,165,36,.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 2,
        },
        {
          label: "Profit",
          data: profit,
          borderColor: chartColors.accent2,
          backgroundColor: "rgba(53,208,186,.08)",
          fill: true,
          tension: 0.3,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: chartColors.text } } },
      scales: {
        x: { grid: { color: chartColors.grid } },
        y: { grid: { color: chartColors.grid } },
      },
    },
  });
}

async function loadCategoryChart(category) {
  const products = await apiGet(`/products/top?limit=50`);
  const catRevenue = {};
  products.forEach((p) => {
    catRevenue[p.category] = (catRevenue[p.category] || 0) + p.revenue;
  });
  let labels = Object.keys(catRevenue);
  let values = Object.values(catRevenue);

  const ctx = document.getElementById("categoryChart");
  if (charts.category) charts.category.destroy();
  charts.category = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Revenue", data: values, backgroundColor: chartColors.accent, borderRadius: 6 }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: chartColors.grid } }, y: { grid: { display: false } } },
    },
  });
}

async function loadTopProductsTable() {
  const products = await apiGet("/products/top?limit=10");
  const tbody = document.querySelector("#topProductsTable tbody");
  tbody.innerHTML = products
    .map((p) => `<tr><td>${p.product_name}</td><td>${p.category}</td><td class="mono">${fmtCurrency(p.revenue)}</td></tr>`)
    .join("");
}

async function loadStoreChart() {
  const stores = await apiGet("/stores");
  const labels = stores.map((s) => s.store_name.replace("RetailIQ ", ""));
  const values = stores.map((s) => s.revenue);

  const ctx = document.getElementById("storeChart");
  if (charts.store) charts.store.destroy();
  charts.store = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Revenue", data: values, backgroundColor: chartColors.accent2, borderRadius: 6 }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: chartColors.grid } }, y: { grid: { display: false } } },
    },
  });
}

async function loadForecastChart() {
  try {
    const forecast = await apiGet("/forecast");
    const labels = forecast.map((f) => f.Date);
    const values = forecast.map((f) => f.Revenue);

    const ctx = document.getElementById("forecastChart");
    if (charts.forecast) charts.forecast.destroy();
    charts.forecast = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Forecasted Revenue",
          data: values,
          borderColor: chartColors.accent,
          backgroundColor: "rgba(245,165,36,.12)",
          borderDash: [6, 4],
          fill: true,
          tension: 0.3,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: chartColors.text } } },
        scales: { x: { grid: { color: chartColors.grid } }, y: { grid: { color: chartColors.grid } } },
      },
    });
  } catch (e) {
    console.warn("Forecast not available yet:", e.message);
  }
}

async function loadReorderTable() {
  const rows = await apiGet("/inventory/reorder");
  const tbody = document.querySelector("#reorderTable tbody");
  tbody.innerHTML = rows
    .slice(0, 15)
    .map((r) => `<tr><td>${r.product_name}</td><td>${r.store_id}</td><td class="mono">${r.stock_quantity}</td></tr>`)
    .join("");
}

async function loadAll() {
  try {
    await Promise.all([
      loadDashboardKPIs(),
      loadMonthlyChart(),
      loadCategoryChart(),
      loadTopProductsTable(),
      loadStoreChart(),
      loadForecastChart(),
      loadReorderTable(),
    ]);
    setApiStatus(true);
  } catch (e) {
    console.error(e);
    setApiStatus(false);
  }
}

document.getElementById("apiBase").textContent = API_BASE;
document.getElementById("regionFilter").addEventListener("change", loadAll);
document.getElementById("categoryFilter").addEventListener("change", loadAll);

document.querySelectorAll(".side-link").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".side-link").forEach((l) => l.classList.remove("active"));
    link.classList.add("active");
    document.querySelector(`[data-section="${link.dataset.section}"]`)?.scrollIntoView({ behavior: "smooth" });
  });
});

loadAll();
