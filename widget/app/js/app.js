/**
 * ParkM CSR Wizard — Main App Orchestrator
 * Initializes Zoho Desk SDK, loads ticket data, fetches wizard content,
 * and wires up the correction dropdown and event listeners.
 */
var ParkMApp = (function () {
  var currentWizard = null;
  var currentIntent = null;
  var ticketId = null;
  var customFields = {};

  /* ── Show / hide state panels ─────────────────────────────────────── */

  function showState(stateId) {
    var states = ["loading-state", "error-state", "no-classification-state", "wizard-container"];
    states.forEach(function (id) {
      document.getElementById(id).style.display = (id === stateId) ? "" : "none";
    });
    // The wizard-container and state panels use different default displays
    if (stateId === "wizard-container") {
      document.getElementById("wizard-container").style.display = "block";
    }
  }

  function showError(msg) {
    document.getElementById("error-message").textContent = msg || "Unable to load wizard data.";
    showState("error-state");
  }

  /* ── Fetch wizard content from Railway API ────────────────────────── */

  function fetchWizard(intent, tktId) {
    var url = ParkMConfig.API_BASE_URL + "/wizard/" + encodeURIComponent(intent);
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

  /* ── Render the full wizard ───────────────────────────────────────── */

  function renderWizard(wizard) {
    currentWizard = wizard;
    WizardRenderer.renderHeader(wizard, customFields);
    WizardRenderer.renderEntities(wizard);
    WizardRenderer.renderSteps(wizard.steps);
    TemplatePanel.renderButtons(wizard.quick_templates);
    showState("wizard-container");
  }

  /* ── Populate the correction dropdown ─────────────────────────────── */

  function populateCorrectionDropdown(currentIntentValue) {
    var select = document.getElementById("corrected-intent-select");

    // Clear existing options (keep the first "AI is correct" option)
    while (select.options.length > 1) {
      select.remove(1);
    }

    ParkMConfig.INTENTS.forEach(function (intent) {
      if (intent === currentIntentValue) return; // skip current — it's the default
      var opt = document.createElement("option");
      opt.value = intent;
      opt.textContent = ParkMConfig.INTENT_LABELS[intent] || intent;
      select.appendChild(opt);
    });

    // Set to current corrected value if one exists
    var correctedValue = customFields[ParkMConfig.FIELDS.AGENT_CORRECTED] || "";
    if (correctedValue && correctedValue !== currentIntentValue) {
      select.value = correctedValue;
    }

    // Listen for changes
    select.addEventListener("change", onCorrectionChange);
  }

  /* ── Handle correction dropdown change ────────────────────────────── */

  function onCorrectionChange() {
    var select = document.getElementById("corrected-intent-select");
    var newIntent = select.value;

    if (!newIntent) {
      // Reset to original AI classification
      if (currentIntent) {
        loadWizardForIntent(currentIntent);
      }
      return;
    }

    // Update custom field in Zoho
    try {
      ZOHODESK.set("ticket.cf." + ParkMConfig.FIELDS.AGENT_CORRECTED, { value: newIntent });
    } catch (e) {
      console.warn("Could not set corrected intent field:", e);
    }

    // Reload wizard for new intent
    loadWizardForIntent(newIntent);
  }

  /* ── Load wizard for a specific intent ────────────────────────────── */

  function loadWizardForIntent(intent) {
    showState("loading-state");

    fetchWizard(intent, ticketId)
      .then(function (wizard) {
        renderWizard(wizard);
      })
      .catch(function (err) {
        console.error("Failed to load wizard:", err);
        showError("Failed to load wizard for " + intent);
      });
  }

  /* ── Redirect wizard (called by decision points) ──────────────────── */

  function onRedirectWizard(newIntent) {
    // Update correction dropdown
    var select = document.getElementById("corrected-intent-select");
    select.value = newIntent;
    loadWizardForIntent(newIntent);
  }

  /* ── Validation confirmed callback ────────────────────────────────── */

  function onValidationConfirmed() {
    console.log("Validation confirmed — ticket can be closed.");
  }

  /* ── Initialize the app ───────────────────────────────────────────── */

  function init() {
    showState("loading-state");

    // Init sub-modules
    TemplatePanel.init();
    ValidationModal.init();

    // Retry button
    document.getElementById("retry-btn").addEventListener("click", function () {
      init();
    });

    // Check SDK is available
    if (typeof ZOHODESK === "undefined") {
      showError("Zoho Desk SDK not loaded. Please refresh.");
      return;
    }

    // Initialize Zoho Desk SDK
    ZOHODESK.extension.onload().then(function (App) {
      console.log("SDK loaded, fetching ticket data...");
      // Get ticket ID and custom fields in parallel
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

      // Read AI intent from custom fields
      var aiIntent = customFields[ParkMConfig.FIELDS.AI_INTENT];

      if (!aiIntent) {
        showState("no-classification-state");
        return;
      }

      currentIntent = aiIntent;

      // Populate correction dropdown
      populateCorrectionDropdown(aiIntent);

      // Check if agent already overrode the intent
      var correctedIntent = customFields[ParkMConfig.FIELDS.AGENT_CORRECTED];
      var activeIntent = correctedIntent || aiIntent;

      // Fetch and render wizard
      return fetchWizard(activeIntent, ticketId).then(function (wizard) {
        renderWizard(wizard);
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

    /** Access current state (for template tracking and validation) */
    getTicketId: function () { return ticketId; },
    getCurrentIntent: function () { return currentIntent; },
    getWizard: function () { return currentWizard; },
    getSteps: function () { return currentWizard ? currentWizard.steps : []; },

    /** Show validation modal (called externally or by status change) */
    showValidation: function () {
      if (currentWizard) {
        ValidationModal.show(currentWizard, currentWizard.steps);
      }
    }
  };
})();

// Boot the app when the page fully loads (Zoho SDK requires window.onload)
window.onload = function () {
  ParkMApp.init();
};
