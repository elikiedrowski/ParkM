# Priority 1 Implementation Plan: Email Triage & Classification System

**Timeline:** 2-3 weeks  
**Status:** In Progress - Classifier Built ✅  
**Next:** Zoho Integration

---

## Overview

Build an AI-powered email classification system that automatically categorizes and routes incoming support tickets in Zoho Desk.

---

## Week 1: AI Classifier Development and Testing ✅ COMPLETE

### Tasks Completed
- [x] Set up development environment
- [x] Configure Zoho Desk API access (OAuth)
- [x] Build email classifier using GPT-4o
- [x] Create classification schema with 10 data points
- [x] Test with 7 sample ParkM scenarios
- [x] Validate accuracy and confidence scores

### Deliverables
- ✅ `src/services/classifier.py` - Email classification service
- ✅ Classification test suite with sample emails
- ✅ Test results documentation
- ✅ 95% confidence achieved across all test cases

### Classification Categories Implemented
1. **Intent Detection:** refund_request, account_update, permit_inquiry, payment_issue, technical_issue, move_out, general_question, unclear
2. **Complexity:** simple, moderate, complex
3. **Language:** english, spanish, other, mixed
4. **Urgency:** high, medium, low
5. **Entity Extraction:** license_plate, move_out_date, property_name, amount
6. **Routing Recommendation:** Auto-resolution, escalation, department-specific queues

---

## Week 2: Zoho Webhook Integration and Auto-Tagging

### Objective
Integrate the classifier with Zoho Desk to automatically process incoming tickets in real-time.

### Tasks

#### 2.1 Webhook Receiver Setup (Days 1-2)
- [ ] Create FastAPI webhook endpoint to receive Zoho ticket notifications
- [ ] Set up webhook authentication and verification
- [ ] Configure Zoho Desk to send webhook on new ticket creation
- [ ] Test webhook delivery and payload parsing

**Technical Components:**
```python
# src/api/webhooks.py
- POST /webhooks/zoho/ticket-created
- Verify Zoho signature
- Extract ticket ID, subject, body, sender
- Queue for classification
```

#### 2.2 Zoho API Token Management (Day 2)
- [ ] Implement OAuth refresh token handling
- [ ] Create token caching mechanism (60-min expiry)
- [ ] Add automatic token refresh on expiry
- [ ] Error handling for authentication failures

**Technical Components:**
```python
# src/api/zoho_auth.py
- get_valid_access_token()
- refresh_access_token()
- Token cache with TTL
```

#### 2.3 Auto-Tagging Implementation (Days 3-4)
- [ ] Create custom fields in Zoho Desk for classification data
  - `cf_ai_intent` (dropdown)
  - `cf_ai_complexity` (dropdown)
  - `cf_ai_language` (dropdown)
  - `cf_ai_urgency` (dropdown)
  - `cf_ai_confidence` (number)
  - `cf_requires_refund` (checkbox)
  - `cf_license_plate` (text)
- [ ] Build tagging service to update tickets via API
- [ ] Implement batch update for initial backlog
- [ ] Add error handling and retry logic

**Technical Components:**
```python
# src/services/tagger.py
- apply_classification_tags(ticket_id, classification)
- update_custom_fields()
- Handle API rate limits
```

#### 2.4 Integration Testing (Day 5)
- [ ] Test end-to-end flow: new ticket → webhook → classify → tag
- [ ] Verify custom fields update correctly
- [ ] Test with various email types (refund, update, inquiry)
- [ ] Test Spanish language emails
- [ ] Test error scenarios and recovery
- [ ] Performance testing (response time < 5 seconds)

---

## Week 3: Queue Routing Logic and Monitoring Dashboard

### Objective
Implement intelligent routing and create visibility into classification performance.

### Tasks

#### 3.1 Queue/Department Setup in Zoho (Day 1)
- [ ] Create specialized queues in Zoho Desk:
  - **Auto-Resolution Queue** (simple, high-confidence cases)
  - **Quick Updates Queue** (account updates)
  - **Accounting/Refunds Queue** (refund requests)
  - **Escalations Queue** (complex, high urgency)
  - **Spanish Support Queue** (Spanish language)
  - **General Support Queue** (default)
- [ ] Get department IDs for API routing
- [ ] Configure queue assignment rules

#### 3.2 Routing Logic Implementation (Days 2-3)
- [ ] Build routing decision engine
- [ ] Implement routing rules based on:
  - Intent + Complexity combinations
  - Urgency level
  - Language
  - Confidence threshold
- [ ] Add manual override capability
- [ ] Create routing configuration file for easy rule updates

**Routing Rules:**
```yaml
# routing_rules.yaml
- rule: "Simple refund (high confidence)"
  conditions:
    intent: refund_request
    complexity: simple
    confidence: > 0.90
  route_to: Auto-Resolution Queue

- rule: "Complex or low confidence"
  conditions:
    complexity: complex
    OR confidence: < 0.70
  route_to: Escalations Queue

- rule: "Spanish language"
  conditions:
    language: spanish
  route_to: Spanish Support Queue
```

**Technical Components:**
```python
# src/services/router.py
- determine_routing(classification)
- apply_routing_rules()
- route_ticket(ticket_id, department_id)
```

#### 3.3 Monitoring Dashboard (Days 4-5)
- [ ] Create simple web dashboard to monitor:
  - Classification volume by intent
  - Confidence score distribution
  - Routing decisions breakdown
  - Processing time metrics
  - Error rate tracking
- [ ] Set up logging for all classifications
- [ ] Create daily summary email report
- [ ] Add alerting for low confidence trends or errors

**Technical Components:**
```python
# src/services/analytics.py
- log_classification(ticket_id, classification, routing)
- generate_daily_report()
- get_metrics(date_range)

# Dashboard (simple HTML + charts)
- Real-time classification stats
- Routing distribution pie chart
- Confidence score histogram
- Recent tickets table
```

#### 3.4 Documentation and Handoff (Day 5)
- [ ] Create admin guide for managing queues
- [ ] Document routing rules and how to modify them
- [ ] Create troubleshooting guide
- [ ] Record demo video showing the system in action
- [ ] Prepare metrics for stakeholder presentation

---

## Technical Architecture

### System Components

```
┌─────────────────┐
│  Incoming Email │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Zoho Desk     │
│  (New Ticket)   │
└────────┬────────┘
         │
         │ Webhook
         ▼
┌─────────────────┐
│ FastAPI Server  │
│  /webhooks/...  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Email Classifier│
│   (GPT-4o)      │
└────────┬────────┘
         │
         ├─────────────┐
         ▼             ▼
┌─────────────┐  ┌──────────────┐
│   Tagger    │  │    Router    │
│ (Update CF) │  │ (Route Queue)│
└─────────────┘  └──────────────┘
         │             │
         └──────┬──────┘
                ▼
        ┌──────────────┐
        │  Zoho Desk   │
        │   (Updated)  │
        └──────────────┘
                │
                ▼
        ┌──────────────┐
        │  Analytics   │
        │  Dashboard   │
        └──────────────┘
```

### Technology Stack
- **Backend:** Python 3.11, FastAPI
- **AI:** OpenAI GPT-4o
- **API Client:** httpx (async)
- **Database:** PostgreSQL (optional, for analytics)
- **Deployment:** Docker container on cloud VM
- **Monitoring:** Custom dashboard + logs

---

## Deployment Plan

### Infrastructure Requirements
- **Server:** Cloud VM (2 vCPU, 4GB RAM)
- **Domain:** Webhook endpoint needs public URL with HTTPS
- **Secrets Management:** Environment variables for API keys
- **Backup:** Database backup (if using analytics DB)

### Deployment Steps
1. Set up cloud VM (AWS EC2, Google Cloud, or DigitalOcean)
2. Configure firewall (allow HTTPS on port 443)
3. Install Docker and Docker Compose
4. Deploy application container
5. Configure Zoho webhook to point to public endpoint
6. Test end-to-end in production
7. Monitor for 24-48 hours before full rollout

### Rollout Strategy
- **Phase A (Days 1-3):** Shadow mode - classify but don't route
- **Phase B (Days 4-7):** Route only "Auto-Resolution Queue" cases
- **Phase C (Days 8+):** Full routing enabled for all queues

---

## Success Metrics (Week 3 End)

### Performance Targets
- ✅ **Classification Accuracy:** >90% match with human judgment (validate 50 tickets)
- ✅ **Response Time:** <5 seconds from webhook to Zoho update
- ✅ **Uptime:** 99.5% availability
- ✅ **Error Rate:** <1% failed classifications

### Business Impact Targets (End of Month 1)
- 📊 **Routing Accuracy:** 85%+ tickets routed correctly first time
- 📊 **Time Savings:** 30 seconds saved per ticket (auto-classification)
- 📊 **Escalation Reduction:** 20% fewer mis-routed tickets
- 📊 **CSR Feedback:** Positive feedback from 80%+ of CSRs

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Zoho API rate limits | High | Implement request queuing and backoff |
| OpenAI API downtime | High | Add fallback to simpler keyword-based classification |
| Webhook delivery failures | Medium | Implement retry mechanism with exponential backoff |
| Low classification accuracy | High | Human review queue for low confidence cases |
| Token expiry issues | Medium | Proactive refresh 5 minutes before expiry |
| Cost overruns (OpenAI) | Medium | Set budget alerts, use caching for similar emails |

---

## Budget Estimate

### Development Costs (Internal)
- Week 1: ✅ Complete
- Week 2: 40 hours @ developer rate
- Week 3: 40 hours @ developer rate

### Operational Costs (Monthly)
- **OpenAI API:** ~$50-100/month (assuming 1000 tickets/month @ $0.005/email)
- **Server Hosting:** $20-50/month (cloud VM)
- **Total:** ~$70-150/month

### ROI Calculation
- **CSR time saved:** 1000 tickets × 30 seconds = 8.3 hours/month
- **At $20/hour:** $166/month saved
- **ROI:** Positive after month 1

---

## Next Steps

### Immediate (This Week)
1. Create custom fields in Zoho Desk sandbox
2. Set up FastAPI webhook endpoint
3. Deploy to test server with public URL
4. Configure webhook in Zoho

### Week 2 Goals
- Complete webhook integration
- Test auto-tagging on 10+ tickets
- Validate classification accuracy

### Week 3 Goals
- Implement routing
- Launch monitoring dashboard
- Begin shadow mode testing

---

## Status Updates

**Current Status:** ✅ Week 1 Complete - Classifier Built and Tested  
**Next Milestone:** Week 2 Day 1 - Webhook Endpoint Setup  
**Blockers:** None  
**On Track:** Yes
