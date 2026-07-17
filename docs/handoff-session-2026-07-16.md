# Session Handoff — 2026-07-16/17 (Sadie's renewal-date question; joint email to Sadie + Stephen)

Portable record so this can be resumed on another computer. **No code changed
this session** — analysis, verification, and a client email only.

## Machine catch-up (this box was behind)
- Prod repo fast-forwarded 6 commits to `a3ef761` (now = origin/master HEAD).
- Sandbox clone (`~/ParkM_Zoho_Sandbox`) fast-forwarded 4 commits to `6e8a0f9`
  (includes `8e3fe09`, the sandbox port of the nextRecurringDate fix).
- Prod backend verified healthy via `/health` (zoho connected, classifier ready).
- **Railway CLI auth is expired on this machine** — needs interactive
  `railway login` in a real terminal before any Railway/ParkM-creds work here.
  Fallback: `.env.prod` has working `PARKM_API_*` creds.
- Gmail MCP on this machine = personal account, NOT eli@thecrmwizards.com —
  cannot read/send CRM Wizards mail from here.

## The question (Sadie, July 14, Phase 5 thread, w/ screenshot)
After confirming the #110449 fixes work, Sadie asked: *"We need a way to
clear/delete the next renewal date so the resident is NOT charged. If I
remember correctly, we already had this in place. I don't remember switching it
to this new 'warning' message instead?"* Screenshot: permit renews Aug 8,
cancel scheduled Aug 14 → one more charge.

## Analysis (verified against repo history)
- She remembers correctly. The editable "Next recurring date" field + Clear
  button was **deliberately removed** in `187b24a` (committed June 25, deployed
  June 26) as part of the #5685 root-cause fix — clearing `nextRecurringDate`
  in the SAME `CreateOrEdit` as the cancellation is what tore down Stripe subs.
  The warning banner (refund-panel.js ~1242) replaced it.
- **Confirmed unsafe:** combined update (clear + cancel in one request).
- **Unverified (NOT proven either way):** a standalone clear in its own
  request; whether .APP's "Actions → Edit → Delete Next Recurring Date" is that
  same operation; whether clearing the date actually prevents the Stripe
  charge at all (could be display-only); clearing after a cancel is already
  scheduled.
- Phase 5.1 implication (parked, not raised with Sadie): auto delay-cancels up
  to 30 days out hit the same renewal-before-cancel window; whatever mechanism
  Stephen blesses should be mirrored there.

## Action taken — joint email to Sadie + Stephen (finalized July 16)
Iterated with Eli + a GPT cross-review; final version is precise about what is
confirmed vs unverified. Key content:
- Sadie: control removed intentionally as part of June 25–26 fix; gap is real;
  we will NOT restore the old combined-update control; awaiting ParkM's
  supported billing-safe method before deciding the wizard approach.
- Interim CSR guidance: schedule the cancel BEFORE the displayed renewal date
  (when resident agrees coverage ends earlier). Hold off on manual .APP
  renewal-date clears after a cancel is scheduled until Stephen confirms.
- Questions for Stephen (verbatim, these gate the rebuild):
  1. Is there a supported, billing-safe way to prevent the next renewal charge
     for a permit with a future scheduled cancellation?
  2. Is a standalone operation that changes only nextRecurringDate (no
     cancellation fields in the same request) safe for the Stripe subscription?
  3. Is that standalone operation what .APP performs through Actions → Edit →
     Delete Next Recurring Date? Does deleting the date actually prevent the
     upcoming charge, or only change what is displayed?
  4. If the supported sequence is clear-first then schedule-cancel as two
     separate operations, is that sequence safe for the Stripe subscription?
  5. For a permit that already has a scheduled (unfired) cancellation, is there
     a supported way to suppress the intervening renewal charge without
     disrupting the cancellation or Stripe subscription?
- Test permits: per Eli, **Sadie has test permits** — the earlier ask for
  Source Logic Testing-env permits was dropped from the email. CAUTION: her
  known test permits (e.g. R000020 / Sadiebrad@2email.com) are in PROD with
  real Stripe subs — time any validation so a misfire is caught + reactivated
  before a billing event.

## NEXT ACTIONS
1. Await Stephen's answers to Q1–Q5.
2. Validate the blessed flow on a test permit (see caution above).
3. Then design the wizard piece (likely a checkbox in Schedule Cancellation
   running the supported sequence) + mirror the decision in Phase 5.1.
4. Update `docs/handoff-delayed-cancellation-fix.md` open items as answers land.

## DO-NOT list
- Do NOT re-add the nextRecurringDate clear inside the cancel call (#5685).
- Do NOT ship a standalone clear before Stephen confirms it is supported AND a
  test permit validates it actually blocks the charge.
- Do NOT present the standalone clear as known-unsafe either — it is unverified.
