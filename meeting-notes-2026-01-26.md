# ParkM & CRM Wizards - Initial Meeting

**Date:** January 26, 2026  
**Participants:** 
- **ParkM:** Chad Craven (CEO), Katie Schaeffer (Operations Manager), Patrick Cameron (Outside Sales Consultant)
- **CRM Wizards:** Eli Kiedrowski, Lauren Kiedrowski

---

## Meeting Summary

### Meeting Context and Introductions

Patrick Cameron explained the meeting originated from a Friday lunch conversation with Lauren Kiedrowski, where she mentioned doing "agent type stuff" for insurance companies. Patrick asked if they could apply that expertise to ParkM with Zoho, to which they said yes (00:02:25). Patrick emphasized that Lauren and Eli are known for moving quickly and providing candid feedback without drama, stating "they'll tell you when you're full of s*** or your ideas are full of s***" (00:02:25).

### About ParkM

ParkM is a virtual parking permit provider for multifamily housing communities operating on a revenue-share model. Instead of selling software, ParkM goes to properties and positions a revenue share, splitting revenue from guest or resident permits, which increases the asset value by adding an additional revenue stream (00:10:27).

**Support Team:**
- 23-25 person customer support division (00:04:07)
- 100% email-based support (no phone/chat)
- Support quality is a key differentiator and selling point - "we sell on it," "we're known for our support in a really good way" (00:04:07)
- Team consists mainly of part-time college students and stay-at-home moms (00:05:04)
- Takes approximately 3 months for new hires to become fully effective (not just training time, but time to work confidently) (00:05:04, 00:28:01)
- Recent growth: 6 new hires in the last year causing escalations due to not following complete processes (00:26:16)

**Customer Base:**
- B2C support for multifamily residents (00:11:27)
- Lower-income demographic, less educated (00:11:27)
- Many customers with English as second language
- Some literacy challenges - "there are some literacy challenges... more so in our English speakers" (00:11:27)
- Communication challenge: "the bloody complicated part is trying to figure out what is this person really asking for" (00:21:01)

### Current Challenges

1. **Scaling Issues:** 6 new hires in the past year leading to increased escalations (00:26:16)
2. **Process Inconsistencies:** New staff "not going through the process like we'd like them to" - not handling things efficiently and missing steps (00:26:16)
3. **Training Time:** 3-month ramp-up time for full effectiveness (00:05:04)
4. **High Volume Categories:** 20% of tickets are refund requests (00:09:28)
5. **Lack of Workflow Guidance:** No in-system reminders or process checkers - "there's nothing in the flow that reminds them right now" (00:26:16)
6. **Complex Inbound Questions:** Understanding what customers are actually asking for is extremely challenging (00:21:01)

### Spanish Language Support Strategy

ParkM receives many inbound Spanish requests. They use Google Translate to understand incoming messages, but send responses back in English rather than translating them to Spanish (00:12:33). 

**Rationale:** Customers typically have their phones set up to translate anyway, so double-translating created a "game of telephone" effect that was worse than just responding in English (00:12:33). This approach has proven more effective despite the counter-intuitive nature.

### Technical Environment

- **Zoho Desk:** Email ticketing and queue management
- **App Platform:** Separate system for permit data (no current API integration with Zoho)
- **Stripe:** Payment processing (APIs through app platform)
- **Google Translate:** Spanish language support (respond in English, customer's phone translates)

### Proposed Solution Approach

**CRM Wizards Background:**
- Lauren Kiedrowski recently stepped away from Google (July 2025) after a decade to work with Eli's consulting business (00:05:59)
- Eli Kiedrowski has run a software consulting business since 2019, primarily in Salesforce ecosystem but expanding across platforms (00:07:16)
- Team recently built an AI call receptionist for another client, suggesting similar capabilities for email-based support (00:08:16)
- Lauren mentioned their team is "building so much faster" with AI, allowing them to take on more customers and work (00:07:16)

**Initial Phase (80/20 Rule):**
- Eli Kiedrowski recommended starting with 80% human interaction, 20% AI assistance (00:17:44)
- Monitor and validate before scaling up - "once we get comfortable, we have some good time under our belt, then we can say, 'Okay, we feel comfortable, let's flip it now 20/80 or vice versa'" (00:17:44)
- Build confidence with quick wins - finding smaller, simpler use cases first (00:14:17)
- Katie Schaeffer confirmed preference for "baby step" approach with AI as assist or running in back end with human double-checking (00:16:40)

**Potential Use Cases:**
1. **Refund Processing:** 20% of ticket volume (00:09:28)
   - Initial target but may be too complex for first implementation (00:13:23)
   - Validate move-out date
   - Check permit status
   - Apply 30-day refund policy
   - Route to accounting team
   - Auto-respond to customer

2. **Account Updates:** License plate changes, vehicle updates (00:22:03)
   - Potentially simpler starting point
   - Customer example: "I just bought a new car. I need to update my plate" but they don't specify which car to replace (00:30:52)

3. **Permit Inquiries:** Status checks, general questions
4. **AI Wizard/Process Guide:** Help CSRs follow proper procedures with in-system reminders (00:26:16, 00:27:11)

**Chad Craven's Vision for Full Automation:**

Chad described the ideal future state for easy refund cases (00:17:44):
1. Email arrives: "Hey, I moved out last month and you guys charge me. I demand a refund."
2. Bot verifies: Customer lived in community, already canceled permit
3. Bot responds: "Yes, we see that you've already canceled your permit, so you'll no longer be charged again in the future and I've submitted your refund request over to our accounting team."
4. Accounting approves
5. Bot follows up: "We see you've moved out. I've processed the refund already. You should see an email about it. Give 5-10 days for your bank to post it."

**For Complex Cases:** When scenarios aren't clear-cut (multiple permits, guest permits, unclear account connections), the bot would recognize limitations and respond: "Hey, I've gotten your request. I've sent it over to our accounting team to review and get back to you" (00:19:30).

**Goal:** Not necessarily to replace headcount but to "grow with the same number of people" (00:20:20). As Chad noted, the flow isn't huge enough to eliminate positions, but it would allow scaling without proportional staff increases. Board expectations about replacing people may not align with reality.

**Risk Mitigation:** Financial transactions are low-risk since charges are only $10 per permit, and bot could be constrained to "only get to do one refund" per customer within the 30-day window (00:18:38).

**AI Wizard for CSR Guidance:**

Katie identified a critical need for in-workflow guidance (00:26:16): "One thing we could desperately need is like a wizard or something that's telling the CSR here's what you need to do and did you do all of these things... They get trained on it, but there's nothing in the flow that reminds them right now."

Eli suggested implementing simple guardrails/handrails with instructions directly on the page agents view, similar to lead process steps that drop down to show what needs to be done next (00:27:11). This could help reduce the 3-month ramp-up time for new hires.

Lauren referenced a recent AI wizard they built for the roofing industry - a two-way voice AI helping roofers on the job take measurements and photos in proper sequence, even while wearing gloves in freezing weather (00:29:08). A similar but simpler concept could guide CSRs through support processes.

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

1. **Start Simple:** Focus on smaller, clearer use cases first for quick wins rather than complex refund processing (00:13:23)
2. **Human-in-Loop:** Maintain human validation/approval initially before full automation (00:16:40, 00:17:44)
3. **Phased Approach:** Build confidence with 80/20 human/AI split, then scale AI involvement (00:17:44)
4. **Integration Required:** API integration between Zoho and app platform is necessary (00:32:34)
5. **Process Guidance Priority:** Consider "wizard" UI to help CSRs follow proper procedures and reduce training time (00:26:16, 00:27:11)
6. **Goal is Growth, Not Reduction:** Primary objective is to handle growth without proportional headcount increases rather than replacing existing team (00:20:20)

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
1. Email arrives at support@parkm.com (00:30:01)
2. Forwarded to Zoho Desk (00:30:01)
3. Enters queue (4-5 agents working simultaneously) (00:30:01)
4. Agent takes ownership of ticket (00:30:01)
5. Agent reviews notes in Zoho (00:30:52)
6. Agent switches to app platform to view/modify permit data (00:30:52)
7. Agent responds via Zoho Desk

**Eli's Questions About Workflow (00:30:52, 00:32:34):**
- Confirmed email goes to Zoho Desk queue
- Agents take ownership of tickets
- Most work done in separate app platform, not Zoho
- No current API between the two systems
- Integration will be necessary to enable AI solution to access both systems and take actions

### Integration Considerations
- Zoho Desk has no current API connection to app platform (00:31:36)
- App platform has other integrations (just not with Zoho) - both systems are API-capable (00:31:36)
- Need to evaluate Zoho's API capabilities and customization options
- **Chad's Concern:** Where/how external app data would be displayed, labeled, and categorized within Zoho's structure (00:34:24, 00:36:28)
- **Eli's Response:** May not need to store app data in Zoho; Zoho primarily used for email extraction and case management, with API calls retrieving app data as needed (00:38:46, 00:39:34)
- May need custom components/views within Zoho or potentially display data in app platform instead
- **Third System:** Stripe for payments, but most refunds can be processed through app platform which APIs to Stripe (00:36:28)
- **Historical Data Available:** 8 years of email history in Zoho available for bot training/testing (00:43:44)

**Eli's Technical Approach (00:38:46, 00:39:34):**
- Use Zoho to extract information from emails and manage case flow
- API calls to app platform to gather customer/permit information
- Apply logic, reasoning, and decision-making based on extracted data
- May use custom AI/LLMs for complex reasoning or standard automation for simpler data-based decisions
- Not necessarily storing all app data within Zoho's structure

---

## Next Steps

1. **Immediate (Mon-Wed):**
   - Execute action items (access, NDA, documentation)
   - Eli to validate Zoho technical capabilities and limitations (00:41:05, 00:43:44)
   - Eli to meet with technical architect to assess feasibility - "I should have an answer in terms of the technicalities by tomorrow. I'm honestly not concerned though" (00:47:46)
   - Katie to document use cases - "Don't bang your head on it, Katie. Just nice and simple. Send it my way when you're done. If I need more detail, I'll ask a question" (00:49:11)
   - Chad to provide Zoho access for technical exploration (00:43:44, 00:47:46)
   - Exchange mutual NDA (00:47:00, 00:47:46)

2. **Friday Meeting (00:49:55):**
   - Review detailed use cases
   - Discuss technical feasibility findings
   - Present scope and investment estimates ("rough order of magnitude" / "bigger than a bread basket") (00:42:08)
   - Identify best quick-win use case for POC

3. **Future Considerations:**
   - Potential proof of concept vs. demo approach (00:44:28)
   - Lauren suggested possibly creating a demo with historical data showing categorization capabilities (00:44:28)
   - Eli noted POCs typically show UI/interactions, but this case is more about data manipulation (00:45:11)
   - Phased rollout plan
   - Training and change management

**What Eli Needs from ParkM (00:42:08, 00:46:03):**
- Access to Zoho Desk (doesn't need to be production - sandbox fine, just to see system capabilities)
- Detailed use case documentation from Katie with process steps and tools involved
- Understanding of which use cases to prioritize and in what order

---

## Additional Notes

- **Historical Data:** 8 years of email history available in Zoho for training/testing - Chad offered: "I don't know if it's helpful if you've got a bot that just sort of helps you go, 'Okay, bot, go look at these eight years worth of emails and tell me what see'" (00:43:44)
- **Spanish Support:** Currently using Google Translate; customers respond better when replies stay in English (they translate on their end) (00:12:33)
- **Risk Mitigation:** Financial transactions are low value ($10 permits), reducing risk of automation errors (00:18:38)
- **Scale Potential:** Looking to handle growth without adding headcount rather than replacing existing team (00:20:20)
- **Complexity Challenge:** "The bloody complicated part is trying to figure out what is this person really asking for" - not the backend systems but understanding customer intent (00:21:01)
- **Bot Estimation:** Chad's gut feeling - bot might handle 10% initially, then maybe 20%, would be "lucky if it could handle 50%" (00:21:01)
- **Email Categorization Idea:** Patrick suggested AI could categorize incoming emails before they enter the queue, potentially routing to specialized agents (00:41:05)
- **Personal Note:** Patrick needs to pick up Girl Scout cookies at 10 AM before Friday meeting; Lauren's daughter Avery is interested in buying from Patrick's daughter Evelyn, who is defending her crown as top seller (00:49:55)

---

## Contact Information

**ParkM Team:**
- Chad Craven - CEO
- Katie Schaeffer - Operations Manager
- Patrick Cameron - Outside Sales Consultant

**CRM Wizards Team:**
- Eli Kiedrowski - Technical Lead
- Lauren Kiedrowski - Business Development
