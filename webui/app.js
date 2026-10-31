// ── Curvin Intelligence — frontend logic ────────────────────────────
// Single-page app: Dashboard / AI Report / Chat views share one article
// store fetched from the FastAPI backend (same-origin or Render URL).

(function () {
  "use strict";

  const state = { articles: [], industry: "", region: "" };

  const INDUSTRIES = [
    "Finance", "Banking", "Insurance", "Healthcare", "Pharmaceuticals",
    "Biotechnology", "Agriculture", "Food Industry", "Energy", "Oil & Gas",
    "Renewable Energy", "Technology", "Artificial Intelligence", "Cybersecurity",
    "Semiconductors", "Aviation", "Space Industry", "Automotive", "Electric Vehicles",
    "Logistics", "Retail", "E-commerce", "Real Estate", "Construction",
    "Telecommunications", "Media", "Entertainment", "Sports Industry",
    "Defense", "Geopolitics", "Cryptocurrency"
  ];

  const REGIONS = ["United States", "United Kingdom", "India", "Canada", "Australia", "Global"];

  const COLORS = { Positive: "#10b981", Negative: "#ef4444", Neutral: "#86868b" };

  const $ = (id) => document.getElementById(id);

  // ── API helper ─────────────────────────────────────────────────────
  async function api(path, body) {
    const res = await fetch(`${window.API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
    return data;
  }

  // ── View switching (segmented control) ─────────────────────────────
  function showView(name) {
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    $(`view-${name}`).classList.add("active");
    document.querySelectorAll(".seg-btn").forEach((b) => {
      const on = b.dataset.view === name;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    window.scrollTo({ top: 0 });
  }

  // ── Status helpers ─────────────────────────────────────────────────
  function setStatus(el, text, isError) {
    el.textContent = text;
    el.classList.toggle("error", Boolean(isError));
  }

  function busy(btn, on, busyText) {
    btn.classList.toggle("busy", on);
    if (on) {
      btn.dataset.label = btn.textContent;
      btn.textContent = busyText || "Working…";
    } else if (btn.dataset.label) {
      btn.textContent = btn.dataset.label;
    }
  }

  // ── Dashboard: fetch + render ──────────────────────────────────────
  async function fetchIntelligence() {
    const btn = $("fetch-btn");
    const status = $("fetch-status");
    const payload = {
      industry: $("industry").value,
      region: $("region").value,
      max_articles: parseInt($("max-articles").value, 10) || 50,
    };
    busy(btn, true, "Fetching…");
    setStatus(status, `Fetching ${payload.max_articles} articles for ${payload.industry}…`);
    try {
      const data = await api("/api/fetch", payload);
      state.articles = data.articles;
      state.industry = data.industry;
      state.region = data.region;
      renderDashboard(data);
      const deepCount = data.articles.filter((a) => a.has_full_text).length;
      const storedNote = data.stored ? ` · ${data.stored} saved to history` : "";
      setStatus(status, `Fetched ${data.count} articles · ${deepCount} deep-read in full · Gemini sentiment${storedNote}.`);
      unlockViews();
    } catch (err) {
      setStatus(status, err.message, true);
    } finally {
      busy(btn, false);
    }
  }

  function renderDashboard(data) {
    const articles = data.articles;
    const total = articles.length;
    const count = (s) => articles.filter((a) => a.sentiment === s).length;
    const pct = (s) => `${((count(s) / total) * 100).toFixed(1)}%`;

    $("m-total").textContent = total;
    $("m-pos").textContent = pct("Positive");
    $("m-neg").textContent = pct("Negative");
    $("m-neu").textContent = pct("Neutral");

    // Bar chart — sentiment distribution
    const labels = ["Positive", "Neutral", "Negative"];
    const values = labels.map(count);
    Plotly.newPlot("chart-bar", [{
      type: "bar", x: labels, y: values,
      marker: { color: labels.map((l) => COLORS[l]) },
      hovertemplate: "%{y} articles<extra>%{x}</extra>",
    }], plotLayout({ barmode: "group" }), { displayModeBar: false, responsive: true });

    // Donut — sentiment ratio
    Plotly.newPlot("chart-pie", [{
      type: "pie", labels, values, hole: 0.45,
      marker: { colors: labels.map((l) => COLORS[l]) },
      textinfo: "percent",
    }], plotLayout({ showlegend: true }), { displayModeBar: false, responsive: true });

    // Histogram — confidence distribution by sentiment
    Plotly.newPlot("chart-hist", ["Positive", "Neutral", "Negative"].map((s) => ({
      type: "histogram",
      name: s,
      x: articles.filter((a) => a.sentiment === s).map((a) => a.confidence),
      marker: { color: COLORS[s] },
      opacity: 0.75,
      nbinsx: 20,
    })), plotLayout({ barmode: "overlay", bargap: 0.05 }),
      { displayModeBar: false, responsive: true });

    // Feed table
    $("feed-body").innerHTML = articles.map((a) => `
      <tr>
        <td class="title-cell"><a href="${a.link || "#"}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a></td>
        <td>${escapeHtml(a.source || "Unknown")}</td>
        <td>${escapeHtml(String(a.published || ""))}</td>
        <td><span class="badge ${a.sentiment}">${a.sentiment}</span>${a.has_full_text ? '<span class="deep-badge">📖 Deep read</span>' : ""}</td>
        <td>${a.confidence != null ? a.confidence.toFixed(2) : "—"}</td>
      </tr>`).join("");

    ["metrics", "charts", "feed-section"].forEach((id) => { $(id).hidden = false; });
    $("dashboard-empty").hidden = true;
  }

  function plotLayout(extra) {
    return Object.assign({
      font: { family: "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif", color: "#1d1d1f", size: 13 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      margin: { l: 40, r: 20, t: 10, b: 40 },
    }, extra || {});
  }

  function unlockViews() {
    $("report-btn").disabled = false;
    $("chat-input").disabled = false;
    document.querySelector("#chat-form .btn").disabled = false;
    $("chat-sub").textContent = `Chatting about ${state.industry} — ${state.articles.length} articles ingested.`;
  }

  // ── Report view ────────────────────────────────────────────────────
  async function generateReport() {
    if (!state.articles.length) return;
    const btn = $("report-btn");
    const status = $("report-status");
    busy(btn, true, "Synthesizing…");
    setStatus(status, `Synthesizing institutional intelligence for ${state.industry}…`);
    try {
      const report = await api("/api/report", {
        industry: state.industry,
        articles: state.articles.map((a) => ({
          title: a.title,
          description: a.description,
          article_text: a.article_text || "",
        })),
      });
      renderReport(report);
      setStatus(status, "Report generated.");
    } catch (err) {
      setStatus(status, err.message, true);
    } finally {
      busy(btn, false);
    }
  }

  function renderReport(report) {
    const sentiment = String(report.overall_sentiment || "N/A");
    $("banner-label").textContent = `Overall Market Sentiment — ${state.industry}`;
    $("banner-value").textContent = sentiment;
    $("report-banner").hidden = false;

    fillList("list-drivers", report.key_drivers);
    fillList("list-risks", report.risks);
    fillList("list-opps", report.opportunities);
    fillList("list-entities", report.companies_to_watch);
    $("report-grid").hidden = false;
    $("report-empty").hidden = true;
    $("report-disclaimer").hidden = false;
  }

  function fillList(id, items) {
    const ul = $(id);
    ul.innerHTML = "";
    (items || ["None identified."]).forEach((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      ul.appendChild(li);
    });
  }

  // ── Chat view ─────────────────────────────────────────────────────
  function addMessage(role, text) {
    const log = $("chat-log");
    const div = document.createElement("div");
    div.className = `chat-msg ${role}`;
    div.textContent = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
  }

  async function sendChat(event) {
    event.preventDefault();
    const input = $("chat-input");
    const query = input.value.trim();
    if (!query || !state.articles.length) return;

    input.value = "";
    input.disabled = true;
    addMessage("user", query);
    const pending = addMessage("assistant", "Thinking…");

    try {
      const res = await api("/api/chat", {
        query,
        industry: state.industry,
        articles: state.articles.map((a) => ({
          title: a.title,
          description: a.description,
          article_text: a.article_text || "",
        })),
      });
      pending.textContent = res.answer;
    } catch (err) {
      pending.textContent = err.message;
    } finally {
      input.disabled = false;
      input.focus();
      $("chat-log").scrollTop = $("chat-log").scrollHeight;
    }
  }

  // ── Utilities ──────────────────────────────────────────────────────
  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  // ── Init ───────────────────────────────────────────────────────────
  function init() {
    $("industry").innerHTML = INDUSTRIES.map((i) => `<option${i === "Finance" ? " selected" : ""}>${i}</option>`).join("");
    $("region").innerHTML = REGIONS.map((r) => `<option${r === "United States" ? " selected" : ""}>${r}</option>`).join("");

    document.querySelectorAll(".seg-btn").forEach((b) =>
      b.addEventListener("click", () => showView(b.dataset.view)));
    $("fetch-btn").addEventListener("click", fetchIntelligence);
    $("report-btn").addEventListener("click", generateReport);
    $("chat-form").addEventListener("submit", sendChat);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
