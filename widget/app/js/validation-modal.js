/**
 * ParkM CSR Wizard — Validation Modal
 * Pre-close checklist shown when agent attempts to close a ticket.
 */
var ValidationModal = (function () {
  var validationChecks = {};
  var wizardSteps = [];

  /* ── Show the validation modal ────────────────────────────────────── */

  function show(wizard, steps) {
    wizardSteps = steps || wizard.steps || [];
    validationChecks = {};

    var modal = document.getElementById("validation-modal");
    var checklist = document.getElementById("validation-checklist");
    var warning = document.getElementById("incomplete-steps-warning");
    var confirmBtn = document.getElementById("validation-confirm-btn");

    checklist.innerHTML = "";

    // Check if all required steps are done
    var allRequiredDone = typeof WizardRenderer !== "undefined" &&
      WizardRenderer.allRequiredComplete(wizardSteps);

    warning.style.display = allRequiredDone ? "none" : "block";

    // Render validation_on_close items as checkboxes
    var questions = wizard.validation_on_close || [];
    questions.forEach(function (question, idx) {
      var item = document.createElement("div");
      item.className = "validation-item";

      var checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = "validation-" + idx;
      checkbox.addEventListener("change", function () {
        validationChecks[idx] = this.checked;
        updateConfirmButton(questions.length);
      });

      var label = document.createElement("label");
      label.htmlFor = "validation-" + idx;
      label.textContent = question;

      item.appendChild(checkbox);
      item.appendChild(label);
      checklist.appendChild(item);
    });

    // Disable confirm button initially
    confirmBtn.disabled = true;
    modal.style.display = "flex";
  }

  /* ── Update confirm button state ──────────────────────────────────── */

  function updateConfirmButton(totalQuestions) {
    var allChecked = true;
    for (var i = 0; i < totalQuestions; i++) {
      if (!validationChecks[i]) {
        allChecked = false;
        break;
      }
    }
    document.getElementById("validation-confirm-btn").disabled = !allChecked;
  }

  /* ── Close modal ──────────────────────────────────────────────────── */

  function close() {
    document.getElementById("validation-modal").style.display = "none";
    validationChecks = {};
  }

  /* ── Confirm and close ────────────────────────────────────────────── */

  function confirm() {
    close();
    // The modal is advisory — Zoho SDK cannot block status changes.
    // Optionally notify the app that validation passed.
    if (typeof ParkMApp !== "undefined" && ParkMApp.onValidationConfirmed) {
      ParkMApp.onValidationConfirmed();
    }
  }

  /* ── Init event listeners ─────────────────────────────────────────── */

  function init() {
    document.getElementById("validation-modal-close").addEventListener("click", close);
    document.getElementById("validation-back-btn").addEventListener("click", close);
    document.getElementById("validation-confirm-btn").addEventListener("click", confirm);

    // Close on overlay click
    document.getElementById("validation-modal").addEventListener("click", function (e) {
      if (e.target === this) close();
    });
  }

  /* ── Public API ───────────────────────────────────────────────────── */

  return {
    init: init,
    show: show,
    close: close
  };
})();
