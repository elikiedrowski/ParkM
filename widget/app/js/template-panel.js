/**
 * ParkM CSR Wizard — Template Panel
 * Renders template buttons, preview modal, and insert into reply.
 */
var TemplatePanel = (function () {
  var currentTemplateHtml = "";
  var currentTemplateFile = "";

  /* ── Render template pill buttons ─────────────────────────────────── */

  function renderButtons(quickTemplates) {
    var container = document.getElementById("template-buttons");
    container.innerHTML = "";

    if (!quickTemplates || quickTemplates.length === 0) {
      document.getElementById("templates-panel").style.display = "none";
      return;
    }

    document.getElementById("templates-panel").style.display = "block";

    quickTemplates.forEach(function (tmpl) {
      var btn = document.createElement("button");
      btn.className = "template-btn";
      btn.textContent = tmpl.label;
      btn.addEventListener("click", function () {
        loadAndPreview(tmpl.file);
      });
      container.appendChild(btn);
    });
  }

  /* ── Load template from API and show preview modal ────────────────── */

  function loadAndPreview(filename) {
    currentTemplateFile = filename;
    currentTemplateHtml = "";

    var modal = document.getElementById("template-modal");
    var title = document.getElementById("template-modal-title");
    var body = document.getElementById("template-modal-body");

    title.textContent = filename.replace(/_/g, " ").replace(".html", "");
    body.innerHTML = "<div class='state-panel'><div class='spinner'></div><p>Loading template...</p></div>";
    modal.style.display = "flex";

    var url = ParkMConfig.API_BASE_URL + "/templates/" + encodeURIComponent(filename);

    fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error("Template not found (" + res.status + ")");
        return res.json();
      })
      .then(function (data) {
        currentTemplateHtml = data.html || "";
        body.innerHTML = "<div class='template-preview'>" + currentTemplateHtml + "</div>";
      })
      .catch(function (err) {
        body.innerHTML = "<div class='state-panel'><div class='state-icon state-icon--error'>!</div><p>" +
          err.message + "</p></div>";
      });
  }

  /* ── Insert template into Zoho reply editor ───────────────────────── */

  function insertIntoReply() {
    if (!currentTemplateHtml) return;

    try {
      ZOHODESK.invoke("INSERT", "ticket.replyEditor", { value: currentTemplateHtml });
    } catch (e) {
      // Fallback: copy to clipboard
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(currentTemplateHtml);
        alert("Template copied to clipboard (unable to insert directly).");
      } else {
        alert("Unable to insert template. Please copy it manually from the preview.");
      }
    }

    closeModal();
  }

  /* ── Modal controls ───────────────────────────────────────────────── */

  function closeModal() {
    document.getElementById("template-modal").style.display = "none";
    currentTemplateHtml = "";
    currentTemplateFile = "";
  }

  /* ── Init event listeners ─────────────────────────────────────────── */

  function init() {
    document.getElementById("template-modal-close").addEventListener("click", closeModal);
    document.getElementById("template-cancel-btn").addEventListener("click", closeModal);
    document.getElementById("template-insert-btn").addEventListener("click", insertIntoReply);

    // Close modal on overlay click
    document.getElementById("template-modal").addEventListener("click", function (e) {
      if (e.target === this) closeModal();
    });
  }

  /* ── Public API ───────────────────────────────────────────────────── */

  return {
    init: init,
    renderButtons: renderButtons,
    loadAndPreview: loadAndPreview,
    insertIntoReply: insertIntoReply,
    closeModal: closeModal
  };
})();
