# ParkM & CRM Wizards - Initial Meeting

**Date:** January 26, 2026  
**Participants:** 
- **ParkM:** Chad Craven (CEO), Katie Schaeffer (Operations Manager), Patrick Cameron (Outside Sales Consultant)
- **CRM Wizards:** Eli Kiedrowski, Lauren Kiedrowski

---

## Meeting Summary

### About ParkM

ParkM is a virtual parking permit provider for multifamily housing communities operating on a revenue-share model. Instead of selling software, ParkM goes to properties and positions a revenue share, splitting revenue from guest or resident permits, which increases the asset value by adding an additional revenue stream.

**Support Team:**
- 23-25 person customer support division
- 100% email-based support (no phone/chat)
- Support quality is a key differentiator and selling point - "we sell on it," "we're known for our support in a really good way"
- Team consists mainly of part-time college students and stay-at-home moms
- Takes approximately 3 months for new hires to become fully effective (not just training time, but time to work confidently)
- Recent growth: 6 new hires in the last year causing escalations due to not following complete processes

**Customer Base:**
- B2C support for multifamily residents
- Lower-income demographic, less educated
- Many customers with English as second language
- Some literacy challenges - "there are some literacy challenges... more so in our English speakers"
- Communication challenge: "the bloody complicated part is trying to figure out what is this person really asking for"

### Current Challenges

1. **Scaling Issues:** 6 new hires in the past year leading to increased escalations
2. **Process Inconsistencies:** New staff "not going through the process like we'd like them to" - not handling things efficiently and missing steps
3. **Training Time:** 3-month ramp-up time for full effectiveness
4. **High Volume Categories:** 20% of tickets are refund requests
5. **Lack of Workflow Guidance:** No in-system reminders or process checkers - "there's nothing in the flow that reminds them right now"
6. **Complex Inbound Questions:** Understanding what customers are actually asking for is extremely challenging

### Spanish Language Support Strategy

ParkM receives many inbound Spanish requests. They use Google Translate to understand incoming messages, but send responses back in English rather than translating them to Spanish. 

**Rationale:** Customers typically have their phones set up to translate anyway, so double-translating created a "game of telephone" effect that was worse than just responding in English. This approach has proven more effective despite the counter-intuitive nature.

### Technical Environment

- **Zoho Desk:** Email ticketing and queue management
- **App Platform:** Separate system for permit data (no current API integration with Zoho)
- **Stripe:** Payment processing (APIs through app platform)
- **Google Translate:** Spanish language support (respond in English, customer's phone translates)

### Proposed Solution Approach

**Initial Phase (80/20 Rule):**
- Recommended starting with 80% human interaction, 20% AI assistance
- Monitor and validate before scaling up - "once we get comfortable, we have some good time under our belt, then we can say, 'Okay, we feel comfortable, let's flip it now 20/80 or vice versa'"
- Build confidence with quick wins - finding smaller, simpler use cases first
- Katie Schaeffer confirmed preference for "baby step" approach with AI as assist or running in back end with human double-checking

**Potential Use Cases:**
1. **Refund Processing:** 20% of ticket volume
   - Initial target but may be too complex for first implementation
   - Validate move-out date
   - Check permit status
   - Apply 30-day refund policy
   - Route to accounting team
   - Auto-respond to customer

2. **Account Updates:** License plate changes, vehicle updates
   - Potentially simpler starting point
   - Customer example: "I just bought a new car. I need to update my plate" but they don't specify which car to replace

3. **Permit Inquiries:** Status checks, general questions
4. **AI Wizard/Process Guide:** Help CSRs follow proper procedures with in-system reminders

**Chad Craven's Vision for Full Automation:**

Chad described the ideal future state for easy refund cases:
1. Email arrives: "Hey, I moved out last month and you guys charge me. I demand a refund."
2. Bot verifies: Customer lived in community, already canceled permit
3. Bot responds: "Yes, we see that you've already canceled your permit, so you'll no longer be charged again in the future and I've submitted your refund request over to our accounting team."
4. Accounting approves
5. Bot follows up: "We see you've moved out. I've processed the refund already. You should see an email about it. Give 5-10 days for your bank to post it."

**For Complex Cases:** When scenarios aren't clear-cut (multiple permits, guest permits, unclear account connections), the bot would recognize limitations and respond: "Hey, I've gotten your request. I've sent it over to our accounting team to review and get back to you".

**Goal:** Not necessarily to replace headcount but to "grow with the same number of people". As Chad noted, the flow isn't huge enough to eliminate positions, but it would allow scaling without proportional staff increases. Board expectations about replacing people may not align with reality.

**Risk Mitigation:** Financial transactions are low-risk since charges are only $10 per permit, and bot could be constrained to "only get to do one refund" per customer within the 30-day window.

**AI Wizard for CSR Guidance:**

Katie identified a critical need for in-workflow guidance: "One thing we could desperately need is like a wizard or something that's telling the CSR here's what you need to do and did you do all of these things... They get trained on it, but there's nothing in the flow that reminds them right now."

Eli suggested implementing simple guardrails/handrails with instructions directly on the page agents view, similar to lead process steps that drop down to show what needs to be done next. This could help reduce the 3-month ramp-up time for new hires.

Lauren referenced a recent AI wizard they built for the roofing industry - a two-way voice AI helping roofers on the job take measurements and photos in proper sequence, even while wearing gloves in freezing weather. A similar but simpler concept could guide CSRs through support processes.

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
5. **Process Guidance Priority:** Consider "wizard" UI to help CSRs follow proper procedures and reduce training time
6. **Goal is Growth, Not Reduction:** Primary objective is to handle growth without proportional headcount increases rather than replacing existing team

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
4. Agent takes ownership of ticket
5. Agent reviews notes in Zoho
6. Agent switches to app platform to view/modify permit data
7. Agent responds via Zoho Desk

**Eli's Questions About Workflow:**
- Confirmed email goes to Zoho Desk queue
- Agents take ownership of tickets
- Most work done in separate app platform, not Zoho
- No current API between the two systems
- Integration will be necessary to enable AI solution to access both systems and take actions

### Integration Considerations
- Zoho Desk has no current API connection to app platform
- App platform has other integrations (just not with Zoho) - both systems are API-capable
- Need to evaluate Zoho's API capabilities and customization options
- **Chad's Concern:** Where/how external app data would be displayed, labeled, and categorized within Zoho's structure
- **Eli's Response:** May not need to store app data in Zoho; Zoho primarily used for email extraction and case management, with API calls retrieving app data as needed
- May need custom components/views within Zoho or potentially display data in app platform instead
- **Third System:** Stripe for payments, but most refunds can be processed through app platform which APIs to Stripe
- **Historical Data Available:** 8 years of email history in Zoho available for bot training/testing

**Eli's Technical Approach:**
- Use Zoho to extract information from emails and manage case flow
- API calls to app platform to gather customer/permit information
- Apply logic, reasoning, and decision-making based on extracted data
- May use custom AI/LLMs for complex reasoning or standard automation for simpler data-based decisions
- Not necessarily storing all app data within Zoho's structure

---

## Next Steps

1. **Immediate (Mon-Wed):**
   - Execute action items (access, NDA, documentation)
   - Eli to validate Zoho technical capabilities and limitations
   - Eli to meet with technical architect to assess feasibility - "I should have an answer in terms of the technicalities by tomorrow. I'm honestly not concerned though"
   - Katie to document use cases - "Don't bang your head on it, Katie. Just nice and simple. Send it my way when you're done. If I need more detail, I'll ask a question"
   - Chad to provide Zoho access for technical exploration
   - Exchange mutual NDA

2. **Friday Meeting:**
   - Review detailed use cases
   - Discuss technical feasibility findings
   - Present scope and investment estimates ("rough order of magnitude" / "bigger than a bread basket")
   - Identify best quick-win use case for POC

3. **Future Considerations:**
   - Potential proof of concept vs. demo approach
   - Lauren suggested possibly creating a demo with historical data showing categorization capabilities
   - Eli noted POCs typically show UI/interactions, but this case is more about data manipulation
   - Phased rollout plan
   - Training and change management

**What Eli Needs from ParkM:**
- Access to Zoho Desk (doesn't need to be production - sandbox fine, just to see system capabilities)
- Detailed use case documentation from Katie with process steps and tools involved
- Understanding of which use cases to prioritize and in what order

---

## Additional Notes

- **Historical Data:** 8 years of email history available in Zoho for training/testing - Chad offered: "I don't know if it's helpful if you've got a bot that just sort of helps you go, 'Okay, bot, go look at these eight years worth of emails and tell me what see'"
- **Spanish Support:** Currently using Google Translate; customers respond better when replies stay in English (they translate on their end)
- **Risk Mitigation:** Financial transactions are low value ($10 permits), reducing risk of automation errors
- **Scale Potential:** Looking to handle growth without adding headcount rather than replacing existing team
- **Complexity Challenge:** "The bloody complicated part is trying to figure out what is this person really asking for" - not the backend systems but understanding customer intent
- **Bot Estimation:** Chad's gut feeling - bot might handle 10% initially, then maybe 20%, would be "lucky if it could handle 50%"
- **Email Categorization Idea:** Patrick suggested AI could categorize incoming emails before they enter the queue, potentially routing to specialized agents
- **Personal Note:** Patrick needs to pick up Girl Scout cookies at 10 AM before Friday meeting; Lauren's daughter Avery is interested in buying from Patrick's daughter Evelyn, who is defending her crown as top seller

---

## Contact Information

**ParkM Team:**
- Chad Craven - CEO
- Katie Schaeffer - Operations Manager
- Patrick Cameron - Outside Sales Consultant

**CRM Wizards Team:**
- Eli Kiedrowski - Technical Lead
- Lauren Kiedrowski - Business Development
