# Post Go-Live Fixes — May 2026

Production bug fixes applied during the first weeks after the May 2026 go-live, driven by Sadie's pilot feedback. Each item below maps to one or more commits on `master` and was verified against the original failing ticket in production.

## ParkM API — "Edit permit" permission

**Tickets:** #95241, #95512

**Symptom:** Widget's *Cancel Permit* and *Delay Cancel* buttons failed with
`HTTP 403 — Required permissions are not granted: Edit permit`. CSRs had to
fall back to manually cancelling in parkm.app.

**Root cause:** Our integration account (`eli@thecrmwizards.com`) had read
access on ParkM but was missing the *Edit permit* permission required to call
`Permits/CancelPermit` and `Permits/CreateOrEdit`. Not a code bug.

**Resolution:** Stephen at ParkM granted *Edit permit* to the integration
account. Verified by replaying the exact failing call (`CreateOrEdit` against
permit R000016 from #95512) — returned 200 OK.

**Long-term recommendation:** Spin up a dedicated `zoho-api@parkm.com` service
account so cancellations show up under the integration user instead of mine in
audit logs.

---

## Refund eligibility — free permits flagged as eligible

**Tickets:** #95512 (permit RT000530 first pass; permit R000016 second pass)

**Symptom:** Free permits (e.g. *Free monthly recurring*) showed
**ELIGIBLE FOR REFUND** even though the customer had never been charged.

**Root cause (phase 1):** Eligibility logic treated a permit's
`effectiveDate` as a proxy for "last charge." A free permit issued 29 days ago
looked identical to a paid permit charged 29 days ago.

**Phase 1 fix — inactive permits** (commit **559f7a5**, `refund_service.py`):
- Always pull `Permits/GetAllPaymentsForPermit` per inactive permit instead of
  trusting `effectiveDate`.
- New `total_paid_within_window` field summed from successful Stripe payments
  in the last 30 days.
- Eligibility check requires `total_paid_within_window > 0`.

**Phase 2 fix — active + scheduled-to-cancel permits** (commit **c921870**,
`refund_service.py`): Phase 1 only enriched the inactive list. R000016 is
`status=Active` with `delayCancellationDate` set, so it routes through
`_get_scheduled_to_cancel_permits` and skipped the new guard entirely. Added
`_enrich_permits_with_payment_totals` which runs after the active +
scheduled-to-cancel list is assembled, pulling Stripe payments in parallel and
attaching the same field. The eligibility guard now fires uniformly for all
permit states.

**Reason wording:** split into two cases:
- *"Free permit — customer was not charged"* — no price configured at all.
- *"No charge within the 30-day refund window — nothing to refund"* — priced
  permit, no recent charge.

**Verification:** Confirmed against R000016 in prod — `total_paid=0`, returns
*"Free permit — customer was not charged"* with no *Forward to Accounting*
button.

---

## License plate extraction

This area went through several iterations. Each pass fixed the previously
reported failure but uncovered a new edge case in production.

### Pass 1 — classifier misses obvious plates

**Ticket:** #95071

**Symptom:** Widget showed *License Plate: Not found* despite `CO-7705793`
being right in the subject line.

**Fix** (commit **e655d1d**, `classifier.py` + `main.py`): post-LLM regex
backfill with two patterns — US state prefix and explicit
*plate/license/tag* context word. Same regex also runs in the wizard endpoint
at read time so already-classified tickets pick up plates without
re-classifying. Never overwrites a manually-entered plate.

### Pass 2 — strip ParkM permit-name prefix

**Ticket:** #95071 (follow-up)

**Symptom:** Extraction returned `CO-7705793` (ParkM's permit naming
convention) instead of the bare plate `7705793`.

**Fix** (commit **3c4e79e**, `classifier.py`): strip the state prefix from
state-prefix matches. The "CO-" is permit naming, not part of the plate
itself. ParkM's plate-search expects the bare value.

### Pass 3 — Payment Help widget + late-arriving plates

**Ticket:** #95129

**Symptom:** Payment Help wizard did not show the license plate in the
*Extracted Information* panel. Also, plates arriving in a customer reply (not
the original email) never appeared anywhere because classification only runs
on `Ticket_Add`.

**Fix** (commit **41a86bc**, `wizard-renderer.js` + `main.py`):
- Widget renderer now displays any classification entity from
  `wizard.extracted_entities`, not only entities tied to a flagged wizard
  step. Payment Help (and future tags) get the plate for free.
- Wizard endpoint scans up to 10 conversation threads (in parallel) for a
  plate when both the cf field and the initial email come up empty.

### Pass 4 — regression: thread regex matches Spanish + ZIP codes

**Tickets:** #96559, #96673, #96736

**Symptom:** After Pass 3, the widget started surfacing junk values:
`2026` (date), `2012` (vehicle year), `75243` (ZIP). The extraction logic
that broadened plate capture was too aggressive on multilingual / address
content.

**Root cause:** Two compounding issues.
1. **Classifier blind spot.** The classifier only saw `subject + description`.
   For email-sourced tickets in Zoho, `description` is empty and the
   customer's original email lives in the **first thread**. So the LLM was
   classifying off the subject alone and never saw the body — meaning bad
   classifications upstream and no entity extraction.
2. **Regex too permissive at read time.** The wizard endpoint's thread-scan
   regex matched (a) lowercase Spanish article *"la"* as Louisiana state code
   (`la 2012` → `2012`), (b) 4-digit vehicle years that satisfied
   `_looks_like_plate`, and (c) 5-digit ZIP codes after legitimate state
   prefixes (`TX 75243`).

**Fix** (commits **3ee2900** + **52a9e5d**, `webhooks.py` + `classifier.py` +
`main.py`):
- **Thread-body fallback for classifier:** when `description` is empty, pull
  the first email thread as the body and feed it to the classifier (mirrors
  the pattern already used for Parker chat tickets).
- **Tightened plate validation:**
  - State-prefix regex now requires an uppercase state code (so lowercase
    Spanish words don't match).
  - `_looks_like_plate` rejects pure-4-digit years in 1900-2099, pure-5-digit
    ZIPs, and any pure-numeric token under 6 chars.
- **Crash fix** (commit **52a9e5d**): normalize `None` descriptions before
  the thread fallback runs so tickets with a truly missing field don't crash
  the webhook (`'NoneType' object has no attribute 'strip'`).

**Verification:** Reclassified all three flagged tickets through the new
pipeline in prod:

| Ticket | Tag | Confidence | Plate |
|---|---|---|---|
| #96559 | Customer Canceling a Permit and Refunding | 0.90 | None (no false `2026`) |
| #96673 | Customer Canceling a Permit and Refunding | 0.95 | `UT-791010` (correctly pulled from Spanish-language body) |
| #96736 | Property Approving Grandfathered Permit | 0.95 | `PBC8383` |

#96736 also flipped from the wrong *"Property Permitting PAID Resident
Vehicle for Them"* tag to the correct *"Property Approving Grandfathered
Permit"* — a side effect of the classifier finally seeing the email body.

---

## Commit map

| Date | Commit | Area | Summary |
|---|---|---|---|
| May 14 | `559f7a5` | refund | Free-permit guard for inactive permits |
| May 14 | `e655d1d` | classifier | Regex license-plate fallback |
| May 14 | `3c4e79e` | classifier | Strip ParkM state-code prefix |
| May 14 | `41a86bc` | widget + endpoint | Plate visible on all tags + scan replies |
| May 14 | `c921870` | refund | Free-permit guard extended to active permits |
| May 20 | `3ee2900` | classifier | Use first email thread as body when description empty |
| May 20 | `52a9e5d` | webhook | Normalize `None` descriptions before thread fallback |

All commits also ported to `ParkM_Sandbox` so sandbox and production stay in
lockstep on these fixes.

---

## Operational notes

- **Model:** Production classifier was upgraded from `gpt-4o-mini` to
  `gpt-4.1-mini` on 2026-05-20 (Railway env var `AI_MODEL`). The thread-body
  fallback above benefits substantially from the new model's better
  multilingual handling — most of the bad classifications it caught were in
  Spanish-language emails.
- **ParkM permit naming reminder:** `CO-7705793` is the permit *name* in
  parkm.app (state code + dash + plate). The license plate itself is the part
  after the dash. Strip the prefix before storing or searching.
- **Email-sourced tickets in Zoho Desk:** `description` is almost always
  empty. The customer's original email is in the first thread. Any code that
  needs the email body should use the thread fallback pattern in
  `src/api/webhooks.py` and `main.py`.
