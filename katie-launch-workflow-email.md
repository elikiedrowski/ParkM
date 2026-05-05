# Email to Katie — Pre-Thursday Business Process Review

**Context:** Katie Schaeffer (VP of Ops, ParkM) emailed on 2026-05-05 proposing a guided-workflow automation for the property launch resident-letter process. This email previews the questions Eli will be asking during Thursday's business process review.

**To:** katie@parkm.com
**Subject:** Re: Resident communication automation — a few questions ahead of Thursday

---

Hi Katie,

Thanks for sending this over — I spent some time mapping it against what we've already built for the CSR widget and refund automation, and I think there's a real opportunity here. A good chunk of the underlying plumbing (guided steps, Zoho ↔ parkm.app data fusion, dynamic email generation, status writeback) is reusable, so we'd mostly be building the PM-facing piece and the bulk-send leg on top of foundations that are already in production.

Before Thursday, I wanted to share a handful of questions I'll be digging into during the business process review. No need to answer in advance — these are mostly so you (and Stephen, if helpful) can think about them ahead of the call:

**Today's process**
- Where exactly does the resident letter template live in Zoho today — KB article, ticket template, snippet, or attached to a record somewhere?
- Are launches tracked in Zoho Desk or Zoho CRM? Is there a Blueprint or custom module driving the workflow stages, or is it more informal?
- What does "launch complete" actually look like — a sign-up percentage, a date threshold, a coordinator marking it done?

**Property managers**
- Are PMs already users in parkm.app today? If so, can we lean on that for the "minimal friction" login, or were you imagining a magic-link flow?
- Where does PM contact info live — Zoho, parkm.app, or a spreadsheet somewhere? Source of truth matters for how we pre-fill things.

**Sending to residents**
- This is probably the biggest unknown for me: when the PM hits "Approve & Send," who is the audience? Does ParkM already have the resident roster at launch time, or does the PM provide it?
- Email only, or email + SMS?
- From a deliverability standpoint — should residents see the message coming from ParkM, or from the property/PM's domain? The latter is doable but adds setup overhead per property.

**ParkM API**
- I'd love to know from Stephen whether there are existing endpoints for property metadata, PM contacts, and resident rosters — or if those would be new on his side. That's a critical-path item for scoping.

**Scope alignment**
- You mentioned the work Patrick requested — would be great to get a quick read on that scope so we can sequence things sensibly and avoid stepping on each other.
- Is the vision a full launch-team rollout from day one, or do you want to pilot this with one coordinator first (similar to how we phased Sadie into the refund flow)?

Thursday still works on my end. I'll come prepared with a phased proposal we can react to live, and I'm happy to whiteboard the PM-side flow once we've nailed down the data model.

Talk soon,
Eli

---

## Internal notes (not in email)

**Deliberately omitted:**
- Full architectural breakdown — too much for an email; deliver as a doc after Thursday
- Compliance/legal questions (CAN-SPAM, on-behalf-of sending) — kept email business-process-focused
- Reminder cadence and audit trail questions — tactical, cover live

**Reusability assessment from repo survey (~40-50% plumbing reusable):**
- ✅ Wizard engine (`src/wizard/`, `src/services/wizard.py`) — context-agnostic, can take new intents
- ✅ ParkM client (`src/services/parkm_client.py`) — customer/permit/transaction lookups (no property/PM/resident endpoints yet)
- ✅ Zoho writeback (`src/api/zoho_client.py`, `src/services/tagger.py`) — generic PATCH; can write any custom field
- ✅ Email template generation (`src/templates/`, `src/services/refund_service.py` pattern)
- ❌ PM-facing surface — net-new (widget is CSR-only, runs in Zoho Desk iframe)
- ❌ Bulk send to residents — net-new pipeline (SMTP/SendGrid/Twilio)

**Critical-path unknowns:**
1. ParkM API gaps (Stephen dependency)
2. PM identity/auth model
3. Resident roster source of truth
4. Zoho Desk vs. CRM (different SDK if CRM)
5. Patrick's parallel work (resourcing/field-naming conflicts)
