# ParkM Zoho — Permit Cancellation Fixes: Session Handoff (June 2026)

Working session resolving a cluster of related issues in the ParkM Zoho Desk CSR
Wizard around permit cancellation, reported by **Sadie Hardy** (ParkM CSR lead).
All work was done in the production working folder (`~/ParmM_Zoho`) and deployed
to **both** prod and sandbox Railway.

---

## Issues addressed (4)

### 1. Account Preview showed a stale expiration date after a delay-cancel (cosmetic)
- **Symptom:** After a delay-cancel in the wizard, .APP "Account Preview" still
  showed the old (far-future) expiration date instead of the cancel date.
- **Cause:** The Preview renders `expirationDate`; a delay-cancel didn't change it.
- **Resolution:** Fixed as a **side effect of Issue 2** — setting `isCancelled=true`
  moves `expirationDate` to the delay date, which is what the Preview reads.
  Confirmed by Sadie.

### 2. Delayed cancellations never fired (CRITICAL — paid permits kept billing)
- **Symptom:** Permits delay-cancelled via the wizard stayed `Active` past their
  `delayCancellationDate` and never cancelled. Residents on paid permits kept
  getting charged.
- **Investigation:** Native .APP delay-cancel worked (free + paid both fired on
  time) → therefore it was **our wizard's bug**, not ParkM's scheduler.
- **Root cause (confirmed with Stephen Lambert):** the wizard set ONLY
  `delayCancellationDate` via `Permits/CreateOrEdit`. ParkM's background
  cancellation job only acts on permits flagged `isCancelled=true`. Writing the
  date alone persists/displays it but never schedules the job.
- **Fix:** set `permit_dto["isCancelled"] = True` alongside `delayCancellationDate`
  in `src/services/parkm_client.py::delay_cancel_permit`.
- **Validated:** live test on a Sadie test permit — `isCancelled=true` + a future
  date stayed `Active` until the date, then cancelled exactly on schedule.
  `permitCancellationReason` is NOT required.
- **Confirmed end-to-end by Sadie** through the actual wizard.
- **Commit:** prod `8341dbc` / sandbox `89d6945`.

### 3. Overdue scheduled cancels were masked as "already handled" (safety net)
- **Latent issue:** `process_refund_request` returned synthetic success for ANY
  `delay_cancellation_date`, even ones already past-due and still Active — so a
  CSR reprocessing such a permit silently forwarded it to accounting.
- **Fix:** split future vs overdue. Overdue + still Active → immediate cancel
  inline (`cancel_type: "overdue_converted_to_immediate"`); unparseable date →
  treated as overdue (fail toward acting). Added timezone-safe `_parse_iso_utc()`
  helper + a widget result message.
- **Scope:** only fires when a CSR reprocesses an *eligible* permit — a safety
  net, not a systemic sweep.
- **Commit:** prod `22904dc` / sandbox `b1fd62d`.

### 4. Stripe "already-canceled subscription" error (clean CSR message)
- **Symptom:** delay-cancel on a paid permit failed with a raw Stripe 500:
  *"A canceled subscription can only update its cancellation_details and
  metadata."* Reproduced in native .APP too (ticket #102166, permit OP1000168,
  ethan.ferfie@yahoo.com).
- **Cause (original assumption — since DISPROVEN, see UPDATE below):** the
  permit's underlying Stripe subscription was already canceled while the permit
  still showed active/recurring, so Stripe blocked scheduling a cancel on it.
- **Workaround:** immediate `CancelPermit` works — it doesn't reschedule the
  subscription. The CSR did this and it succeeded.
- **Fix (original):** `_friendly_cancel_error()` in `parkm_client.py` translated
  the error into a CSR message pointing to the immediate-cancel path.
- **Commit:** prod `3541005` / sandbox `b8c8a2d` (+ `c2ffb52` retrigger after a
  transient sandbox build flake).

> **UPDATE (June 11, 2026) — "already-canceled" cause DISPROVEN; failure is
> state-dependent.** A second case (ticket #102434, permit MOL000621) plus a
> production-log + ParkM-API review overturned the original diagnosis:
> - It's **not all paid recurring permits.** Genuine paid-recurring delay-cancels
>   succeed — R000679 (sub *Active*) and MO000337 (sub *Trialing*) both scheduled
>   with `delayCancellationDate=2026-06-16` and still have live subs.
> - The failing permits were **NOT pre-canceled.** They were billing normally
>   right up to the attempt (last charges: MOL000621 5/29, RT000752 6/9,
>   OG000601 6/10 hours before, SC1000281 5/11). A canceled sub can't bill.
> - **MOL000621 is the clearest case:** our failing call ran 2026-06-10 11:57:50
>   UTC and Stripe shows the sub *Ended* 5:57 AM the same instant — strongly
>   suggesting **the failed attempt itself canceled the sub**, then failed before
>   persisting the schedule (permit left Active, `isCancelled=false`,
>   `delayCancellationDate=null`).
> - Failures are **not uniform**: all 4 now show 0 active subs, but SC1000281
>   still ended up with `isCancelled=true` + `delayCancellationDate=2026-06-17`.
> - **Message corrected** in `_friendly_cancel_error()` to a neutral, non-
>   committal wording (no longer claims "already canceled" or pushes immediate
>   cancel — Sadie's feedback was that delayed cancel should work even with no
>   active Stripe sub, as free permits prove).
> - **Open with Stephen (ParkM):** the internal Stripe call ordering in the
>   delay-cancel path, and what differs between subs that schedule cleanly vs.
>   error (suspect open/past-due invoice, proration, or billing-cycle state).
>   Also requested 3-4 paid recurring test permits w/ active subs in the
>   **Testing** environment (Stripe test mode, prod fallback) to reproduce safely
>   and validate a fix. See memory `project_delaycancel_stripe_root_cause`.

> **RESOLVED (June 2026) — root cause was OUR `nextRecurringDate` clearing.**
> Source Logic (ParkM vendor, support ticket #5685) confirmed: our delay-cancel
> was *clearing* `nextRecurringDate`, which triggers a Stripe **price/cycle
> update** on the very subscription being canceled — that update collides with
> the cancellation and throws "A canceled subscription can only update its
> cancellation_details and metadata," tearing down the sub and leaving the
> permit Active with no schedule. Their guidance: **do not change
> `nextRecurringDate` or `recurringPrice` when canceling.**
> - **Backend fix:** `delay_cancel_permit` no longer modifies `nextRecurringDate`
>   /`recurringPrice` — round-trips them unchanged, sets only `isCancelled` +
>   `delayCancellationDate`. The `update_next_recurring_date` params are now
>   ignored (logged + dropped, ref #5685).
> - **Widget fix:** removed the editable "Next recurring date" field + the
>   misleading "clear this to prevent the next auto-charge" note (the backend now
>   ignores it, so it was misleading CSRs about billing). Replaced with a
>   read-only renewal warning ("⚠️ This permit renews on <date>; a cancellation
>   after that date lets one more charge occur"). Requires a widget zip rebuild +
>   re-install.
> - **DEPLOYED (June 26 2026):** backend + widget — prod `187b24a` / sandbox
>   `8e3fe09` (sandbox rebased onto Phase 5, no history rewrite). Both environments
>   healthy. Widget shipped via rebuilt zips (see Widget zips section).
> - **Still TODO:** validate end-to-end once Source Logic provisions 3-4 paid
>   recurring test permits with active subs (requested in support ticket #5685).

---

## Key technical findings / gotchas (don't relearn these)
- **Scheduled cancellation recipe:** `isCancelled=true` **+** a future
  `delayCancellationDate`, set together via `Permits/CreateOrEdit`. Date alone is
  a no-op that still displays on Permit Details.
- **`Permits/GetAll` omits `delayCancellationDate`** — it returns the key but
  ALWAYS null; only `GetPermitForEdit` populates it (verified 0/41 in GetAll vs
  2/41 in edit DTO). So you **cannot** bulk-scan for stuck permits via GetAll;
  it would need `GetPermitForEdit` per permit (infeasible at ~165k active).
- **A "stuck" permit = `Active` + `delayCancellationDate` set + `isCancelled=false`.**
  Native cancels set `isCancelled=true`, so this state is unique to the pre-fix
  wizard bug — which is why Stephen can isolate them with one DB query.
- **Fired delay-cancel end state:** `isCancelled=true`, `expirationDate` moved to
  the delay date, `permitCancellationReason=6`.
- **Only Swagger delay endpoint is `Permits/DelayCancelAllPermits`** (org-wide) —
  not the per-permit path; the real mechanism is CreateOrEdit + isCancelled=true.
- **Restore a test permit:** `Permits/ReActivatePermit?Id=X`, then `CreateOrEdit`
  to clear the date + restore the original expiration.
- **Do NOT touch `nextRecurringDate`/`recurringPrice` when canceling** — changing
  either triggers a Stripe price/cycle update on the sub being canceled, which
  collides and throws "A canceled subscription can only update its
  cancellation_details and metadata" (ParkM/Source Logic ticket #5685). This was
  the REAL root cause of the delay-cancel failures.
- **Railway CLI auth expires** and CANNOT be re-authed non-interactively (`railway
  login` and `--browserless` both fail in a headless/sandboxed shell). Since ParkM
  creds live in Railway, an expired session = no ParkM API access until you re-auth
  in a real terminal, OR pass `RAILWAY_TOKEN=<project-token> railway variables`, OR
  put `PARKM_API_*` in local `.env`. A sandboxed agent shell does NOT share your
  terminal's Railway login.
- **Refund/reversed charge status is NOT exposed by any permit-keyed ParkM
  endpoint** (verified live June 26): `GetAllPaymentsForPermit` returns a slim DTO
  `{id, created, description, amount}`; `GetPermitSubscriptions` has no charge/refund
  detail; `GetAllTransactions` empty; `GetPayment` needs a session id; `GetPaymentResult`
  is a bool. The data exists in the `Charge` schema (`refunded`/`amount_refunded`) but
  isn't surfaced — needs Stephen to expose it.

---

## Access notes (for the new machine)
- **ParkM API creds:** NOT in local `.env` — they live in Railway (project
  `ParkM_Production`). Pull via `railway variables --json`. Prod URL
  `https://api.parkm.app`. Auth: `POST /api/TokenAuth/Authenticate`
  `{userNameOrEmailAddress, password}` with header `X-TenantId`.
- **Zoho:** local `.env` points to the **sandbox** org (856336669). Prod org
  (854251057) creds are in Railway. The prod Zoho OAuth token **lacks the
  `Desk.search` scope**, so the search API is blocked (use list + per-ticket cf,
  or add the scope).
- **Railway:** logged in as `eli@thecrmwizards.com`; both `ParkM_Production` and
  `ParkM_Sandbox` are accessible. Use `railway status --json` for deploy state.
- **Repos:** prod `github.com/elikiedrowski/ParkM` (remote `origin`), sandbox
  `github.com/elikiedrowski/ParkM_Sandbox`. Develop in the sandbox folder
  normally; this session worked in the prod folder. Mirror a commit with:
  `git format-patch -1 <sha> --stdout | (cd ../ParkM_Zoho_Sandbox && git am)`.

---

## Commits & deployments (all live in prod + sandbox, confirmed SUCCESS)
| Fix | Prod | Sandbox |
|---|---|---|
| Overdue-cancel safety net | `22904dc` | `b1fd62d` |
| `isCancelled=true` (delayed-cancel + preview) | `8341dbc` | `89d6945` |
| Clean Stripe error message | `3541005` | `b8c8a2d` (+`c2ffb52`) |
| **Stop clearing `nextRecurringDate` (REAL root-cause fix) + widget control removal** | `187b24a` | `8e3fe09` |

## Widget zips — TWO of them, per environment (do NOT cross them)
Build each zip from its **own folder** so `config.js` carries the right backend URL:
- **`parkm-widget-prod.zip`** (build from `~/ParmM_Zoho`) → `API_BASE_URL` =
  `parkm-production-7e56.up.railway.app` → install in the **PROD** Zoho org.
- **`parkm-widget-sandbox.zip`** (build from `~/ParkM_Zoho_Sandbox`) → `API_BASE_URL`
  = `parkm-production.up.railway.app` (NO `-7e56`) → install in the **SANDBOX** Zoho org.
- **TRAP (this bit us):** the sandbox URL is literally `parkm-production…` (no suffix)
  while prod is `parkm-production-7e56…`. Installing the sandbox zip into prod (or
  vice-versa) makes the widget call the wrong backend → **"Failed to load wizard
  data."** That symptom = wrong-zip/wrong-URL, NOT a code bug (verify the backend is
  healthy and check the failed request URL in the Network tab).
- Re-install via the **Install URL** (publishing alone won't update an installed
  widget). Build with Python `zipfile` (no `zip` binary on this box): walk `widget/`,
  arcnames relative to `widget/`, 14 files. **Backend fixes do NOT require a zip.**
- Widget contents: 5pm default cancel time (`9cb9bb0`), overdue message (`22904dc`),
  and next-recurring-control removal + renewal warning (`187b24a`/`8e3fe09`).

## Emails
- **Stephen:** confirmed the `isCancelled` fix + requested the stuck-permit query
  (`delayCancellationDate` set AND `isCancelled=false`). Separate thread opened on
  the Stripe active-but-canceled-subscription root cause.
- **Sadie:** root cause fixed + deployed; she tested E2E and confirmed both the
  delay-cancel and the Preview now work; explained the Stripe error is not a
  wizard bug.
- **Combined support reply (ticket #5685, June 26):** confirmed the `nextRecurringDate`
  root cause + that the fix is deployed; requested test permits to validate; folded
  in the refund/reversed-status question for Stephen (all parties on the thread).
- **Sadie / Phase 5 thread (June 26):** proposed starting **5.4** in sandbox now that
  the delay-cancel blocker is resolved (5.2/5.3 stay parked in sandbox; nothing to
  prod until she's satisfied 1-3 + the delay-cancel are solid).
- **Sadie / refund-eligibility thread (June 26):** status update — refund data not
  exposed by the API; re-asked Stephen; guardrail to follow once exposed.

---

## Refund-eligibility: reversed-charge guardrail (OPEN — separate from delay-cancel)
Sadie's request (ticket #102525 / R000018): a charge already refunded/reversed in
Stripe should be **excluded from refund eligibility** so a CSR can't double-refund.
Wizard would show "Already refunded N days ago — check with accounting" in the
"X days since last charge" slot. (The reactivation-as-last-charge half is already
FIXED + live — R000018 shows the June 4 charge, not the June 10 reactivation.)

**Blocker (confirmed via live API testing June 26):** the refund/reversed status is
**not exposed by any reachable permit-keyed endpoint** — see the gotcha bullet above.
The data exists in ParkM's `Charge` schema (`refunded`/`amount_refunded`/`refunds`/
`status`) but isn't surfaced. **Asked Stephen** to (a) add `refunded`/`amount_refunded`
(or a `reversed` flag) to `GetAllPaymentsForPermit`, or (b) point us at an endpoint
returning the full Charge/PaymentIntent for a permit. Build the guardrail once exposed.

## OPEN ITEMS
1. **Validate the delay-cancel fix end-to-end** — waiting on Source Logic (ticket
   #5685) to provision 3-4 paid recurring test permits w/ active Stripe subs; then
   run a delayed cancel and confirm the sub cancels cleanly on schedule.
2. **Refund-data exposure (Stephen)** — see refund-eligibility section above.
3. **Phase 5.4** — proposed to Sadie; awaiting her go-ahead to build it in sandbox.
