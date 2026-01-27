# ParkM & CRM Wizards - Initial Meeting

**Date:** January 26, 2026  
**Participants:** 
- **ParkM:** Chad Craven (CEO), Katie Schaeffer (Operations Manager), Patrick Cameron (Outside Sales Consultant)
- **CRM Wizards:** Eli Kiedrowski, Lauren Kiedrowski

---

## Meeting Summary

### About ParkM

ParkM is a virtual parking permit provider for multifamily housing communities operating on a revenue-share model.

**Support Team:**
- 23-25 person customer support division
- 100% email-based support (no phone/chat)
- Support quality is a key differentiator and selling point
- Team consists mainly of part-time college students and stay-at-home moms
- Takes approximately 3 months for new hires to become fully effective

**Customer Base:**
- B2C support for multifamily residents
- Lower-income demographic
- Many customers with English as second language
- Some literacy challenges

### Current Challenges

1. **Scaling Issues:** 6 new hires in the past year leading to increased escalations
2. **Process Inconsistencies:** New staff not following complete processes
3. **Training Time:** 3-month ramp-up time for full effectiveness
4. **High Volume Categories:** 20% of tickets are refund requests
5. **Lack of Workflow Guidance:** No in-system reminders or process checkers

### Technical Environment

- **Zoho Desk:** Email ticketing and queue management
- **App Platform:** Separate system for permit data (no current API integration with Zoho)
- **Stripe:** Payment processing (APIs through app platform)
- **Google Translate:** Spanish language support (respond in English, customer's phone translates)

### Proposed Solution Approach

**Initial Phase (80/20 Rule):**
- Start with 80% human interaction, 20% AI assistance
- Monitor and validate before scaling up
- Build confidence with quick wins

**Potential Use Cases:**
1. **Refund Processing:** 20% of ticket volume
   - Validate move-out date
   - Check permit status
   - Apply 30-day refund policy
   - Route to accounting team
   - Auto-respond to customer

2. **Account Updates:** License plate changes, vehicle updates
3. **Permit Inquiries:** Status checks, general questions

**Technical Requirements:**
- API integration between Zoho Desk and app platform
- Email parsing and categorization
- Data extraction and validation
- Automated workflow triggers
- Process guidance/wizard for CSRs

**Benefits:**
- Reduce time to effectiveness for new hires
- Handle growth with same headcount
- Improve consistency and reduce escalations
- Free up team for complex cases
- Maintain strong customer service brand

---

## Action Items

| Owner | Task | Due Date |
|-------|------|----------|
| **Katie Schaeffer** | Document detailed use cases with full process steps (12-step level detail) including tools used at each step | Wednesday, Jan 28 |
| **Chad Craven** | Provide Zoho Desk access to Eli/team for technical review | Monday EOD, Jan 26 |
| **Eli Kiedrowski** | Validate technical feasibility with architect (Zoho API capabilities, integration requirements) | Tuesday, Jan 27 |
| **Eli Kiedrowski** | Send mutual NDA document | ASAP |
| **Lauren Kiedrowski** | Send mutual NDA document | Monday evening, Jan 26 |
| **Eli Kiedrowski** | Review Katie's use cases and prepare effort/investment estimates | After receiving documentation |
| **All Participants** | **Follow-up meeting** | **Friday, Jan 30 @ 12:30 PM Central** |

---

## Key Decisions

1. **Start Simple:** Focus on smaller, clearer use cases first for quick wins rather than complex refund processing
2. **Human-in-Loop:** Maintain human validation/approval initially before full automation
3. **Phased Approach:** Build confidence with 80/20 human/AI split, then scale AI involvement
4. **Integration Required:** API integration between Zoho and app platform is necessary
5. **Process Guidance:** Consider "wizard" UI to help CSRs follow proper procedures

---

## Technical Notes

### Refund Process Flow
1. Customer emails refund request
2. CSR validates move-out date and permit status in app platform
3. Apply 30-day refund policy rules
4. If approved, route to accounting/internal manager team
5. Accounting reviews and approves
6. Refund issued via app platform (which APIs to Stripe)
7. CSR responds to customer

### Current Workflow
1. Email arrives at support@parkm.com
2. Forwarded to Zoho Desk
3. Enters queue (4-5 agents working simultaneously)
4. Agent takes ownership
5. Agent reviews notes in Zoho
6. Agent switches to app platform to view/modify permit data
7. Agent responds via Zoho Desk

### Integration Considerations
- Zoho Desk has no current API connection to app platform
- App platform has other integrations (just not with Zoho)
- Need to evaluate Zoho's API capabilities and customization options
- May need custom components/views within Zoho
- Consider where data should be displayed (Zoho vs app platform)

---

## Next Steps

1. **Immediate (Mon-Wed):**
   - Execute action items (access, NDA, documentation)
   - Technical validation of Zoho capabilities
   - Use case documentation with detailed process flows

2. **Friday Meeting:**
   - Review detailed use cases
   - Discuss technical feasibility findings
   - Present scope and investment estimates
   - Identify best quick-win use case for POC

3. **Future Considerations:**
   - Proof of concept development
   - Demo with actual email data (8 years of historical emails available)
   - Phased rollout plan
   - Training and change management

---

## Additional Notes

- **Historical Data:** 8 years of email history available in Zoho for training/testing
- **Spanish Support:** Currently using Google Translate; customers respond better when replies stay in English (they translate on their end)
- **Risk Mitigation:** Financial transactions are low value ($10 permits), reducing risk of automation errors
- **Scale Potential:** Looking to handle growth without adding headcount rather than replacing existing team

---

## Contact Information

**ParkM Team:**
- Chad Craven - CEO
- Katie Schaeffer - Operations Manager
- Patrick Cameron - Outside Sales Consultant

**CRM Wizards Team:**
- Eli Kiedrowski - Technical Lead
- Lauren Kiedrowski - Business Development
