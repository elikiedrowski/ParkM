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
    // Clear any lingering banner/selection from a previous ticket view
    _selectedPermitId = null;
    _lastPermitsData = null;
    var existingBanner = document.getElementById("refund-floating-banner");
    if (existingBanner) existingBanner.remove();
    document.body.style.paddingTop = "";

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

  var SEARCH_TABS = [
    { id: "email", label: "Email", placeholder: "name@example.com" },
    { id: "name", label: "Name", placeholder: "First or last name" },
    { id: "plate", label: "Plate", placeholder: "License plate" }
  ];
  var activeSearchTab = "email";

  function _renderLookupUI(container) {
    var tabsHtml = '<div class="refund-search-tabs">';
    for (var i = 0; i < SEARCH_TABS.length; i++) {
      var t = SEARCH_TABS[i];
      tabsHtml += '<button class="refund-search-tab' + (t.id === activeSearchTab ? ' refund-search-tab--active' : '') + '" data-tab="' + t.id + '">' + t.label + '</button>';
    }
    tabsHtml += '</div>';

    container.innerHTML =
      tabsHtml +
      '<div class="refund-lookup-row">' +
        '<input type="text" class="refund-search-input refund-email-input" placeholder="">' +
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

    var tabBtns = container.querySelectorAll(".refund-search-tab");
    for (var j = 0; j < tabBtns.length; j++) {
      tabBtns[j].addEventListener("click", function () {
        _switchTab(this.getAttribute("data-tab"));
      });
    }

    _applyTabPlaceholder();
  }

  function _switchTab(tabId) {
    activeSearchTab = tabId;
    if (!lookupContainer) return;
    var tabBtns = lookupContainer.querySelectorAll(".refund-search-tab");
    for (var i = 0; i < tabBtns.length; i++) {
      if (tabBtns[i].getAttribute("data-tab") === tabId) {
        tabBtns[i].classList.add("refund-search-tab--active");
      } else {
        tabBtns[i].classList.remove("refund-search-tab--active");
      }
    }
    var input = lookupContainer.querySelector(".refund-search-input");
    if (input) {
      input.value = "";
      input.focus();
    }
    _hideError();
    _hideEl(lookupContainer.querySelector(".refund-search-results"));
    _applyTabPlaceholder();
  }

  function _applyTabPlaceholder() {
    if (!lookupContainer) return;
    var input = lookupContainer.querySelector(".refund-search-input");
    if (!input) return;
    for (var i = 0; i < SEARCH_TABS.length; i++) {
      if (SEARCH_TABS[i].id === activeSearchTab) {
        input.placeholder = SEARCH_TABS[i].placeholder;
        return;
      }
    }
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
      _showError("Enter a search term");
      return;
    }

    var btn = lookupContainer.querySelector(".refund-lookup-btn");
    btn.disabled = true;
    btn.textContent = "Searching...";
    _hideError();
    _hideEl(lookupContainer.querySelector(".refund-search-results"));
    _hideEl(lookupContainer.querySelector(".refund-customer-info"));
    if (refundContainer) {
      refundContainer.innerHTML = '<div class="refund-eval-placeholder">Searching...</div>';
    }

    if (activeSearchTab === "email" || (activeSearchTab !== "email" && _isEmail(query))) {
      _doEmailLookup(query);
    } else if (activeSearchTab === "name") {
      _doNameSearch(query);
    } else if (activeSearchTab === "plate") {
      _doPlateSearch(query);
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

  function _doPlateSearch(query) {
    var btn = lookupContainer.querySelector(".refund-lookup-btn");
    var url = ParkMConfig.API_BASE_URL + "/parkm/search/plate?q=" + encodeURIComponent(query);

    _fetchWithTimeout(url, null, 35000)
      .then(function (data) {
        btn.disabled = false;
        btn.textContent = "Search";

        var results = data.results || [];
        if (results.length === 0) {
          _showError('No vehicles found for plate "' + _esc(query) + '".');
          if (refundContainer) {
            refundContainer.innerHTML = '<div class="refund-eval-placeholder">No vehicle found — cannot evaluate refunds.</div>';
          }
          return;
        }

        _renderPlateResults(results);
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = "Search";
        _showError("Plate search failed: " + err.message);
      });
  }

  function _doUnitSearch(query) {
    var btn = lookupContainer.querySelector(".refund-lookup-btn");
    var url = ParkMConfig.API_BASE_URL + "/parkm/search/unit?q=" + encodeURIComponent(query);

    _fetchWithTimeout(url, null, 35000)
      .then(function (data) {
        btn.disabled = false;
        btn.textContent = "Search";

        var results = data.results || [];
        if (results.length === 0) {
          _showError('No units found for "' + _esc(query) + '".');
          if (refundContainer) {
            refundContainer.innerHTML = '<div class="refund-eval-placeholder">No unit found — cannot evaluate refunds.</div>';
          }
          return;
        }

        _renderUnitResults(results);
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = "Search";
        _showError("Unit search failed: " + err.message);
      });
  }

  function _renderPlateResults(results) {
    var container = lookupContainer.querySelector(".refund-search-results");
    container.style.display = "block";
    var html = '<div class="refund-search-results-title">' + results.length + ' vehicle' + (results.length !== 1 ? 's' : '') + ' found</div>';

    for (var i = 0; i < results.length; i++) {
      var r = results[i];
      var detailParts = [];
      if (r.customer_name) detailParts.push(r.customer_name);
      if (r.community) detailParts.push(r.community);

      html += '<div class="refund-search-result-item" data-idx="' + i + '">' +
        '<div class="refund-search-result-info">' +
          '<div class="refund-search-result-name">' + _esc(r.plate_state || r.plate || "Unknown plate") + '</div>' +
          (r.vehicle_description ? '<div class="refund-search-result-detail">' + _esc(r.vehicle_description.trim()) + '</div>' : '') +
          (detailParts.length > 0 ? '<div class="refund-search-result-detail">' + _esc(detailParts.join(" · ")) + '</div>' : '') +
        '</div>' +
        '<div class="refund-search-result-select">Select &rarr;</div>' +
      '</div>';
    }

    container.innerHTML = html;
    if (refundContainer) {
      refundContainer.innerHTML = '<div class="refund-eval-placeholder">Pick a vehicle above to load the customer\'s permits.</div>';
    }

    var items = container.querySelectorAll(".refund-search-result-item");
    for (var j = 0; j < items.length; j++) {
      (function (idx) {
        items[idx].addEventListener("click", function () {
          _selectPlateResult(results[idx]);
        });
      })(j);
    }
  }

  function _selectPlateResult(result) {
    // Plate search returns customer_name but not customerId. Look the customer
    // up by name and load their record.
    if (!result.customer_name) {
      _showError("This vehicle has no customer linked. Try a different search.");
      return;
    }
    _hideEl(lookupContainer.querySelector(".refund-search-results"));
    _hideError();
    if (refundContainer) {
      refundContainer.innerHTML = '<div class="refund-eval-placeholder">Loading customer...</div>';
    }

    var url = ParkMConfig.API_BASE_URL + "/parkm/customer/search?q=" + encodeURIComponent(result.customer_name);
    _fetchWithTimeout(url, null, 65000)
      .then(function (data) {
        var matches = (data.results || []).filter(function (c) {
          return c.email && c.email.indexOf("@fake.com") === -1;
        });
        if (matches.length === 0) {
          _showError("Could not find a customer record for " + _esc(result.customer_name) + ".");
          if (refundContainer) {
            refundContainer.innerHTML = '<div class="refund-eval-placeholder">No customer record found.</div>';
          }
          return;
        }
        if (matches.length === 1) {
          _selectSearchResult(matches[0]);
          return;
        }
        // Multiple matches — show name picker
        _renderSearchResults(matches);
      })
      .catch(function (err) {
        _showError("Customer lookup failed: " + err.message);
      });
  }

  function _renderUnitResults(results) {
    var container = lookupContainer.querySelector(".refund-search-results");
    container.style.display = "block";
    var html = '<div class="refund-search-results-title">' + results.length + ' unit' + (results.length !== 1 ? 's' : '') + ' found</div>';

    for (var i = 0; i < results.length; i++) {
      var r = results[i];
      var residentCount = (r.customers || []).length;
      var residentLabel = residentCount === 1 ? r.customers[0].name : (residentCount + " residents");

      html += '<div class="refund-search-result-item" data-idx="' + i + '">' +
        '<div class="refund-search-result-info">' +
          '<div class="refund-search-result-name">Unit ' + _esc(r.unit_number || "?") + '</div>' +
          (r.address ? '<div class="refund-search-result-detail">' + _esc(r.address) + '</div>' : '') +
          (residentCount > 0 ? '<div class="refund-search-result-detail">' + _esc(residentLabel) + '</div>' : '<div class="refund-search-result-detail">No residents</div>') +
        '</div>' +
        '<div class="refund-search-result-select">Select &rarr;</div>' +
      '</div>';
    }

    container.innerHTML = html;
    if (refundContainer) {
      refundContainer.innerHTML = '<div class="refund-eval-placeholder">Pick a unit above to load the resident\'s permits.</div>';
    }

    var items = container.querySelectorAll(".refund-search-result-item");
    for (var j = 0; j < items.length; j++) {
      (function (idx) {
        items[idx].addEventListener("click", function () {
          _selectUnitResult(results[idx]);
        });
      })(j);
    }
  }

  function _selectUnitResult(result) {
    var residents = (result.customers || []);
    if (residents.length === 0) {
      _showError("This unit has no residents on file.");
      return;
    }
    if (residents.length === 1) {
      _selectSearchResult(residents[0]);
      return;
    }
    // Multiple residents — show resident picker using the existing search results renderer
    _renderSearchResults(residents);
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
    } else if (result.id) {
      _doLookupById(result.id);
    } else {
      _showError("This account has no email or ID on file. Please try a different search.");
    }
  }

  function _doLookupById(customerId) {
    if (refundContainer) {
      refundContainer.innerHTML = '<div class="refund-eval-placeholder">Loading customer...</div>';
    }
    var url = ParkMConfig.API_BASE_URL + "/parkm/customer/by-id/" + encodeURIComponent(customerId);
    _fetchWithTimeout(url, null, 35000)
      .then(function (data) {
        customerData = data;
        if (!data.found) {
          _showError("Customer record could not be loaded.");
          return;
        }
        _renderCustomerInfo(data);
        _renderPermits(data);
      })
      .catch(function (err) {
        _showError("Customer lookup failed: " + err.message);
      });
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

  // Module-level selection state. When set, _renderPermits collapses non-selected
  // permits behind a "Show all permits" toggle.
  var _selectedPermitId = null;
  var _lastPermitsData = null;

  function _selectPermit(permitId) {
    _selectedPermitId = permitId;
    if (_lastPermitsData) _renderPermits(_lastPermitsData);
    _renderFloatingBanner();
  }

  function _clearPermitSelection() {
    _selectedPermitId = null;
    if (_lastPermitsData) _renderPermits(_lastPermitsData);
    _renderFloatingBanner();
  }

  /* ── Floating permit card ────────────────────────────────────────────
     Renders the FULL selected permit card (with action buttons) pinned to the
     top of the widget viewport so CSRs keep both context AND actions as they
     scroll through wizard steps. */

  function _renderFloatingBanner() {
    var existing = document.getElementById("refund-floating-banner");
    if (existing) existing.remove();
    if (!_selectedPermitId || !_lastPermitsData) {
      document.body.style.paddingTop = "";
      return;
    }

    var active = (_lastPermitsData.permits || []).filter(function (p) {
      var now = new Date();
      if (p.is_cancelled) return false;
      if (p.expiration_date && new Date(p.expiration_date) < now) return false;
      return true;
    });
    var inactivePermits = _lastPermitsData.inactive_permits || [];
    var customer = _lastPermitsData.customer;

    var banner = document.createElement("div");
    banner.id = "refund-floating-banner";

    var header = document.createElement("div");
    header.className = "refund-floating-header";
    header.innerHTML =
      '<span class="refund-floating-label">Selected Permit</span>' +
      '<button class="refund-floating-clear" type="button">Clear</button>';
    banner.appendChild(header);

    var activeSel = active.find(function (p) { return p.id === _selectedPermitId; });
    if (activeSel) {
      banner.appendChild(_buildPermitCard(activeSel, customer));
    } else {
      var inacSel = inactivePermits.find(function (p) { return p.id === _selectedPermitId; });
      if (inacSel) banner.appendChild(_buildInactivePermitCard(inacSel, customer));
    }

    document.body.appendChild(banner);
    banner.querySelector(".refund-floating-clear").addEventListener("click", _clearPermitSelection);
    _syncBodyPaddingForBanner();
    // Re-measure whenever the card's content changes (eligibility result,
    // email preview, error messages, etc.)
    new MutationObserver(_syncBodyPaddingForBanner).observe(banner, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  // Keep the body padded enough so the floating banner doesn't overlap the
  // wizard content beneath it. Re-measured on each render since the card's
  // result area can grow (eligibility block, email preview, etc.).
  function _syncBodyPaddingForBanner() {
    var banner = document.getElementById("refund-floating-banner");
    if (!banner) {
      document.body.style.paddingTop = "";
      return;
    }
    // Use requestAnimationFrame so we measure after layout
    requestAnimationFrame(function () {
      var h = banner.getBoundingClientRect().height;
      document.body.style.paddingTop = (h + 8) + "px";
    });
  }

  function _renderPermits(data) {
    if (!refundContainer) return;
    _lastPermitsData = data;
    refundContainer.innerHTML = "";
    // Keep the floating banner in sync with the latest permit data
    setTimeout(_renderFloatingBanner, 0);

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

    // Reset selection if the selected permit is no longer in the list
    if (_selectedPermitId) {
      var stillHere =
        active.some(function (p) { return p.id === _selectedPermitId; }) ||
        inactivePermits.some(function (p) { return p.id === _selectedPermitId; });
      if (!stillHere) _selectedPermitId = null;
    }

    var totalOthers = active.length + inactivePermits.length - (_selectedPermitId ? 1 : 0);

    // When a permit is selected, the full card renders in the floating banner
    // at the top of the widget (see _renderFloatingBanner). The normal flow just
    // shows a "change selection" link so the CSR can go back to the full list.
    if (_selectedPermitId) {
      var placeholder = document.createElement("div");
      placeholder.className = "refund-selected-placeholder";
      placeholder.innerHTML =
        '<div class="refund-selected-placeholder-text">Permit selected — see the permit card pinned at the top of the widget.</div>';

      var toggle = document.createElement("button");
      toggle.className = "btn btn-link refund-show-all-btn";
      toggle.textContent = "↺ Change selection / show all permits" +
        (totalOthers + 1 > 1 ? " (" + (totalOthers + 1) + ")" : "");
      toggle.addEventListener("click", _clearPermitSelection);
      placeholder.appendChild(toggle);

      refundContainer.appendChild(placeholder);
      return;
    }

    // Unselected: full list
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

    if (inactivePermits.length > 0) {
      var inactiveHeader = document.createElement("h4");
      inactiveHeader.className = "refund-permits-title refund-inactive-title";
      inactiveHeader.innerHTML = 'Inactive Permits <span class="refund-inactive-subtitle">(charged within 30 days)</span>';
      refundContainer.appendChild(inactiveHeader);

      var inactiveList = document.createElement("div");
      inactiveList.className = "refund-inactive-list";
      inactivePermits.forEach(function (permit) {
        inactiveList.appendChild(_buildInactivePermitCard(permit, data.customer));
      });
      refundContainer.appendChild(inactiveList);
    }
  }

  function _buildInactivePermitCard(permit, customer) {
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
      '</div>' +
      '<div class="refund-permit-actions"></div>' +
      '<div class="refund-permit-result"></div>';

    // Inactive permits skip the Cancel Permit button (already cancelled/expired)
    // but can still go through Evaluate Refund if charged within 30 days.
    if (customer) {
      var actionsDiv = card.querySelector(".refund-permit-actions");
      var evalBtn = document.createElement("button");
      evalBtn.className = "btn btn-primary refund-action-btn";
      evalBtn.textContent = "Evaluate Refund";
      evalBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        _evaluateRefund(permit, customer, card);
      });
      actionsDiv.appendChild(evalBtn);
    }

    return card;
  }

  function _buildPermitCard(permit, customer) {
    var card = document.createElement("div");
    var isSelected = (_selectedPermitId === permit.id);
    card.className = "refund-permit-card" + (isSelected ? " refund-permit-card--selected" : "");
    card.setAttribute("data-permit-id", permit.id);
    // Whole-card click = select this permit (ignoring clicks on buttons)
    if (!isSelected) {
      card.style.cursor = "pointer";
      card.addEventListener("click", function (e) {
        if (e.target.closest(".refund-action-btn")) return;
        _selectPermit(permit.id);
      });
    }

    var vehicle = permit.vehicle || {};
    var vehicleStr = [vehicle.year, vehicle.make, vehicle.model, vehicle.color]
      .filter(Boolean).join(" ");
    var plateStr = vehicle.plate ? " — " + vehicle.plate : "";

    var effDate = permit.effective_date ? _formatDate(permit.effective_date) : "N/A";
    var expDate = permit.expiration_date ? _formatDate(permit.expiration_date) : "N/A";

    var price = permit.recurring_price || permit.permit_price || permit.total_amount;
    var priceStr = price ? "$" + parseFloat(price).toFixed(2) : "N/A";
    var recurStr = permit.is_recurring ? " /mo" : " one-time";

    var delayCancelLine = '';
    if (permit.delay_cancellation_date) {
      delayCancelLine = '<div class="refund-permit-detail refund-delay-cancel-notice">' +
        '<span class="refund-detail-label">Cancellation Scheduled:</span> ' +
        _formatDate(permit.delay_cancellation_date) +
      '</div>';
    }

    card.innerHTML =
      '<div class="refund-permit-header">' +
        '<div class="refund-permit-type">' + _esc(permit.type_name) + '</div>' +
        (permit.delay_cancellation_date ? '<span class="refund-delay-badge">Permit Set to be Cancelled</span>' : '') +
      '</div>' +
      '<div class="refund-permit-details">' +
        (vehicleStr ? '<div class="refund-permit-detail"><span class="refund-detail-label">Vehicle:</span> ' + _esc(vehicleStr + plateStr) + '</div>' : '') +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Effective:</span> ' + effDate + '</div>' +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Expires:</span> ' + expDate + '</div>' +
        '<div class="refund-permit-detail"><span class="refund-detail-label">Price:</span> ' + priceStr + recurStr + '</div>' +
        (permit.balance_due > 0 ? '<div class="refund-permit-detail refund-balance-due"><span class="refund-detail-label">Balance Due:</span> $' + parseFloat(permit.balance_due).toFixed(2) + '</div>' : '') +
        delayCancelLine +
      '</div>' +
      '<div class="refund-permit-actions"></div>' +
      '<div class="refund-permit-result"></div>';

    // Action buttons only show on the selected card — unselected permits are
    // click-to-select only (no Evaluate Refund / Cancel Permit available).
    if (isSelected) {
      var actionsDiv = card.querySelector(".refund-permit-actions");

      var evalBtn = document.createElement("button");
      evalBtn.className = "btn btn-primary refund-action-btn";
      evalBtn.textContent = "Evaluate Refund";
      evalBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        _evaluateRefund(permit, customer, card);
      });
      actionsDiv.appendChild(evalBtn);

      var cancelBtn = document.createElement("button");
      cancelBtn.className = "btn btn-secondary refund-action-btn";
      cancelBtn.textContent = "Cancel Permit";
      cancelBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        _cancelPermit(permit, card);
      });
      actionsDiv.appendChild(cancelBtn);
    }

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

    var alreadyHandled = permit.is_cancelled || !!permit.delay_cancellation_date;
    var processBtnLabel = alreadyHandled ? "Forward to Accounting" : "Cancel & Forward to Accounting";

    if (eligible) {
      html += '<div class="refund-eval-actions">';
      html += '<button class="btn btn-primary refund-action-btn" id="' + btnId + '">' + processBtnLabel + '</button>';
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
    var alreadyHandled = permit.is_cancelled || !!permit.delay_cancellation_date;
    var doProcess = function (opts) {
      // opts: { cancel_date: null|string, send_notice: bool, refund_reason: string }
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
        reason: opts.refund_reason || "Customer requested cancellation/refund",
        ticket_id: ticketId,
        cancel_date: opts.cancel_date
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
            processBtn.textContent = alreadyHandled
              ? "Forward to Accounting"
              : "Cancel & Forward to Accounting";
          }
          resultDiv.insertAdjacentHTML("beforeend",
            '<div class="refund-error">Processing failed: ' + _esc(err.message) + '</div>');
        });
    };

    if (alreadyHandled) {
      // Permit already cancelled or scheduled to cancel — skip the Cancel/Delay
      // dialog entirely. Reuse the existing scheduled date if any; backend will
      // not re-cancel an already-handled permit.
      _showRefundReasonDialog({
        cancel_date: permit.delay_cancellation_date || null,
        send_notice: false,
      }, doProcess);
    } else {
      _showCancelDialog(permit, doProcess, /* requireReason */ true);
    }
  }

  function _renderProcessResult(data, permit, resultDiv) {
    var permitResult = null;
    (data.results || []).forEach(function (r) {
      if (r.permit && r.permit.id === permit.id) {
        permitResult = r;
      }
    });

    var cancelOk = permitResult && permitResult.cancel_result && permitResult.cancel_result.success;
    var cancelResult = permitResult && permitResult.cancel_result;
    var acctEmail = permitResult && permitResult.accounting_email;

    var html = '<div class="refund-process-result">';

    var cancelMsg;
    if (cancelOk && cancelResult.cancel_type === "delayed") {
      cancelMsg = "Permit cancellation scheduled for " + _formatDate(cancelResult.cancel_date);
    } else if (cancelOk && cancelResult.cancel_type === "already_cancelled") {
      cancelMsg = "Permit was already cancelled";
    } else if (cancelOk) {
      cancelMsg = "Permit cancelled";
    } else {
      cancelMsg = "Cancel may have failed — verify in ParkM";
    }
    html += '<div class="refund-process-step ' + (cancelOk ? 'step-ok' : 'step-fail') + '">';
    html += cancelMsg;
    html += '</div>';

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
    _showCancelDialog(permit, function (opts) {
      // opts: { cancel_date: null|string, send_notice: bool }
      var btns = card.querySelectorAll(".refund-action-btn");
      for (var i = 0; i < btns.length; i++) btns[i].disabled = true;

      var resultDiv = card.querySelector(".refund-permit-result");
      resultDiv.innerHTML = '<div class="refund-loading">Cancelling...</div>';

      _fetchWithTimeout(ParkMConfig.API_BASE_URL + "/parkm/permit/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          permit_id: permit.id,
          send_notice: opts.send_notice,
          cancel_date: opts.cancel_date
        })
      })
        .then(function (data) {
          if (data.success) {
            var msg = data.cancel_type === "delayed"
              ? "Permit cancellation scheduled for " + _formatDate(opts.cancel_date)
              : "Permit cancelled successfully";
            resultDiv.innerHTML = '<div class="refund-process-step step-ok">' + _esc(msg) + '</div>';
            card.classList.add("refund-permit-card--cancelled");
            _refreshPermits();
          } else {
            resultDiv.innerHTML = '<div class="refund-process-step step-fail">Cancel failed — try manually in ParkM</div>';
            var btns2 = card.querySelectorAll(".refund-action-btn");
            for (var j = 0; j < btns2.length; j++) btns2[j].disabled = false;
          }
        })
        .catch(function (err) {
          resultDiv.innerHTML = '<div class="refund-error">Cancel failed: ' + _esc(err.message) + '</div>';
          var btns2 = card.querySelectorAll(".refund-action-btn");
          for (var j = 0; j < btns2.length; j++) btns2[j].disabled = false;
        });
    });
  }

  /* ── Cancel Dialog (two-step: immediate vs delay) ─────────────────
     requireReason: when true, appends the Refund Reason dialog before
     onConfirm fires. Used for the Evaluate Refund flow.
     When false, cancel-only flow — no reason, no accounting email. */

  function _showCancelDialog(permit, onConfirm, requireReason) {
    // Remove any existing dialog
    var existing = document.getElementById("cancel-dialog-overlay");
    if (existing) existing.remove();

    // Default delay date: 1 week from now
    var defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 7);
    var defaultDateStr = defaultDate.toISOString().slice(0, 16); // yyyy-MM-ddTHH:mm

    var overlay = document.createElement("div");
    overlay.id = "cancel-dialog-overlay";
    overlay.className = "cancel-dialog-overlay";

    // Step 1: Choose cancel type
    overlay.innerHTML =
      '<div class="cancel-dialog">' +
        '<div class="cancel-dialog-header">' +
          '<h3 class="cancel-dialog-title">Delay Cancellation</h3>' +
          '<button class="cancel-dialog-x" data-action="close">&times;</button>' +
        '</div>' +
        '<div class="cancel-dialog-body">' +
          '<p>Would you like to cancel immediately or delay the cancellation to a future date?</p>' +
        '</div>' +
        '<div class="cancel-dialog-footer">' +
          '<button class="btn btn-link cancel-dialog-btn" data-action="close">Close</button>' +
          '<button class="btn btn-secondary cancel-dialog-btn" data-action="now">Cancel Now</button>' +
          '<button class="btn btn-primary cancel-dialog-btn" data-action="delay">Delay</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);

    // Event delegation for step 1
    overlay.addEventListener("click", function handler(e) {
      var action = e.target.getAttribute("data-action");
      if (!action) {
        // Click on overlay background closes
        if (e.target === overlay) {
          overlay.remove();
        }
        return;
      }

      if (action === "close") {
        overlay.remove();
      } else if (action === "now") {
        overlay.remove();
        var nowOpts = { cancel_date: null, send_notice: true };
        if (requireReason) {
          _showRefundReasonDialog(nowOpts, onConfirm);
        } else {
          onConfirm(nowOpts);
        }
      } else if (action === "delay") {
        // Transition to step 2: date picker
        _showDelayDatePicker(overlay, defaultDateStr, onConfirm, requireReason);
      }
    });
  }

  function _showRefundReasonDialog(baseOpts, onConfirm) {
    var overlay = document.createElement("div");
    overlay.id = "cancel-dialog-overlay";
    overlay.className = "cancel-dialog-overlay";

    overlay.innerHTML =
      '<div class="cancel-dialog">' +
        '<div class="cancel-dialog-header">' +
          '<h3 class="cancel-dialog-title">Refund Reason</h3>' +
          '<button class="cancel-dialog-x" data-action="close">&times;</button>' +
        '</div>' +
        '<div class="cancel-dialog-body">' +
          '<p>Enter the reason for this refund (required):</p>' +
          '<textarea class="cancel-dialog-reason-input" rows="4" placeholder="e.g. Resident moved out, stopped using the permit, etc."></textarea>' +
          '<div class="cancel-dialog-reason-error" style="display:none; color:#dc2626; font-size:12px; margin-top:6px;">Refund reason is required.</div>' +
        '</div>' +
        '<div class="cancel-dialog-footer">' +
          '<button class="btn btn-link cancel-dialog-btn" data-action="close">Cancel</button>' +
          '<button class="btn btn-primary cancel-dialog-btn" data-action="submit">Forward to Accounting</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);

    var textarea = overlay.querySelector(".cancel-dialog-reason-input");
    var errorEl = overlay.querySelector(".cancel-dialog-reason-error");
    if (textarea) textarea.focus();

    overlay.addEventListener("click", function (e) {
      var action = e.target.getAttribute("data-action");
      if (!action) {
        if (e.target === overlay) overlay.remove();
        return;
      }
      if (action === "close") {
        overlay.remove();
      } else if (action === "submit") {
        var reason = (textarea && textarea.value || "").trim();
        if (!reason) {
          errorEl.style.display = "block";
          textarea.style.borderColor = "#dc2626";
          textarea.focus();
          return;
        }
        overlay.remove();
        var finalOpts = Object.assign({}, baseOpts, { refund_reason: reason });
        onConfirm(finalOpts);
      }
    });
  }

  function _showDelayDatePicker(overlay, defaultDateStr, onConfirm, requireReason) {
    // Replace the overlay entirely to avoid stacking event listeners
    overlay.remove();

    var overlay2 = document.createElement("div");
    overlay2.id = "cancel-dialog-overlay";
    overlay2.className = "cancel-dialog-overlay";

    overlay2.innerHTML =
      '<div class="cancel-dialog">' +
        '<div class="cancel-dialog-header">' +
          '<h3 class="cancel-dialog-title">Schedule Cancellation</h3>' +
          '<button class="cancel-dialog-x" data-action="close">&times;</button>' +
        '</div>' +
        '<div class="cancel-dialog-body">' +
          '<p>Select the date and time for the cancellation:</p>' +
          '<div class="cancel-dialog-date-row">' +
            '<input type="datetime-local" class="cancel-dialog-date-input" value="' + defaultDateStr + '">' +
          '</div>' +
          '<label class="cancel-dialog-notice-label">' +
            '<input type="checkbox" class="cancel-dialog-notice-check" checked> ' +
            'Send cancellation notice to resident' +
          '</label>' +
        '</div>' +
        '<div class="cancel-dialog-footer">' +
          '<button class="btn btn-link cancel-dialog-btn" data-action="back">Back</button>' +
          '<button class="btn btn-secondary cancel-dialog-btn" data-action="close">Cancel</button>' +
          '<button class="btn btn-primary cancel-dialog-btn" data-action="schedule">Schedule Cancellation</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay2);

    var dialog = overlay2.querySelector(".cancel-dialog");

    overlay2.addEventListener("click", function (e) {
      var action = e.target.getAttribute("data-action");
      if (!action) {
        if (e.target === overlay2) overlay2.remove();
        return;
      }

      if (action === "close") {
        overlay2.remove();
      } else if (action === "back") {
        overlay2.remove();
        _showCancelDialog(null, onConfirm, requireReason); // re-show step 1
      } else if (action === "schedule") {
        var dateInput = dialog.querySelector(".cancel-dialog-date-input");
        var noticeCheck = dialog.querySelector(".cancel-dialog-notice-check");
        var dateVal = dateInput ? dateInput.value : "";
        if (!dateVal) {
          dateInput.style.borderColor = "#e74c3c";
          dateInput.focus();
          return;
        }
        var selectedDate = new Date(dateVal);
        if (isNaN(selectedDate.getTime())) {
          dateInput.style.borderColor = "#e74c3c";
          dateInput.focus();
          return;
        }
        overlay2.remove();
        var scheduledOpts = {
          cancel_date: selectedDate.toISOString(),
          send_notice: noticeCheck ? noticeCheck.checked : true
        };
        if (requireReason) {
          _showRefundReasonDialog(scheduledOpts, onConfirm);
        } else {
          onConfirm(scheduledOpts);
        }
      }
    });
  }

  /* ── Insert Accounting Email ────────────────────────────────────── */

  function _insertAccountingEmail(acctEmail) {
    var inserted = false;
    try {
      ZOHODESK.set("ticket.replyEditorRecipients", {
        to: [acctEmail.to],
        cc: [],
        bcc: []
      });
      ZOHODESK.invoke("INSERT", "ticket.replyEditor", { value: acctEmail.body_html, type: "replace" });
      inserted = true;
    } catch (e) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        var tmp = document.createElement("div");
        tmp.innerHTML = acctEmail.body_html;
        navigator.clipboard.writeText(tmp.textContent || tmp.innerText || "");
        alert("Email copied to clipboard (unable to insert directly).");
        inserted = true;
      }
    }
    // Once the email is in the reply, the permit's refund workflow is done —
    // collapse the floating card so the CSR can see the remaining wizard
    // steps (respond to resident, update ticket status, send survey).
    if (inserted) _clearPermitSelection();
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
