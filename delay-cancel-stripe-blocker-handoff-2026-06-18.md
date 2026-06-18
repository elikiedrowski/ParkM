# Session Handoff — Delay-Cancel Stripe Blocker & Phase 5 Hold (2026-06-18)

Portable record so this can be picked up on another computer. Captures the
production bug blocking the project, who we're waiting on, the emails sent, and
the exact next steps.

---

## 1. The headline — what's blocking everything

**Sadie has formally paused Phase 5 rollout** until the delay-cancel Stripe
failure from Phases 1–3 is fixed and stable in production. Her words (email
2026-06-17, 4:36 PM, to Eli + Katie):

> "I want to hold off here — at least until the following (from our emails on
> June 10th) is fixed and working well from the previous phases... It's
> important to me that all of phases 1-3 are running smoothly without any bumps
> in the road before we keep moving forward with the next few phases."

So: Phase 5.2 and 5.3 are **built and validated in sandbox** but **parked** —
we do not advance to 5.4 or push 5.2/5.3 to production until the delay-cancel
bug is resolved.

---

## 2. The production bug (delay-cancel cancels Stripe sub, then fails)

**Symptom:** A CSR uses the wizard's delay-cancel (schedule a permit to cancel
on a future date). It errors with:

> "A canceled subscription can only update its cancellation_details and metadata"

The same error then appears if they try the delay-cancel manually in **.APP**.
CSRs have been working around it by **canceling immediately** or by **manually
setting the expiration date** in .APP.

**Diagnosis (well-supported):** The delayed-cancel path appears to **cancel the
Stripe subscription _before_ scheduling the cancellation**, and does **not
unwind** that cancellation when the overall operation fails. Net result: the
subscription is dead, the permit's delay fields don't persist, and any retry
hits the "already canceled" error.

**Smoking gun — permit MOL000621:**
- Account: `idalialopez6945@icloud.com`, Ticket **#102434**
- Our backend log shows the failing call at **2026-06-10 5:57:50 AM MDT
  (11:57:50 UTC)**.
- Stripe shows the subscription **Ended at 5:57 AM** — the same minute.
- Sadie confirmed in Stripe that the subscription was **active before** the
  wizard attempt; it died on the failed attempt.
- MOL000621 ended up **Active with no delay fields persisted**.

**It's not all recurring permits — that's the key clue.** From 60 days of logs
(all paid recurring permits):

| Permit | Outcome |
| --- | --- |
| R000679 | Scheduled OK — sub Active, delayCancellationDate=2026-06-16 |
| MO000337 | Scheduled OK — sub Trialing, delayCancellationDate=2026-06-16 |
| MOL000621 | FAILED — now Active, no delay fields persisted |
| SC1000281 | FAILED — but ended isCancelled=true + delayCancellationDate=2026-06-17 |
| RT000752 | FAILED |
| OG000601 | FAILED |

Last successful charges on the failures: RT000752 6/9, OG000601 6/10,
MOL000621 5/29, SC1000281 5/11 — so their subs were likely active going in.
Outcomes vary even within the failures, so the differentiator (billing state:
open/past-due invoice? proration? trialing vs active?) is still unconfirmed.

---

## 3. Root cause owner — we are WAITING ON STEPHEN

The fix hinges on where **ParkM talks to Stripe** in the delayed-cancel path —
that's Stephen's code (ParkM API), not ours. **Stephen has not responded** to
the substantive asks (Jun 9 and Jun 10 emails).

**Two specific things we need from Stephen** (re-asked in the 2026-06-18 nudge):

1. **Confirm the flow.** In the delayed-cancel path, does `CreateOrEdit` cancel
   the Stripe subscription *before* scheduling/updating it — and can that step
   leave the subscription canceled when the overall operation fails? Stripe
   event history for MOL000621 (~11:57:50 UTC 6/10), RT000752, and OG000601
   would confirm whether **our call** is what canceled them, and what differs
   between the subs that schedule fine (R000679/MO000337) and the ones that
   error.
2. **A safe way to reproduce.** A few **disposable test permits** in the sandbox
   Testing environment — paid recurring permits with active Stripe subs across
   a couple of billing states (one healthy active, one trialing like MO000337,
   and if he suspects it, one with an open/past-due invoice) — with our
   integration account (`eli@thecrmwizards.com`) able to delay-cancel and
   reactivate them repeatedly. Fall back to production if sandbox isn't possible.

Without #2 we **cannot reproduce the failure or validate a fix** without
touching real customers.

---

## 4. What WE already shipped on our side (interim mitigations)

These are in prod already — they reduce harm but do **not** fix the root cause
(which is in ParkM/Stephen's Stripe integration):

- **Neutralized the alarming error message** — commit `2cbdebf` ("Neutralize
  delay-cancel Stripe error message; correct handoff doc"). The wizard no longer
  claims the subscription was "already canceled" or tells CSRs to cancel
  immediately. A permit-level delayed cancellation should still be possible even
  with no active Stripe subscription.
- Related prior work: safety-net for delayed cancellations not firing (see memory
  `project_delayed_cancel_not_firing`) and the reactivation-as-last-charge refund
  fix (commit `ea679df`, ticket #102525/R000018).

**Interim safe path for CSRs:** manually set the permit's expiration date in
.APP (what Sadie's CSR did). Communicate this as the workaround until the root
cause is fixed.

---

## 5. Related earlier ticket — #102166 (same root cause)

- Account `ethan.ferfie@yahoo.com`, permit **OP1000168** ($10/mo, 1st Car Open
  Lot). Same error in both wizard AND .APP. This is the ticket that kicked off
  the Stephen thread (Jun 9). Same diagnosis as #102434.

---

## 6. Emails — current state of the threads

**Thread A — "Wizard error?" (Sadie → Eli/Katie, started Jun 9):**
- Jun 9: Sadie reports #102166 wizard error.
- Jun 9: Eli replies — not a wizard bug (same error in .APP), pings Stephen.
- Jun 10: Sadie reports a 2nd case, #102434 / MOL000621.
- Jun 10: Eli → Stephen with full production data + the two asks (flow + test
  records). **No reply from Stephen.**

**Thread B — "Phase 5 — two new stages validated in sandbox (5.2 + 5.3)":**
- Long thread refining 5.2 (missing-info auto-reply) and 5.3 (auto-submit
  refund-eligible cancellations) + the delay-cancel cap (now **30 days**, was 90;
  schedules for **5:00 PM property-local time**).
- Jun 17: Sadie's **hold** message (quoted in §1).

**2026-06-18 — Eli sent a gentle-nudge follow-up to Stephen, CC Katie + Sadie**,
re-asking the two items in §3. (This is the "I just sent the email to Stephen
and copied the ladies" action.)

**Reply to Sadie (drafted 2026-06-18, confirm sent):** agrees with the hold,
confirms Phases 1–3 come first, points to the Stephen email she was CC'd on,
restates the manual-expiration workaround as the interim safe path, promises to
update her + Katie the moment Stephen responds. **No date promised** — critical
path runs through Stephen.

---

## 7. Open items / next steps

- [ ] **Waiting on Stephen** — flow confirmation + disposable sandbox test
      permits. This is the critical-path blocker for the entire project.
- [ ] If a week passes with no Stephen reply (~Jun 25), **escalate**: add the
      project-level impact (Phase 5 paused) and push for a 15-min call; consider
      escalating through Katie.
- [ ] Once Stephen confirms the flow + provides test records: **reproduce the
      failure**, implement the unwind/ordering fix (cancel-after-schedule, or
      roll back the sub-cancel on failure), validate end-to-end in sandbox,
      then ship to prod.
- [ ] Confirm with Sadie that the **neutralized error message** (`2cbdebf`) is
      live so her CSRs no longer see the "cancel immediately" wording — a
      concrete win to hand her while the root cause waits on Stephen.
- [ ] **Phase 5.2 / 5.3 stay parked in sandbox** — do not advance to 5.4 or
      push 5.2/5.3 to prod until the delay-cancel bug is fixed and stable.

---

## 8. Quick reference

- Tickets: **#102434** (MOL000621 / idalialopez6945@icloud.com), **#102166**
  (OP1000168 / ethan.ferfie@yahoo.com).
- Delay-cancel scheduled for **5:00 PM property-local time**, cap **30 days**.
- Prod folder: `/home/elikiedrowski12/ParmM_Zoho` · remote `ParkM`
  (`github.com/elikiedrowski/ParkM.git`) · branch `master`.
- Sandbox folder: `/home/elikiedrowski12/ParkM_Zoho_Sandbox` · remote
  `ParkM_Sandbox`.
- Phase 5 code (5.2/5.3) lives in **sandbox**, validated, not in production.
