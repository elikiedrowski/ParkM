# Session Handoff — 2026-06-12 (delay-cancel message + reactivation refund fix)

Portable record of this working session so it can be resumed on another
computer. Two related-but-distinct issues in the ParkM Zoho CSR Wizard were
worked, both reported by **Sadie Hardy**. All code is committed and pushed to
**both** repos; production fixes are deployed and verified.

Repos & deploy targets:
- **Prod:** `github.com/elikiedrowski/ParkM` (folder `~/ParkM_Zoho`) → Railway
  project **ParkM_Production** (`parkm-production-7e56.up.railway.app`), auto-deploys on push to `master`.
- **Sandbox:** `github.com/elikiedrowski/ParkM_Sandbox` (folder `~/ParkM_Zoho_Sandbox`) → Railway
  project **ParkM_Sandbox**, auto-deploys on push to `master`. Sandbox = prod **+ Phase 5** dev.

---

## Issue 1 — Delay-cancel Stripe error message was inaccurate (shipped)

**Background:** the wizard's delayed-cancel can fail with ParkM's Stripe 500
*"A canceled subscription can only update its cancellation_details and
metadata."* Our shipped `_friendly_cancel_error()` message asserted the
subscription was "already canceled" and told CSRs to use immediate cancel.

**What we found (production logs + ParkM API):**
- Failure is **state-dependent, NOT all paid recurring permits.** Genuine
  paid-recurring delay-cancels succeed (R000679 sub Active, MO000337 sub
  Trialing — both scheduled with `delayCancellationDate=2026-06-16`).
- The "already canceled" assumption is **disproven**: the failing permits
  (MOL000621, SC1000281, RT000752, OG000601) were billing normally right up to
  the attempt. MOL000621 is clearest — our failing call ran 2026-06-10
  11:57:50 UTC and Stripe shows the sub *Ended* 5:57 AM the same instant, i.e.
  the failed attempt itself appears to cancel the sub, then fails before
  scheduling. All four now show 0 active subscriptions.
- The exact internal ParkM/Stripe ordering still needs **Stephen** to confirm.

**Change shipped:** neutralized the `_friendly_cancel_error()` message (no longer
claims "already canceled" or pushes immediate cancel) + corrected the
`handoff-delayed-cancellation-fix.md` Issue #4 root cause.
- Prod commit **`2cbdebf`** (Railway deploy SUCCESS) · Sandbox commit **`1a45381`** (Railway deploy SUCCESS).

**Emails (SENT 2026-06-10/11):**
- **Stephen** — reframed: subs were active, not pre-canceled; asked him to
  confirm whether delay-cancel cancels Stripe before scheduling, what differs
  between succeeding vs failing subs, and to set up **3-4 paid recurring test
  permits w/ active subs in the Testing environment** (Stripe test mode, prod
  fallback) so we can reproduce safely and validate a fix.
- **Sadie** — acknowledged the wording feedback; explained it's state-dependent.

**OPEN (waiting on Stephen):** internal Stripe call ordering; the failing-subset
differentiator (suspect open/past-due invoice, proration, billing-cycle state);
Testing-env repro records. Widget still appends a redundant "— try manually in
ParkM" suffix (`refund-panel.js:1076`) — trim on next widget rebuild.

---

## Issue 2 — Reactivation treated as the "last charge" date (shipped + verified)

**Reported:** Sadie, ticket **#102525**, permit **R000018**
(`Sadiebrad@2email.com`). Refund check showed "last charge 1 day ago (Jun 10)"
when her real last charge was **Jun 4**. She reactivated the permit on Jun 10;
the reactivation must not count as a charge.

**Root cause:** a reactivation stamps the permit's `effectiveDate` to the
reactivation date (no money moves). `_get_inactive_permits` used the *more
recent* of `effectiveDate` vs. the real Stripe charge, so the Jun 10
reactivation beat the Jun 4 charge.

**Fix (`src/services/refund_service.py`):**
- The per-permit Stripe charge feed is now **authoritative** for
  `last_charge_date` — a real charge wins whenever one exists, even if older
  than `effectiveDate` (this is what fixes R000018).
- New helper `_is_effective_date_reactivation_artifact(effective, reactivation)`
  (tolerance compare) gates the `effectiveDate` fallbacks (inactive seed +
  `evaluate_refund_eligibility` deepest fallback) so a reactivation stamp is
  never used as a charge. Preserves the genuine-signup fallback for recent
  no-payment permits.
- `reactivation_date` added to all three summary builders.
- 4 regression tests in `tests/test_refund_inactive_permits.py`.
- Prod commit **`ea679df`** (Railway deploy SUCCESS) · Sandbox commit **`7eb5e5d`** (Railway deploy SUCCESS).

**Live verification (deployed prod `/parkm/refund/evaluate`, R000018):**
`last_charge_date = 2026-06-04`, `days_since_charge = 8`, eligible, `$10.44`.
(Was Jun 10 / 1 day before the fix.)

**Known limitation (not a regression):** ParkM `GetAll` omits `reactivationDate`,
so on the **inactive** path the Tier-2 reactivation guard is dormant
(`reactivation_date` comes back `None`). R000018 is fixed by the Tier-1
"real charge wins" logic regardless. Making the guard fully effective for
cancelled permits would need a per-permit `GetPermitForEdit` (extra API cost) —
possible follow-up.

**Tests note:** the local folders have no pip/httpx/pytest, so logic was verified
via a stub-httpx standalone harness (all scenarios pass) — `tests/test_refund_*`
and `tests/test_phase5_*` should be run in a deps-enabled env.

**Sadie email — DRAFTED, NOT YET SENT.** Confirms the fix is live + verified
(R000018 → Jun 4) and asks the reversed-charge question below. Draft is in the
session transcript; send when ready.

**OPEN — reversed/refunded-charge eligibility (decision: ask Sadie first).**
R000018's Jun 4 charge shows **Reversed** in Stripe yet still reads ELIGIBLE
$10.44. Separate from the date bug. Our charge feed
(`Permits/GetAllPaymentsForPermit`) returns only `{id, created, description,
amount}` — **no status** — so excluding reversed charges needs a different data
source. Pending Sadie's answer on whether reversed charges should be excluded.

---

## Working agreement — porting prod hotfixes to the sandbox (Option A)

Phase 5 is developed in a **separate folder/VS Code window** (its own clone of
the `ParkM_Sandbox` remote), distinct from `~/ParkM_Zoho_Sandbox` (the
hotfix-mirror folder). Chosen model: **direct-to-master + checklist** (not
branch/PR). For every port: (1) `git pull --ff-only` first; (2) clean-tree
precheck; (3) surgical, anchor-matched edits — confirm diff has zero Phase 5
lines; (4) run `tests/test_phase5_*` after; (5) coordinate push timing (sandbox
push auto-deploys) — Phase 5 folder pushes before / pulls after. Verified this
session: both sandbox commits touched only `refund_service.py` + its test file,
Phase 5.1–5.3 confirmed intact in HEAD.

---

## Commit summary (all pushed)

| Fix | Prod | Sandbox |
|---|---|---|
| Neutralize delay-cancel Stripe message + doc | `2cbdebf` | `1a45381` |
| Reactivation not treated as last charge + tests | `ea679df` | `7eb5e5d` |

## Pick-up checklist on the other machine
1. `git pull` in **both** `~/ParkM_Zoho` and the Phase 5 sandbox clone (and `~/ParkM_Zoho_Sandbox`).
2. Send the drafted **Sadie reactivation email** (and decide on the reversed-charge follow-up).
3. Watch for **Stephen's reply** (delay-cancel internals + Testing-env test records).
4. Run `tests/test_refund_inactive_permits.py` + `tests/test_phase5_*` in a deps env to close the local-test gap.
