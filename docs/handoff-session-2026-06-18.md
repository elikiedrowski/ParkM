# Session Handoff — 2026-06-18 (reversed-charge eligibility scoped; #4 still open)

Portable record so this can be resumed on another computer. This session
**investigated and scoped** two items from the prior 2026-06-12 handoff; **no
production code changed** this session. All findings below are verified against
live prod API + Railway, not assumed.

Repos & deploy targets (unchanged):
- **Prod:** `github.com/elikiedrowski/ParkM` (folder `~/ParmM_Zoho`, remote `origin`)
  → Railway project **ParkM_Production** (`parkm-production-7e56.up.railway.app`),
  auto-deploys on push to `master`.
- **Sandbox:** the `sandbox` remote here is a **local folder** clone
  (`/home/elikiedrowski12/ParkM_Zoho_Sandbox`), NOT GitHub. Phase 5 dev lives in
  a separate clone/VS Code window.

**Git state at session end:** prod `origin/master` HEAD = `1f475cf`, local HEAD
matches it exactly (0 ahead / 0 behind). Prod Railway is running the June-12
deploy `e21fbca2` = HEAD. Nothing stranded; nothing to pull.

---

## Issue A — Reversed/refunded-charge eligibility (NOW SCOPED, blocked on Stephen)

**Origin:** ticket **#102525**, permit **R000018**, test acct
`Sadiebrad@2email.com`. After last week's reactivation fix, Eli noticed
R000018's last charge shows **Reversed** in Stripe (already refunded) yet the
wizard still marks the permit **eligible** → double-refund risk. Eli asked Sadie
whether already-refunded charges should be excluded.

**Sadie's decision (email, ~June 15/16):** YES — exclude already-reversed/
refunded charges from eligibility. AND don't just say "Not Eligible": show an
explicit message paralleling the "X days since last charge" line, e.g.
**"Already refunded 4 days ago — check with accounting."**

**THE BLOCKER — confirmed against LIVE PROD (June 16):** I dumped R000018's real
charge feed. R000018 = permit **`596bb305-72b9-4790-b9b4-1f84a4d9f941`** (Open
Lot $10 "grandfathered - CO-EPVS85"; it's the ONLY one of Sadie's 10 permits
with payments — the rest return `[]`). `Permits/GetAllPaymentsForPermit` returns
entries of **exactly** `{ id (pi_… Stripe intent), created, description, amount }`
and nothing else — **no status, no `refunded`/`amountRefunded`, no negative
reversal entry.** A reversed charge is byte-for-byte identical to a normal one in
our feed. `GetPermitForEdit` has no refund sub-object; `GetAllTransactions`
returns `[]`. **So we genuinely cannot detect a reversal with current API
access.** (Data-churn caveat: `GetCustomerFromEmail` for this test acct now
returns a different customer id than June 12, and permit `name` comes back empty
via the API — known prod test-data quirk; does not change the structural
conclusion.)

**GPT cross-review (this session) — all three code refs verified accurate:**
- `src/services/refund_service.py:535` — counts any payment whose status is not
  in `_NON_CHARGE_STATUSES` (failed/canceled/requires_*) as a real charge. A
  `refunded`/`reversed` status would still read as refundable. NOTE: prod never
  sends a status at all, so this filter is **dormant in prod today** — adding
  "refunded"/"reversed" to the set is correct + harmless but does nothing until
  ParkM populates the field.
- `src/services/parkm_client.py:281` — docstring confirms the 4-field feed.
- `widget/app/js/refund-panel.js:895/897` — shows ONE generic hint ("Inform
  customer they do not qualify. Send Terms & Conditions.") for EVERY ineligible
  result. Needs a dedicated branch for the already-refunded state.
- Backend already returns `{ eligible, reason, days_since_charge, ... }` with
  multiple distinct reasons; widget already renders `elig.reason` (refund-panel.js:883)
  and `days_since_charge` (885). So Sadie's message slots into the existing
  pattern cleanly.
- `python3 -m pytest tests/test_refund_inactive_permits.py -q` → **16 passed**
  (this machine HAS pytest/httpx, contrary to the June-12 doc's note about the
  other computer).

**THE BUILD (once Stephen gives us the refund signal — do NOT build before):**
1. `_payment_window_summary` (refund_service.py ~531): detect a fully-reversed
   latest charge; carry a `refunded_date`.
2. `evaluate_refund_eligibility`: new state → `eligible: False`, reason
   `"Already refunded N days ago — check with accounting"`.
3. Widget (refund-panel.js ~895): branch on that reason instead of the generic
   Terms hint.
Then sandbox → prod, run tests.

---

## Issue B — Delay-cancel Stripe-500 root cause (#4) — STILL OPEN, NOT fixed

Eli wondered if #4 (the state-dependent Stripe "canceled subscription can only
update…" error on delay-cancel) had been fixed on a different thread.
**VERIFIED it was NOT:** no root-cause code fix exists in any branch; the only #4
code change ever shipped is the **neutral CSR message** (`_friendly_cancel_error`,
prod `2cbdebf`). Prod Railway = HEAD `e21fbca2`/`1f475cf`. Recent prod logs show
no current Stripe delay-cancel errors, and the #102166 account (OP1000168,
ethan.ferfie@yahoo.com) now shows healthy fired delay-cancels (isCancelled=true +
delayCancellationDate + expiration moved) — symptom quiet, but that is **not** a
fix. **Eli confirmed it was not addressed/resolved.** Still awaiting Stephen on:
internal Stripe call ordering in the delay-cancel path; what differs between subs
that schedule cleanly vs error; Testing-env repro permits; and the stuck-permit
DB-query list (`delayCancellationDate IS NOT NULL AND isCancelled=false`).
Loose end: widget still appends redundant "— try manually in ParkM" suffix
(refund-panel.js:1076) — trim on next widget rebuild.

---

## NEXT ACTIONS (in order)

1. **SEND Email 1 → Stephen** (the unblocker for Issue A). Ask: is there a ParkM
   or underlying-Stripe field/endpoint that tells us a payment intent was
   refunded/reversed (a `status`/`refunded`/`amountRefunded` on the intent, or a
   refunds endpoint), or can a refund flag/amount be added to
   `GetAllPaymentsForPermit`? Evidence to cite: R000018 / permit
   `596bb305-72b9-4790-b9b4-1f84a4d9f941` shows Reversed in Stripe but identical
   in our feed. **(Drafted, not yet sent — full text in session transcript.)**
2. **SEND Email 2 → Sadie (cc Katie):** confirm we'll build exactly what she
   asked (exclude refunded charges + "Already refunded N days ago — check with
   accounting"); be upfront it depends on ParkM exposing refund data, which we're
   requesting from Stephen; reactivation fix from last week still live & working.
   **(Drafted, not yet sent — full text in session transcript.)**
3. **When Stephen replies** with the refund signal → do THE BUILD above
   (sandbox → prod, run tests).
4. **Watch Stephen** on the separate Issue B / delay-cancel root cause.

## DO-NOT list
- Do NOT implement reversal-detection before Stephen confirms the data source —
  it would be unverifiable guessing (same trap the delay-cancel work warned of).
- Do NOT assume #4 is fixed — it is not.
