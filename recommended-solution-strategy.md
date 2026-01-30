# Recommended Solution Strategy for ParkM

## Executive Summary: Development Timeline & Effort

| Priority | Focus Area | Hours | Timeline | Dependencies |
|----------|-----------|-------|----------|--------------|
| **1** | Email Classification & Auto-Tagging | 80-100 | 2-3 weeks | OpenAI API integration |
| **2** | In-Workflow Guidance System | 100-140 | 3-4 weeks | Priority 1 data |
| **3** | Refund Automation + ParkM.app API | 120-160 | 3-4 weeks | Priority 1 data |
| **4** | Unified Agent Desktop | 140-180 | 4-5 weeks | Priority 3 API |
| **5** | Progressive Automation (3 phases) | 160-200 | 5-6 weeks | Priorities 1-4 |

**Total Estimated Effort:** 600-780 hours (15-20 weeks)  
**Parallel Execution Possible:** Priorities 1-2 can overlap; 3 can run parallel

**Critical Path:** ParkM.app API integration (Priority 3) unlocks Priority 4  
**Quick Wins:** Priority 1 delivers immediate value

---

## Priority 1: Intelligent Email Triage & Classification System

**Estimated Effort:** 80-100 hours | **Timeline:** 2-3 weeks

**Problem it solves:** New CSRs struggling to understand what customers are asking for; 3-month training time; process inconsistencies; refund/cancellation requests require specific eligibility checks

**Solution:**
- Build an AI-powered email classifier that runs immediately upon email receipt in Zoho Desk
- Automatically tags emails with: intent (refund/cancellation/account update/inquiry), complexity level (simple/moderate/complex), language, urgency
- Extract key entities: move-out dates, license plates, charge amounts, dates (critical for 30-day refund window)
- Auto-detect missing information (license plate, bank statement) and flag for agent follow-up
- Routes emails to specialized queues based on classification:
  - **Accounting/Refunds Queue:** Refund requests with move-out date within 30-day window
  - **Quick Updates Queue:** Simple cancellations (no refund) or missing info requests
  - **Auto-Resolution Queue:** Status inquiries, simple questions
  - **Escalations Queue:** Complex issues, angry customers, legal threats
- Adds confidence scores to help agents understand email clarity

**Why this first:**
- Non-invasive - doesn't change CSR workflow, just enhances it
- Immediate value - reduces decision fatigue and routing errors
- Foundation for future automation - classification data informs what to automate next
- Low risk - no customer-facing automation yet
- Directly supports refund/cancellation process workflow (30-day window validation)

**Estimated impact:** 30-40% reduction in training time; 50% reduction in escalations from misrouted tickets; 70% faster routing of refund-eligible requests to accounting

---

## Priority 2: Dynamic In-Workflow Guidance System

**Estimated Effort:** 100-140 hours | **Timeline:** 3-4 weeks

**Problem it solves:** CSRs missing steps in refund/cancellation process; "nothing in the flow that reminds them right now"; inconsistent application of 30-day refund window; forgetting to update ticket status

**Solution:**
- **Contextual guidance overlay** within Zoho Desk based on ticket classification:
  - **Refund requests:** Step-by-step checklist from refund-cancellation-process.pdf:
    1. Search parkm.app by email
    2. Review Vehicles and Permits tab
    3. Check if permit already canceled
    4. Verify last transaction date in Payments and Transactions
    5. Validate move-out date within 30-day window
    6. Cancel permit (Actions → Cancel → Cancel Now → Send Email)
    7. Submit refund to accounting or send denial with T&C
  - **Missing info requests:** Template for requesting license plate + bank statement screenshot
  - **Account updates:** Validation prompts before sending response
- **Smart forms** (can be implemented with basic Zoho features initially, enhanced with API later)
- **Real-time validation:**
  - "Did you verify the move-out date is within 30 days?"
  - "Did you cancel the permit in parkm.app before closing?"
  - "Did you update the ticket status to 'Waiting on Accounting'?"
- **Knowledge base snippets** appear inline based on ticket context

**Technical Dependencies:**
- Priority 1 classification data
- Zoho Desk extension/widget development
- Custom UI components in ticket view

**Why second:**
- Directly addresses Katie's acute pain point about missing steps
- Can start with Zoho's built-in workflow features before API integration
- Prevents errors before they happen vs. fixing them after
- Reduces cognitive load on part-time workers
- Standardizes application of refund eligibility rules
- Creates process compliance data to identify automation candidates
- Lower technical complexity than full API integration

**Estimated impact:** 60-70% reduction in training time; 40% reduction in escalations; 25% faster ticket resolution; 90% reduction in missed process steps

---

## Priority 3: Refund Process Automation & Validation

**Estimated Effort:** 120-160 hours | **Timeline:** 3-4 weeks

**Problem it solves:** 20% of customers request refunds; manual eligibility checking; accounting handoff delays; CSR confusion on 30-day refund window; high-volume repetitive workflow

**Solution:**
- **ParkM.app API Integration** (critical foundation):
  - Build authenticated API client for parkm.app system
  - Implement endpoints for:
    * Customer account lookup by email
    * Vehicles and Permits data retrieval
    * Payments and Transactions history access
    * Last charge date and amount extraction
    * Permit status checking (active/canceled)
    * Permit cancellation automation (Actions → Cancel → Cancel Now → Send Email)
  - Handle authentication, rate limiting, and error cases
  - Cache frequently accessed data to minimize API calls
- **Automated eligibility validation** based on refund-cancellation-process.pdf workflow:
  - Extract move-out date from email (via Priority 1 classifier)
  - Query parkm.app API for last charge date
  - Calculate if within 30-day refund window
  - Flag permit cancellation status (already canceled vs. needs cancellation)
  - Detect missing information (license plate not in system, no payment history)
- **Auto-generated refund submission emails** to accounting@parkm.com with:
  - Resident email (from parkm.app account data)
  - Refund amount (from last transaction via API)
  - Reason for refund (move-out date + charge date)
  - Permit details (license plate, community name)
- **Smart templates** for common scenarios:
  - Refund approved (auto-populated with 5-day timeline)
  - Refund denied (with Terms & Conditions attachment)
  - Missing information (license plate or bank statement request)
- **Accounting workflow integration:**
  - Update ticket status to "Waiting on Accounting" automatically
  - Reopen ticket when accounting replies
  - Track refund processing time and volume

**Technical Dependencies:**
- Priority 1 classification data (move-out dates, refund intent detection)
- ParkM.app API access and documentation
- OAuth or API key authentication setup
- Test environment for parkm.app integration

**Why third:**
- Requires significant external API integration work
- Directly addresses 20% of all support volume (refund requests)
- Eliminates manual date math and eligibility confusion
- Reduces accounting back-and-forth delays
- Leverages Priority 1 classification data (move-out dates, intents)
- High ROI - impacts both CSR efficiency and customer satisfaction
- Enables enhanced Priority 2 guidance with real parkm.app data

**Estimated impact:** 60-80% time savings on refund request processing; 90% reduction in eligibility errors; 40% faster refund cycle time

---

## Priority 4: Unified Agent Desktop

**Estimated Effort:** 140-180 hours | **Timeline:** 4-5 weeks

**Problem it solves:** Context switching between Zoho Desk and parkm.app; inefficiency during refund/cancellation processing; data lookup delays; manual permit cancellation steps

**Solution:**
- **Custom Zoho Desk extension** that embeds parkm.app data directly in ticket view:
  - Customer account details (email, permit count, status)
  - Vehicles and Permits tab (license plates, active/canceled status)
  - Payments and Transactions tab (last charge date, amount, refund history)
  - Move-out date and refund eligibility indicator (30-day window calculation)
- **Bi-directional API integration** with parkm.app (read and write operations)
- **Single-screen workflow:** ticket on left, customer permit data on right
- **One-click actions** without leaving Zoho:
  - Cancel permit (executes: Actions → Cancel → Cancel Now → Send Email)
  - Submit refund to accounting (auto-generates email with resident email + amount + reason)
  - Reverse charge (for accounting users)
  - Update vehicle information
- **Status automation:** Auto-update ticket status based on action (e.g., "Waiting on Accounting" after refund submission)

**Technical Dependencies:**
- Priority 3 parkm.app API integration (must be complete)
- Zoho Desk Extension SDK/Widget framework
- parkm.app write API endpoints (permit cancellation, vehicle updates)

**Why fourth:**
- Technical dependency - requires parkm.app API integration work (Priority 3)
- Significant efficiency gains once implemented (eliminates app switching)
- Enables faster execution of refund/cancellation workflow
- Improves CSR satisfaction and retention
- Foundation for Priority 5 automation

**Estimated impact:** 35-40% faster ticket resolution; 50% reduction in context-switching delays; improved CSR satisfaction; enables one-click refund processing

---

## Priority 5: Progressive Automation for High-Volume Simple Cases

**Estimated Effort:** 160-200 hours | **Timeline:** 5-6 weeks (phased rollout)

**Problem it solves:** Simple account updates and refund requests; scaling challenges; repetitive refund/cancellation workflow; CSR time spent on straightforward cases

**Solution:**

**Phase 1: Simple cancellation requests** (no refund, customer already moved out) - 60 hours | 2 weeks
- AI detects "just cancel my permit" intents
- Validates account found in parkm.app via API
- Auto-cancels permit if already past move-out date and no refund mentioned
- Sends confirmation email to customer
- CSR reviews in batch daily for quality assurance

**Phase 2: Vehicle updates** (vehicle changes where there's only one permit) - 50 hours | 1.5 weeks
- AI validates request clarity and completeness (license plate clearly stated)
- Auto-updates permit in parkm.app via API if unambiguous
- Sends confirmation email to customer
- Human review for ambiguous cases

**Phase 3: Straightforward refund requests** (single permit, within 30-day window, already canceled) - 50 hours | 1.5 weeks
- AI validates all eligibility criteria automatically via parkm.app API:
  - Move-out date extracted and within 30 days of last charge
  - Permit already canceled or customer confirms cancellation intent
  - Single permit only (no multi-permit complexity)
  - No dispute or legal language detected
- Auto-generates refund submission to accounting with all required details
- Notifies customer that refund is being processed (5-day timeline)
- Tracks status and follows up automatically when accounting completes
- **Human approval still required for financial transactions** (accounting reviews before processing)

**Why this approach:**
- Handles real volume reduction (refunds = 20% of all tickets)
- Maintains quality and brand protection through human oversight
- Starts with lower-risk cancellations before financial transactions
- Uses data from earlier phases to identify best automation candidates
- Follows proven refund-cancellation-process.pdf workflow

**Estimated impact:** 25-35% reduction in CSR workload on simple tasks; 60-70% time savings on straightforward refund processing; supports 2x growth with same team size

---

## Implementation Phasing Recommendation

### Phase 1: Email Classification & Refund Intelligence
**Priorities:** 1 (Email Classification)

- Quick wins with immediate measurable impact
- Builds foundation for refund automation
- Reduces escalations and routing errors immediately
- Extracts critical data (move-out dates, 30-day window validation)

### Phase 2: Workflow Guidance & Process Compliance
**Priorities:** 2 (Workflow Guidance)

- Prevents missed steps in refund/cancellation process
- Reduces training time for new CSRs
- Standardizes application of business rules
- Creates compliance data for automation candidates
- Can start with Zoho native features before API work

### Phase 3: Refund Process Automation
**Priorities:** 3 (Refund Automation)

- Addresses 20% of all support volume
- Eliminates manual eligibility checking
- Accelerates accounting handoff
- High ROI and immediate time savings
- Requires ParkM.app API integration

### Phase 4: Unified Agent Desktop
**Priorities:** 4 (Unified Desktop)

- Streamline CSR workflow (eliminate app switching)
- Single-pane-of-glass experience
- One-click permit cancellation and refund submission
- Foundation for full automation

### Phase 5: Progressive Automation
**Priorities:** 5 (Progressive Automation)

- Start with simple cancellations (no refund)
- Expand to vehicle updates
- Finally automate straightforward refunds (with accounting approval)
- Continuously improve based on data and feedback

---

## Why NOT Start with Full Refund Automation

1. **Complexity:** Multi-step approval process per refund-cancellation-process.pdf (account lookup, permit check, 30-day validation, accounting handoff, status tracking)
2. **Risk:** Even at $10/permit, errors damage brand reputation and customer trust
3. **Prerequisites:** Need classification and workflow systems first to:
   - Extract move-out dates reliably
   - Validate 30-day refund window accurately
   - Detect edge cases (multiple permits, disputes, already-canceled permits)
   - Gather data on automation candidates
4. **Better ROI:** Start with intelligence/validation layer (Priorities 1-2) to assist CSRs, then move to full automation (Priority 5) once proven
5. **Human oversight:** Financial transactions require accounting approval - automation should streamline submission, not bypass approval

---

## Key Success Metrics to Track

- Time to resolution per ticket type
- Escalation rate by CSR and by ticket type
- Training time for new CSRs to independence
- Customer satisfaction scores
- CSR confidence scores by ticket type
- Automation accuracy rates
- Volume handled per CSR (capacity metric)


