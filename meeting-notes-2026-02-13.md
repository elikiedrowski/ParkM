# ParkM & CRM Wizards - Project Kickoff Call

**Date:** February 13, 2026
**Participants:**
- **ParkM:** Katie Schaeffer (Operations Manager)
- **CRM Wizards:** Eli Kiedrowski
- **Optional (did not attend):** Chad Craven, Patrick Cameron, Lauren Kiedrowski

---

## Meeting Summary

### Purpose
Formal project kickoff to review the Statement of Work, confirm alignment on scope and priorities, and establish a weekly project cadence. A traditional sales-to-delivery handoff was unnecessary since both teams joined the initial discovery call together.

### Scope Confirmed: Priorities 1-3 Only

The project will focus exclusively on the first three priorities. Priorities 4 and 5 are shelved indefinitely.

| Priority | Focus | Notes |
|---|---|---|
| **1** | Email Classification & Auto-Tagging | Starting immediately — foundation for everything |
| **2** | In-Workflow Guidance System | Begins ~Week 2-3 |
| **3** | Refund Automation + ParkM.app API | Begins ~Week 3-4 |
| ~~4~~ | ~~Unified Agent Desktop~~ | Shelved |
| ~~5~~ | ~~Progressive Automation~~ | Shelved |

### Key Decisions Made

**1. Queue Routing — REMOVED FROM SCOPE**
Eli confirmed that automatic ticket routing to queues, previously discussed, has been eliminated from the project scope per ParkM's direction.

**2. Guided Workflow Coverage**
Katie raised the question of whether the Priority 2 guided workflow would cover all ticket intent types or just a subset. Eli confirmed the plan is one workflow per intent type (refund, vehicle update, permit inquiry, etc.). This does not need to be finalized now — will be shaped during weekly calls.

**3. CSR Feedback Mechanism — NEEDS FURTHER DISCUSSION**
Discussed building a mechanism for CSRs to correct misclassifications, which feeds back into LLM training. Katie is less concerned about misclassification itself and more about multi-intent emails and unclear requests. The mechanism design is not finalized — marked for future discussion.

**4. Phased / Iterative Approach Confirmed**
Katie confirmed alignment with the phased approach: start as an assist, gain confidence, then expand automation. The project is not locked in — both parties can adjust direction at any weekly call based on results.

**5. Server Ownership**
The production virtual server will be owned by ParkM. Setup will be coordinated with ParkM's **IT team** (not Stuart). IT contact to be provided by Katie when the time comes. IT team will not be on recurring weekly calls.

---

## Cadence & Communication

### Weekly Status Calls
- **Day:** Thursday
- **Time:** 2:00 PM Mountain / 3:00 PM Central / 1:00 PM Pacific
- **Duration:** 1 hour (can end early)
- **Format:** Demos, feedback, adjustments, deployment decisions
- **Invite sent to:** Katie Schaeffer (she distributes to her team)

### ParkM Weekly Call Attendees
| Name | Role | Attendance |
|---|---|---|
| Katie Schaeffer | Operations Manager | Required |
| Sy | (team member) | Standing invite |
| Cara | Arizona-based (support manager) | Standing invite |
| Stuart | Zoho Admin | As needed |
| Chad Craven | CEO | Optional |
| Patrick Cameron | Sales Consultant | Optional |

### First Weekly Call
**Thursday, February 19, 2026 — 2:00 PM Mountain**

---

## What Eli Needs from ParkM

At the time of the call, Eli stated he had everything he needed to begin technical work. Key contacts already established:
- Katie Schaeffer — primary project contact
- Stuart — Zoho environment (prior calls already had)
- Chad, Lauren, Patrick — context from discovery call

**Future asks (not yet needed):**
- IT team contact for server handoff
- Ticket export (100-200 production tickets) for LLM training in Phase 1.3

---

## Action Items

| Owner | Task | Timing |
|---|---|---|
| **Eli** | Begin technical setup — server, infrastructure, environment | Immediately |
| **Eli** | Continue building from POC — run production tickets through classifier | Week 1 |
| **Katie** | Forward weekly call invite to Sy, Cara; add Stuart as needed | This week |
| **Katie** | Provide IT team contact when server deployment is ready | Future |
| **Both** | First weekly status call | Thursday Feb 19 |

---

## Technical Notes

### Current POC Status (as of kickoff)
- Sandbox environment: working
- OAuth authentication: working
- GPT-4o classifier: 95% confidence on 8 test cases
- 10 custom fields: created and tested in Zoho sandbox
- FastAPI server + webhook endpoint: built, running locally
- Auto-tagging: end-to-end tested in sandbox
- All code committed to git (~30+ commits)

### Volume Confirmed
- 4,000–5,000 tickets/month (Katie corrected Eli's initial 1,000 estimate)
- Cost confirmed: ~$25–50/month for infrastructure + OpenAI at this volume

### What's Remaining for Priority 1 Launch
1. Production server provisioned and deployed
2. Custom fields created in production Zoho org
3. Webhook configured in Zoho Desk (production)
4. End-to-end integration test in production
5. 100-200 production tickets exported for LLM training/validation

---

## Notes & Observations

- Katie expressed confidence and enthusiasm: *"We're looking forward to it and excited what this can do for us"*
- Eli set the right tone — iterative, not locked in, always building forward
- The "no queues" decision was referenced by Eli as something already decided in a prior conversation; this confirms it applies to Phase 1.4 of the action plan
- The CSR feedback/correction mechanism (mentioned in the LLM improvement enhancement) should be revisited during Priority 2 design, as it's most relevant when the wizard is being built
