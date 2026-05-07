# ParkM:CRM Wizards - Weekly Status Call

**Date:** May 7, 2026
**Participants:**
- **ParkM:** Katie Schaeffer (Operations), Sadie Hardy (CSR Lead)
- **CRM Wizards:** Eli Kiedrowski

---

## Meeting Summary

### Purpose
Weekly status call covering Phase 1-3 post-go-live feedback, layout/UI cleanup planning for full team launch, and a forward-looking discussion on Phase 4/5 scope plus a new launch-coordinator automation opportunity raised by Katie.

### Project Phases Status

| Phase | Status | Notes |
|---|---|---|
| **1** — AI Classification & Auto-Tagging | ✅ Live (production) | Sadie-only pilot |
| **2** — In-Workflow Guidance (Wizard) | ✅ Live (production) | 51 tags, full wizard content |
| **3** — Refund Automation + ParkM.app API | ✅ Live (production) | CSR-driven; accounting forward working |
| **4** — Unified Agent Desktop | ⏸ Deferred | Pending Phase 1-3 feedback close + scope decision |
| **5** — Progressive Automation | ⏸ Deferred | Pending Phase 1-3 feedback close + scope decision |

---

## Key Decisions

### 1. Phase 1-3 feedback iteration — direct in production
- Sadie submitted 9 feedback items. All categorized as **post-go-live bug fixes** — included in current scope, no additional billable hours.
- Because production access is currently limited to Eli + Sadie, iteration will happen **directly in production** (sandbox can't simulate the cases).
- Eli added more logs to assist with debugging the next round.
- Sadie has read through Eli's comments on all 9 items but hasn't re-tested yet — will iterate in coming days.

### 2. License plate field logic — preserves manual input
- Removed the duplicate AI-created license plate field; now using the existing standard ParkM license-plate field.
- AI **only writes** to the field if it's empty — manual resident input is never overwritten.
- AI still extracts plate from email body when the field is blank.

### 3. Page layout cleanup — DEFERRED until full team launch
- The `tagging` field is currently required and will **stay in the layout for now** — changing profiles/page layouts for a 2-person pilot isn't worth the disruption.
- **On full team launch (off-hours):**
  - Remove `tagging` field from the ticket layout entirely
  - Move `cf_ai_tags` and `cf_agent_corrected_tags` to the top of the ticket under "Additional Information"
  - Hide the standalone "AI Classification" section (data continues to display in the wizard on the right-hand side — duplication eliminated)
- Sadie + Katie both confirmed the wizard already shows this data, so on-ticket display in two places is unnecessary.

### 4. User access — Delaney + McKenzie added Monday May 11
- Sadie will send Eli an email Monday confirming readiness; Eli adds them to production then.
- The page-layout cleanup will **not** happen at the same time — separate decision once the broader team launch is approved.

### 5. Phase 4 development DEFERRED
- Aligned that Phase 4 will not start until the Phase 1-3 feedback loop is closed and the team is satisfied.
- Eli to provide detailed Phase 4 + Phase 5 scope documentation so Katie can make a prioritization decision against competing initiatives (Patrick's sales-process work and Katie's launch-coordinator automation idea).

---

## NEEDS FURTHER DISCUSSION

### Launch Coordinator workflow automation (new opportunity from Katie)

Katie raised this as a potential Phase 5 alternative. Current state and proposal:

**Today:**
- Launches tracked in **Zoho CRM deal pipeline** (not Desk), driven by a Blueprint
- Launch Coordinator team (~3 people) manually pulls letter templates from the deal record and emails them to the property manager
- PM sends letters to residents via Yardi or their own property-management software
- Series: 1 initial letter + 4-5 reminders (residents are slow to act on signups)
- "Launch complete" is a manual flag set by the coordinator after enforcement is in place
- ParkM has resident rosters **inconsistently** — sometimes yes, sometimes no email addresses

**Katie's proposed end state:**
- Replace the coordinator's manual email workflow with automation
- New PM-portal interface inside `pm.parkm.app` (existing PM dashboard)
- Notification to PM via email and/or SMS (Twilio is already in use for resident payment notifications)
- Notification deep-links to the exact letter at the exact stage in the PM dashboard
- PM clicks approve → can download to send manually OR (future state) upload resident contact list and send directly from the portal
- Doubles as a forcing function to introduce PMs to a dashboard they already have access to but rarely use

**Framing constraints:**
- Do **not** position as "replacing the launch coordinator team" — frame as "make them more productive, redirect to net-new work" (signs, enforcement setup, sales rep handholding). Goal is to avoid scaling to a 20-person team.
- Some of this might be doable inside Zoho CRM natively (Blueprint extensions, automation rules); doesn't have to be a custom build on top.

**Acceptance status:** Valid exploration path. Requires a formal scoping review with the launch team before proceeding.

---

## Action Items

| Owner | Task | Timing |
|---|---|---|
| **Sadie** | Test all 9 updated items from Phase 1-3 feedback; report back fixed/not fixed | This week |
| **Sadie** | Send Eli an email when ready to add Delaney + McKenzie to production | Monday May 11 |
| **Eli** | Add Delaney + McKenzie to production once Sadie confirms | After Sadie's email |
| **Eli** | Compile detailed Phase 4 + Phase 5 scope documentation | Before next priority decision |
| **Eli** | Meet with Patrick to discuss his competing priorities | Monday May 11 |
| **Eli** | Schedule business process review with the Launch Coordinator team if Katie greenlights | TBD |
| **Katie** | Meet with Chad and Patrick to confirm priority and scope for next development engagement | TBD |

---

## Notes & Observations

- Chad has reviewed the wizard + refund flow and is happy with the current calculated rollout pace — useful validation for the phased approach.
- Katie's stated end-state vision for refund automation: **100% bot-driven, no CSR involvement** (currently CSR drives the wizard; accounting still does the Reverse Charge). Phase 5 should be structured around progressive movement toward this.
- The "Parker bot" use case was previously unknown to Eli/CRM Wizards but has been folded into the current build for Sadie to validate.
- Eli reinforced the "crawl, walk, run" framing — Katie and Chad both endorse this approach over an aggressive cutover.
- No work has started on Phase 4. ParkM retains full flexibility to pivot to Patrick's work, the launch-coordinator initiative, or stay the original Phase 4/5 course.
