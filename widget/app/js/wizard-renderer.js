/**
 * ParkM CSR Wizard — Wizard Renderer
 * Renders header, entities, step checklist, and decision points.
 */
var WizardRenderer = (function () {
  // Track checked steps and decision selections
  var checkedSteps = {};
  var decisionSelections = {};

  /* ── Header Panel ─────────────────────────────────────────────────── */

  function renderHeader(wizard, customFields) {
    var intent = wizard.ai_intent || customFields[ParkMConfig.FIELDS.AI_INTENT] || "unclear";
    var confidence = wizard.ai_confidence || customFields[ParkMConfig.FIELDS.AI_CONFIDENCE] || 0;
    var urgency = customFields[ParkMConfig.FIELDS.AI_URGENCY] || "medium";
    var complexity = customFields[ParkMConfig.FIELDS.AI_COMPLEXITY] || "moderate";
    var needsReview = wizard.requires_human_review ||
      customFields[ParkMConfig.FIELDS.REQUIRES_HUMAN_REVIEW] === "true";

    // Icon + label
    var iconEl = document.getElementById("intent-icon");
    var labelEl = document.getElementById("intent-label");
    iconEl.textContent = wizard.icon || "";
    labelEl.textContent = wizard.label || ParkMConfig.INTENT_LABELS[intent] || intent;

    // Confidence badge
    var confBadge = document.getElementById("confidence-badge");
    var confPct = Math.round(parseFloat(confidence) * 100);
    confBadge.textContent = confPct + "% conf.";
    if (confPct >= 85) {
      confBadge.style.background = "#e8f5e9";
      confBadge.style.color = "#27ae60";
    } else if (confPct >= 65) {
      confBadge.style.background = "#fff3e0";
      confBadge.style.color = "#e67e22";
    } else {
      confBadge.style.background = "#fdecea";
      confBadge.style.color = "#c0392b";
    }

    // Urgency badge
    var urgBadge = document.getElementById("urgency-badge");
    var urgStyle = ParkMConfig.URGENCY_STYLES[urgency] || ParkMConfig.URGENCY_STYLES.medium;
    urgBadge.textContent = urgStyle.label;
    urgBadge.style.background = urgStyle.bg;
    urgBadge.style.color = urgStyle.text;

    // Complexity badge
    var cmpBadge = document.getElementById("complexity-badge");
    var cmpStyle = ParkMConfig.COMPLEXITY_STYLES[complexity] || ParkMConfig.COMPLEXITY_STYLES.moderate;
    cmpBadge.textContent = complexity.charAt(0).toUpperCase() + complexity.slice(1);
    cmpBadge.style.background = cmpStyle.bg;
    cmpBadge.style.color = cmpStyle.text;

    // Human review banner
    var banner = document.getElementById("human-review-banner");
    banner.style.display = needsReview ? "block" : "none";

    // Intro text
    var introEl = document.getElementById("wizard-intro");
    introEl.textContent = wizard.intro || "";
  }

  /* ── Entity Panel ─────────────────────────────────────────────────── */

  function renderEntities(wizard) {
    var entities = wizard.extracted_entities || {};
    var panel = document.getElementById("entity-panel");
    var list = document.getElementById("entity-list");
    list.innerHTML = "";

    // Collect entity info from steps that have entity_field
    var entitySteps = (wizard.steps || []).filter(function (s) { return s.entity_field; });

    if (entitySteps.length === 0 && Object.keys(entities).length === 0) {
      panel.style.display = "none";
      return;
    }

    panel.style.display = "block";

    // Show extracted entities from steps
    entitySteps.forEach(function (step) {
      var card = document.createElement("div");
      card.className = "entity-card";

      var labelSpan = document.createElement("span");
      labelSpan.className = "entity-label";
      labelSpan.textContent = step.entity_field.replace(/_/g, " ");

      var rightDiv = document.createElement("div");

      if (step.entity_found && step.entity_value) {
        var valueSpan = document.createElement("span");
        valueSpan.className = "entity-value";
        valueSpan.textContent = step.entity_value;
        rightDiv.appendChild(valueSpan);
      } else {
        var missingSpan = document.createElement("span");
        missingSpan.className = "entity-value entity-value--missing";
        missingSpan.textContent = "Not found";
        rightDiv.appendChild(missingSpan);

        if (step.missing_action) {
          var btn = document.createElement("button");
          btn.className = "entity-action-btn";
          btn.textContent = step.missing_action.label || "Request";
          btn.setAttribute("data-template", step.missing_action.template);
          btn.addEventListener("click", function () {
            if (typeof TemplatePanel !== "undefined") {
              TemplatePanel.loadAndPreview(step.missing_action.template);
            }
          });
          rightDiv.appendChild(btn);
        }
      }

      card.appendChild(labelSpan);
      card.appendChild(rightDiv);
      list.appendChild(card);
    });
  }

  /* ── Step Checklist ───────────────────────────────────────────────── */

  function renderSteps(steps) {
    var container = document.getElementById("steps-list");
    container.innerHTML = "";
    checkedSteps = {};
    decisionSelections = {};

    (steps || []).forEach(function (step) {
      var row = document.createElement("div");
      row.className = "step-row";

      if (step.decision_point) {
        renderDecisionStep(row, step);
      } else {
        renderCheckboxStep(row, step);
      }

      container.appendChild(row);
    });
  }

  function renderCheckboxStep(row, step) {
    var main = document.createElement("div");
    main.className = "step-main";

    var checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = "step-" + step.id;
    checkbox.addEventListener("change", function () {
      checkedSteps[step.id] = this.checked;
      textSpan.className = this.checked ? "step-text checked" : "step-text";
    });

    var textSpan = document.createElement("span");
    textSpan.className = "step-text";
    textSpan.textContent = step.text;

    main.appendChild(checkbox);
    main.appendChild(textSpan);

    if (step.required) {
      var req = document.createElement("span");
      req.className = "step-required";
      req.textContent = "REQ";
      main.appendChild(req);
    }

    main.addEventListener("click", function (e) {
      if (e.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event("change"));
      }
    });

    row.appendChild(main);

    // Entity missing warning
    if (step.entity_field && !step.entity_found) {
      var warning = document.createElement("div");
      warning.className = "step-entity-warning";
      warning.innerHTML = "&#9888; " + step.entity_field.replace(/_/g, " ") + " not found in email";
      row.appendChild(warning);
    }

    // Substep
    if (step.substep) {
      var substepDiv = document.createElement("div");
      substepDiv.className = "step-substep";
      substepDiv.textContent = step.substep;
      substepDiv.id = "substep-" + step.id;

      var toggle = document.createElement("span");
      toggle.className = "step-toggle";
      toggle.textContent = "Show details";
      toggle.addEventListener("click", function () {
        var expanded = substepDiv.classList.toggle("expanded");
        toggle.textContent = expanded ? "Hide details" : "Show details";
      });

      row.appendChild(toggle);
      row.appendChild(substepDiv);
    }
  }

  function renderDecisionStep(row, step) {
    // Decision point header (no checkbox)
    var main = document.createElement("div");
    main.className = "step-main";
    main.style.cursor = "default";

    var textSpan = document.createElement("span");
    textSpan.className = "step-text";
    textSpan.style.marginLeft = "24px"; // align with checkbox steps
    textSpan.textContent = step.text;

    main.appendChild(textSpan);

    if (step.required) {
      var req = document.createElement("span");
      req.className = "step-required";
      req.textContent = "REQ";
      main.appendChild(req);
    }

    row.appendChild(main);

    // Substep text (if any)
    if (step.substep) {
      var substepDiv = document.createElement("div");
      substepDiv.className = "step-substep expanded";
      substepDiv.textContent = step.substep;
      row.appendChild(substepDiv);
    }

    // Decision buttons
    var btnGroup = document.createElement("div");
    btnGroup.className = "decision-buttons";

    (step.options || []).forEach(function (option) {
      var btn = document.createElement("button");
      btn.className = "decision-btn";
      btn.textContent = option.label;
      btn.setAttribute("data-action", option.action || "");

      btn.addEventListener("click", function () {
        // Mark this step as completed with the selected decision
        decisionSelections[step.id] = option.action;
        checkedSteps[step.id] = true;

        // Update button states
        var siblings = btnGroup.querySelectorAll(".decision-btn");
        for (var i = 0; i < siblings.length; i++) {
          siblings[i].classList.remove("selected");
          siblings[i].classList.add("dimmed");
        }
        btn.classList.add("selected");
        btn.classList.remove("dimmed");

        // If option has a next_template, preview it
        if (option.next_template && typeof TemplatePanel !== "undefined") {
          TemplatePanel.loadAndPreview(option.next_template);
        }

        // If option has redirect_wizard, notify the app
        if (option.redirect_wizard && typeof ParkMApp !== "undefined" && ParkMApp.onRedirectWizard) {
          ParkMApp.onRedirectWizard(option.redirect_wizard);
        }
      });

      btnGroup.appendChild(btn);
    });

    row.appendChild(btnGroup);
  }

  /* ── Public API ───────────────────────────────────────────────────── */

  return {
    renderHeader: renderHeader,
    renderEntities: renderEntities,
    renderSteps: renderSteps,

    /** Get map of step id → checked boolean */
    getCheckedSteps: function () {
      return Object.assign({}, checkedSteps);
    },

    /** Get map of step id → selected action for decision points */
    getDecisionSelections: function () {
      return Object.assign({}, decisionSelections);
    },

    /** Check if all required steps are completed */
    allRequiredComplete: function (steps) {
      return (steps || []).every(function (step) {
        if (!step.required) return true;
        return !!checkedSteps[step.id];
      });
    }
  };
})();
