/**
 * ParkM Analytics — Dashboard Orchestrator
 * Fetches data from API endpoints, manages tab navigation, renders all sections.
 */
var Dashboard = (function () {
  var BASE_URL = window.location.origin;
  var currentDays = null; // null = all time
  var chartsRendered = {};

  /* ── Fetch helpers ────────────────────────────────────────────────── */

  function fetchJSON(path) {
    var url = BASE_URL + path;
    if (currentDays) url += (url.includes("?") ? "&" : "?") + "days=" + currentDays;
    return fetch(url, { credentials: "same-origin" }).then(function (r) {
      if (r.status === 401 || r.status === 307) {
        window.location.href = "/analytics/login";
        return Promise.reject(new Error("Session expired"));
      }
      if (!r.ok) return Promise.reject(new Error("HTTP " + r.status));
      return r.json();
    });
  }

  /* ── Tab Navigation ─────────────────────────────────────────────── */

  function initTabs() {
    var tabs = document.querySelectorAll(".tab");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var target = tab.getAttribute("data-tab");

        // Update active tab
        tabs.forEach(function (t) { t.classList.remove("active"); });
        tab.classList.add("active");

        // Show target panel
        document.querySelectorAll(".tab-panel").forEach(function (p) {
          p.classList.remove("active");
        });
        document.getElementById("panel-" + target).classList.add("active");

        // Re-render charts in the newly visible tab (canvas needs visible parent)
        if (!chartsRendered[target]) {
          chartsRendered[target] = true;
          redrawChartsForTab(target);
        }
      });
    });
  }

  /* ── Stored data for re-rendering on tab switch ────────────────── */

  var cachedData = {};

  function redrawChartsForTab(tab) {
    var d = cachedData;
    if (!d.summary) return;

    if (tab === "classifications") {
      renderConfidenceByIntent(d.classifications.confidence_by_intent);
      renderEntityRates(d.entities.extraction_rates);
      renderTemplateUsage(d.templates.by_template);
      renderErrorTable(d.performance.errors_by_type);
    } else if (tab === "corrections") {
      renderConfusionMatrix(d.corrections.confusion_matrix);
      renderConfusionPairs(d.corrections.confusion_pairs);
    } else if (tab === "api-costs") {
      renderApiUsage(d.apiUsage);
    }
  }

  /* ── Load all data ────────────────────────────────────────────────── */

  function loadAll() {
    document.getElementById("loading").style.display = "flex";
    document.getElementById("dashboard").style.display = "none";
    chartsRendered = { overview: true };

    Promise.all([
      fetchJSON("/analytics/summary"),
      fetchJSON("/analytics/classifications"),
      fetchJSON("/analytics/corrections"),
      fetchJSON("/analytics/templates"),
      fetchJSON("/analytics/performance"),
      fetchJSON("/analytics/entities"),
      fetchJSON("/analytics/api-usage")
    ]).then(function (results) {
      cachedData = {
        summary: results[0],
        classifications: results[1],
        corrections: results[2],
        templates: results[3],
        performance: results[4],
        entities: results[5],
        apiUsage: results[6]
      };

      document.getElementById("loading").style.display = "none";
      document.getElementById("dashboard").style.display = "block";

      // Check if there's any data
      if (cachedData.summary.total_classifications === 0 &&
          cachedData.summary.total_corrections === 0 &&
          cachedData.apiUsage.total_api_calls === 0) {
        document.getElementById("no-data").style.display = "block";
        return;
      }
      document.getElementById("no-data").style.display = "none";

      // Render Overview tab (visible by default)
      renderSummaryCards(cachedData.summary);
      renderVolumeOverTime(cachedData.classifications.volume_over_time);
      renderPerformance(cachedData.performance);
      renderIntentDistribution(cachedData.classifications.intent_distribution);
      renderAccuracyOverTime(cachedData.corrections.accuracy_over_time);

      // Mark which tab is currently active and render its charts
      var activeTab = document.querySelector(".tab.active");
      if (activeTab) {
        var tabName = activeTab.getAttribute("data-tab");
        if (tabName !== "overview") {
          chartsRendered[tabName] = true;
          redrawChartsForTab(tabName);
        }
      }

      document.getElementById("last-updated").textContent =
        new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    }).catch(function (err) {
      document.getElementById("loading").style.display = "none";
      document.getElementById("dashboard").style.display = "block";
      document.getElementById("no-data").style.display = "block";
      document.getElementById("no-data").querySelector("p").textContent =
        "Error loading data: " + err.message;
      console.error("Dashboard load failed:", err);
    });
  }

  /* ── Summary Cards ────────────────────────────────────────────────── */

  function renderSummaryCards(s) {
    setText("card-total", formatNumber(s.total_classifications || 0));
    setText("card-accuracy", s.accuracy_rate !== null ? s.accuracy_rate + "%" : "N/A");
    setText("card-confidence", s.avg_confidence !== null ? Math.round(s.avg_confidence * 100) + "%" : "N/A");
    setText("card-time", s.avg_processing_time_seconds !== null ? s.avg_processing_time_seconds + "s" : "N/A");
    setText("card-errors", s.error_rate + "%");
    setText("card-templates", s.templates_used || 0);
  }

  /* ── Intent Distribution ──────────────────────────────────────────── */

  function renderIntentDistribution(data) {
    Charts.drawHorizontalBarChart("chart-intents", (data || []).map(function (d, i) {
      return { label: formatIntent(d.intent), value: d.count, color: Charts.getColor(i) };
    }));
  }

  /* ── Confidence by Intent ─────────────────────────────────────────── */

  function renderConfidenceByIntent(data) {
    Charts.drawHorizontalBarChart("chart-confidence", (data || []).map(function (d, i) {
      return { label: formatIntent(d.intent), value: Math.round(d.avg_confidence * 100), color: Charts.getColor(i) };
    }), { suffix: "%" });
  }

  /* ── Volume Over Time ─────────────────────────────────────────────── */

  function renderVolumeOverTime(data) {
    Charts.drawLineChart("chart-volume", (data || []).map(function (d) {
      return { label: d.date, value: d.count };
    }), { color: "#046bd2" });
  }

  /* ── Accuracy Over Time ───────────────────────────────────────────── */

  function renderAccuracyOverTime(data) {
    Charts.drawLineChart("chart-accuracy-time", (data || []).map(function (d) {
      return { label: d.week, value: d.accuracy };
    }), { color: "#003060", maxValue: 100, minValue: 0, formatValue: function (v) { return Math.round(v) + "%"; } });
  }

  /* ── Confusion Matrix ─────────────────────────────────────────────── */

  function renderConfusionMatrix(matrix) {
    var container = document.getElementById("confusion-matrix");
    if (!matrix || Object.keys(matrix).length === 0) {
      container.innerHTML = "<div class='empty-state'>No corrections recorded yet</div>";
      return;
    }

    var intents = new Set();
    Object.keys(matrix).forEach(function (orig) {
      intents.add(orig);
      Object.keys(matrix[orig]).forEach(function (corr) { intents.add(corr); });
    });
    var intentList = Array.from(intents).sort();

    var html = "<table class='confusion-table'><thead><tr><th><span class='rotated-label'>AI Said \\ Corrected To</span></th>";
    intentList.forEach(function (i) {
      html += "<th><span class='rotated-label'>" + formatIntent(i) + "</span></th>";
    });
    html += "</tr></thead><tbody>";

    intentList.forEach(function (orig) {
      html += "<tr><td>" + formatIntent(orig) + "</td>";
      intentList.forEach(function (corr) {
        var val = (matrix[orig] && matrix[orig][corr]) || 0;
        var cls = "cm-cell";
        if (orig === corr) cls += " cm-cell--diagonal";
        else if (val > 5) cls += " cm-cell--high";
        else if (val > 2) cls += " cm-cell--med";
        else if (val > 0) cls += " cm-cell--low";
        var display = (orig === corr) ? "—" : (val || "");
        html += "<td class='" + cls + "'>" + display + "</td>";
      });
      html += "</tr>";
    });

    html += "</tbody></table>";
    container.innerHTML = html;
  }

  /* ── Confusion Pairs ──────────────────────────────────────────────── */

  function renderConfusionPairs(pairs) {
    var container = document.getElementById("confusion-pairs");
    if (!pairs || pairs.length === 0) {
      container.innerHTML = "<div class='empty-state'>No misclassifications recorded</div>";
      return;
    }

    var html = "";
    pairs.slice(0, 10).forEach(function (p) {
      html += "<div class='pair-item'>" +
        "<span class='pair-label'>" + formatIntent(p.original) +
        "<span class='pair-arrow'> &rarr; </span>" + formatIntent(p.corrected) +
        "</span><span class='pair-count'>" + p.count + "</span></div>";
    });
    container.innerHTML = html;
  }

  /* ── Template Usage ───────────────────────────────────────────────── */

  function renderTemplateUsage(data) {
    Charts.drawHorizontalBarChart("chart-templates", (data || []).map(function (d, i) {
      var label = d.template.replace(/_/g, " ").replace(".html", "");
      return { label: label, value: d.count, color: Charts.getColor(i) };
    }));
  }

  /* ── Entity Extraction Rates ──────────────────────────────────────── */

  function renderEntityRates(rates) {
    if (!rates) return;
    var data = Object.keys(rates).map(function (field, i) {
      return {
        label: field.replace(/_/g, " "),
        value: Math.round(rates[field].rate),
        color: Charts.getColor(i)
      };
    });
    Charts.drawHorizontalBarChart("chart-entities", data, { suffix: "%" });
  }

  /* ── Performance Stats ────────────────────────────────────────────── */

  function renderPerformance(perf) {
    var container = document.getElementById("perf-stats");
    var pt = perf.processing_time || {};

    var items = [
      { label: "Average", value: pt.avg_seconds !== null ? pt.avg_seconds + "s" : "N/A" },
      { label: "P50 (Median)", value: pt.p50_seconds !== null ? pt.p50_seconds + "s" : "N/A" },
      { label: "P95", value: pt.p95_seconds !== null ? pt.p95_seconds + "s" : "N/A" },
      { label: "P99", value: pt.p99_seconds !== null ? pt.p99_seconds + "s" : "N/A" },
      { label: "Tagging Success", value: perf.tagging_success_rate + "%" },
      { label: "Total Processed", value: perf.total_processed }
    ];

    var html = "";
    items.forEach(function (item) {
      html += "<div class='stat-item'><div class='stat-value'>" + item.value +
        "</div><div class='stat-label'>" + item.label + "</div></div>";
    });
    container.innerHTML = html;
  }

  /* ── Error Table ──────────────────────────────────────────────────── */

  function renderErrorTable(errors) {
    var container = document.getElementById("error-table");
    if (!errors || errors.length === 0) {
      container.innerHTML = "<div class='empty-state'>No errors recorded</div>";
      return;
    }

    var html = "<table><thead><tr><th>Error Type</th><th>Count</th></tr></thead><tbody>";
    errors.forEach(function (e) {
      html += "<tr><td>" + e.error + "</td><td>" + e.count + "</td></tr>";
    });
    html += "</tbody></table>";
    container.innerHTML = html;
  }

  /* ── API Usage & Costs ────────────────────────────────────────────── */

  function renderApiUsage(data) {
    if (!data || data.total_api_calls === 0) {
      setText("card-api-total", "0");
      setText("card-api-cost", "$0");
      setText("card-api-avg-cost", "$0");
      setText("card-api-tokens", "0");
      return;
    }

    // Summary cards
    setText("card-api-total", formatNumber(data.total_api_calls));
    setText("card-api-cost", "$" + data.total_cost_usd.toFixed(4));
    setText("card-api-avg-cost", "$" + data.avg_cost_per_ticket.toFixed(4));
    var tb = data.token_breakdown || {};
    setText("card-api-tokens", formatNumber(tb.total_tokens || 0));

    // Cost over time line chart
    Charts.drawLineChart("chart-api-cost-time", (data.cost_over_time || []).map(function (d) {
      return { label: d.date, value: d.cost };
    }), { color: "#046bd2", formatValue: function (v) { return "$" + v.toFixed(4); } });

    // API calls by type horizontal bar chart
    Charts.drawHorizontalBarChart("chart-api-calls-type", (data.calls_by_type || []).map(function (d, i) {
      return { label: d.call_type.replace(/_/g, " "), value: d.count, color: Charts.getColor(i) };
    }));

    // OpenAI token breakdown horizontal bar chart
    Charts.drawHorizontalBarChart("chart-api-tokens", [
      { label: "Input Tokens", value: tb.prompt_tokens || 0, color: "#003060" },
      { label: "Output Tokens", value: tb.completion_tokens || 0, color: "#FFC107" }
    ]);

    // Zoho API call distribution
    Charts.drawHorizontalBarChart("chart-zoho-dist", (data.zoho_distribution || []).map(function (d, i) {
      return { label: d.call_type.replace(/_/g, " "), value: d.count, color: Charts.getColor(i) };
    }));
  }

  /* ── Helpers ──────────────────────────────────────────────────────── */

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function formatIntent(intent) {
    if (!intent) return "unknown";
    return intent.replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
    if (n >= 1000) return (n / 1000).toFixed(1) + "K";
    return String(n);
  }

  /* ── Init ─────────────────────────────────────────────────────────── */

  function init() {
    initTabs();

    // Time range buttons
    var buttons = document.querySelectorAll(".range-btn");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        currentDays = btn.getAttribute("data-days") || null;
        if (currentDays === "") currentDays = null;
        else currentDays = parseInt(currentDays);
        loadAll();
      });
    });

    // Initial load
    loadAll();
  }

  return { init: init };
})();

window.addEventListener("DOMContentLoaded", function () {
  Dashboard.init();
});
