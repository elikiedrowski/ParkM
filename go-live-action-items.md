# CSR Wizard — Go-Live Action Items

**Prepared for:** Katie Schaeffer, Sadie Hardy
**Prepared by:** Eli Kiedrowski, Nagy Elshal
**Date:** April 21, 2026

---

## Overview

All three priorities (AI Classification, CSR Wizard, Refund Automation) are complete and tested in sandbox. This document lists the work remaining to cut over to production and begin a controlled pilot with 2–3 CSRs, with expansion to the full team after a 2-week validation period.

| Phase | Target |
| --- | --- |
| Pre-flight (environment + Zoho setup) | 1 week before go-live |
| Training + comms | 2–3 days before go-live |
| Go-live (pilot, 2–3 CSRs) | Day 0 |
| Pilot monitoring | Days 1–14 |
| Full-team rollout | Day 15+ (contingent on pilot metrics) |

---

## 1. Zoho Production Setup

| Item | Owner | Notes |
| --- | --- | --- |
| Install CSR Wizard widget on production org (854251057) | Eli | Upload latest `parkm-widget.zip`; re-install after any update |
| Verify `cf_ai_tags` and `cf_agent_corrected_tags` are on Ticket layout | Nagy | Already created; confirm visibility in ticket detail view |
| Configure per-agent widget visibility for pilot CSRs only | Eli | Uses existing agent access control |
| Register production webhook URL → Railway | Eli | `https://parkm-production.up.railway.app/webhooks/zoho` |
| Validate production OAuth refresh token + required scopes | Eli | `Desk.tickets.ALL`, `Desk.contacts.READ`, `Desk.search.READ` |

---

## 2. Railway Environment Configuration

| Item | Owner | Notes |
| --- | --- | --- |
| Swap `ZOHO_ORG_ID` to 854251057 (production) | Eli | |
| Rotate `ZOHO_REFRESH_TOKEN` to production credential | Eli | Remove `.production_refresh_token` from repo |
| Point `PARKM_API_BASE` to `https://api.parkm.app` | Eli | |
| Rotate ParkM API user/password to production credentials | Stephen / Eli | |
| Confirm `OPENAI_API_KEY` has sufficient budget / no rate-limit risk | Eli | |
| Audit repo for hardcoded sandbox references | Eli | Grep for `856336669`, `app-api-dev-parkm` |
| Confirm Railway Pro plan ($20/mo) and set **usage alert at $18** | Nagy | Expected all-in: $40–70/mo (Railway + OpenAI) |
| Enable automated Postgres backups | Eli | |

---

## 3. Tagging Field Migration

Decision pending — see [tagging-field-migration-options.md](tagging-field-migration-options.md). Katie & Sadie to confirm:
- Target field (AI Tag vs Agent Corrected Tag vs new historical field)
- Scope (open only / 30 / 90 / 365 days / all-time)
- Whether to hide/delete the old Tagging field post-cutover

---

## 4. Pilot Group

| Item | Owner | Notes |
| --- | --- | --- |
| Confirm pilot CSR list (3 max) | Sadie | Proposed: Sadie, Mackenzie, Delaney |
| Grant widget access to pilot CSRs in Zoho | Eli | Per-agent visibility already supported |
| Share go-live date and meeting invite | Katie | |

---

## 5. CSR Training & Communications

| Item | Owner | Notes |
| --- | --- | --- |
| One-page quick reference card (PDF) | Eli | Tag review, correction flow, refund wizard, search tabs |
| Loom walkthrough (~10 min) | Eli | Record against production widget |
| Live demo + Q&A at CSR standup | Eli / Sadie | Day before go-live |
| Kickoff announcement email to pilot CSRs | Katie | Day of |
| Feedback channel (Slack, email, or dedicated form) | Sadie | How CSRs report issues / suggestions |

---

## 6. Monitoring & Safety

| Item | Owner | Notes |
| --- | --- | --- |
| Error alerting on webhook failures / 5xx responses | Eli | Railway → email or Slack |
| Confirm `correction_logger` persistence survives Railway redeploys | Eli | Write to Postgres, not ephemeral file |
| Verify no outbound emails fire without explicit CSR click | Eli | Refund accounting email requires "Send" button |
| Document rollback procedure | Eli | 1. Disable Zoho webhook, 2. Hide widget, 3. Revert env vars |
| Confirm backup/restore path for Postgres | Eli | Manual restore tested once before go-live |

---

## 7. Baseline Metrics & Success Criteria

Before go-live, capture a snapshot so we can measure impact:

| Metric | Source | Baseline |
| --- | --- | --- |
| Tickets/day (last 30-day avg) | Zoho Reports | TBD |
| Tag distribution (top 10 values) | Zoho Reports | TBD |
| Average CSR handle time (if tracked) | Zoho Reports | TBD |

**Pilot success criteria (proposed):**
- AI tag accuracy ≥ **80%** on pilot tickets (measured by correction rate)
- CSR satisfaction: qualitative thumbs-up from pilot group (weekly check-ins)
- Zero critical incidents (no erroneous customer emails, no widget-caused ticket data loss)
- Refund wizard successfully used on ≥ 5 real refund tickets without rework

---

## 8. Day-of Go/No-Go Checklist

Must all be green before enabling the webhook in production:

- [ ] End-to-end smoke test: create a test ticket in prod Zoho → confirm AI tag written
- [ ] Widget loads in pilot CSR's Zoho view; tag review + correction flow works
- [ ] Refund wizard pulls real customer from production ParkM API
- [ ] Railway service healthy; no errors in last 1 hour
- [ ] Pilot CSRs have confirmed they received the install + training
- [ ] Kickoff announcement sent
- [ ] Rollback procedure reviewed and team knows who to contact

---

## 9. Post-Launch — First 2 Weeks

| Cadence | Activity |
| --- | --- |
| Daily (first week) | 15-min check-in with pilot CSRs; review corrections; triage any bugs |
| Weekly (Katie + Sadie + Eli + Nagy) | Metrics review: accuracy, correction rate, CSR feedback |
| End of week 2 | Go / no-go decision for full-team rollout |

---

## 10. Full-Team Rollout (Day 15+)

Contingent on pilot metrics:

| Item | Owner | Notes |
| --- | --- | --- |
| Expand widget visibility to full CSR team | Eli | |
| All-hands training session | Sadie / Eli | Loom already recorded |
| Announce to customer-facing team + any internal stakeholders | Katie | |
| Archive / hide old Tagging field (per Decision 1 outcome) | Eli | |

---

## Open Questions for Katie & Sadie

1. Confirm pilot CSR list (Sadie, Mackenzie, Delaney?)
2. Target go-live date
3. Decisions on tagging field migration (see separate doc)
4. Preferred feedback channel for pilot CSRs (Slack, email, form?)
5. Any Zoho automations on ticket-update that could conflict with AI-written fields — need to pause during initial load?
