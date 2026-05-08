# ParkM — Launch Coordinator Workflow Automation
**Scope of work — v1 draft**

> **Note:** This is a v1 draft built from Katie's May 5 email and the May 7 call discussion. Several scope items are gated on a business process review with the Launch Coordinator team (Delaney, McKenzie, et al.) and an API discovery call with Stephen. Sections marked **[TBD — BPR]** or **[TBD — Stephen]** will be filled in after those conversations.

---

## TL;DR

- The Launch Coordinator team's biggest manual lift today is **resident-letter communication** — pulling templates from Zoho, emailing PMs, and following up 3–5+ times to drive resident sign-ups.
- Proposed end state: a **PM-facing surface inside `pm.parkm.app`** that receives a notification, displays the right letter at the right launch stage, lets the PM approve/edit, and either sends to residents directly or hands back a download. Status syncs back to Zoho automatically.
- A meaningful chunk of the underlying plumbing already exists from the CSR widget and refund automation — wizard engine, parkm.app client, Zoho writeback, dynamic email templates. We're mostly building the **PM-facing surface** and the **bulk-send leg** on top of foundations already in production.
- This work is a candidate for **Phase 5 alternative** in the broader roadmap — it competes with (but doesn't block) Phase 4/5 of the CSR/refund track, and runs in parallel with Patrick's sales-process work.
- **Two decisions** asked of ParkM at the end of this doc, both gated on completing the BPR + Stephen discovery first.

---

## What we know today

From Katie's May 5 email and the back half of the May 7 call:

| Topic | What we know |
|---|---|
| **Where launches are tracked** | Zoho **CRM** deal pipeline (not Desk), driven by a blueprint |
| **Where letter template lives** | "Embedded in or part of each deal record" — Katie wasn't 100% sure of exact location. **[TBD — BPR]** |
| **Letter cadence** | 1 initial letter + 4–5 reminders per launch (residents are slow to act) |
| **"Launch complete" definition** | Manual flag set by the coordinator after enforcement is set up; usually a sales-rep ↔ coordinator conversation |
| **PM identity / portal** | PMs already have `pm.parkm.app` accounts (granted at deal-flow start). Currently used for resident/vehicle/revenue lookups, not launch comms |
| **PM contact info** | Lives in **both** Zoho and parkm.app — source-of-truth question is open |
| **Resident roster availability** | **Inconsistent** — ParkM sometimes has resident emails, sometimes not |
| **SMS capability** | Twilio is already in production for resident SMS (payment notifications). Not currently used for launch comms or PMs |
| **Coordinator team size** | ~3 people today; Katie wants to avoid scaling to 20 |
| **Framing constraint** | Position as "free coordinators for higher-leverage work" (signs, enforcement setup, sales-rep handholding) — **not** "replace headcount" |

---

## What we don't know yet (gates v2 of this doc)

### Open for the BPR with the Launch Coordinator team

- Step-by-step process detail for what a coordinator does today (pre-launch, launch-day, post-launch)
- Where exactly each letter template lives in Zoho (KB article, ticket template, deal-attached doc, snippet, …)
- How coordinators decide when to send each reminder vs wait
- What signal tells them "this PM is responding well / poorly"
- Edge cases: what happens when a PM goes silent, when a property goes live before sign-ups hit threshold, when a sales rep wants to escalate
- What the coordinator does with the bulk-send result — track sign-ups manually, pull from parkm.app, both?
- How the Yardi (or other) PMS factors in — do PMs *prefer* to send via their own system, or would they happily delegate to ParkM?

### Open for Stephen (parkm.app API discovery)

- Endpoints for **property metadata** (currently no clear endpoint surface)
- Endpoints for **PM contact info** (Zoho vs parkm.app source-of-truth conflict)
- Endpoints for **resident rosters** — read access for at least the properties where ParkM already has the data
- Whether `pm.parkm.app` already exposes a deep-link / single-page surface we can extend, or if a net-new dashboard module is required
- Bulk-send infrastructure inside parkm.app — does it exist, or is this net-new?

### Open for Katie / ParkM

- Deliverability strategy: should resident-facing letters come **from ParkM's domain** (simpler, one DKIM/SPF setup) or **from the PM/property's domain** (better trust, but per-property setup overhead)?
- Is the vision a full launch-team rollout from day one, or pilot with one coordinator first (similar to how Sadie piloted refund/wizard)?
- Compliance posture: CAN-SPAM, on-behalf-of sending, opt-out mechanics — does ParkM have a stance, or do we need to define one?

---

## What's reusable from the existing build (~40-50% plumbing)

Foundations already in production from the Phase 1–3 work that this proposal can lean on:

| Capability | Source | How it applies here |
|---|---|---|
| Wizard engine (guided, multi-step flows) | `src/wizard/`, `src/services/wizard.py` | Extends to a PM-facing wizard for "review and approve letter" |
| ParkM.app client (auth, lookups) | `src/services/parkm_client.py` | Extends with property/PM/resident endpoints once Stephen confirms |
| Zoho writeback (field updates, status changes) | `src/api/zoho_client.py`, `src/services/tagger.py` | Used to sync "letter approved/sent" status back to the CRM deal record |
| Dynamic email template generation | `src/templates/`, refund-forward pattern | Used to render personalized resident letters at scale |
| OAuth + multi-environment infra | Existing FastAPI on Railway | Same deploy footprint; new endpoints, no new infra |

**Net-new components required:**

- PM-facing UI surface inside `pm.parkm.app` (current widget is CSR-only and runs in Zoho Desk iframe)
- Bulk-send pipeline to residents (SMTP/SendGrid for email; Twilio for SMS — Twilio already exists)
- Reminder scheduler / cadence engine (or a Zoho Blueprint extension if we lean on what's already there)
- Notification delivery to PMs (email + optional SMS, deep-linked to portal)
- Status reconciliation: parkm.app PM action → Zoho deal-record stage update

---

## Proposed approach (high-level — to be refined after BPR)

Structured as four stages so ParkM can stop at any point and still be better off than today.

### Stage 0 — Discovery (prerequisite, not billable)
- Business process review with the Launch Coordinator team (Delaney, McKenzie, others)
- Stephen API discovery call
- Document the actual current-state flow with screenshots and timing
- Output: a v2 of this doc with concrete scope and the unknowns closed

### Stage 1 — Coordinator-side automation in Zoho only
- Auto-generate the first letter from deal-record data
- Auto-trigger reminder follow-ups on a schedule
- Coordinator stays in the loop for approvals — system does the rote work
- **Why first:** All inside Zoho; no parkm.app changes; lowest dependency footprint; proves the cadence engine before exposing it to PMs

### Stage 2 — PM-side review and approve surface
- New surface inside `pm.parkm.app`: PM gets notified (email/SMS), clicks deep-link, sees the letter at the current stage, clicks Approve
- On approval: PM downloads + sends manually OR hands back to ParkM for download/forwarding
- Zoho deal-record auto-advances stage on approval
- **Why second:** Adds the PM-facing piece; still no resident-facing automation; keeps the existing PM-sends-via-Yardi pattern intact for now

### Stage 3 — ParkM-direct resident send (where we have the roster)
- For properties where ParkM already has resident emails: PM clicks "ParkM sends for me" → bulk send through our pipeline
- Tracks open / click / sign-up conversion per letter
- Feeds data back to coordinator dashboard
- **Why third:** Requires resident roster availability + deliverability decision (domain question above) + PM trust in ParkM-from sending

### Stage 4 — End-to-end automation, minimal PM involvement
- For "trusted" PMs / repeat properties: auto-send with notification (no approval click required)
- Reserved for after Stages 1–3 prove the pattern
- **[TBD — depends on Stage 1–3 results and PM appetite]**

---

## Decisions for ParkM

**Decision 1 — Approve a one-week discovery sprint (Stage 0).**
- BPR with Launch Coordinator team (Delaney, McKenzie)
- Stephen API discovery call
- Output: v2 of this doc with concrete scope, closed unknowns, and a stage-by-stage plan
- **Why this is the ask:** Without the BPR + Stephen input, any further commitment would be guessing. Discovery is the smallest possible commitment to keep this initiative moving.

**Decision 2 — Approve Stage 1 (coordinator-side Zoho automation) to start after Stage 0.**
- Conditional approval: kicks off automatically once the v2 SOW is signed off post-discovery
- Lowest-risk piece — all inside Zoho, no parkm.app changes, no resident-facing exposure
- Provides immediate ROI for coordinators while Stage 2's PM surface is being designed

**Stages 2–4 stay deferred** until Stage 1 is in production and the team has data to react to. Same crawl-walk-run pattern as the Phase 5 refund proposal.

---

## How this fits with everything else

- **Runs in parallel with** Phase 4/5 of the CSR/refund track (different surface area: PM-facing vs CSR-facing)
- **Runs in parallel with** Patrick's sales-process work (different Zoho product: CRM deal-pipeline blueprint vs sales-rep tooling)
- **Shares plumbing** with Phase 4 (property/PM endpoints in parkm.app are useful for both)
- **Independent of** the Sadie pilot — no overlap with the post-go-live feedback loop

---

## Sections to be filled in after the BPR + Stephen call

- [ ] Concrete current-state process map (with timings)
- [ ] Confirmed letter-template inventory (what letters, in what order, for which property types)
- [ ] PM segmentation (which PMs are good candidates for Stage 3/4 vs which need to stay in Stage 2)
- [ ] Final stage-by-stage scope with actual deliverables
- [ ] Decision criteria for moving Stage N → Stage N+1
- [ ] Compliance / deliverability decisions
- [ ] Pilot plan (which property, which coordinator, success criteria)
