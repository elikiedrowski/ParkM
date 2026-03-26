/**
 * ParkM CSR Wizard — Refund Automation Panel
 * Provides customer lookup, permit review, refund eligibility evaluation,
 * permit cancellation, and accounting email forwarding — all inline in the wizard.
 *
 * Only visible for refund/cancellation-related tags.
 */
var RefundPanel = (function () {
  var customerData = null;
  var ticketEmail = "";

  // Tags that trigger the refund panel
  var REFUND_TAGS_KEYWORDS = [
    "cancel", "refund", "double charged", "extra charges",
    "charged", "move out", "moved out"
  ];

  /* ── Should this panel be visible? ──────────────────────────────── */

  function shouldShow(tags) {
    if (!tags || tags.length === 0) return false;
    var joined = tags.join(" ").toLowerCase();
    return REFUND_TAGS_KEYWORDS.some(function (kw) {
      return joined.indexOf(kw) !== -1;
    });
  }

  /* ── Initialize / show the panel ────────────────────────────────── */

  function init(tags, contactEmail) {
    var panel = document.getElementById("refund-panel");
    if (!shouldShow(tags)) {
      panel.style.display = "none";
      return;
    }

    panel.style.display = "block";
    _resetPanel();

    // Attach event handlers
    document.getElementById("refund-lookup-btn").onclick = _onLookup;

    // Pre-populate email and auto-lookup
    if (contactEmail) {
      ticketEmail = contactEmail;
      var input = document.getElementById("refund-email-input");
      if (input) input.value = contactEmail;
      _onLookup();
    }
  }

  function _resetPanel() {
    customerData = null;
    document.getElementById("refund-email-input").value = "";
    document.getElementById("refund-customer-info").style.display = "none";
    document.getElementById("refund-customer-info").innerHTML = "";
    document.getElementById("refund-permits-list").innerHTML = "";
    document.getElementById("refund-permits-section").style.display = "none";
    document.getElementById("refund-inactive-list").innerHTML = "";
    document.getElementById("refund-inactive-section").style.display = "none";
    document.getElementById("refund-lookup-error").style.display = "none";
    document.getElementById("refund-lookup-error").textContent = "";
    document.getElementById("refund-lookup-btn").disabled = false;
    document.getElementById("refund-lookup-btn").textContent = "Lookup";
  }

  /* ── Customer Lookup ────────────────────────────────────────────── */

  function _onLookup() {
    var email = document.getElementById("refund-email-input").value.trim();
    if (!email) {
      _showError("Enter an email address");
      return;
    }

    var btn = document.getElementById("refund-lookup-btn");
    btn.disabled = true;
    btn.textContent = "Searching...";
    _hideError();

    var url = ParkMConfig.API_BASE_URL + "/parkm/customer?email=" + encodeURIComponent(email);

    _fetchWithTimeout(url, null, 35000)
      .then(function (data) {
        btn.disabled = false;
        btn.textContent = "Lookup";
        customerData = data;

        if (!data.found) {
          _showError("No ParkM account found for this email.");
          _showNotFoundActions(email);
          return;
        }

        _renderCustomerInfo(data);
        _renderPermits(data);
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = "Lookup";
        _showError("Lookup failed: " + err.message);
      });
  }

  /* ── Render Customer Info Card ──────────────────────────────────── */

  function _renderCustomerInfo(data) {
    var c = data.customer;
    var infoDiv = document.getElementById("refund-customer-info");
    infoDiv.style.display = "block";

    infoDiv.innerHTML =
      '<div class="refund-customer-card">' +
        '<div class="refund-customer-name">' + _esc(c.name) + '</div>' +
        '<div class="refund-customer-detail">' + _esc(c.email) + '</div>' +
        (c.phone ? '<div class="refund-customer-detail">' + _esc(c.phone) + '</div>' : '') +
        '<div class="refund-customer-meta">Account #' + _esc(String(c.account_id || '')) + '</div>' +
      '</div>';
  }

  /* ── Render Permits ─────────────────────────────────────────────── */

  function _renderPermits(data) {
    var section = document.getElementById("refund-permits-section");
    var list = document.getElementById("refund-permits-list");
    list.innerHTML = "";

    var permits = data.permits || [];
    var now = new Date();
    var active = permits.filter(function (p) {
      if (p.is_cancelled) return false;
      // Hide expired permits
      if (p.expiration_date && new Date(p.expiration_date) < now) return false;
      return true;
    });
    var cancelled = permits.filter(function (p) { return p.is_cancelled; });
    var expired = permits.filter(function (p) {
      return !p.is_cancelled && p.expiration_date && new Date(p.expiration_date) < now;
    });

    var inactivePermits = data.inactive_permits || [];
    var inactiveSection = document.getElementById("refund-inactive-section");
    var inactiveList = document.getElementById("refund-inactive-list");
    inactiveList.innerHTML = "";

    if (active.length === 0 && inactivePermits.length === 0) {
      section.style.display = "block";
      list.innerHTML = '<div class="refund-no-permits">No permits found</div>';
      inactiveSection.style.display = "none";
      return;
    }

    // Render active permits
    if (active.length > 0) {
      section.style.display = "block";
      active.forEach(function (permit) {
        list.appendChild(_buildPermitCard(permit, data.customer));
      });
    } else {
      section.style.display = "block";
      list.innerHTML = '<div class="refund-no-permits">No active permits</div>';
    }

    // Render inactive permits (display-only, no action buttons)
    if (inactivePermits.length > 0) {
      inactiveSection.style.display = "block";
      inactivePermits.forEach(function (permit) {
        inactiveList.appendChild(_buildInactivePermitCard(permit));
      });
    } else {
      inactiveSection.style.display = "none";
    }
  }

  function _buildInactivePermitCard(permit) {
    var card = document.createElement("div");
    card.className = "refund-permit-card refund-permit-card--inactive";

    var vehicle = permit.vehicle || {};
    var vehicleStr = [vehicle.year, vehicle.make, vehicle.model, vehicle.color]
      .filter(Boolean).join(" ");
    var plateStr = vehicle.plate ? " — " + vehicle.plate : "";

    var effDate = permit.effective_date ? _formatDate(permit.effective_date) : "N/A";
    var expDate = permit.expiration_date ? _formatDate(permit.expiration_date) : "N/A";
    var lastCharge = permit.last_charge_date ? _formatDate(permit.last_charge_date) : "N/A";

    var price = permit.recurring_price || permit.permit_price || permit.total_amount;
    var priceStr = price ? "$" + parseFloat(price).toFixed(2) : "N/A";
    var recurStr = permit.is_recurring ? " /mo" : " one-time";

    var statusLabel = permit.is_cancelled ? "Cancelled" : "Expired";

    card.innerHTML =
      '<div class="refund-permit-header">' +
        '<div class="refund-permit-type">' + _esc(permit.type_name) + '</div>' +
        '<span class="refund-inactive-badge">' + statusLabel + '</span>' +
      '</div>' +
      '<div class="refund-permit-details">' +
        (vehicleStr ? '<div class="refund-permit-detail"><span class="refund-detail-label">Vehicle:</span> ' + _esc(vehicleStr + plateStr) + '</div>' : '') +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Effective:</span> ' + effDate + '</div>' +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Expires:</span> ' + expDate + '</div>' +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Last Charge:</span> ' + lastCharge + '</div>' +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Price:</span> ' + priceStr + recurStr + '</div>' +
      '</div>';

    return card;
  }

  function _buildPermitCard(permit, customer) {
    var card = document.createElement("div");
    card.className = "refund-permit-card";

    var vehicle = permit.vehicle || {};
    var vehicleStr = [vehicle.year, vehicle.make, vehicle.model, vehicle.color]
      .filter(Boolean).join(" ");
    var plateStr = vehicle.plate ? " — " + vehicle.plate : "";

    // Format dates
    var effDate = permit.effective_date ? _formatDate(permit.effective_date) : "N/A";
    var expDate = permit.expiration_date ? _formatDate(permit.expiration_date) : "N/A";

    // Price
    var price = permit.recurring_price || permit.permit_price || permit.total_amount;
    var priceStr = price ? "$" + parseFloat(price).toFixed(2) : "N/A";
    var recurStr = permit.is_recurring ? " /mo" : " one-time";

    card.innerHTML =
      '<div class="refund-permit-header">' +
        '<div class="refund-permit-type">' + _esc(permit.type_name) + '</div>' +
      '</div>' +
      '<div class="refund-permit-details">' +
        (vehicleStr ? '<div class="refund-permit-detail"><span class="refund-detail-label">Vehicle:</span> ' + _esc(vehicleStr + plateStr) + '</div>' : '') +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Effective:</span> ' + effDate + '</div>' +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Expires:</span> ' + expDate + '</div>' +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Price:</span> ' + priceStr + recurStr + '</div>' +
        (permit.balance_due > 0 ? '<div class="refund-permit-detail refund-balance-due"><span class="refund-detail-label">Balance Due:</span> $' + parseFloat(permit.balance_due).toFixed(2) + '</div>' : '') +
      '</div>' +
      '<div class="refund-permit-actions" id="permit-actions-' + permit.id + '"></div>' +
      '<div class="refund-permit-result" id="permit-result-' + permit.id + '"></div>';

    // Add action buttons after innerHTML is set
    var actionsDiv = card.querySelector(".refund-permit-actions");

    var evalBtn = document.createElement("button");
    evalBtn.className = "btn btn-primary refund-action-btn";
    evalBtn.textContent = "Evaluate Refund";
    evalBtn.addEventListener("click", function () {
      _evaluateRefund(permit, customer, card);
    });
    actionsDiv.appendChild(evalBtn);

    var cancelBtn = document.createElement("button");
    cancelBtn.className = "btn btn-secondary refund-action-btn";
    cancelBtn.textContent = "Cancel Permit";
    cancelBtn.addEventListener("click", function () {
      _cancelPermit(permit, card);
    });
    actionsDiv.appendChild(cancelBtn);

    return card;
  }

  /* ── Evaluate Refund ────────────────────────────────────────────── */

  function _evaluateRefund(permit, customer, card) {
    var resultDiv = card.querySelector(".refund-permit-result");
    resultDiv.innerHTML = '<div class="refund-loading">Evaluating...</div>';

    // Disable buttons during evaluation
    var btns = card.querySelectorAll(".refund-action-btn");
    for (var i = 0; i < btns.length; i++) btns[i].disabled = true;

    var ticketId = (typeof ParkMApp !== "undefined" && ParkMApp.getTicketId)
      ? ParkMApp.getTicketId() : "";

    var body = {
      customer_email: customer.email,
      permit_id: permit.id,
      reason: "Customer requested cancellation/refund",
      ticket_id: ticketId
    };

    _doEvaluate(body, permit, customer, resultDiv);
  }

  function _doEvaluate(body, permit, customer, resultDiv) {
    var card = resultDiv.closest(".refund-permit-card");
    _fetchWithTimeout(ParkMConfig.API_BASE_URL + "/parkm/refund/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })
      .then(function (data) {
        _renderEvalResult(data, permit, customer, resultDiv);
      })
      .catch(function (err) {
        resultDiv.innerHTML =
          '<div class="refund-error">Evaluation failed: ' + _esc(err.message) + '</div>';
        // Re-enable buttons on failure
        if (card) {
          var btns = card.querySelectorAll(".refund-action-btn");
          for (var i = 0; i < btns.length; i++) btns[i].disabled = false;
        }
      });
  }

  function _renderEvalResult(data, permit, customer, resultDiv) {
    // Find the result for this specific permit
    var permitResult = null;
    (data.results || []).forEach(function (r) {
      if (r.permit && r.permit.id === permit.id) {
        permitResult = r;
      }
    });

    if (!permitResult) {
      resultDiv.innerHTML = '<div class="refund-error">Could not evaluate this permit</div>';
      return;
    }

    var elig = permitResult.eligibility;
    var eligible = elig.eligible;

    var html =
      '<div class="refund-eval-result ' + (eligible ? 'refund-eval-eligible' : 'refund-eval-ineligible') + '">' +
        '<div class="refund-eval-status">' +
          (eligible ? 'ELIGIBLE FOR REFUND' : 'NOT ELIGIBLE') +
        '</div>' +
        '<div class="refund-eval-reason">' + _esc(elig.reason) + '</div>' +
        (elig.refund_amount ? '<div class="refund-eval-amount">Refund: $' + parseFloat(elig.refund_amount).toFixed(2) + '</div>' : '') +
        (elig.days_since_charge !== null ? '<div class="refund-eval-detail">' + elig.days_since_charge + ' days since last charge</div>' : '') +
      '</div>';

    if (eligible) {
      html += '<div class="refund-eval-actions">';
      html += '<button class="btn btn-primary refund-action-btn" id="process-refund-' + permit.id + '">Cancel & Forward to Accounting</button>';
      html += '</div>';
    } else {
      html += '<div class="refund-eval-actions">';
      html += '<div class="refund-eval-hint">Inform customer they do not qualify. Send Terms & Conditions.</div>';
      html += '</div>';
    }

    resultDiv.innerHTML = html;

    // Attach process handler if eligible
    if (eligible) {
      var processBtn = document.getElementById("process-refund-" + permit.id);
      if (processBtn) {
        processBtn.addEventListener("click", function () {
          _processRefund(permit, customer, resultDiv);
        });
      }
    }
  }

  /* ── Process Refund (Cancel + Forward to Accounting) ────────────── */

  function _processRefund(permit, customer, resultDiv) {
    if (!confirm("Cancel this permit and forward refund details to accounting@parkm.com?")) {
      return;
    }
    var processBtn = document.getElementById("process-refund-" + permit.id);
    if (processBtn) {
      processBtn.disabled = true;
      processBtn.textContent = "Processing...";
    }

    var ticketId = (typeof ParkMApp !== "undefined" && ParkMApp.getTicketId)
      ? ParkMApp.getTicketId() : "";

    var body = {
      customer_email: customer.email,
      permit_id: permit.id,
      reason: "Customer requested cancellation/refund",
      ticket_id: ticketId
    };

    _fetchWithTimeout(ParkMConfig.API_BASE_URL + "/parkm/refund/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })
      .then(function (data) {
        _renderProcessResult(data, permit, resultDiv);
      })
      .catch(function (err) {
        if (processBtn) {
          processBtn.disabled = false;
          processBtn.textContent = "Cancel & Forward to Accounting";
        }
        resultDiv.insertAdjacentHTML("beforeend",
          '<div class="refund-error">Processing failed: ' + _esc(err.message) + '</div>');
      });
  }

  function _renderProcessResult(data, permit, resultDiv) {
    var permitResult = null;
    (data.results || []).forEach(function (r) {
      if (r.permit && r.permit.id === permit.id) {
        permitResult = r;
      }
    });

    var cancelOk = permitResult && permitResult.cancel_result && permitResult.cancel_result.success;
    var acctEmail = permitResult && permitResult.accounting_email;

    var html = '<div class="refund-process-result">';

    // Cancel status
    html += '<div class="refund-process-step ' + (cancelOk ? 'step-ok' : 'step-fail') + '">';
    html += (cancelOk ? 'Permit cancelled' : 'Cancel may have failed — verify in ParkM');
    html += '</div>';

    // Zoho status update
    if (data.zoho_status_updated) {
      html += '<div class="refund-process-step step-ok">Ticket set to "Waiting on Accounting"</div>';
    } else if (data.zoho_status_updated === false) {
      html += '<div class="refund-process-step step-fail">Could not update ticket status — please set to "Waiting on Accounting" manually</div>';
    }

    // Accounting email preview
    if (acctEmail) {
      html += '<div class="refund-accounting-email">';
      html += '<div class="refund-accounting-label">Email to <strong>' + _esc(acctEmail.to) + '</strong>:</div>';
      html += '<div class="refund-accounting-preview">' + acctEmail.body_html + '</div>';
      html += '<button class="btn btn-primary refund-action-btn" id="insert-accounting-' + permit.id + '">Insert Email into Reply</button>';
      html += '</div>';
    }

    html += '</div>';
    resultDiv.innerHTML = html;

    // Attach insert handler
    if (acctEmail) {
      var insertBtn = document.getElementById("insert-accounting-" + permit.id);
      if (insertBtn) {
        insertBtn.addEventListener("click", function () {
          _insertAccountingEmail(acctEmail);
        });
      }
    }

    // Update customerData in background but don't re-render (preserve result view)
    if (cancelOk && customerData && customerData.customer) {
      var url = ParkMConfig.API_BASE_URL + "/parkm/customer?email=" + encodeURIComponent(customerData.customer.email);
      fetch(url, { signal: AbortSignal.timeout(30000) })
        .then(function (res) { return res.ok ? res.json() : null; })
        .then(function (data) { if (data && data.found) customerData = data; })
        .catch(function () {});
    }
  }

  /* ── Cancel Permit (standalone, no refund) ──────────────────────── */

  function _cancelPermit(permit, card) {
    if (!confirm("Cancel this permit?\n\n" + permit.type_name + "\n\nThis will send a cancellation notice to the customer.")) {
      return;
    }

    // Disable all buttons on this card during cancel
    var btns = card.querySelectorAll(".refund-action-btn");
    for (var i = 0; i < btns.length; i++) btns[i].disabled = true;

    var resultDiv = card.querySelector(".refund-permit-result");
    resultDiv.innerHTML = '<div class="refund-loading">Cancelling...</div>';

    _fetchWithTimeout(ParkMConfig.API_BASE_URL + "/parkm/permit/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        permit_id: permit.id,
        send_notice: true
      })
    })
      .then(function (data) {
        if (data.success) {
          resultDiv.innerHTML = '<div class="refund-process-step step-ok">Permit cancelled successfully</div>';
          card.classList.add("refund-permit-card--cancelled");
          _refreshPermits();
        } else {
          resultDiv.innerHTML = '<div class="refund-process-step step-fail">Cancel failed — try manually in ParkM</div>';
          var btns = card.querySelectorAll(".refund-action-btn");
          for (var i = 0; i < btns.length; i++) btns[i].disabled = false;
        }
      })
      .catch(function (err) {
        resultDiv.innerHTML = '<div class="refund-error">Cancel failed: ' + _esc(err.message) + '</div>';
        var btns = card.querySelectorAll(".refund-action-btn");
        for (var i = 0; i < btns.length; i++) btns[i].disabled = false;
      });
  }

  /* ── Insert Accounting Email ────────────────────────────────────── */

  function _insertAccountingEmail(acctEmail) {
    try {
      // Set the To field to accounting email, clear CC
      ZOHODESK.set("ticket.replyEditorRecipients", {
        to: [acctEmail.to],
        cc: [],
        bcc: []
      });
      // Insert the email body
      ZOHODESK.invoke("INSERT", "ticket.replyEditor", { value: acctEmail.body_html, type: "replace" });
    } catch (e) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        // Strip HTML tags for plain-text clipboard fallback
        var tmp = document.createElement("div");
        tmp.innerHTML = acctEmail.body_html;
        navigator.clipboard.writeText(tmp.textContent || tmp.innerText || "");
        alert("Email copied to clipboard (unable to insert directly).");
      }
    }
  }

  /* ── Refresh Permits After Cancel ──────────────────────────────── */

  function _refreshPermits() {
    if (!customerData || !customerData.customer) return;
    var email = customerData.customer.email;
    var url = ParkMConfig.API_BASE_URL + "/parkm/customer?email=" + encodeURIComponent(email);

    fetch(url, { signal: AbortSignal.timeout(30000) })
      .then(function (res) {
        if (!res.ok) return;
        return res.json();
      })
      .then(function (data) {
        if (data && data.found) {
          customerData = data;
          _renderPermits(data);
        }
      })
      .catch(function () { /* best-effort refresh */ });
  }

  /* ── Not Found Actions ──────────────────────────────────────────── */

  function _showNotFoundActions(email) {
    var infoDiv = document.getElementById("refund-customer-info");
    infoDiv.style.display = "block";
    infoDiv.innerHTML =
      '<div class="refund-not-found">' +
        '<div class="refund-not-found-msg">No account found for ' + _esc(email) + '</div>' +
        '<div class="refund-not-found-hint">Request from customer:<br>' +
          '&bull; Vehicle license plate number<br>' +
          '&bull; Screenshot of bank statement showing the charge<br>' +
          '&bull; Last four digits of the card used</div>' +
      '</div>';
  }

  /* ── Helpers ────────────────────────────────────────────────────── */

  function _showError(msg) {
    var el = document.getElementById("refund-lookup-error");
    el.textContent = msg;
    el.style.display = "block";
  }

  function _hideError() {
    var el = document.getElementById("refund-lookup-error");
    el.style.display = "none";
    el.textContent = "";
  }

  function _esc(str) {
    var div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  }

  function _fetchWithTimeout(url, opts, timeoutMs) {
    timeoutMs = timeoutMs || 30000;
    opts = opts || {};
    opts.signal = AbortSignal.timeout(timeoutMs);
    return fetch(url, opts).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (body) {
          var detail = body.detail || "";
          if (res.status === 401) throw new Error("Authentication failed — check API key configuration");
          if (res.status === 400) throw new Error(detail || "Invalid request — check email format");
          if (res.status === 503) throw new Error("ParkM API is unreachable — try again later");
          throw new Error(detail || "Server error (" + res.status + ") — try again");
        });
      }
      return res.json();
    }).catch(function (err) {
      if (err.name === "TimeoutError") throw new Error("Request timed out — ParkM API may be slow, try again");
      throw err;
    });
  }

  function _formatDate(isoStr) {
    try {
      var d = new Date(isoStr);
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch (e) {
      return isoStr;
    }
  }

  /* ── Public API ─────────────────────────────────────────────────── */

  return {
    init: init,
    shouldShow: shouldShow
  };
})();
