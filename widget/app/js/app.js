/**
 * ParkM CSR Wizard — Main App Orchestrator
 * Supports multi-intent classification: reads semicolon-separated tags from
 * cf_ai_tags and stacks wizard steps for each tag.
 */
var ParkMApp = (function () {
  var currentWizards = [];   // array of wizard objects (one per tag)
  var currentTags = [];      // array of tag strings from AI
  var ticketId = null;
  var customFields = {};
  var pollTimer = null;
  var POLL_INTERVAL = 5000;  // 5 seconds
  var isLoadingTicket = false;  // guard against concurrent loadTicket calls

  /* ── Show / hide state panels ─────────────────────────────────────── */

  function showState(stateId) {
    var states = ["loading-state", "error-state", "no-classification-state", "wizard-container"];
    states.forEach(function (id) {
      document.getElementById(id).style.display = (id === stateId) ? "" : "none";
    });
    if (stateId === "wizard-container") {
      document.getElementById("wizard-container").style.display = "block";
    }
  }

  function showError(msg) {
    document.getElementById("error-message").textContent = msg || "Unable to load wizard data.";
    showState("error-state");
  }

  /* ── Parse multi-select tags ───────────────────────────────────────── */

  function parseTags(tagValue) {
    if (!tagValue) return [];
    return tagValue.split(";").map(function (t) { return t.trim(); }).filter(Boolean);
  }

  /* ── Fetch wizard content from Railway API ────────────────────────── */

  function fetchWizard(tag, tktId) {
    var url = ParkMConfig.API_BASE_URL + "/wizard/" + encodeURIComponent(tag);
    if (tktId) url += "?ticket_id=" + encodeURIComponent(tktId);

    return fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error("API error: " + res.status);
        return res.json();
      })
      .then(function (data) {
        return { wizard: data.wizard, contact_email: data.contact_email || "" };
      });
  }

  /* ── Fetch and render all wizards (stacked) ────────────────────────── */

  function loadWizardsForTags(tags) {
    showState("loading-state");

    var promises = tags.map(function (tag) {
      return fetchWizard(tag, ticketId);
    });

    Promise.all(promises)
      .then(function (results) {
        currentWizards = results.map(function (r) { return r.wizard; });
        // Extract contact email from first wizard response that has one
        var contactEmail = "";
        for (var i = 0; i < results.length; i++) {
          if (results[i].contact_email) { contactEmail = results[i].contact_email; break; }
        }
        renderStackedWizards(tags, currentWizards);
        // Initialize step-embedded refund tools (account lookup + refund evaluation)
        if (typeof RefundPanel !== "undefined") {
          RefundPanel.initEmbedded(contactEmail);
        }
        showState("wizard-container");
        resizeWidget();
      })
      .catch(function (err) {
        console.error("Failed to load wizards:", err);
        showError("Failed to load wizard data.");
      });
  }

  /* ── Render stacked wizards ────────────────────────────────────────── */

  function renderStackedWizards(tags, wizards) {
    // Render header for the primary (first) tag
    var primary = wizards[0];
    WizardRenderer.renderHeader(primary, customFields);

    // If multiple tags, show a tag list
    var tagListEl = document.getElementById("tag-list");
    if (tagListEl) {
      tagListEl.innerHTML = "";
      if (tags.length > 1) {
        tagListEl.style.display = "block";
        tags.forEach(function (tag, idx) {
          var pill = document.createElement("span");
          pill.className = "tag-pill" + (idx === 0 ? " tag-pill--primary" : "");
          pill.textContent = tag;
          pill.setAttribute("data-section-idx", idx);
          pill.addEventListener("click", function () {
            // Highlight this pill
            var allPills = tagListEl.querySelectorAll(".tag-pill");
            for (var i = 0; i < allPills.length; i++) {
              allPills[i].classList.remove("tag-pill--primary");
            }
            pill.classList.add("tag-pill--primary");
            // Scroll to section header
            var sectionEl = document.getElementById("section-header-" + idx);
            if (sectionEl) {
              sectionEl.scrollIntoView({ behavior: "smooth", block: "start" });
            }
          });
          tagListEl.appendChild(pill);
        });
      } else {
        tagListEl.style.display = "none";
      }
    }

    // Render entities from primary wizard
    WizardRenderer.renderEntities(primary);

    // Stack steps from all wizards with section headers
    var allSteps = [];
    var allTemplates = [];
    wizards.forEach(function (wizard, idx) {
      // Add section header step if multiple wizards
      if (wizards.length > 1) {
        allSteps.push({
          id: "_section_" + idx,
          text: tags[idx],
          is_section_header: true
        });
      }
      (wizard.steps || []).forEach(function (step) {
        // Namespace step IDs to avoid collisions between wizards
        var namespacedStep = Object.assign({}, step, {
          id: idx + "_" + step.id
        });
        // Also namespace depends_on for conditional steps
        if (step.depends_on !== undefined) {
          namespacedStep.depends_on = idx + "_" + step.depends_on;
        }
        allSteps.push(namespacedStep);
      });
      (wizard.quick_templates || []).forEach(function (tpl) {
        if (allTemplates.indexOf(tpl) === -1) allTemplates.push(tpl);
      });
    });

    WizardRenderer.renderSteps(allSteps);
    TemplatePanel.renderButtons(allTemplates);
  }

  /* ── Populate the correction dropdown ─────────────────────────────── */

  function populateCorrectionDropdown() {
    var select = document.getElementById("corrected-intent-select");

    // Correction dropdown not applicable for multi-select tags in the same way.
    // Hide it — CSRs use the Agent Corrected Tags field in Zoho directly.
    if (select) {
      var wrapper = select.closest(".correction-section") || select.parentElement;
      if (wrapper) wrapper.style.display = "none";
    }
  }

  /* ── Resize widget to fill available panel height ─────────────────── */

  function resizeWidget() {
    try {
      if (typeof ZOHODESK !== "undefined") {
        // Use the larger of content height or viewport to fill the panel
        var contentHeight = document.body.scrollHeight;
        var viewportHeight = window.innerHeight || 800;
        var targetHeight = Math.max(contentHeight, viewportHeight, 600);
        ZOHODESK.invoke("RESIZE", { height: targetHeight + "px", width: "100%" });
      }
    } catch (e) {
      console.log("Resize failed:", e);
    }
  }

  // Keep widget height dynamic as content changes
  if (typeof ResizeObserver !== "undefined") {
    var _resizeTimer;
    var ro = new ResizeObserver(function () {
      clearTimeout(_resizeTimer);
      _resizeTimer = setTimeout(resizeWidget, 100);
    });
    ro.observe(document.body);
  }

  /* ── Poll for classification updates ─────────────────────────────── */

  function startPolling() {
    stopPolling();
    console.log("Starting poll for AI classification...");
    pollTimer = setInterval(function () {
      ZOHODESK.get("ticket.cf").then(function (cfResponse) {
        var cf = cfResponse["ticket.cf"] || {};
        var aiTagsRaw = cf[ParkMConfig.FIELDS.AI_TAGS];
        var aiTags = parseTags(aiTagsRaw);

        if (aiTags.length > 0) {
          console.log("Classification detected:", aiTags);
          stopPolling();
          customFields = cf;
          currentTags = aiTags;

          var correctedTagsRaw = cf[ParkMConfig.FIELDS.AGENT_CORRECTED_TAGS];
          var correctedTags = parseTags(correctedTagsRaw);
          var activeTags = correctedTags.length > 0 ? correctedTags : aiTags;

          populateCorrectionDropdown();
          loadWizardsForTags(activeTags);
        }
      }).catch(function (err) {
        console.log("Poll check failed:", err);
      });
    }, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  /* ── Redirect wizard (called by decision points) ──────────────────── */

  function onRedirectWizard(newTag) {
    loadWizardsForTags([newTag]);
  }

  /* ── Validation confirmed callback ────────────────────────────────── */

  function onValidationConfirmed() {
    console.log("Validation confirmed — ticket can be closed.");
  }

  /* ── Reset state for ticket switch ─────────────────────────────────── */

  function resetState() {
    stopPolling();
    currentWizards = [];
    currentTags = [];
    ticketId = null;
    customFields = {};
  }

  /* ── Load ticket data (used by init and ticket change handler) ───── */

  function loadTicket() {
    if (isLoadingTicket) return;
    isLoadingTicket = true;
    resetState();
    showState("loading-state");

    Promise.all([
      ZOHODESK.get("ticket.id"),
      ZOHODESK.get("ticket.cf")
    ]).then(function (results) {
      var idResponse = results[0];
      var cfResponse = results[1];

      console.log("ticket.id response:", JSON.stringify(idResponse));
      console.log("ticket.cf response:", JSON.stringify(cfResponse));

      ticketId = idResponse["ticket.id"];
      customFields = cfResponse["ticket.cf"] || {};

      if (!ticketId) {
        showError("Could not read ticket ID from Zoho.");
        return;
      }

      // Read AI tags (semicolon-separated multi-select)
      var aiTagsRaw = customFields[ParkMConfig.FIELDS.AI_TAGS];
      var aiTags = parseTags(aiTagsRaw);

      if (aiTags.length === 0) {
        showState("no-classification-state");
        startPolling();
        return;
      }

      currentTags = aiTags;

      // Check if agent already overrode the tags
      var correctedTagsRaw = customFields[ParkMConfig.FIELDS.AGENT_CORRECTED_TAGS];
      var correctedTags = parseTags(correctedTagsRaw);
      var activeTags = correctedTags.length > 0 ? correctedTags : aiTags;

      populateCorrectionDropdown();

      // Fetch and render stacked wizards
      loadWizardsForTags(activeTags);
    }).catch(function (err) {
      console.error("Load ticket failed:", err);
      showError("Failed to load ticket: " + (err.message || String(err)));
    }).finally(function () {
      isLoadingTicket = false;
    });
  }

  /* ── Agent Access Check ───────────────────────────────────────────── */

  function _checkAgentAccess(callback) {
    ZOHODESK.get("user.email").then(function (resp) {
      var agentEmail = resp["user.email"] || "";
      console.log("Agent email:", agentEmail);

      if (!agentEmail) {
        // Can't determine agent — allow access (fail open)
        callback(true);
        return;
      }

      var url = ParkMConfig.API_BASE_URL + "/widget/access?email=" + encodeURIComponent(agentEmail);
      fetch(url)
        .then(function (res) { return res.json(); })
        .then(function (data) {
          console.log("Access check:", data.allowed ? "allowed" : "restricted");
          callback(data.allowed);
        })
        .catch(function (err) {
          console.log("Access check failed, allowing access:", err);
          callback(true); // fail open
        });
    }).catch(function (err) {
      console.log("Could not get agent email, allowing access:", err);
      callback(true); // fail open
    });
  }

  /* ── Initialize the app ───────────────────────────────────────────── */

  function init() {
    showState("loading-state");

    TemplatePanel.init();
    ValidationModal.init();

    document.getElementById("retry-btn").addEventListener("click", function () {
      loadTicket();
    });

    if (typeof ZOHODESK === "undefined") {
      showError("Zoho Desk SDK not loaded. Please refresh.");
      return;
    }

    ZOHODESK.extension.onload().then(function (App) {
      console.log("SDK loaded, checking access...");
      resizeWidget();

      // Check agent access before loading anything
      _checkAgentAccess(function (allowed) {
        if (!allowed) {
          document.getElementById("loading-state").style.display = "none";
          document.getElementById("wizard-container").style.display = "none";
          document.getElementById("error-state").style.display = "none";
          document.getElementById("no-classification-state").style.display = "none";
          var body = document.body;
          var notice = document.createElement("div");
          notice.className = "access-restricted";
          notice.innerHTML = '<p style="text-align:center;color:#888;padding:40px 16px;font-size:13px;">' +
            'The CSR Wizard is not yet available for your account.</p>';
          body.appendChild(notice);
          return;
        }

        // Listen for ticket switches
        try {
          ZOHODESK.on("ticket_detail.changed", function () {
            console.log("ticket_detail.changed fired, reloading...");
            loadTicket();
          });
        } catch (e) { console.log("ticket_detail.changed not supported"); }

        try {
          ZOHODESK.on("ticket.id.changed", function () {
            console.log("ticket.id.changed fired, reloading...");
            loadTicket();
          });
        } catch (e) { console.log("ticket.id.changed not supported"); }

        // Fallback: poll for ticket ID changes every 2s
        setInterval(function () {
          ZOHODESK.get("ticket.id").then(function (resp) {
            var newId = resp["ticket.id"];
            if (newId && newId !== ticketId) {
              console.log("Ticket ID changed from", ticketId, "to", newId, "— reloading...");
              loadTicket();
            }
          }).catch(function () {});
        }, 2000);

        loadTicket();
      });
    }).catch(function (err) {
      console.error("Initialization failed:", err);
      showError("Failed to initialize: " + (err.message || String(err)));
    });
  }

  /* ── Public API ───────────────────────────────────────────────────── */

  return {
    init: init,
    onRedirectWizard: onRedirectWizard,
    onValidationConfirmed: onValidationConfirmed,

    getTicketId: function () { return ticketId; },
    getCurrentTags: function () { return currentTags; },
    getCurrentIntent: function () { return currentTags[0] || null; },
    getWizard: function () { return currentWizards[0] || null; },
    getSteps: function () {
      var steps = [];
      currentWizards.forEach(function (w) {
        steps = steps.concat(w.steps || []);
      });
      return steps;
    },

    showValidation: function () {
      if (currentWizards.length > 0) {
        var allSteps = [];
        currentWizards.forEach(function (w) {
          allSteps = allSteps.concat(w.steps || []);
        });
        ValidationModal.show(currentWizards[0], allSteps);
      }
    }
  };
})();

// Boot the app when the page fully loads
window.onload = function () {
  ParkMApp.init();
};
