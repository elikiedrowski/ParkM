# Session Handoff — Refund Wizard Fee Fixes (2026-06-10)

Portable record of the refund-amount fee work so it can be picked up on another
computer. Captures the problem, the fix, verification, commits, and open items.

---

## 1. The problem (Sadie's pre-go-live feedback)

The refund wizard was populating the **refund amount as the permit's base price
only**, dropping any fees. Accounting therefore received a short amount.

Concrete example she sent:
- **Ticket #98779** ("TEST - wrong permit")
- Account: `sadiebrad@2email.com`
- Permit **R000017**, price **$10**, CC surcharge **$0.44**
- Correct total refund should be **$10.44** — wizard showed **$10.00**

Sadie's full fee policy (the rules we had to honor):

| Fee | Rule |
| --- | --- |
| **Credit Card Surcharge** (4.4% of permit cost) | Refund it (it's part of the purchase) |
| **Convenience Fee** (Texas only, 4.4%, replaces CC fee) | Refund it |
| **ACH Fee** ($15–25 bounced-payment charge) | Do **NOT** refund |
| **Park Guard** | Refundable, but **NOT** the 1st payment / first month |

---

## 2. What we implemented

All changes are **server-side** in `src/services/refund_service.py`. No widget /
front-end change, so **no new widget zip and no re-install needed** — the widget
just displays `eligibility.refund_amount` from the backend
(`widget/app/js/refund-panel.js:884`).

### a) Refund amount = actual amount charged (incl. surcharge / convenience fee)
The refund amount now comes from the **most recent successful Stripe charge**
(`Permits/GetAllPaymentsForPermit`), not the permit's configured price. The Stripe
charge total already includes the CC surcharge / Texas convenience fee (ParkM bills
permit price + fee as one charge), so they're captured automatically.

- `_payment_window_summary(...)` now returns a 3-tuple:
  `(latest_date, total_paid_within_window, latest_charge_amount)`.
- `latest_charge_amount` is stored on each permit as `last_charge_amount` in both
  `_enrich_permits_with_payment_totals` (active/scheduled) and
  `_get_inactive_permits` (cancelled/expired).
- `evaluate_refund_eligibility` uses `last_charge_amount` as the refund amount when
  it's > 0, falling back to `recurring_price` → `permit_price` → `total_amount`
  when there's no charge data.

### b) ACH bounce fees — excluded automatically
ACH bounce fees are separate balance charges, **not** part of the permit payment
feed, so they never enter the refund amount. No extra code required.

### c) Park Guard first month — blocked (added by follow-up commit)
A guard in `evaluate_refund_eligibility` (placed after the guest check, before the
no-charge guard): if the permit's type/name/community contains "park guard" AND its
`effective_date` is within the 30-day window, it returns **not eligible**
("Park Guard first payment / first month is not eligible for refund"). Park Guard
charges after the first month stay eligible under the normal rules.

> **Heuristic note:** "first month" is approximated as `effective_date ≤ 30 days
> ago`. Since ParkM's `effectiveDate` is the original signup date, this correctly
> blocks brand-new Park Guard accounts and allows established ones — but it's a
> calendar-day proxy, not a literal first-billing-cycle check. Revisit if Park
> Guard billing cycles aren't ~monthly.

---

## 3. Verification against the REAL production record

Drove `ParkMClient` + `RefundService` directly against the live ParkM API
(`https://api.parkm.app`) for permit **R000017**:

- `GetAllPaymentsForPermit` returned: `amount = 10.44`
  (`pi_3Tc5atDONdlsjp2O2fGW3WJp`, dated 2026-05-28, "Kaitlyn's Magic Carpet - Open
  Lot - R000017 - CO-SADIE124").
- End-to-end `process_refund_request(...)` → `refund_amount = 10.44`, and the
  generated **accounting email "Refund Amount" line now reads `$10.44`** (was
  `$10.00`).

### How to re-verify against prod records (from another machine)
Prod ParkM creds live in Railway (project **ParkM_Production** must be linked):
```
railway variables --kv | grep PARKM_API_PASSWORD
```
- URL: `https://api.parkm.app`  ·  User: `eli@thecrmwizards.com`  ·  Tenant: `0`
- Set those as `PARKM_API_URL` / `PARKM_API_USERNAME` / `PARKM_API_PASSWORD` /
  `PARKM_API_TENANT_ID` env vars and instantiate `RefundService()` to drive lookups.

---

## 4. Tests

`tests/test_refund_inactive_permits.py` — **12 passed** in both repos. New cases:
- `test_refund_amount_uses_charged_total_including_surcharge` ($10 base + $0.44 →
  refund $10.44).
- `test_refund_amount_falls_back_to_base_price_without_charge_data`.
- `test_park_guard_first_month_is_not_refundable`.
- `test_park_guard_after_first_month_can_be_refunded`.

> Pre-existing failures in `tests/test_wizard.py` and
> `tests/test_classifier_routing.py` are **unrelated** (stale from the 51-tag
> refactor) — confirmed by stashing the refund change; they were failing before.

---

## 5. Commits & deploy state

Both repos are independent (changes do not auto-sync; backport by hand — cherry-pick
often conflicts because the folders drifted; the **prod folder leads** on refund
code).

**Production** — folder `/home/elikiedrowski12/ParmM_Zoho`, remote
`github.com/elikiedrowski/ParkM.git`:
- `bb5fcfb` Include credit-card surcharge/convenience fee in refund amount
- `63fcca3` Block Park Guard first-month refunds
- Pushed to `master`; Railway (**ParkM_Production**,
  `parkm-production-7e56.up.railway.app`) auto-deployed on push.

**Sandbox** — folder `/home/elikiedrowski12/ParkM_Zoho_Sandbox`, remote
`github.com/elikiedrowski/ParkM_Sandbox.git`:
- `5cd7091` Include credit-card surcharge/convenience fee in refund amount
- `17ffd8c` Block Park Guard first-month refunds
- Pushed to `master`.

No `widget/` files changed in any of these → **installed widget zip is unchanged**.

---

## 6. Draft email to Sadie (not yet sent)

> **Subject:** Refund wizard — fees now included (surcharge, convenience, ACH, Park Guard)
>
> Hi Sadie,
>
> Thank you for the detailed fee breakdown — that was exactly what we needed. All
> four rules are now handled in the refund wizard, and the changes are live in both
> sandbox and production:
>
> - **Credit card surcharge & Texas convenience fee — now included.** The refund
>   amount now pulls the *actual total charged to the card* rather than just the
>   permit's base price, so the 4.4% fee is captured automatically. Your example
>   (ticket #98779, permit R000017) now correctly shows **$10.44** instead of $10.00.
> - **ACH bounce fees — excluded.** These are billed separately from the permit
>   payment, so they're never pulled into the refund amount.
> - **Park Guard — first payment / first month is now blocked** from refund
>   eligibility. Park Guard charges after the first month remain refundable under the
>   normal rules.
>
> I verified the surcharge fix against the real production record for R000017 — the
> payment feed returned $10.44 and the accounting email now reflects that exact
> amount.
>
> Whenever you have a moment, feel free to re-run a couple of test refunds (including
> a Park Guard one if handy) to confirm everything looks right before we go live with
> the CSRs. Let me know if you spot anything off.
>
> Thanks again,
> Eli

---

## 7. Open items / next steps

- [ ] **Send the email** to Sadie (decide whether to CC Katie). Not yet sent.
- [ ] Clarify the **"5.2 & 5.3"** reference from the initial request — was this email
      meant to be framed around Phases 5.2/5.3 automation, or is the refund-fee email
      separate? (Sandbox has Phase 5.2 dedup + Phase 5.3 auto-submit scaffold commits.)
- [ ] Optional: revisit the Park Guard "first month" heuristic (§2c note) if billing
      cycles aren't ~monthly.
- [ ] Have Sadie re-test refunds in the widget before CSR go-live.
