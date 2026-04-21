# Tagging Field Migration — Options for Go-Live

**Prepared for:** Katie Schaeffer, Sadie Hardy
**Prepared by:** Eli Kiedrowski, Nagy Elshal
**Date:** April 21, 2026

---

## Background

Today, ParkM CSRs manually tag tickets in Zoho using the **Tagging** picklist (single-value). As part of the CSR Wizard go-live, we are introducing two new fields:

- **AI Tag** (`cf_ai_tags`) — multi-select, written by the AI classifier
- **Agent Corrected Tag** (`cf_agent_corrected_tags`) — multi-select, written by the CSR when the AI is wrong

The question is: **what do we do with the historical values sitting in the old Tagging field?**

---

## Decision 1 — Where should the old Tagging values go?

### Option A — Load into **AI Tag** (`cf_ai_tags`)
Populate the new AI Tag field with the old human-selected values for all historical tickets.

| Pros | Cons |
| --- | --- |
| Every ticket immediately has a value in the new field — reporting "just works" | **Pollutes AI accuracy metrics** — we can no longer tell "AI got it right" from "this was backfilled by humans" |
| No new fields to create | Confusing for CSRs — the field labeled "AI Tag" would contain values the AI never produced |

### Option B — Load into **Agent Corrected Tag** (`cf_agent_corrected_tags`) ⭐ *Recommended*
Treat historical human tags as "corrections" and load them into the corrections field.

| Pros | Cons |
| --- | --- |
| Semantically honest — these values **were** human-selected | Corrections field will show a value on tickets that were never actually "corrected" |
| Keeps AI Tag field clean for true AI output → accurate go-forward metrics | Slightly inflates the "corrections" count in early reporting |
| Reporting on "final tag" still works (corrections take precedence over AI) | |

### Option C — Create a **new field** (`cf_historical_tag`)
Keep the old values in their own dedicated field, separate from both AI Tag and Agent Corrected Tag.

| Pros | Cons |
| --- | --- |
| Cleanest separation — no contamination of either new field | Requires a third field in Zoho (one-time setup) |
| Preserves old data verbatim for audit | CSRs have to know to look in a third place for historical context |
| Future reporting can show "old tag vs new tag" side-by-side | Slightly more complex Zoho layout |

### Option D — No migration
Leave the Tagging field in place on historical tickets, and only use the new fields going forward.

| Pros | Cons |
| --- | --- |
| Zero risk, zero effort | Two fields to look at forever — old tickets look different from new ones |
| Old tickets keep their exact original value | Reporting across the boundary is awkward |

---

## Decision 2 — How far back should we migrate?

| Scope | Approx. effort | Best for |
| --- | --- | --- |
| **Open tickets only** | Smallest load | Minimum-risk cutover |
| **Last 30 days** | Small | Matches the refund-eligibility window — practical for CSRs |
| **Last 90 days** | Medium | Quarterly reporting continuity |
| **Last 12 months** | Large | Annual reporting continuity |
| **All time** | Largest | Full historical audit |

> **Record count:** We will pull the exact count from Zoho before execution. Based on the 200-ticket batch pulled from the last 30 days, we estimate roughly **X,XXX tickets** with a non-empty Tagging value over the full history — we will confirm the number in the Zoho UI under **Reports → Tickets → Tagging is not empty** before load.

---

## Decision 3 — How do we map old values to new values?

The old Tagging picklist and the new 51-value AI Tag list are **not identical**. We will need to produce a mapping table before loading.

Three categories of old values:

1. **Direct match** — old name is identical or near-identical to a new tag → auto-mapped
2. **Renamed** — old name maps cleanly to a renamed new tag → mapped via lookup table (Sadie to review)
3. **No equivalent** — old value has no match in the new list → loaded as `Needs Tag` so CSRs can triage

We will share the mapping table with Sadie for approval **before** running the load.

---

## Execution Plan (assuming Option B is chosen)

1. **Pre-load**
   - Pull full list of distinct values currently in the Tagging field (production)
   - Build value-mapping table; Sadie reviews and approves
   - Confirm Zoho automations / webhooks / SLA rules that fire on ticket update — **temporarily pause** any that could misfire during bulk load
2. **Load** (off-hours, e.g., Sunday evening)
   - Export tickets to CSV with: Ticket ID + old Tagging value
   - Transform: apply mapping, convert to multi-select format (semicolon-separated)
   - Bulk-import via Zoho Desk's CSV update (Ticket ID as match key, `cf_agent_corrected_tags` as target)
3. **Verify**
   - Spot-check 20 random migrated tickets
   - Confirm reporting shows expected counts
   - Re-enable any paused automations
4. **Cutover**
   - Mark the old Tagging field as read-only (or hide from layout) so CSRs only use the new fields going forward
   - Announce in CSR standup

---

## Recommendation

- **Field target:** Option B — load into **Agent Corrected Tag**
- **Scope:** Last **90 days** (balances reporting continuity with risk and effort)
- **Timing:** Load the weekend before go-live; cutover Monday morning

---

## Open Questions for Katie & Sadie

1. Which option (A / B / C / D) do you prefer?
2. How far back should we migrate?
3. Are there any Zoho automations that fire on ticket update that we need to pause during the load?
4. Once migrated, should the old Tagging field be **hidden**, **read-only**, or **deleted**?
