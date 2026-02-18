# Priority 2: In-Workflow Guidance System - Implementation Progress

**Started:** February 17, 2026
**Target Completion:** Week 3-5 (overlapping with Priority 1 deployment)
**Current Status:** 🟡 Phase 2.1 In Progress — Backend Foundation Complete

**Last Updated:** February 17, 2026

---

## Summary

Priority 2 builds the CSR wizard — a guided workflow that appears when a CSR opens a classified ticket and walks them step-by-step through the correct resolution process. The backend data layer is complete. Next: Nagy builds the Zoho Widget SDK frontend.

| Component | Status | Owner | Notes |
|-----------|--------|-------|-------|
| Response template library (HTML) | ✅ Complete | Eli | 10 templates in src/templates/ |
| Wizard content definitions (JSON) | ✅ Complete | Eli | All 9 intents in src/wizard/ |
| Wizard service + API endpoints | ✅ Complete | Eli | 4 new endpoints in main.py |
| Zoho Widget SDK extension | ⏳ Pending | Nagy | Frontend widget development |
| Template review with Katie | ⏳ Pending | Eli + Katie | Schedule after Feb 19 call |
| Phase 2.3 Validation prompts | ⏳ Pending | Eli | After widget built |
| Phase 2.4 CSR beta testing | ⏳ Pending | Eli + Katie | After widget deployed |

---

## Phase 2.1: UI/UX Design (COMPLETE — Backend)

### Wizard Content Designed for All 9 Intents

Each intent has a full wizard definition in [src/wizard/wizard_content.json](src/wizard/wizard_content.json):

| Intent | Label | Steps |
|--------|-------|-------|
| `refund_request` | Refund Request | 10 steps + 3 validation checks |
| `permit_cancellation` | Permit Cancellation (No Refund) | 6 steps |
| `account_update` | Account / Vehicle Update | 7 steps |
| `payment_issue` | Payment Issue | 6 steps |
| `permit_inquiry` | Permit Inquiry | 5 steps |
| `move_out` | Move-Out Notification | 4 steps + redirect logic |
| `technical_issue` | Technical Issue | 6 steps |
| `general_question` | General Question | 4 steps |
| `unclear` | Unclear / Needs Review | 5 steps + AI correction |

**Features per wizard:**
- Step-by-step checklist with substep guidance
- Entity placeholders auto-filled from AI extraction (license plate, move-out date, amount)
- Decision points with branching options
- "Missing info" actions that pre-select the right template
- Validation questions shown before ticket can be closed
- Quick-access template buttons

---

## Phase 2.1: Response Template Library (COMPLETE)

All templates in [src/templates/](src/templates/):

| Template File | Use Case |
|---------------|----------|
| `missing_license_plate.html` | Customer didn't provide plate number |
| `missing_move_out_date.html` | Refund request missing move-out date |
| `missing_bank_statement.html` | Refund needs statement for verification |
| `refund_approved.html` | Refund approved, submitted to accounting |
| `refund_denied_outside_window.html` | Outside 30-day window |
| `refund_denied_tos.html` | Denied per Terms of Service |
| `cancellation_confirmed.html` | Permit canceled, no refund |
| `cancellation_with_refund_pending.html` | Permit canceled + refund submitted |
| `vehicle_update_confirmed.html` | License plate / vehicle updated |
| `account_update_confirmed.html` | Account info updated |
| `payment_issue_follow_up.html` | Payment investigation follow-up |
| `general_inquiry_response.html` | General purpose (CSR customizes) |

**Template variables** use `{{variable_name}}` syntax. Common variables:
- `{{customer_name}}` — customer's first name
- `{{license_plate}}` — AI-extracted or manually entered
- `{{move_out_date}}` — AI-extracted date
- `{{amount}}` — refund amount
- `{{processing_time}}` — default: "5-7 business days"
- `{{update_description}}` — what was changed (account update template)

> **Action:** Review all templates with Katie (Thu Feb 19 or following week) to ensure correct tone, legal language (T&C link), and refund timeline (confirm 5-7 days with accounting).

---

## Phase 2.1: Backend API Endpoints (COMPLETE)

New endpoints added to [main.py](main.py):

| Endpoint | Description |
|----------|-------------|
| `GET /wizard/{intent}` | Return wizard steps for a given intent. Optional `?ticket_id=` to auto-fill entities |
| `GET /wizard-intents` | List all 9 supported intents |
| `GET /templates` | List all available template filenames |
| `GET /templates/{filename}` | Return raw HTML of a specific template |

**Example calls:**
```bash
# Get wizard steps for a refund request
curl https://<railway-url>/wizard/refund_request

# Get wizard with entities filled from a real ticket
curl "https://<railway-url>/wizard/refund_request?ticket_id=12345"

# Get template HTML
curl https://<railway-url>/templates/refund_approved.html
```

**New service file:** [src/services/wizard.py](src/services/wizard.py)
- `get_wizard_for_intent(intent, classification)` — loads wizard + fills placeholders
- `get_template_html(filename)` — returns raw template HTML
- `list_templates()` — lists available templates
- `list_intents()` — lists supported intents

---

## Phase 2.2: Zoho Widget SDK Extension (PENDING — Nagy)

**Owner:** Nagy
**Technology:** Zoho Desk Widget SDK (JavaScript/HTML/CSS)
**Decision:** Option 1 (Widget SDK) — embedded in ticket sidebar, accesses Zoho APIs

### Nagy's Setup Tasks
- [ ] Install Zoho CLI: `npm install -g @zoho/cli`
- [ ] Create widget project: `zet init` → Desk Extension
- [ ] Set up local dev environment with hot reload
- [ ] Configure widget to load when a ticket opens

### Widget Components to Build
- [ ] **Header panel** — shows intent label, confidence %, urgency indicator
- [ ] **Checklist** — interactive checkboxes for each step, substep expandable
- [ ] **Entity panel** — displays AI-extracted license plate, move-out date, amount
- [ ] **Template buttons** — click to load template into reply box
- [ ] **Decision point UI** — branching buttons when wizard hits a choice
- [ ] **Validation modal** — pre-close checklist confirmation
- [ ] **Agent Corrected Intent** — quick dropdown to correct the AI's classification

### Widget Data Flow
```
CSR opens ticket in Zoho Desk
  → Widget loads (Zoho Widget SDK)
  → Widget reads cf_ai_intent from ticket custom fields
  → Widget calls GET /wizard/{intent} on Railway API
  → API returns steps with entity placeholders filled
  → Widget renders checklist
  → CSR works through steps, clicks templates
  → On "Close Ticket": validation modal appears
  → CSR confirms all steps → ticket closes
```

### API Integration Points
```javascript
// Read AI classification from Zoho ticket
ZOHO.DESK.get("ticket").then(ticket => {
  const intent = ticket.cf.cf_ai_intent;
  const confidence = ticket.cf.cf_ai_confidence;
  const licensePlate = ticket.cf.cf_license_plate;
  const moveOutDate = ticket.cf.cf_move_out_date;

  // Call Railway API for wizard steps
  fetch(`${RAILWAY_API}/wizard/${intent}`)
    .then(r => r.json())
    .then(data => renderWizard(data.wizard));
});
```

---

## Phase 2.3: Validation & Real-Time Prompts (PLANNED)

- [ ] Add validation modal that appears when CSR tries to close a ticket
- [ ] Show intent-specific confirmation checklist (from `validation_on_close` in wizard JSON)
- [ ] Add auto status update when refund is submitted ("Waiting on Accounting")
- [ ] Add inline help tooltips (30-day window calculation, permit cancellation steps)

---

## Phase 2.4: CSR Beta Testing (PLANNED)

- [ ] Select 2-3 experienced beta tester CSRs (Katie to nominate)
- [ ] 1-week beta test with real tickets
- [ ] Feedback session — adjust wizard content as needed
- [ ] Full team training + quick reference guide

---

## Pending Reviews with Katie (Thu Feb 19 or after)

1. **Template language** — Review all 12 templates for tone and accuracy
2. **T&C link** — Confirm correct URL for `refund_denied_tos.html`
3. **Refund processing time** — Confirm "5-7 business days" with accounting
4. **Wizard step accuracy** — Do the parkm.app steps match current process?
5. **Escalation path** — Who gets escalated tickets? (supervisor name/queue)
6. **Agent Corrected Intent values** — Confirm the 10 dropdown options are correct

---

## File Structure (Priority 2)

```
src/
  templates/               ← HTML response templates (12 files)
  wizard/
    wizard_content.json    ← Step definitions for all 9 intent types
  services/
    wizard.py              ← Wizard service (loads JSON, fills placeholders)
```

---

*Last Updated: February 17, 2026 — Backend foundation complete, waiting for Nagy to build Zoho Widget*
