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

## Widget zip
`parkm-widget.zip` rebuilt (production build, `API_BASE_URL` →
`parkm-production-7e56.up.railway.app`). Contains the 5pm default cancel time
(`9cb9bb0`) + overdue message (`22904dc`). User re-installed it. **The backend
fixes do NOT require the zip.** Minor TODO: trim the widget's now-redundant
"— try manually in ParkM" suffix on the next rebuild.

## Emails
- **Stephen:** confirmed the `isCancelled` fix + requested the stuck-permit query
  (`delayCancellationDate` set AND `isCancelled=false`). Separate thread opened on
  the Stripe active-but-canceled-subscription root cause.
- **Sadie:** root cause fixed + deployed; she tested E2E and confirmed both the
  delay-cancel and the Preview now work; explained the Stripe error is not a
  wizard bug.

---

## OPEN ITEMS (waiting on Stephen)
1. **Stuck-permit cleanup list** — Stephen to DB-query permits where
   `delayCancellationDate IS NOT NULL AND isCancelled = false`. Then cancel each
   via immediate `CancelPermit` (works even on the Stripe edge case) to stop any
   ongoing charges.
2. **Stripe root cause** — why some permits show Active while their Stripe
   subscription is already canceled, and whether more permits are affected.
