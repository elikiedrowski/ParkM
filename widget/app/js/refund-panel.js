/**
 * ParkM CSR Wizard — Refund Automation Panel (Step-Embedded)
 * Renders account lookup and refund evaluation inline within wizard steps.
 *
 * Step 1 (interactive: "account_lookup") — search by email or name, show customer info
 * Step 4 (interactive: "refund_evaluation") — show permits, evaluate/process refunds
 *
 * Called by app.js after wizard steps are rendered, targets the
 * .step-interactive-embed containers created by WizardRenderer.
 */
var RefundPanel = (function () {
  var customerData = null;
  var ticketEmail = "";

  // Track which embed containers we're using (set during initEmbedded)
  var lookupContainer = null;
  var refundContainer = null;

  /* ── Initialize embedded panels ────────────────────────────────── */

  function initEmbedded(contactEmail) {
    customerData = null;
    ticketEmail = contactEmail || "";

    // Find all interactive embed containers rendered by WizardRenderer
    var allEmbeds = document.querySelectorAll(".step-interactive-embed");
    lookupContainer = null;
    refundContainer = null;

    for (var i = 0; i < allEmbeds.length; i++) {
      var embedId = allEmbeds[i].id || "";
      // The step id is namespaced as "0_1", "0_4" etc by app.js
      // The interactive field from JSON propagates through
      var stepRow = allEmbeds[i].closest(".step-row");
      if (!stepRow) continue;
      var interactiveType = allEmbeds[i].getAttribute("data-interactive");
      if (interactiveType === "account_lookup") {
        lookupContainer = allEmbeds[i];
      } else if (interactiveType === "refund_evaluation") {
        refundContainer = allEmbeds[i];
      }
    }

    if (lookupContainer) {
      _renderLookupUI(lookupContainer);
      // Auto-search if we have a contact email
      if (contactEmail) {
        var input = lookupContainer.querySelector(".refund-search-input");
        if (input) input.value = contactEmail;
        _onSearch();
      }
    }

    if (refundContainer) {
      refundContainer.innerHTML = '<div class="refund-eval-placeholder">Complete account lookup above to view permits and evaluate refunds.</div>';
    }
  }

  /* ── Render Lookup UI into container ───────────────────────────── */

  function _renderLookupUI(container) {
    container.innerHTML =
      '<div class="refund-lookup-row">' +
        '<input type="text" class="refund-search-input refund-email-input" placeholder="Search by email or name...">' +
        '<button class="btn btn-primary refund-lookup-btn">Search</button>' +
      '</div>' +
      '<div class="refund-lookup-error" style="display:none;"></div>' +
      '<div class="refund-search-results" style="display:none;"></div>' +
      '<div class="refund-customer-info" style="display:none;"></div>';

    var btn = container.querySelector(".refund-lookup-btn");
    var input = container.querySelector(".refund-search-input");
    btn.addEventListener("click", _onSearch);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") _onSearch();
    });
  }

  /* ── Customer Search / Lookup ────────────────────────────────────── */

  function _isEmail(str) {
    return str.indexOf("@") !== -1;
  }

  function _onSearch() {
    if (!lookupContainer) return;
    var input = lookupContainer.querySelector(".refund-search-input");
    var query = input ? input.value.trim() : "";
    if (!query) {
      _showError("Enter an email address or name");
      return;
    }

    var btn = lookupContainer.querySelector(".refund-lookup-btn");
    btn.disabled = true;
    btn.textContent = "Searching...";
    _hideError();
    _hideEl(lookupContainer.querySelector(".refund-search-results"));
    _hideEl(lookupContainer.querySelector(".refund-customer-info"));
    // Clear refund container while searching
    if (refundContainer) {
      refundContainer.innerHTML = '<div class="refund-eval-placeholder">Searching...</div>';
    }

    if (_isEmail(query)) {
      _doEmailLookup(query);
    } else {
      _doNameSearch(query);
    }
  }

  function _doEmailLookup(email) {
    var btn = lookupContainer.querySelector(".refund-lookup-btn");
    var url = ParkMConfig.API_BASE_URL + "/parkm/customer?email=" + encodeURIComponent(email);

    _fetchWithTimeout(url, null, 35000)
      .then(function (data) {
        btn.disabled = false;
        btn.textContent = "Search";
        customerData = data;

        if (!data.found) {
          _showError("No ParkM account found for this email.");
          _showNotFoundActions(email);
          if (refundContainer) {
            refundContainer.innerHTML = '<div class="refund-eval-placeholder">No account found — cannot evaluate refunds.</div>';
          }
          return;
        }

        _renderCustomerInfo(data);
        _renderPermits(data);
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = "Search";
        _showError("Lookup failed: " + err.message);
      });
  }

  function _doNameSearch(query) {
    var btn = lookupContainer.querySelector(".refund-lookup-btn");
    var url = ParkMConfig.API_BASE_URL + "/parkm/customer/search?q=" + encodeURIComponent(query);

    _fetchWithTimeout(url, null, 65000)
      .then(function (data) {
        btn.disabled = false;
        btn.textContent = "Search";

        var results = data.results || [];
        if (results.length === 0) {
          _showError('No accounts found for "' + _esc(query) + '".');
          if (refundContainer) {
            refundContainer.innerHTML = '<div class="refund-eval-placeholder">No account found — cannot evaluate refunds.</div>';
          }
          return;
        }

        if (results.length === 1 && results[0].email && results[0].email.indexOf("@fake.com") === -1) {
          _selectSearchResult(results[0]);
          return;
        }

        _renderSearchResults(results);
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = "Search";
        _showError("Search failed: " + err.message);
      });
  }

  function _renderSearchResults(results) {
    var container = lookupContainer.querySelector(".refund-search-results");
    container.style.display = "block";
    var html = '<div class="refund-search-results-title">' + results.length + ' accounts found</div>';

    for (var i = 0; i < results.length; i++) {
      var r = results[i];
      var detailParts = [];
      if (r.email && r.email.indexOf("@fake.com") === -1) detailParts.push(r.email);
      if (r.unit_number) detailParts.push("Unit " + r.unit_number);
      if (r.phone) detailParts.push(r.phone);

      html += '<div class="refund-search-result-item" data-idx="' + i + '">' +
        '<div class="refund-search-result-info">' +
          '<div class="refund-search-result-name">' + _esc(r.name || "Unknown") + '</div>' +
          (detailParts.length > 0 ? '<div class="refund-search-result-detail">' + _esc(detailParts.join(" · ")) + '</div>' : '') +
        '</div>' +
        '<div class="refund-search-result-select">Select &rarr;</div>' +
      '</div>';
    }

    container.innerHTML = html;

    var items = container.querySelectorAll(".refund-search-result-item");
    for (var j = 0; j < items.length; j++) {
      (function (idx) {
        items[idx].addEventListener("click", function () {
          _selectSearchResult(results[idx]);
        });
      })(j);
    }
  }

  function _selectSearchResult(result) {
    var searchResults = lookupContainer.querySelector(".refund-search-results");
    searchResults.style.display = "none";

    if (result.email && result.email.indexOf("@fake.com") === -1) {
      var input = lookupContainer.querySelector(".refund-search-input");
      if (input) input.value = result.email;
      _doEmailLookup(result.email);
    } else {
      _showError("This account has no email on file. Please look up using a different identifier.");
    }
  }

  /* ── Render Customer Info Card ──────────────────────────────────── */

  function _renderCustomerInfo(data) {
    var c = data.customer;
    var infoDiv = lookupContainer.querySelector(".refund-customer-info");
    infoDiv.style.display = "block";

    infoDiv.innerHTML =
      '<div class="refund-customer-card">' +
        '<div class="refund-customer-name">' + _esc(c.name) + '</div>' +
        '<div class="refund-customer-detail">' + _esc(c.email) + '</div>' +
        (c.phone ? '<div class="refund-customer-detail">' + _esc(c.phone) + '</div>' : '') +
        '<div class="refund-customer-meta">Account #' + _esc(String(c.account_id || '')) + '</div>' +
      '</div>';
  }

  /* ── Render Permits (into refund evaluation step) ───────────────── */

  function _renderPermits(data) {
    if (!refundContainer) return;
    refundContainer.innerHTML = "";

    var permits = data.permits || [];
    var now = new Date();
    var active = permits.filter(function (p) {
      if (p.is_cancelled) return false;
      if (p.expiration_date && new Date(p.expiration_date) < now) return false;
      return true;
    });

    var inactivePermits = data.inactive_permits || [];

    if (active.length === 0 && inactivePermits.length === 0) {
      refundContainer.innerHTML = '<div class="refund-no-permits">No permits found for this customer.</div>';
      return;
    }

    // Active permits section
    if (active.length > 0) {
      var activeHeader = document.createElement("h4");
      activeHeader.className = "refund-permits-title";
      activeHeader.textContent = "Active Permits";
      refundContainer.appendChild(activeHeader);

      var activeList = document.createElement("div");
      activeList.className = "refund-permits-list";
      active.forEach(function (permit) {
        activeList.appendChild(_buildPermitCard(permit, data.customer));
      });
      refundContainer.appendChild(activeList);
    } else {
      var noActive = document.createElement("div");
      noActive.className = "refund-no-permits";
      noActive.textContent = "No active permits";
      refundContainer.appendChild(noActive);
    }

    // Inactive permits section
    if (inactivePermits.length > 0) {
      var inactiveHeader = document.createElement("h4");
      inactiveHeader.className = "refund-permits-title refund-inactive-title";
      inactiveHeader.innerHTML = 'Inactive Permits <span class="refund-inactive-subtitle">(charged within 30 days)</span>';
      refundContainer.appendChild(inactiveHeader);

      var inactiveList = document.createElement("div");
      inactiveList.className = "refund-inactive-list";
      inactivePermits.forEach(function (permit) {
        inactiveList.appendChild(_buildInactivePermitCard(permit));
      });
      refundContainer.appendChild(inactiveList);
    }
  }

  function _buildInactivePermitCard(permit) {
    var card = document.createElement("div");
    card.className = "refund-permit-card refund-permit-card--inactive";

    var vehicle = permit.vehicle || {};
    var vehicleStr = [vehicle.year, vehicle.make, vehicle.model, vehicle.color]
      .filter(Boolean).join(" ");
    var plateStr = vehicle.plate || "";
    var vehicleLine = vehicleStr ? vehicleStr + (plateStr ? " — " + plateStr : "") : plateStr;

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
        (permit.permit_name ? '<div class="refund-permit-detail"><span class="refund-detail-label">Permit:</span> ' + _esc(permit.permit_name) + '</div>' : '') +
        (vehicleLine ? '<div class="refund-permit-detail"><span class="refund-detail-label">Vehicle:</span> ' + _esc(vehicleLine) + '</div>' : '') +
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

    var effDate = permit.effective_date ? _formatDate(permit.effective_date) : "N/A";
    var expDate = permit.expiration_date ? _formatDate(permit.expiration_date) : "N/A";

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
      '<div class="refund-permit-actions"></div>' +
      '<div class="refund-permit-result"></div>';

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
        var btns = card.querySelectorAll(".refund-action-btn");
        for (var i = 0; i < btns.length; i++) btns[i].disabled = false;
      });
  }

  function _renderEvalResult(data, permit, customer, resultDiv) {
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
    var btnId = "process-refund-" + permit.id;

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
      html += '<button class="btn btn-primary refund-action-btn" id="' + btnId + '">Cancel & Forward to Accounting</button>';
      html += '</div>';
    } else {
      html += '<div class="refund-eval-actions">';
      html += '<div class="refund-eval-hint">Inform customer they do not qualify. Send Terms & Conditions.</div>';
      html += '</div>';
    }

    resultDiv.innerHTML = html;

    if (eligible) {
      var processBtn = document.getElementById(btnId);
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

    html += '<div class="refund-process-step ' + (cancelOk ? 'step-ok' : 'step-fail') + '">';
    html += (cancelOk ? 'Permit cancelled' : 'Cancel may have failed — verify in ParkM');
    html += '</div>';

    if (data.zoho_status_updated) {
      html += '<div class="refund-process-step step-ok">Ticket set to "Waiting on Accounting"</div>';
    } else if (data.zoho_status_updated === false) {
      html += '<div class="refund-process-step step-fail">Could not update ticket status — please set to "Waiting on Accounting" manually</div>';
    }

    if (acctEmail) {
      var insertBtnId = "insert-accounting-" + permit.id;
      html += '<div class="refund-accounting-email">';
      html += '<div class="refund-accounting-label">Email to <strong>' + _esc(acctEmail.to) + '</strong>:</div>';
      html += '<div class="refund-accounting-preview">' + acctEmail.body_html + '</div>';
      html += '<button class="btn btn-primary refund-action-btn" id="' + insertBtnId + '">Insert Email into Reply</button>';
      html += '</div>';
    }

    html += '</div>';
    resultDiv.innerHTML = html;

    if (acctEmail) {
      var insertBtn = document.getElementById("insert-accounting-" + permit.id);
      if (insertBtn) {
        insertBtn.addEventListener("click", function () {
          _insertAccountingEmail(acctEmail);
        });
      }
    }

    // Refresh customer data in background
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
      ZOHODESK.set("ticket.replyEditorRecipients", {
        to: [acctEmail.to],
        cc: [],
        bcc: []
      });
      ZOHODESK.invoke("INSERT", "ticket.replyEditor", { value: acctEmail.body_html, type: "replace" });
    } catch (e) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
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
    if (!lookupContainer) return;
    var infoDiv = lookupContainer.querySelector(".refund-customer-info");
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
    if (!lookupContainer) return;
    var el = lookupContainer.querySelector(".refund-lookup-error");
    if (el) {
      el.textContent = msg;
      el.style.display = "block";
    }
  }

  function _hideError() {
    if (!lookupContainer) return;
    var el = lookupContainer.querySelector(".refund-lookup-error");
    if (el) {
      el.style.display = "none";
      el.textContent = "";
    }
  }

  function _hideEl(el) {
    if (el) {
      el.style.display = "none";
      el.innerHTML = "";
    }
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
    initEmbedded: initEmbedded,
    getCustomerData: function () { return customerData; }
  };
})();
