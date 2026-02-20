/**
 * ParkM AI Usage Dashboard
 * Fetches /analytics/api-usage and renders the page.
 */
(function () {
  "use strict";

  var currentDays = null;
  var rawData = null;

  /* ── Utilities ─────────────────────────────────────────────────────── */

  function fmt(n) {
    if (n === null || n === undefined) return "--";
    return n.toLocaleString();
  }

  function fmtK(n) {
    if (n === null || n === undefined || n === 0) return "0";
    if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
    if (n >= 1000)    return (n / 1000).toFixed(1) + "K";
    return String(n);
  }

  function fmtCost(v) {
    if (v === null || v === undefined) return "--";
    if (v === 0) return "$0.0000";
    if (v < 0.001) return "$" + v.toFixed(6);
    if (v < 1)     return "$" + v.toFixed(4);
    return "$" + v.toFixed(2);
  }

  function fmtTime(ts) {
    if (!ts) return "--";
    var d = new Date(ts);
    if (isNaN(d)) return ts.slice(0, 16).replace("T", " ");
    var mo = d.toLocaleString("default", { month: "short" });
    return mo + " " + d.getDate() + ", " + d.getHours().toString().padStart(2, "0") +
           ":" + d.getMinutes().toString().padStart(2, "0") + " " +
           (d.getHours() < 12 ? "AM" : "PM");
  }

  function intentLabel(s) {
    if (!s) return "—";
    return s.replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  /* ── Fetch ──────────────────────────────────────────────────────────── */

  function load(days) {
    document.getElementById("loading").style.display = "flex";
    document.getElementById("content").style.display = "none";

    var url = "/analytics/api-usage" + (days ? "?days=" + days : "");

    fetch(url, { credentials: "same-origin" })
      .then(function (r) {
        if (r.status === 401 || r.status === 307) {
          window.location.href = "/analytics/login";
          throw new Error("Session expired");
        }
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        rawData = data;
        render(data);
        document.getElementById("loading").style.display = "none";
        document.getElementById("content").style.display = "block";
      })
      .catch(function (err) {
        document.getElementById("loading").innerHTML =
          "<p style='color:#c0392b'>Failed to load: " + err.message + "</p>";
      });
  }

  /* ── Cards ──────────────────────────────────────────────────────────── */

  function renderCards(d) {
    var totalCalls = (d.total_openai_calls || 0) + (d.total_zoho_calls || 0);
    document.getElementById("c-total-calls").textContent = fmt(totalCalls);

    var sub = "";
    if (d.total_openai_calls || d.total_zoho_calls) {
      sub = fmt(d.total_openai_calls || 0) + " OpenAI · " + fmt(d.total_zoho_calls || 0) + " Zoho";
    }
    document.getElementById("c-calls-sub").textContent = sub || "API requests made";

    var tb = d.token_breakdown || {};
    var total = tb.total_tokens || 0;
    document.getElementById("c-total-tokens").textContent = fmtK(total);
    var tokSub = "";
    if (tb.prompt_tokens || tb.completion_tokens) {
      tokSub = fmtK(tb.prompt_tokens) + " in / " + fmtK(tb.completion_tokens) + " out";
    }
    document.getElementById("c-tokens-sub").textContent = tokSub || "Token usage";

    document.getElementById("c-total-cost").textContent = fmtCost(d.total_cost_usd);
    document.getElementById("c-avg-cost").textContent = fmtCost(d.avg_cost_per_ticket);
  }

  /* ── Usage by Intent list ───────────────────────────────────────────── */

  function renderIntentList(byIntent) {
    var ul = document.getElementById("intent-list");
    ul.innerHTML = "";

    if (!byIntent || byIntent.length === 0) {
      ul.innerHTML = "<li class='au-empty'>No OpenAI calls recorded yet.</li>";
      return;
    }

    var maxCalls = Math.max.apply(null, byIntent.map(function (x) { return x.calls; }));

    byIntent.forEach(function (item) {
      var li = document.createElement("li");
      li.className = "au-list-item";

      var pct = maxCalls > 0 ? Math.round((item.calls / maxCalls) * 100) : 0;

      li.innerHTML =
        "<div class='au-list-name'>" +
          intentLabel(item.intent) +
          "<small>" + fmt(item.calls) + " call" + (item.calls !== 1 ? "s" : "") + "</small>" +
        "</div>" +
        "<div>" +
          "<div class='au-bar-wrap'>" +
            "<div class='au-bar'><div class='au-bar-fill' style='width:" + pct + "%'></div></div>" +
          "</div>" +
        "</div>" +
        "<div class='au-list-meta'>" +
          "<div class='au-list-cost'>" + fmtCost(item.cost) + "</div>" +
          "<div class='au-list-tokens'>" + fmtK(item.total_tokens) + " tok</div>" +
        "</div>";

      ul.appendChild(li);
    });
  }

  /* ── Zoho API Calls list ────────────────────────────────────────────── */

  function renderZohoList(zohoDistribution) {
    var ul = document.getElementById("zoho-list");
    ul.innerHTML = "";

    if (!zohoDistribution || zohoDistribution.length === 0) {
      ul.innerHTML = "<li class='au-empty'>No Zoho API calls recorded yet.</li>";
      return;
    }

    var maxCount = Math.max.apply(null, zohoDistribution.map(function (x) { return x.count; }));
    var total = zohoDistribution.reduce(function (s, x) { return s + x.count; }, 0);

    zohoDistribution.forEach(function (item) {
      var li = document.createElement("li");
      li.className = "au-list-item";

      var pct = maxCount > 0 ? Math.round((item.count / maxCount) * 100) : 0;
      var share = total > 0 ? Math.round((item.count / total) * 100) : 0;
      var label = item.call_type.replace(/_/g, " ");

      li.innerHTML =
        "<div class='au-list-name'>" +
          label +
          "<small>" + share + "% of calls</small>" +
        "</div>" +
        "<div class='au-bar-wrap' style='width:120px'>" +
          "<div class='au-bar'><div class='au-bar-fill au-bar-fill--zoho' style='width:" + pct + "%'></div></div>" +
        "</div>" +
        "<div class='au-bar-count'>" + fmt(item.count) + "</div>";

      ul.appendChild(li);
    });
  }

  /* ── Recent Usage Table ─────────────────────────────────────────────── */

  function buildTable(rows) {
    if (!rows || rows.length === 0) {
      return "<div class='au-empty'>" +
        "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.5'>" +
        "<circle cx='12' cy='12' r='10'/>" +
        "<line x1='12' y1='8' x2='12' y2='12'/>" +
        "<line x1='12' y1='16' x2='12.01' y2='16'/></svg>" +
        "<p>No API calls recorded yet.<br>Classification events will appear here.</p>" +
        "</div>";
    }

    var html = "<table class='au-table'><thead><tr>" +
      "<th>Intent</th><th>Model</th><th>Tokens</th><th>Cost</th><th>Status</th><th>Time</th>" +
      "</tr></thead><tbody>";

    rows.forEach(function (row) {
      var success = row.success !== false;
      var intentHtml = row.intent
        ? "<span class='intent-chip'>" + intentLabel(row.intent) + "</span>"
        : "<span style='color:#94a3b8'>—</span>";

      var tokTotal = fmtK(row.total_tokens);
      var tokIn    = fmtK(row.prompt_tokens);
      var tokOut   = fmtK(row.completion_tokens);
      var tokHtml = row.total_tokens
        ? "<span class='tokens-cell'>" + tokTotal +
          " <span style='color:#cbd5e1'>(<span class='tok-in'>" + tokIn + "</span>/<span class='tok-out'>" + tokOut + "</span>)</span></span>"
        : "—";

      var statusHtml = success
        ? "<span class='status-badge status-badge--success'><span class='status-dot status-dot--success'></span>Success</span>"
        : "<span class='status-badge status-badge--error'><span class='status-dot status-dot--error'></span>Error</span>";

      html += "<tr>" +
        "<td>" + intentHtml + "</td>" +
        "<td><span style='font-size:12px;color:#475569'>" + (row.model || "—") + "</span></td>" +
        "<td>" + tokHtml + "</td>" +
        "<td class='cost-cell'>" + fmtCost(row.estimated_cost_usd) + "</td>" +
        "<td>" + statusHtml + "</td>" +
        "<td class='time-cell'>" + fmtTime(row.timestamp) + "</td>" +
        "</tr>";
    });

    html += "</tbody></table>";
    return html;
  }

  function renderTable(data) {
    var recent = (data && data.recent_usage) || [];

    // Populate intent filter
    var filterIntent = document.getElementById("filter-intent");
    filterIntent.innerHTML = "<option value=''>All Intents</option>";
    var seenIntents = {};
    recent.forEach(function (r) {
      if (r.intent && !seenIntents[r.intent]) {
        seenIntents[r.intent] = true;
        var opt = document.createElement("option");
        opt.value = r.intent;
        opt.textContent = intentLabel(r.intent);
        filterIntent.appendChild(opt);
      }
    });

    applyFilters(recent);
  }

  function applyFilters(rows) {
    var intentVal = document.getElementById("filter-intent").value;
    var statusVal = document.getElementById("filter-status").value;

    var filtered = rows.filter(function (r) {
      if (intentVal && r.intent !== intentVal) return false;
      if (statusVal === "success" && r.success === false) return false;
      if (statusVal === "error"   && r.success !== false) return false;
      return true;
    });

    document.getElementById("recent-table-wrap").innerHTML = buildTable(filtered);
  }

  /* ── Main render ────────────────────────────────────────────────────── */

  function render(data) {
    renderCards(data);
    renderIntentList(data.by_intent || []);
    renderZohoList(data.zoho_distribution || []);
    renderTable(data);
  }

  /* ── Event listeners ────────────────────────────────────────────────── */

  document.getElementById("refresh-btn").addEventListener("click", function () {
    load(currentDays);
  });

  document.querySelectorAll(".range-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".range-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      currentDays = btn.getAttribute("data-days") || null;
      load(currentDays);
    });
  });

  document.getElementById("filter-intent").addEventListener("change", function () {
    if (rawData) applyFilters(rawData.recent_usage || []);
  });

  document.getElementById("filter-status").addEventListener("change", function () {
    if (rawData) applyFilters(rawData.recent_usage || []);
  });

  /* ── Init ───────────────────────────────────────────────────────────── */

  load(null);

})();
