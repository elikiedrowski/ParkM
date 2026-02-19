/**
 * ParkM Analytics — Canvas Chart Renderers
 * Lightweight chart drawing using Canvas 2D API.
 */
var Charts = (function () {

  // Color palette matching the widget design system
  var COLORS = [
    "#1976d2", "#27ae60", "#e67e22", "#c0392b", "#8e44ad",
    "#16a085", "#2c3e50", "#d35400", "#7f8c8d", "#2980b9"
  ];

  function getColor(i) {
    return COLORS[i % COLORS.length];
  }

  /* ── Horizontal Bar Chart ─────────────────────────────────────────── */

  function drawHorizontalBarChart(canvasId, data, options) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) {
      showEmpty(canvas);
      return;
    }

    var ctx = canvas.getContext("2d");
    var dpr = window.devicePixelRatio || 1;
    var w = canvas.parentElement.clientWidth - 32;
    var barHeight = 22;
    var gap = 6;
    var labelWidth = 140;
    var h = (barHeight + gap) * data.length + 30;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.scale(dpr, dpr);

    var maxVal = Math.max.apply(null, data.map(function (d) { return d.value; })) || 1;
    var barAreaWidth = w - labelWidth - 50;

    data.forEach(function (d, i) {
      var y = i * (barHeight + gap) + 5;
      var barW = (d.value / maxVal) * barAreaWidth;

      // Label
      ctx.fillStyle = "#555";
      ctx.font = "12px -apple-system, sans-serif";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      var label = d.label.length > 20 ? d.label.substring(0, 18) + "..." : d.label;
      ctx.fillText(label, labelWidth - 8, y + barHeight / 2);

      // Bar
      ctx.fillStyle = d.color || getColor(i);
      ctx.fillRect(labelWidth, y, barW, barHeight);

      // Value
      ctx.fillStyle = "#333";
      ctx.font = "bold 11px -apple-system, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(d.value, labelWidth + barW + 6, y + barHeight / 2);
    });
  }

  /* ── Vertical Bar Chart ───────────────────────────────────────────── */

  function drawBarChart(canvasId, data, options) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) {
      showEmpty(canvas);
      return;
    }

    var ctx = canvas.getContext("2d");
    var dpr = window.devicePixelRatio || 1;
    var w = canvas.parentElement.clientWidth - 32;
    var h = 250;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.scale(dpr, dpr);

    var padding = { top: 10, right: 10, bottom: 50, left: 40 };
    var chartW = w - padding.left - padding.right;
    var chartH = h - padding.top - padding.bottom;
    var barW = Math.min(40, (chartW / data.length) - 8);
    var gap = (chartW - barW * data.length) / (data.length + 1);

    var maxVal = Math.max.apply(null, data.map(function (d) { return d.value; })) || 1;

    // Y axis labels
    ctx.fillStyle = "#999";
    ctx.font = "10px -apple-system, sans-serif";
    ctx.textAlign = "right";
    for (var tick = 0; tick <= 4; tick++) {
      var val = Math.round(maxVal * tick / 4);
      var yy = padding.top + chartH - (tick / 4) * chartH;
      ctx.fillText(val, padding.left - 6, yy + 3);
      ctx.strokeStyle = "#f0f0f0";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding.left, yy);
      ctx.lineTo(w - padding.right, yy);
      ctx.stroke();
    }

    // Bars
    data.forEach(function (d, i) {
      var x = padding.left + gap + i * (barW + gap);
      var barH = (d.value / maxVal) * chartH;
      var y = padding.top + chartH - barH;

      ctx.fillStyle = d.color || getColor(i);
      ctx.fillRect(x, y, barW, barH);

      // X label
      ctx.fillStyle = "#666";
      ctx.font = "10px -apple-system, sans-serif";
      ctx.textAlign = "center";
      ctx.save();
      ctx.translate(x + barW / 2, h - padding.bottom + 10);
      ctx.rotate(-0.5);
      var label = d.label.length > 12 ? d.label.substring(0, 10) + ".." : d.label;
      ctx.fillText(label, 0, 0);
      ctx.restore();
    });
  }

  /* ── Line Chart ───────────────────────────────────────────────────── */

  function drawLineChart(canvasId, data, options) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) {
      showEmpty(canvas);
      return;
    }

    options = options || {};
    var ctx = canvas.getContext("2d");
    var dpr = window.devicePixelRatio || 1;
    var w = canvas.parentElement.clientWidth - 32;
    var h = 220;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.scale(dpr, dpr);

    var padding = { top: 10, right: 10, bottom: 40, left: 45 };
    var chartW = w - padding.left - padding.right;
    var chartH = h - padding.top - padding.bottom;

    var values = data.map(function (d) { return d.value; });
    var maxVal = options.maxValue || Math.max.apply(null, values) || 1;
    var minVal = options.minValue !== undefined ? options.minValue : 0;
    var range = maxVal - minVal || 1;

    // Grid lines
    ctx.strokeStyle = "#f0f0f0";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#999";
    ctx.font = "10px -apple-system, sans-serif";
    ctx.textAlign = "right";
    for (var tick = 0; tick <= 4; tick++) {
      var val = minVal + range * tick / 4;
      var yy = padding.top + chartH - (tick / 4) * chartH;
      ctx.fillText(options.formatValue ? options.formatValue(val) : Math.round(val), padding.left - 6, yy + 3);
      ctx.beginPath();
      ctx.moveTo(padding.left, yy);
      ctx.lineTo(w - padding.right, yy);
      ctx.stroke();
    }

    // Line
    var color = options.color || "#1976d2";
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.beginPath();

    data.forEach(function (d, i) {
      var x = padding.left + (i / (data.length - 1 || 1)) * chartW;
      var y = padding.top + chartH - ((d.value - minVal) / range) * chartH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots
    ctx.fillStyle = color;
    data.forEach(function (d, i) {
      var x = padding.left + (i / (data.length - 1 || 1)) * chartW;
      var y = padding.top + chartH - ((d.value - minVal) / range) * chartH;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // X labels (show first, middle, last)
    ctx.fillStyle = "#666";
    ctx.font = "10px -apple-system, sans-serif";
    ctx.textAlign = "center";
    var labelIndices = [0, Math.floor(data.length / 2), data.length - 1];
    labelIndices.forEach(function (idx) {
      if (idx >= data.length) return;
      var x = padding.left + (idx / (data.length - 1 || 1)) * chartW;
      ctx.fillText(data[idx].label || "", x, h - padding.bottom + 16);
    });
  }

  /* ── Empty state helper ───────────────────────────────────────────── */

  function showEmpty(canvas) {
    if (!canvas) return;
    var parent = canvas.parentElement;
    var el = document.createElement("div");
    el.className = "empty-state";
    el.textContent = "No data available";
    canvas.style.display = "none";
    parent.appendChild(el);
  }

  /* ── Public API ───────────────────────────────────────────────────── */

  return {
    drawBarChart: drawBarChart,
    drawHorizontalBarChart: drawHorizontalBarChart,
    drawLineChart: drawLineChart,
    COLORS: COLORS,
    getColor: getColor
  };
})();
