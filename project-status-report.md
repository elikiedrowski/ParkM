## ParkM Zoho Desk — Project Status Report
**Date:** March 27, 2026

---

### Phase 1: AI Classification & Auto-Tagging — **COMPLETE (Sandbox)**

**What was built:**
- GPT-4o-mini classifier that reads incoming ticket subject/description and assigns 1+ tags from a taxonomy of 51 values (49 real tags + "Needs Tag" + extras)
- Multi-intent support — tickets can receive multiple tags (e.g., "Refund Request" + "Cancel Permit")
- 9 custom fields auto-populated on ticket creation via Zoho webhook
- Correction logging for future model improvement
- 62 synthetic test tickets created in sandbox for validation

**Production readiness:**
- **9 AI custom fields need to be added to production Zoho** (must be done manually via Zoho UI — cannot be created via API)
- Webhook URL needs to be configured in production Zoho to point to Railway endpoint
- Railway backend is deployed and running

**Owner for go-live:** Eli (webhook config) + Sadie's team (testing/validation)

---

### Phase 2: CSR Wizard Widget — **COMPLETE (Sandbox), V3 Content In Progress**

**What was built:**
- Zoho Desk right-panel widget that displays step-by-step guidance based on ticket tags
- Multi-tag support — shows stacked wizard panels when ticket has multiple tags
- Auto-refresh polling — widget updates when AI tags or agent-corrected tags change
- Full wizard definitions for all 51 tags (sourced from Sadie's "HOW TO DO EVERYTHING PARKM" doc)
- V3 redesign implemented — switched from numbered checklists to grouped suggestions with conditional branching (per Sadie's feedback)

**Outstanding — Wizard V3 content:**
- Sadie is rewriting wizard content in a new "suggestions" format via Google Doc
- **22 of ~51 tags complete** (all customer-related tags done; property, sales rep, other categories still in progress)
- Once Sadie completes the doc, Eli will import the updated content

**Outstanding — Response templates:**
- Templates built but Sadie requested removal (Mar 26) — accuracy concern with evolving wizard steps
- Sadie to discuss with Katie whether templates are permanently removed or revisited later
- Template files kept in codebase pending final decision

**Owner:** Sadie (V3 content writing + template decision with Katie) → Eli (import + widget update)

---

### Phase 3: Refund Automation — **COMPLETE (Sandbox)**

**What was built:**
- ParkM App API integration (customer lookup, permit retrieval, payment history)
- Refund eligibility engine with business rules:
  - Last charge must be within 30 days
  - Guest permits automatically denied (CSR can override manually)
  - Move-out date check removed (per Sadie, Mar 26)
- Active permits displayed with cancel capability
- **Inactive permits section** — shows cancelled/expired permits with charges in last 30 days (new requirement from Mar 26)
- Auto-lookup customer when contact email is available on ticket
- Auto-populate accounting email in reply-to field
- Permit cards show permit name, license plate, community, status

**Owner:** Stephen/Chad (production API credentials) → Eli (configuration) → Sadie's team (testing)

---

### Hours Summary

| Project Task | SOW Hours | Billable Hours |
|---|---|---|
| 1 - AI Email Classification & Auto Tagging | 35.00 | 31.00 |
| 2 - In-Workflow Guidance System | 30.00 | 28.00 |
| 3 - Refund Automation + ParkM.app API | 50.00 | 43.00 |
| 4 - Unified Agent Desktop | 55.00 | 0.00 |
| 5 - Progressive Automation | 35.00 | 0.00 |

---

**Phase 4 (Future):** Full integrated parkm.app desktop wizard — expanding account lookup from refunds-only to all wizard steps.
