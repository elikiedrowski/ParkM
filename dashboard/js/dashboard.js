/**
 * ParkM Analytics — Dashboard Orchestrator
 * Fetches data from API endpoints and renders all dashboard sections.
 */
var Dashboard = (function () {
  var BASE_URL = window.location.origin;
  var currentDays = null; // null = all time

  /* ── Fetch helpers ────────────────────────────────────────────────── */

  function fetchJSON(path) {
    var url = BASE_URL + path;
    if (currentDays) url += (url.includes("?") ? "&" : "?") + "days=" + currentDays;
    return fetch(url).then(function (r) { return r.json(); });
  }

  /* ── Load all data ────────────────────────────────────────────────── */

  function loadAll() {
    document.getElementById("loading").style.display = "flex";
    document.getElementById("dashboard").style.display = "none";

    Promise.all([
      fetchJSON("/analytics/summary"),
      fetchJSON("/analytics/classifications"),
      fetchJSON("/analytics/corrections"),
      fetchJSON("/analytics/templates"),
      fetchJSON("/analytics/performance"),
      fetchJSON("/analytics/entities")
    ]).then(function (results) {
      var summary = results[0];
      var classifications = results[1];
      var corrections = results[2];
      var templates = results[3];
      var performance = results[4];
      var entities = results[5];

      document.getElementById("loading").style.display = "none";
      document.getElementById("dashboard").style.display = "block";

      // Check if there's any data
      if (summary.total_classifications === 0 && summary.total_corrections === 0) {
        document.getElementById("no-data").style.display = "block";
        return;
      }
      document.getElementById("no-data").style.display = "none";

      renderSummaryCards(summary);
      renderIntentDistribution(classifications.intent_distribution);
      renderConfidenceByIntent(classifications.confidence_by_intent);
      renderVolumeOverTime(classifications.volume_over_time);
      renderAccuracyOverTime(corrections.accuracy_over_time);
      renderConfusionMatrix(corrections.confusion_matrix);
      renderConfusionPairs(corrections.confusion_pairs);
      renderTemplateUsage(templates.by_template);
      renderEntityRates(entities.extraction_rates);
      renderPerformance(performance);
      renderErrorTable(performance.errors_by_type);

      document.getElementById("last-updated").textContent =
        "Updated " + new Date().toLocaleTimeString();

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
    setText("card-total", s.total_classifications || 0);
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
    Charts.drawBarChart("chart-confidence", (data || []).map(function (d, i) {
      return { label: formatIntent(d.intent), value: Math.round(d.avg_confidence * 100), color: Charts.getColor(i) };
    }));
  }

  /* ── Volume Over Time ─────────────────────────────────────────────── */

  function renderVolumeOverTime(data) {
    Charts.drawLineChart("chart-volume", (data || []).map(function (d) {
      return { label: d.date, value: d.count };
    }), { color: "#1976d2" });
  }

  /* ── Accuracy Over Time ───────────────────────────────────────────── */

  function renderAccuracyOverTime(data) {
    Charts.drawLineChart("chart-accuracy-time", (data || []).map(function (d) {
      return { label: d.week, value: d.accuracy };
    }), { color: "#27ae60", maxValue: 100, minValue: 0, formatValue: function (v) { return Math.round(v) + "%"; } });
  }

  /* ── Confusion Matrix ─────────────────────────────────────────────── */

  function renderConfusionMatrix(matrix) {
    var container = document.getElementById("confusion-matrix");
    if (!matrix || Object.keys(matrix).length === 0) {
      container.innerHTML = "<div class='empty-state'>No corrections recorded yet</div>";
      return;
    }

    // Collect all intents involved
    var intents = new Set();
    Object.keys(matrix).forEach(function (orig) {
      intents.add(orig);
      Object.keys(matrix[orig]).forEach(function (corr) { intents.add(corr); });
    });
    var intentList = Array.from(intents).sort();

    var html = "<table><thead><tr><th>AI Said \\ Should Be</th>";
    intentList.forEach(function (i) {
      html += "<th>" + formatIntent(i).substring(0, 8) + "</th>";
    });
    html += "</tr></thead><tbody>";

    intentList.forEach(function (orig) {
      html += "<tr><td><strong>" + formatIntent(orig) + "</strong></td>";
      intentList.forEach(function (corr) {
        var val = (matrix[orig] && matrix[orig][corr]) || 0;
        var cls = "cm-cell";
        if (val > 5) cls += " cm-cell--high";
        else if (val > 2) cls += " cm-cell--med";
        else if (val > 0) cls += " cm-cell--low";
        html += "<td class='" + cls + "'>" + (val || "") + "</td>";
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
    Charts.drawBarChart("chart-entities", data);
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

  /* ── Helpers ──────────────────────────────────────────────────────── */

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function formatIntent(intent) {
    if (!intent) return "unknown";
    return intent.replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  /* ── Init ─────────────────────────────────────────────────────────── */

  function init() {
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
