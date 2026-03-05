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
        return data.wizard;
      });
  }

  /* ── Fetch and render all wizards (stacked) ────────────────────────── */

  function loadWizardsForTags(tags) {
    showState("loading-state");

    var promises = tags.map(function (tag) {
      return fetchWizard(tag, ticketId);
    });

    Promise.all(promises)
      .then(function (wizards) {
        currentWizards = wizards;
        renderStackedWizards(tags, wizards);
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

  /* ── Resize widget to fit content ──────────────────────────────────── */

  function resizeWidget() {
    try {
      if (typeof ZOHODESK !== "undefined") {
        var height = document.body.scrollHeight;
        ZOHODESK.invoke("RESIZE", { height: height + "px", width: "100%" });
      }
    } catch (e) { /* resize not supported in this context */ }
  }

  // Keep widget height dynamic as content changes (checkboxes, expand/collapse)
  if (typeof ResizeObserver !== "undefined") {
    var ro = new ResizeObserver(function () { resizeWidget(); });
    ro.observe(document.body);
  }

  /* ── Redirect wizard (called by decision points) ──────────────────── */

  function onRedirectWizard(newTag) {
    loadWizardsForTags([newTag]);
  }

  /* ── Validation confirmed callback ────────────────────────────────── */

  function onValidationConfirmed() {
    console.log("Validation confirmed — ticket can be closed.");
  }

  /* ── Initialize the app ───────────────────────────────────────────── */

  function init() {
    showState("loading-state");

    TemplatePanel.init();
    ValidationModal.init();

    document.getElementById("retry-btn").addEventListener("click", function () {
      init();
    });

    if (typeof ZOHODESK === "undefined") {
      showError("Zoho Desk SDK not loaded. Please refresh.");
      return;
    }

    ZOHODESK.extension.onload().then(function (App) {
      console.log("SDK loaded, fetching ticket data...");
      return Promise.all([
        ZOHODESK.get("ticket.id"),
        ZOHODESK.get("ticket.cf")
      ]);
    }).then(function (results) {
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
