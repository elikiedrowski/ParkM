# ParkM Zoho Desk Automation - Priorities 1-3 Action Plan
**Comprehensive Development Roadmap**

## Project Status: APPROVED
**Client Decision:** Move forward with Priorities 1-3, hold Priorities 4-5  
**Total Timeline:** 6 weeks with overlapping phases  
**Team:** Eli Kiedrowski (Solution Architect), Nagy (Technical Architect)  
**Start Date:** Week of February 10, 2026  
**Client Contacts:** Katie Schaeffer (Primary), Chad (Executive Sponsor), Stuart (Zoho Admin)

---

## Overview: Three-Priority Roadmap

| Priority | Focus Area | Timeline | Dependencies | Key Deliverable |
|----------|-----------|----------|--------------|-----------------|
| **1** | Email Classification & Auto-Tagging | Week 1-3 | OpenAI API integration | Auto-classified tickets in real-time |
| **2** | In-Workflow Guidance System | Week 2-5 | Priority 1 data | CSR wizard with step-by-step checklists |
| **3** | Refund Automation + ParkM.app API | Week 3-6 | Priority 1 data + app API access | Automated refund eligibility validation |

**Total Duration:** 6 weeks with parallel execution starting Week 2  
**Critical Path:** Priority 1 → Priority 2 (week delay) → Priority 3 (week delay)

---

# PRIORITY 1: Email Classification & Auto-Tagging System

## Timeline: Week 1-3
**Goal:** Automatically classify and tag all incoming tickets using AI

## What's Already Built (POC Complete) ✅

### Technical Validation
- **Sandbox Environment:** Zoho Desk sandbox configured and tested
- **OAuth Authentication:** Working refresh token implementation in `src/api/zoho_client.py`
- **OpenAI Integration:** GPT-4o classifier operational with 95% confidence
- **FastAPI Server:** Running on localhost:8000
- **Custom Fields:** 10 fields created and tested in sandbox
- **Test Results:** 8 test tickets classified successfully with entity extraction

### Codebase Status
- `src/api/zoho_client.py` - OAuth client complete
- `src/services/classifier.py` - Email classification service
- `src/services/tagger.py` - Ticket tagging service
- `main.py` - FastAPI application
- All code committed to git (30+ commits)

---

## Phase 1.1: Production Setup (Week 1 Days 1-2)

### Server & Infrastructure Setup
**Owner:** Nagy

**Tasks:**
- [ ] Provision production virtual server (AWS/DigitalOcean)
  - Ubuntu 22.04 LTS
  - 2GB RAM minimum
  - Configure firewall rules (allow 443, 80, SSH)
  - Set up SSH key authentication
  - Estimated cost: $15-20/month

- [ ] Install production dependencies
  - Python 3.11
  - pip, virtualenv
  - nginx (reverse proxy)
  - certbot (SSL certificates)
  - systemd service configuration

- [ ] Configure production environment
  - Create `.env` file with production credentials
  - Set up log directory: `/var/log/parkm-classifier/`
  - Configure log rotation
  - Set up systemd service for auto-restart

### API Keys & Credentials
**Owner:** Eli

**Tasks:**
- [ ] Create production OpenAI API key
  - Sign up/login to OpenAI platform
  - Create new API key for ParkM production
  - Set usage limits ($50/month initially)
  - Add to billing alerts
  - Estimated cost: $10-20/month for 4-5K tickets

- [ ] Verify Zoho OAuth credentials
  - Confirm refresh token works in production
  - Test token refresh cycle
  - Document token refresh process

### Custom Fields in Production
**Owner:** Eli (with Stuart's assistance)

**Tasks:**
- [ ] Request production admin access from Stuart
  - Navigate: Zoho Desk → Setup → Users & Control
  - Need admin role temporarily

- [ ] Create 10 custom fields in production
  - Use checklist: `zoho-custom-fields-setup.md`
  - Fields to create:
    1. AI Intent (dropdown: refund_request, permit_cancellation, account_update, payment_issue, permit_inquiry, move_out, technical_issue, general_question, unclear)
    2. AI Complexity (dropdown: simple, moderate, complex)
    3. AI Language (dropdown: english, spanish, mixed, other)
    4. AI Urgency (dropdown: high, medium, low)
    5. AI Confidence (number: 0-100)
    6. Requires Refund (boolean)
    7. Requires Human Review (boolean)
    8. License Plate (text, max 20 chars)
    9. Move Out Date (date, YYYY-MM-DD)
    10. Routing Queue (text, max 50 chars)

- [ ] Verify API names in production
  - Navigate: Setup → Developer Space → APIs → Fields
  - Document actual API names (may differ from sandbox)
  - Update `src/services/tagger.py` with production field names

**Deliverable:** Production infrastructure ready for deployment

---

## Phase 1.2: Webhook Automation (Week 1 Days 3-5)

### Webhook Endpoint Development
**Owner:** Eli

**Tasks:**
- [ ] Implement webhook endpoint in `main.py`
  ```python
  @app.post("/webhooks/zoho/ticket-created")
  async def handle_ticket_created(request: Request):
      # Validate webhook signature
      # Parse ticket data
      # Queue for async classification
      # Return 200 immediately
  ```

- [ ] Add async classification queue
  - Use background tasks (FastAPI BackgroundTasks)
  - Log all webhook calls to `logs/webhook.log`
  - Handle errors gracefully (retry logic)

- [ ] Deploy to production server
  - Copy code to server
  - Install dependencies in virtualenv
  - Start systemd service
  - Verify service running

### Webhook Configuration in Zoho
**Owner:** Eli (with Stuart's assistance)

**Tasks:**
- [ ] Set up public URL for webhook
  - Option 1: Use server's public IP with nginx
  - Option 2: Use ngrok for initial testing
  - Get SSL certificate (Let's Encrypt)

- [ ] Configure webhook in Zoho Desk
  - Navigate: Setup → Developer Space → Webhooks
  - Click: + New Webhook
  - **Settings:**
    - Name: "AI Classification - Ticket Created"
    - Description: "Triggers AI classification when new ticket is created"
    - URL: `https://{server-url}/webhooks/zoho/ticket-created`
    - Method: POST
    - Event: Ticket Created
    - Department: All departments (or Testing only initially)
    - Format: JSON
    - Include: Ticket ID, Subject, Description, Email, Status

- [ ] Test webhook delivery
  - Create test ticket in production Zoho
  - Verify webhook fires (check server logs)
  - Verify classification runs
  - Verify custom fields populated
  - Check for any errors

**Deliverable:** Production system auto-classifying tickets in real-time

---

## Phase 1.3: Training & Validation (Week 2 Days 1-3)

### Data Collection & Analysis
**Owner:** Eli + Nagy

**Tasks:**
- [ ] Request production ticket export from Katie/Stuart
  - 100-200 recent tickets
  - Include variety: refunds, cancellations, updates, complaints, inquiries
  - Request both subject and full description
  - Request any existing categorization/tags

- [ ] Analyze ticket patterns
  - Identify common phrases for each intent type
  - Document customer language patterns:
    * Refund requests: "moved out", "cancel and refund", "charge me", "money back"
    * Cancellations: "cancel my permit", "no longer need", "stop charging"
    * Updates: "new license plate", "different car", "update vehicle"
    * Complaints: "angry", "terrible", "scam", "lawyer"
  - Note missing information scenarios
  - Identify ambiguous cases (multiple intents in one email)

### LLM Prompt Engineering
**Owner:** Eli

**Tasks:**
- [ ] Refine classification prompts in `src/services/classifier.py`
  - Add ParkM-specific context:
    * "ParkM is a parking permit management company"
    * "Customers purchase monthly permits for parking at apartment complexes"
    * "Common issues: refunds (30-day window), permit cancellations, vehicle updates"
  - Include examples of each intent type
  - Define edge case handling rules:
    * Multiple intents → classify as "complex", flag for human review
    * Angry tone → mark urgency as "high", flag for review
    * Spanish language → set language field, still classify intent
    * Missing info → extract what's available, note what's missing

- [ ] Update entity extraction patterns
  - License plate formats:
    * ABC-1234, ABC1234, ABC 1234
    * State prefix variations
  - Date extraction:
    * "moved out January 1st"
    * "leaving on 1/15/2026"
    * "last month"
  - Amount extraction:
    * "$50", "50 dollars", "fifty bucks"

### Test Suite Development
**Owner:** Nagy

**Tasks:**
- [ ] Create comprehensive test suite: `tests/classification_test_cases.json`
  - 20-30 test cases covering:
    * **Simple refund requests** (5 cases)
      - Clear move-out date mentioned
      - License plate provided
      - Polite tone
    * **Complex multi-issue tickets** (5 cases)
      - Multiple requests in one email
      - Unclear intent
      - Contradictory information
    * **Angry/urgent customers** (3 cases)
      - Legal threats
      - ALL CAPS
      - Profanity/complaints
    * **Spanish language emails** (3 cases)
      - Full Spanish
      - Spanglish (mixed)
      - Spanish name but English email
    * **Missing information scenarios** (3 cases)
      - No license plate
      - No move-out date
      - Vague request
    * **Vehicle updates** (2 cases)
    * **Permit cancellations** (2 cases)
    * **Technical issues** (2 cases)
    * **General questions** (2 cases)

- [ ] Document expected classifications
  - For each test case, define:
    * Expected intent
    * Expected complexity
    * Expected urgency
    * Expected confidence range
    * Expected entities extracted
    * Expected flags (refund, review)

### Validation & Tuning
**Owner:** Eli + Nagy

**Tasks:**
- [ ] Run test suite against classifier
  - Execute all test cases
  - Compare actual vs expected results
  - Calculate accuracy rate (target: >90%)
  - Document failures and edge cases

- [ ] Adjust confidence thresholds
  - Analyze confidence scores distribution
  - Set threshold for "requires human review" flag (default: <80%)
  - Tune urgency detection sensitivity
  - Validate refund flag accuracy

- [ ] Client review session
  - Schedule 1-hour meeting with Katie/Chad
  - Demo classification on 10-15 real production tickets
  - Walk through test suite results
  - Get feedback on intent categories
  - Discuss edge case handling
  - Adjust based on client input

**Deliverable:** Validated classifier with >90% accuracy on test suite

---

## Phase 1.4: Queue Routing & Launch (Week 2 Day 4 - Week 3)

### Queue Design & Configuration
**Owner:** Eli + Katie (collaborative)

**Tasks:**
- [ ] Design queue structure with client
  - **Queue 1: Accounting/Refunds**
    - Tickets with `requires_refund = true`
    - Move-out date within 30 days (if extracted)
    - High priority for accounting team
  - **Queue 2: Quick Updates**
    - Simple cancellations (`intent = permit_cancellation`, `requires_refund = false`)
    - Vehicle updates
    - Missing info requests
  - **Queue 3: Auto-Resolution** (future automation candidates)
    - Status inquiries
    - General questions with clear answers
    - Low complexity tickets
  - **Queue 4: Escalations**
    - `requires_human_review = true`
    - `urgency = high`
    - Complex multi-issue tickets
    - Angry customers

- [ ] Create queues in Zoho Desk
  - Navigate: Setup → Channels → Email → Departments
  - For each queue:
    * Create new view/queue
    * Set filter criteria based on custom fields
    * Assign CSRs to appropriate queues
    * Set queue permissions

### Routing Logic Implementation
**Owner:** Nagy

**Tasks:**
- [ ] Update `src/services/tagger.py` with routing rules
  ```python
  def determine_routing_queue(classification_result):
      if classification_result.requires_refund:
          return "Accounting/Refunds"
      elif classification_result.urgency == "high" or classification_result.requires_human_review:
          return "Escalations"
      elif classification_result.complexity == "simple":
          return "Quick Updates"
      else:
          return "Auto-Resolution"
  ```

- [ ] Create Zoho workflow rules for auto-routing
  - Navigate: Setup → Automation → Workflows
  - Create rule: "Route to Refunds Queue"
    * Trigger: When `cf_routing_queue` = "Accounting/Refunds"
    * Action: Move ticket to Refunds queue
  - Repeat for each queue
  - Test each workflow

### Monitoring & Documentation
**Owner:** Nagy (monitoring) + Eli (docs)

**Tasks:**
- [ ] Set up monitoring dashboard
  - Metrics to track:
    * Tickets classified per day
    * Average confidence scores by intent
    * Intent distribution (pie chart)
    * Queue routing breakdown
    * Error rate (failed classifications)
    * Processing time (webhook → classification complete)
  - Tools: Grafana + Prometheus or simple CSV logging

- [ ] Configure alerting
  - Email/Slack alerts on:
    * Classification errors (>5 per hour)
    * Server downtime
    * Low confidence spike (>20% below 80% confidence)
    * Webhook failures

- [ ] Create operational documentation
  - **Runbook:** `docs/priority-1-runbook.md`
    * How to restart service
    * How to check logs
    * How to update classification prompts
    * How to add new intent types
  - **Troubleshooting Guide:** Common issues and solutions
  - **API Documentation:** Webhook endpoint details

### Client Training & Launch
**Owner:** Eli

**Tasks:**
- [ ] Conduct CSR training session (1 hour)
  - Explain what's happening behind the scenes
  - Show custom fields (even if hidden from CSR view)
  - Demonstrate queue routing
  - Explain confidence scores and flags
  - Walk through a few classified tickets
  - Answer questions

- [ ] Production launch plan
  - **Soft Launch (Week 2 Day 5):**
    * Enable webhook for Testing department only
    * Monitor first 50 tickets closely
    * Fix any issues immediately
  - **Full Launch (Week 3 Day 1):**
    * Enable for all departments
    * Monitor for 48 hours intensively
    * Collect CSR feedback
  - **Post-Launch (Week 3 Days 2-5):**
    * Daily check-ins with Katie
    * Adjust based on feedback
    * Document edge cases

**Deliverable:** Fully automated classification system in production with queue routing

---

## Priority 1 Success Metrics

**Track Weekly:**
- Classification Accuracy: >90% (spot-check 20 tickets/week)
- Processing Time: <5 seconds (webhook → classification complete)
- Uptime: >99%
- Entity Extraction Accuracy: >85% (license plates, dates)
- CSR Feedback: Positive (gather in weekly calls)
- Error Rate: <1%

---

# PRIORITY 2: In-Workflow Guidance System

## Timeline: Week 2-5 (overlapping with Priority 1)
**Goal:** Provide CSRs with step-by-step guidance based on ticket classification

## Dependencies
- ✅ Priority 1 classification data available
- ✅ Custom fields populated in real-time
- ✅ Confidence scores validated

---

## Phase 2.1: UI/UX Design (Week 2 Days 3-5)

### Wizard Design
**Owner:** Eli

**Tasks:**
- [ ] Design wizard user flow
  - **Trigger:** CSR opens ticket that's been classified
  - **Display:** Modal or sidebar widget in Zoho Desk
  - **Content:** Dynamic checklist based on ticket intent

- [ ] Create wizard mockups for each intent type
  - **Refund Request Wizard:**
    ```
    ✓ Ticket classified as: Refund Request
    Confidence: 95%
    
    Follow these steps:
    □ 1. Search parkm.app by customer email
    □ 2. Review Vehicles and Permits tab
    □ 3. Check if permit is already canceled
    □ 4. Verify last transaction date in Payments tab
    □ 5. Validate move-out date within 30-day window
       → Move-out date: [AI extracted date or "Not found - ask customer"]
    □ 6. If eligible, cancel permit in parkm.app
       → Actions → Cancel → Cancel Now → Send Email
    □ 7. Submit refund to accounting OR send denial
    □ 8. Update ticket status
    
    ⚠️ Missing Information:
    - License plate not found in email
    → Use template: "Request License Plate"
    ```
  
  - **Permit Cancellation Wizard:**
    ```
    ✓ Ticket classified as: Permit Cancellation (No Refund)
    Confidence: 92%
    
    Follow these steps:
    □ 1. Search parkm.app by customer email
    □ 2. Confirm customer does NOT want refund
    □ 3. Cancel permit: Actions → Cancel → Cancel Now
    □ 4. Send confirmation email to customer
    □ 5. Close ticket
    ```
  
  - **Vehicle Update Wizard:**
    ```
    ✓ Ticket classified as: Vehicle Update
    Confidence: 88%
    
    Extracted Information:
    - New License Plate: [ABC-1234]
    
    Follow these steps:
    □ 1. Search parkm.app by customer email
    □ 2. Navigate to Vehicles and Permits tab
    □ 3. Update vehicle information with new plate
    □ 4. Verify change saved
    □ 5. Send confirmation to customer
    □ 6. Close ticket
    ```
  
  - **Escalation Wizard:**
    ```
    ⚠️ Ticket flagged for Human Review
    Reason: High urgency / Angry customer detected
    
    Priority Actions:
    □ 1. Read full email carefully
    □ 2. Escalate to supervisor if needed
    □ 3. Respond within 2 hours
    □ 4. Use empathetic tone
    □ 5. Offer phone call if appropriate
    ```

- [ ] Define template responses for common scenarios
  - Missing license plate
  - Missing move-out date
  - Refund approved (with 5-day timeline)
  - Refund denied (with T&C link)
  - Cancellation confirmation
  - Vehicle update confirmation

**Deliverable:** Wizard mockups and content approved by client

---

## Phase 2.2: Zoho Desk Extension Development (Week 3-4)

### Extension Framework Setup
**Owner:** Nagy

**Tasks:**
- [ ] Research Zoho Desk extension options
  - **Option 1:** Zoho Desk Widget SDK
    - Custom widget embedded in ticket view
    - JavaScript/HTML/CSS
    - Access to Zoho APIs
  - **Option 2:** Zoho Extension (Sigma framework)
    - More powerful, full app
    - Can create custom layouts
    - Requires Zoho Marketplace approval
  - **Option 3:** Custom sidebar (simpler)
    - Iframe embedded in Zoho
    - Hosted on our server
    - Limited Zoho API access
  - **Decision:** Choose Option 1 (Widget SDK) for balance of power and simplicity

- [ ] Set up development environment
  - Install Zoho CLI tools
  - Create extension project structure
  - Configure local testing environment
  - Set up hot reload for development

### Widget Development
**Owner:** Nagy (frontend) + Eli (backend integration)

**Tasks:**
- [ ] Create wizard widget UI
  - **Technology Stack:**
    - HTML/CSS/JavaScript (vanilla or React)
    - Zoho JS SDK for API access
    - Responsive design for different screen sizes
  
  - **Components:**
    - Header: Shows classification result and confidence
    - Checklist: Interactive checkboxes for each step
    - Info Panel: Shows extracted entities (dates, plates, amounts)
    - Template Buttons: Quick access to response templates
    - Help/Documentation link

- [ ] Implement dynamic content loading
  - Read ticket custom fields (AI Intent, Complexity, etc.)
  - Load appropriate wizard checklist based on intent
  - Display extracted entities
  - Show/hide steps based on available information

- [ ] Add template response functionality
  - Create template library in JSON
  - Template variables: customer name, license plate, date, amount
  - One-click insert into ticket response
  - Preview before sending

- [ ] Integrate with Zoho Desk APIs
  - Fetch ticket details
  - Read custom field values
  - Update ticket status
  - Add internal notes
  - Send email responses

### Template Library Creation
**Owner:** Eli (with Katie's input)

**Tasks:**
- [ ] Create response templates (stored in `src/templates/`)
  - **Missing Information Templates:**
    - `missing_license_plate.html`
    - `missing_move_out_date.html`
    - `missing_bank_statement.html`
  
  - **Refund Templates:**
    - `refund_approved.html` (variables: name, amount, processing_time)
    - `refund_denied_outside_window.html` (variables: name, move_out_date, last_charge_date)
    - `refund_denied_tos.html` (includes T&C link)
  
  - **Cancellation Templates:**
    - `cancellation_confirmed.html`
    - `cancellation_with_refund_pending.html`
  
  - **Update Confirmation Templates:**
    - `vehicle_update_confirmed.html`
    - `account_update_confirmed.html`

- [ ] Review templates with Katie
  - Ensure brand voice and tone
  - Verify legal language (T&C references)
  - Confirm refund processing timeline (5 days)
  - Get approval for each template

**Deliverable:** Working wizard widget deployed to Zoho Desk

---

## Phase 2.3: Validation & Real-Time Prompts (Week 4-5)

### Smart Validation Rules
**Owner:** Eli

**Tasks:**
- [ ] Implement validation prompts in wizard
  - **Before closing refund ticket:**
    - "Did you verify move-out date is within 30 days of last charge?"
    - "Did you cancel the permit in parkm.app?"
    - "Did you submit refund to accounting OR send denial email?"
  
  - **Before closing cancellation:**
    - "Did you confirm customer does NOT want a refund?"
    - "Did you cancel permit in parkm.app?"
    - "Did you send confirmation email?"
  
  - **Before closing vehicle update:**
    - "Did you verify the update in parkm.app?"
    - "Did you send confirmation to customer?"

- [ ] Add automatic status updates
  - When "Submit refund to accounting" is clicked:
    - Auto-update ticket status to "Waiting on Accounting"
    - Add internal note: "Refund submitted on [date] by [CSR name]"
  - When permit canceled:
    - Add tag: "permit_canceled"
    - Log timestamp

### Knowledge Base Integration
**Owner:** Nagy

**Tasks:**
- [ ] Create inline help snippets
  - **30-Day Refund Window Rule:**
    - Tooltip explaining calculation
    - Link to full policy document
  - **Permit Cancellation Process:**
    - Screenshot/video of parkm.app steps
    - Common troubleshooting issues
  - **Template Usage Guide:**
    - When to use each template
    - How to customize variables

- [ ] Build searchable FAQ within widget
  - "How do I calculate 30-day window?"
  - "What if customer wants partial refund?"
  - "What if permit already canceled?"
  - "What if license plate not in system?"

**Deliverable:** Wizard with validation prompts and inline help

---

## Phase 2.4: Testing & Training (Week 5)

### CSR Testing Program
**Owner:** Eli + Katie

**Tasks:**
- [ ] Select 2-3 CSR beta testers
  - Experienced CSRs who understand current process
  - Willing to provide detailed feedback
  - Available for 30-min daily check-ins

- [ ] Conduct 1-week beta test
  - **Day 1:** Training session (1 hour)
    - How wizard works
    - When it appears
    - How to use templates
    - How to provide feedback
  - **Days 2-4:** Live testing with real tickets
    - Process 20-30 tickets using wizard
    - Log any issues or confusion
    - Track time savings
  - **Day 5:** Feedback session
    - What worked well?
    - What was confusing?
    - What's missing?
    - Suggested improvements

- [ ] Iterate based on feedback
  - Fix bugs immediately
  - Adjust wizard content as needed
  - Add missing steps if identified
  - Improve template wording

### Full Team Training
**Owner:** Eli

**Tasks:**
- [ ] Create training materials
  - **Video Tutorial:** 5-10 minute walkthrough
  - **Quick Reference Guide:** 1-page PDF
  - **FAQ Document:** Common questions

- [ ] Conduct team training session (1.5 hours)
  - **Session 1 (45 min):** Live demo and walkthrough
  - **Break (15 min)**
  - **Session 2 (30 min):** Hands-on practice with test tickets
  - **Q&A:** Record all questions for FAQ

- [ ] Set up ongoing support
  - Slack channel or email for questions
  - Office hours: 2x per week for first month
  - Eli/Nagy available for troubleshooting

**Deliverable:** Full CSR team trained and using wizard in production

---

## Priority 2 Success Metrics

**Track Weekly:**
- CSR Adoption Rate: >90% (using wizard for classified tickets)
- Time Savings: 25% faster ticket resolution (baseline vs with wizard)
- Process Compliance: 90% reduction in missed steps
- CSR Satisfaction: Positive feedback scores
- Template Usage: >70% of responses use templates
- Training Time Reduction: New CSRs productive in 2 weeks (vs 3 months)

---

# PRIORITY 3: Refund Automation + ParkM.app API Integration

## Timeline: Week 3-6 (overlapping with Priority 2)
**Goal:** Automate refund eligibility validation by connecting to parkm.app system

## Dependencies
- ✅ Priority 1 classification data (move-out dates, refund intent)
- ⚠️ ParkM.app API access and documentation (CRITICAL - need from client)
- ⚠️ Test environment for parkm.app integration

---

## Phase 3.1: Discovery & API Analysis (Week 3)

### ParkM.app System Discovery
**Owner:** Eli + Katie/Chad

**Tasks:**
- [ ] Schedule technical discovery session with parkm.app team
  - **Attendees:** Eli, Nagy, Katie, parkm.app technical contact
  - **Agenda:**
    - System architecture overview
    - Database structure (customer, permits, payments)
    - Existing APIs (if any)
    - Authentication methods
    - Rate limits and constraints
    - Test environment access

- [ ] Request parkm.app documentation
  - API documentation (if exists)
  - Database schema
  - User roles and permissions
  - Security requirements
  - Sample data structures

- [ ] Identify required data endpoints
  - **Customer Account Lookup:**
    - Input: Email address
    - Output: Customer ID, name, active permits, account status
  - **Vehicles and Permits:**
    - Input: Customer ID
    - Output: License plates, permit IDs, active/canceled status, community
  - **Payments and Transactions:**
    - Input: Customer ID or Permit ID
    - Output: Transaction history, last charge date, amount, payment method
  - **Permit Operations:**
    - Cancel permit (write operation)
    - Update vehicle info (write operation)
    - Create permit (potentially for future)

### API Access & Authentication
**Owner:** Nagy

**Tasks:**
- [ ] Set up API credentials
  - Request API keys or OAuth credentials
  - Set up test account for development
  - Configure authentication in code
  - Test connectivity

- [ ] Create parkm.app API client: `src/api/parkm_client.py`
  ```python
  class ParkMClient:
      def __init__(self, api_key, base_url):
          self.api_key = api_key
          self.base_url = base_url
      
      async def get_customer_by_email(self, email):
          # API call to fetch customer
      
      async def get_customer_permits(self, customer_id):
          # API call to fetch permits
      
      async def get_payment_history(self, customer_id):
          # API call to fetch payments
      
      async def cancel_permit(self, permit_id):
          # API call to cancel permit
      
      async def update_vehicle(self, permit_id, license_plate):
          # API call to update vehicle
  ```

- [ ] Implement error handling and retry logic
  - Handle API timeouts
  - Handle rate limits (implement backoff)
  - Handle authentication failures
  - Log all API calls for debugging

**Deliverable:** Working API client connected to parkm.app test environment

---

## Phase 3.2: Refund Eligibility Engine (Week 4)

### Business Rules Implementation
**Owner:** Eli

**Tasks:**
- [ ] Document refund eligibility rules (from `refund-cancellation-process.pdf`)
  - **Eligible if ALL true:**
    1. Customer moved out (move-out date extracted or confirmed)
    2. Move-out date is within 30 days of last charge
    3. Permit is active OR customer confirms cancellation intent
    4. Single permit only (multi-permit cases require human review)
    5. No dispute or legal language detected
    6. Valid license plate in system

- [ ] Create refund validation service: `src/services/refund_validator.py`
  ```python
  class RefundValidator:
      def __init__(self, parkm_client, classifier_result):
          self.parkm = parkm_client
          self.classification = classifier_result
      
      async def validate_refund_eligibility(self, ticket_data):
          # 1. Get customer from parkm.app by email
          customer = await self.parkm.get_customer_by_email(ticket_data.email)
          
          # 2. Get permits and payment history
          permits = await self.parkm.get_customer_permits(customer.id)
          payments = await self.parkm.get_payment_history(customer.id)
          
          # 3. Validate move-out date
          move_out_date = self.classification.move_out_date
          last_charge_date = payments[0].date
          days_diff = (last_charge_date - move_out_date).days
          
          # 4. Check 30-day window
          within_window = 0 <= days_diff <= 30
          
          # 5. Check permit status
          active_permits = [p for p in permits if p.status == "active"]
          
          # 6. Return validation result
          return RefundEligibilityResult(
              eligible=within_window and len(active_permits) == 1,
              reason="..." if not eligible else None,
              move_out_date=move_out_date,
              last_charge_date=last_charge_date,
              days_difference=days_diff,
              permit_status=active_permits[0].status,
              refund_amount=payments[0].amount
          )
  ```

- [ ] Handle edge cases
  - **No move-out date extracted:**
    - Flag for human review
    - Suggest template asking customer for date
  - **Multiple permits:**
    - Flag for human review
    - Show all permits in wizard
  - **License plate not found:**
    - Flag for human review
    - Suggest template asking for license plate
  - **Already canceled permit:**
    - Skip cancellation step
    - Proceed with refund eligibility check
  - **Move-out date in future:**
    - Flag as ineligible
    - Suggest denial template

### Date Calculation & Validation
**Owner:** Nagy

**Tasks:**
- [ ] Implement 30-day window calculator
  - Handle timezone differences
  - Account for business days vs calendar days (clarify with client)
  - Display calculation in wizard:
    ```
    Move-out Date: January 15, 2026
    Last Charge Date: February 1, 2026
    Days Difference: 17 days
    Status: ✓ Within 30-day window (Eligible)
    ```

- [ ] Add date extraction improvements
  - Parse natural language dates:
    - "moved out last week"
    - "leaving end of month"
    - "January 1st"
  - Validate reasonable dates (not in future, not >1 year ago)
  - Ask for confirmation if date seems unusual

**Deliverable:** Refund validation engine with parkm.app data integration

---

## Phase 3.3: Automated Workflow (Week 5)

### Auto-Generated Refund Submissions
**Owner:** Eli

**Tasks:**
- [ ] Create email generation service: `src/services/email_generator.py`
  - **Refund submission to accounting@parkm.com:**
    ```
    Subject: Refund Request - [Customer Name] - [Permit ID]
    
    Resident Email: customer@example.com
    Refund Amount: $50.00
    Reason: Moved out on 1/15/2026, last charged on 2/1/2026 (17 days)
    License Plate: ABC-1234
    Community: Sunset Apartments
    Permit ID: 12345
    
    Please process refund within 5 business days.
    
    Zoho Ticket: #69834
    Processed by: [CSR Name]
    Date: 2/9/2026
    ```

- [ ] Implement auto-submit workflow
  - When CSR clicks "Submit Refund to Accounting":
    1. Generate email with all required details
    2. Send email to accounting@parkm.com
    3. CC CSR and customer
    4. Update ticket status to "Waiting on Accounting"
    5. Add internal note with timestamp
    6. Set follow-up reminder for 5 days

- [ ] Create accounting reply webhook
  - When accounting replies to ticket:
    1. Parse email for "approved" or "completed"
    2. Auto-reopen ticket
    3. Notify CSR to send confirmation to customer
    4. Track refund processing time

### Smart Template System
**Owner:** Eli

**Tasks:**
- [ ] Build template engine with parkm.app data
  - Auto-populate templates with:
    * Customer name (from parkm.app)
    * Refund amount (from last transaction)
    * Move-out date (extracted + verified)
    * License plate (from parkm.app)
    * Processing timeline (5 business days)
  
- [ ] Create conditional templates
  - **If eligible:**
    - Use `refund_approved.html`
    - Auto-populate all variables
    - Include processing timeline
  - **If not eligible (outside window):**
    - Use `refund_denied_outside_window.html`
    - Show calculation: "You moved out on [date], but were last charged on [date], which is [X] days - outside our 30-day window"
    - Include link to Terms & Conditions
  - **If missing info:**
    - Use `missing_info.html`
    - List what's needed: license plate, move-out date, etc.

**Deliverable:** Automated refund submission workflow

---

## Phase 3.4: Unified Desktop Preview (Week 5-6)

**NOTE:** This is a preview of Priority 4 functionality, but built as part of Priority 3 to avoid CSRs needing to switch to parkm.app

### Embedded Data Display
**Owner:** Nagy

**Tasks:**
- [ ] Extend Zoho widget to show parkm.app data
  - **Customer Account Panel:**
    ```
    Customer: John Smith (john@example.com)
    Account Status: Active
    Total Permits: 1
    ```
  
  - **Vehicles & Permits Tab:**
    ```
    Permit #12345 - Active
    License Plate: ABC-1234
    Vehicle: 2020 Toyota Camry
    Community: Sunset Apartments
    Start Date: 1/1/2025
    ```
  
  - **Payments & Transactions Tab:**
    ```
    Last Charge: $50.00 on 2/1/2026
    Payment Method: Visa ending in 1234
    History: View all transactions →
    ```
  
  - **Refund Eligibility Indicator:**
    ```
    Move-Out Date: 1/15/2026 (from email)
    Last Charge: 2/1/2026
    Days: 17 days ✓ Within 30-day window
    Status: ELIGIBLE for refund
    ```

- [ ] Add single-screen workflow
  - **Left side:** Zoho ticket
  - **Right side:** parkm.app customer data
  - No need to switch between systems

- [ ] Implement one-click actions (if parkm.app API supports)
  - **Cancel Permit button:**
    - Executes: API call to parkm.app cancel endpoint
    - Confirmation modal
    - Updates widget display
    - Logs action in ticket
  - **Submit Refund button:**
    - Generates email to accounting
    - Sends automatically
    - Updates ticket status

**Deliverable:** Single-pane-of-glass view eliminating need to access parkm.app

---

## Phase 3.5: Testing & Validation (Week 6)

### Integration Testing
**Owner:** Eli + Nagy

**Tasks:**
- [ ] Create test scenarios (use parkm.app test environment)
  - **Scenario 1:** Eligible refund (within 30 days, active permit)
  - **Scenario 2:** Ineligible refund (outside 30 days)
  - **Scenario 3:** Already canceled permit
  - **Scenario 4:** Multiple permits
  - **Scenario 5:** Missing license plate
  - **Scenario 6:** Future move-out date
  - **Scenario 7:** Payment history issues
  - **Scenario 8:** Customer not found in parkm.app

- [ ] Test end-to-end workflow
  - Create ticket → Classify → Validate → Submit refund → Accounting reply → Close
  - Verify each step logs correctly
  - Check error handling
  - Validate data accuracy

- [ ] Performance testing
  - API response times (parkm.app calls)
  - Widget load time
  - Concurrent ticket processing
  - Ensure <10 second total processing time

### Client UAT (User Acceptance Testing)
**Owner:** Eli + Katie

**Tasks:**
- [ ] Set up UAT environment
  - Mirror production setup
  - Use parkm.app test data
  - Create 20 test tickets covering all scenarios

- [ ] Conduct UAT with Katie/CSRs
  - **Week 6 Days 1-3:** CSRs test all workflows
  - **Week 6 Day 4:** Feedback session
  - **Week 6 Day 5:** Final adjustments

- [ ] Sign-off checklist
  - [ ] Refund eligibility validation accurate
  - [ ] 30-day window calculation correct
  - [ ] Auto-generated emails properly formatted
  - [ ] Templates have correct content
  - [ ] parkm.app data displays correctly
  - [ ] One-click actions work (if implemented)
  - [ ] Error handling appropriate
  - [ ] CSR team trained and confident

**Deliverable:** Production-ready refund automation system

---

## Priority 3 Success Metrics

**Track Weekly:**
- Refund Processing Time: 60-80% reduction (baseline vs automated)
- Eligibility Accuracy: >95% (correct 30-day window calculation)
- Data Integration Reliability: >99% uptime (parkm.app API)
- Auto-Submission Success Rate: >98%
- CSR Satisfaction: Elimination of manual date math
- Accounting Team Feedback: Complete refund data in first email

---

# OPTIONAL ENHANCEMENT: LLM Continuous Improvement

## Overview
**Recommended for:** Post-launch (Week 7+) or integrate during Priority 2  
**Purpose:** Improve classification accuracy over time using CSR feedback  
**Effort:** 10-15 hours initial setup, ongoing minimal effort  
**ROI:** 5-10% accuracy improvement over first 3 months

This enhancement creates a feedback loop where CSR corrections train the AI to better understand ParkM-specific language patterns and edge cases.

---

## Phase 1: Feedback Collection System (Week 7-8)

### Goal
Capture CSR corrections to classification errors for future learning

### Implementation

**Add Feedback Logging:**
- Create `src/services/feedback_logger.py`
- Log every classification with metadata
- Store CSR corrections when they occur
- Track confidence vs accuracy correlation

**Code Addition:**
```python
# src/services/feedback_logger.py
class ClassificationFeedbackLogger:
    def __init__(self, log_file="data/classification_feedback.jsonl"):
        self.log_file = log_file
    
    async def log_classification(
        self,
        ticket_id: str,
        email_text: str,
        classification: dict,
        csr_feedback: Optional[dict] = None
    ):
        """Log classification for training data collection"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "email_text": email_text,
            "ai_classification": classification,
            "csr_feedback": csr_feedback,
            "confidence": classification.get("confidence", 0),
            "was_correct": csr_feedback is None  # Assume correct if no feedback
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

**Data to Collect:**
- Original email text
- AI classification result
- Confidence score
- CSR correction (if any)
- Timestamp
- Ticket ID for traceability

---

## Phase 2: CSR Feedback Widget (Priority 2 Integration)

### Goal
Allow CSRs to easily correct misclassifications

### Add to In-Workflow Wizard

**Feedback UI Component:**
```
┌─────────────────────────────────────────────────┐
│ ✓ Ticket classified as: Refund Request         │
│   Confidence: 95%                               │
│                                                  │
│   Was this classification correct?              │
│   [✓ Yes, Correct]  [✗ No, Incorrect]          │
│                                                  │
│   If incorrect, what should it be?              │
│   [Dropdown: Select correct intent...]         │
│   - Permit Cancellation                         │
│   - Account Update                              │
│   - Payment Issue                               │
│   - Permit Inquiry                              │
│   - Technical Issue                             │
│   - General Question                            │
│                                                  │
│   Optional: What was confusing?                 │
│   [Text area for notes]                         │
│                                                  │
│   [Submit Feedback]                             │
└─────────────────────────────────────────────────┘
```

**Implementation Notes:**
- Make feedback optional (don't block workflow)
- Only show if confidence < 90% OR after ticket closed
- 1-2 clicks maximum to provide feedback
- Thank CSR for feedback ("Helps improve AI!")

---

## Phase 3: Few-Shot Learning Updates (Week 9+)

### Goal
Use collected feedback to improve prompts without fine-tuning

### Weekly Prompt Enhancement Process

**Step 1: Analyze Feedback (15 min/week)**
```python
# scripts/analyze_feedback.py
def generate_correction_examples():
    """Find most common misclassifications"""
    feedback = load_feedback_log()
    
    # Find patterns in corrections
    corrections = [f for f in feedback if f['csr_feedback']]
    
    # Group by error type
    by_confusion = defaultdict(list)
    for corr in corrections:
        wrong = corr['ai_classification']['intent']
        right = corr['csr_feedback']['correct_intent']
        key = f"{wrong}_confused_with_{right}"
        by_confusion[key].append(corr)
    
    # Return top 5 confusion patterns
    return sorted(by_confusion.items(), key=lambda x: len(x[1]), reverse=True)[:5]
```

**Step 2: Update Classification Prompt**
```python
# Add to src/services/classifier.py

LEARNED_EXAMPLES = """
LEARNED FROM CSR CORRECTIONS:

Common confusion: account_update vs refund_request
Example:
Email: "Update my vehicle to plate ABC-123"
WRONG: refund_request (no refund keywords)
CORRECT: account_update (clear update intent)

Common confusion: permit_cancellation vs refund_request  
Example:
Email: "Just cancel it, I already moved"
WRONG: refund_request (moving out doesn't always mean refund)
CORRECT: permit_cancellation (explicit cancel request, no refund mention)

Common confusion: payment_issue vs refund_request
Example:
Email: "Why did you charge me twice this month?"
WRONG: refund_request
CORRECT: payment_issue (questioning charge, not requesting refund)
"""

# Add to classification prompt
system_prompt = BASE_PROMPT + LEARNED_EXAMPLES
```

**Step 3: Test & Deploy**
- Run updated prompt against test suite
- Verify accuracy improvement
- Deploy to production

**Expected Results:**
- 5-10% accuracy improvement per iteration
- Fewer repeat errors
- Better handling of edge cases

---

## Phase 4: Advanced - Dynamic Example Selection (Optional)

### Goal
Automatically add relevant examples to each classification request

### Implementation
```python
class AdaptiveClassifier:
    def __init__(self):
        self.feedback_db = load_feedback_corrections()
        self.embeddings = self._build_embeddings()  # Vector search
    
    def build_prompt_with_similar_examples(self, email_text):
        """Add relevant examples based on email similarity"""
        base_prompt = BASE_CLASSIFICATION_PROMPT
        
        # Find 3 most similar corrected emails
        similar_cases = self.find_similar_corrections(
            email_text, 
            limit=3
        )
        
        if similar_cases:
            base_prompt += "\n\nRelevant examples from corrections:\n"
            for case in similar_cases:
                base_prompt += f"""
                Email: {case['email_text']}
                Correct classification: {case['correct_intent']}
                Note: {case['csr_note']}
                """
        
        return base_prompt
```

**Advantages:**
- Self-improving system
- Contextual examples
- No manual prompt updates

**Additional Costs:**
- ~$5-10/month for embeddings (OpenAI text-embedding-3-small)
- Minimal latency increase (~50-100ms)

---

## Phase 5: Fine-Tuning (Future - 6+ Months)

### When to Consider
- After collecting 500+ corrected examples
- Classification accuracy plateaus with prompt engineering
- Budget allows (~$25/training run + higher inference costs)

### Process
1. Export feedback log in OpenAI training format
2. Create JSONL training file
3. Submit fine-tuning job via OpenAI API
4. Test custom model
5. Deploy if accuracy improvement > 5%

**Not recommended initially** - expensive and requires significant data

---

## Metrics to Track

### Classification Quality
- **Accuracy Rate:** % of tickets CSRs mark as correct
- **Confidence vs Correctness:** Are 95% confident tickets actually correct?
- **Intent Confusion Matrix:** Which intents get confused most?
- **Edge Case Capture Rate:** Are we finding new edge cases?

### Improvement Over Time
- **Weekly Accuracy Trend:** Target +1-2% per month
- **Correction Volume:** Should decrease over time
- **CSR Satisfaction:** "AI is getting better" feedback
- **Prompt Updates:** Track each update and resulting accuracy

### Sample Dashboard Queries
```sql
-- Accuracy by intent type
SELECT 
  intent,
  COUNT(*) as total,
  SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct,
  ROUND(100.0 * SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) / COUNT(*), 2) as accuracy_pct
FROM classifications
WHERE timestamp > DATE('now', '-7 days')
GROUP BY intent;

-- Most common corrections
SELECT 
  ai_intent,
  correct_intent,
  COUNT(*) as occurrences
FROM corrections
GROUP BY ai_intent, correct_intent
ORDER BY occurrences DESC
LIMIT 10;
```

---

## Implementation Timeline

**Week 7-8: Setup (10 hours)**
- Build feedback logging system
- Create data storage (JSONL or SQLite)
- Add logging to classification pipeline
- Create analysis scripts

**Week 9: CSR Widget (5 hours)**
- Design feedback UI component
- Add to Priority 2 wizard
- Test with CSRs
- Deploy

**Week 10+: Ongoing (~1 hour/week)**
- Review weekly corrections
- Update prompts with top patterns
- Test accuracy improvements
- Iterate

---

## Quick Win: Manual Example Collection (Week 3-4)

**While waiting for automated feedback:**

Create `data/manual_corrections.json` based on testing:
```json
[
  {
    "email": "Update my vehicle to plate ABC-123",
    "wrong_intent": "refund_request",
    "correct_intent": "account_update",
    "reason": "No refund keywords, clear vehicle update request",
    "confidence_was": 85
  },
  {
    "email": "Just cancel my permit, I moved out last month",
    "wrong_intent": "refund_request",
    "correct_intent": "permit_cancellation", 
    "reason": "Customer wants cancellation, didn't explicitly ask for refund",
    "confidence_was": 80
  },
  {
    "email": "Why was I charged twice?",
    "wrong_intent": "refund_request",
    "correct_intent": "payment_issue",
    "reason": "Questioning charge, not requesting refund yet",
    "confidence_was": 70
  }
]
```

**Add top 5-10 examples to classification prompt immediately** for instant accuracy boost.

---

## ROI Calculation

### Costs
- **Initial Development:** 10-15 hours ($2,250-$3,375)
- **Ongoing Maintenance:** 1 hour/week (~$225/week)
- **Infrastructure:** ~$5-10/month (embeddings if using Phase 4)

### Benefits
- **Accuracy Improvement:** 5-10% over 3 months
- **Reduced CSR Corrections:** -20-30% manual overrides
- **Better Edge Case Handling:** Fewer escalations
- **Continuous Improvement:** Self-optimizing system

**Break-even:** ~4-6 weeks of operation

---

## Recommended Approach

**Best Practice:**
1. ✅ **Week 3-4:** Start collecting manual corrections during testing
2. ✅ **Week 7:** Implement automated feedback logging
3. ✅ **Week 9:** Add CSR feedback widget to Priority 2
4. ✅ **Week 10+:** Weekly prompt updates based on feedback
5. 🔮 **Month 6+:** Consider fine-tuning if needed

**Don't over-engineer early:**
- Start with simple logging
- Add CSR feedback when Priority 2 launches
- Let data accumulate naturally
- Update prompts monthly initially, then quarterly

**This enhancement is optional but highly recommended** - it transforms the AI from static to continuously improving, ensuring long-term value and accuracy.

---

# PROJECT MANAGEMENT & COORDINATION

## Weekly Client Touchpoints

### Week 1: Priority 1 Kickoff
**Agenda:**
- Demo production infrastructure
- Review webhook automation
- Discuss any access/permission issues
- Show initial classification results

### Week 2: Priority 1 Validation + Priority 2 Kickoff
**Agenda:**
- Present test suite results (Priority 1)
- Review classification accuracy
- Demo wizard mockups (Priority 2)
- Get feedback on wizard content

### Week 3: Priority 1 Launch + Priority 2 Development + Priority 3 Discovery
**Agenda:**
- Production launch of classification system
- Demo wizard widget in development
- parkm.app API discovery session
- Review queue routing effectiveness

### Week 4: Priority 2 Testing + Priority 3 Development
**Agenda:**
- CSR beta testing feedback (Priority 2)
- Review parkm.app integration progress
- Demo refund validation engine
- Discuss template content

### Week 5: Priority 2 Training + Priority 3 Testing
**Agenda:**
- Full team wizard training
- Demo automated refund workflow
- Review embedded parkm.app data
- Plan UAT schedule

### Week 6: Priority 3 UAT + Project Wrap-Up
**Agenda:**
- Conduct UAT with CSRs
- Review all three priorities end-to-end
- Collect feedback and final adjustments
- Discuss ongoing support and Phase 4/5

---

## Risk Management

### High-Risk Items

**Risk 1: parkm.app API doesn't exist or is limited**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:**
  - Conduct discovery session Week 3 Day 1
  - If no API, may need to build custom integration (database access, screen scraping, or manual API creation)
  - Budget extra time in Priority 3 if needed
  - Worst case: Delay Priority 3, focus on Priorities 1-2

**Risk 2: Classification accuracy below 90% on production data**
- **Probability:** Low-Medium
- **Impact:** Medium
- **Mitigation:**
  - Extensive testing in Phase 1.3
  - Use 100-200 real production tickets for training
  - Set confidence thresholds appropriately
  - Flag low-confidence cases for human review

**Risk 3: CSR adoption resistance**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Involve Katie in wizard design
  - Beta test with friendly CSRs first
  - Emphasize time savings, not replacement
  - Provide excellent training and support

**Risk 4: Zoho Desk limitations on customization**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Research Zoho capabilities in advance
  - Have fallback options (simpler wizard, iframe-based)
  - Work with Zoho support if needed

---

## Cost Summary

### Development Hours (All 3 Priorities)

| Priority | Anticipated Hours | Notes |
|----------|-------------------|-------|
| **1** | 25-35 hours | Classification, webhooks, queue routing |
| **2** | 20-30 hours | Wizard UI, templates, validation |
| **3** | 40-50 hours | parkm.app API, refund automation |
| **Total** | **85-115 hours** | Assumes parkm.app API exists |

**If parkm.app API requires custom build:** Add 15-25 hours

### Infrastructure Costs (Monthly)

| Item | Cost | Notes |
|------|------|-------|
| Virtual Server | $15-20 | AWS/DigitalOcean |
| OpenAI API | $10-20 | 4-5K tickets/month |
| SSL Certificates | $0 | Let's Encrypt (free) |
| Monitoring Tools | $0-10 | Free tier or basic paid |
| **Total Monthly** | **$25-50** | Ongoing operational cost |

---

## Communication Protocol

### Daily Standups (Internal)
- **When:** 9 AM EST, 15 minutes
- **Who:** Eli + Nagy
- **Format:**
  - What did you do yesterday?
  - What are you doing today?
  - Any blockers?

### Client Check-ins
- **Frequency:** Weekly (Fridays, 2 PM EST)
- **Duration:** 30-60 minutes
- **Format:** Demo progress, gather feedback, plan next week

### Escalation Path
1. **Technical blockers:** Eli → Nagy → Lauren
2. **Client issues:** Eli → Lauren → Katie → Chad
3. **Timeline concerns:** Eli → Lauren → Katie immediately

### Documentation
- **Daily:** Update task progress in `priority-1-action-plan.md`, `priority-2-action-plan.md`, `priority-3-action-plan.md`
- **Weekly:** Email summary to Katie/Chad
- **Major milestones:** Demo video + written summary

---

## Success Criteria (All 3 Priorities)

### Priority 1 (Week 3)
- ✅ 100% of tickets auto-classified in real-time
- ✅ >90% classification accuracy
- ✅ Queue routing functional
- ✅ CSRs can see classifications in their workflow

### Priority 2 (Week 5)
- ✅ Wizard appears for all classified tickets
- ✅ 90% CSR adoption rate
- ✅ 25% faster ticket resolution
- ✅ 90% reduction in missed steps
- ✅ Positive CSR feedback

### Priority 3 (Week 6)
- ✅ parkm.app data integrated successfully
- ✅ Refund eligibility auto-validated
- ✅ 30-day window calculation accurate
- ✅ Auto-generated refund emails to accounting
- ✅ CSRs don't need to access parkm.app
- ✅ 60-80% time savings on refund processing

### Overall Project (Week 6)
- ✅ All 3 priorities delivered on time
- ✅ Client sign-off received
- ✅ CSR team fully trained
- ✅ Documentation complete
- ✅ Monitoring in place
- ✅ Ready for ongoing support phase

---

**Last Updated:** February 9, 2026  
**Status:** Ready to begin Priority 1 development  
**Next Review:** End of Week 1 (February 14, 2026)  
**Project Managers:** Eli Kiedrowski, Nagy (Technical), Lauren Kiedrowski (Client Relations)
