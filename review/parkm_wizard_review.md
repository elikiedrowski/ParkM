# ParkM AI Wizard Review Document

**Generated:** March 12, 2026
**Purpose:** Review all 49 intent classifications and wizard processes for accuracy
**Reviewer:** Sadie Hardy

---

## How to Use This Document

For each test case below, please review:
1. **Classification** - Did the AI correctly identify the intent from the email?
2. **Wizard Steps** - Are the steps accurate and in the right order?
3. **Response Templates** - Are the suggested responses appropriate?
4. **Decision Points** - Do the branching options make sense?

Mark any issues with a note (e.g., 'Step 3 should come before Step 2' or 'Missing step for XYZ').

---

# Part 1: Single-Intent Test Cases (49)

## Test #1: Customer Canceling a Permit and Refunding

**Subject:** Cancel my parking permit - need refund
**From:** jane.doe@gmail.com

**Email Body:**
> Hi, I moved out of Riverside Apartments on March 1st 2026. My license plate is ABC1234. I need to cancel my parking permit and get a refund for the remaining balance. I was charged $75 on February 15th but I already moved out. Please help.

### Classification Results

- **Tags:** Customer Canceling a Permit and Refunding
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **ABC1234**, `move_out_date`: **March 1st 2026**, `property_name`: **Riverside Apartments**, `amount`: **75**
- **Requires Human Review:** No
- **Routing:** Accounting/Refunds

### Wizard Steps

**$ Cancel Permit + Refund**

> Customer wants to cancel their permit AND get a refund. Refund window is 30 days from the LAST charge date.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Vehicles and Permits tab
      - *Confirm the license plate and permit. Extracted plate: ABC1234*
      - Entity `license_plate`: **ABC1234** (found in email)
   3. **[Required]** Check if permit is already canceled
      - *If already canceled, note the cancellation date for eligibility calculation.*
   4. **[Required]** Open the Payments tab - find the last charge date and amount
      - *Refund window is 30 days from the LAST charge date.*
   5. **[Required]** Verify move-out date is within the 30-day refund window
      - *Move-out date from email: March 1st 2026. If not found, ask the customer.*
      - Entity `move_out_date`: **March 1st 2026** (found in email)
   6. **[Required]** Set permit to Delay Cancel (1 week out)
      - *Do NOT cancel immediately. Use Actions > Cancel > Delay Cancellation and set to 1 week. Delete the 'Next Recurring Date' so they are not charged again. Tell resident: 'Your permit is set to cancel on [date]. You will not be charged again.'*
   7. **[Required]** Determine refund eligibility
      - **DECISION POINT** - Choose one:
        - Eligible - Forward to Accounting (action: `submit_refund`) -> template: `refund_forward_accounting.html`
        - Deny - Outside 30-Day Window (action: `deny_outside_window`) -> template: `refund_denied_outside_window.html`
   8. **[Required]** If eligible: Forward WHOLE thread to accounting@parkm.com
      - *Include: customer email on account, refund amount, reason (e.g. 'Moved Out'), and property name. Format:
[email]
$[amount]
[reason]
[property name]
Then set ticket status to 'Waiting on Accounting'.*
      - Email: mailto:accounting@parkm.com
      - *(Only shown if action = `submit_refund`)*
   9. **[Required]** Send response email to customer
   10. **[Required]** Update ticket status (Waiting on Accounting or Closed)

   **Validation Checklist (on close):**
   - [ ] Did you verify the move-out date is within 30 days of the last charge?
   - [ ] Did you set the permit to delay cancel (not immediate)?
   - [ ] Did you delete the Next Recurring Date?
   - [ ] Did you forward to accounting@parkm.com (if eligible) OR send denial?

   **Quick Response Templates:**
   - Missing License Plate (`missing_license_plate.html`)
   - Missing Move-Out Date (`missing_move_out_date.html`)
   - Refund Approved (`refund_approved.html`)
   - Refund Denied - Outside Window (`refund_denied_outside_window.html`)
   - Cancellation Confirmed (`cancellation_confirmed.html`)

---

## Test #2: Customer Inquiring for Grandfathered Permit

**Subject:** Grandfathered permit question
**From:** mike.smith@yahoo.com

**Email Body:**
> Hello, I've been living at Oak Hill Community for over 3 years now. I was told my permit was grandfathered in under the old pricing. Can you confirm that my permit is still valid under the grandfathered rate? My plate is XYZ5678.

### Classification Results

- **Tags:** Customer Inquiring for Grandfathered Permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **XYZ5678**, `property_name`: **Oak Hill Community**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**# Grandfathered Permit Inquiry**

> Customer is asking about a grandfathered permit. Grandfathered permits are free permits issued when a complex approves it. The COMPLEX must email us to approve.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Check if the customer already has a grandfathered permit
      - *Look under Vehicles and Permits for a permit labeled 'grandfathered' or a free permit.*
   3. **[Required]** Does the customer have complex approval?
      - *The leasing office/property manager MUST email support@parkm.com to approve a grandfathered permit. The customer cannot self-approve.*
      - **DECISION POINT** - Choose one:
        - Complex has approved - Issue free permit (action: `issue_grandfathered`)
        - No approval yet - Direct customer to leasing office (action: `direct_to_leasing`)
   4. **[Required]** If approved: Issue a free permit
      - *Actions > Sale Permit > Select community > Toggle 'Issue Free Permit' ON > Set expiration to 1 year (or date from complex if provided, otherwise default 1 year and adjust later). Label permit 'Grandfathered' under custom permit number. Do NOT enter a Next Recurring Date.*
      - *(Only shown if action = `issue_grandfathered`)*
   5. **[Required]** If no approval: Direct customer to their leasing office
      - *Tell them their leasing office needs to email support@parkm.com to approve the grandfathered permit with their vehicle info.*
      - Template: `grandfathered_needs_approval.html`
      - *(Only shown if action = `direct_to_leasing`)*
   6. **[Required]** Send confirmation to customer and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify complex approval before issuing a free permit?
   - [ ] If issued, did you label the permit 'Grandfathered'?

   **Quick Response Templates:**
   - Grandfathered - Needs Approval (`grandfathered_needs_approval.html`)
   - Grandfathered - Permit Issued (`grandfathered_permit_issued.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #3: Customer Inquiring for Locked Down Permit

**Subject:** Why is my permit locked?
**From:** sarah.jones@hotmail.com

**Email Body:**
> I tried to renew my parking permit online but it says my permit is locked down. I live at Maple Grove unit 204. Can someone explain why it's locked and what I need to do? My plate is LMN9012.

### Classification Results

- **Tags:** Customer Inquiring for Locked Down Permit
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **LMN9012**, `property_name`: **Maple Grove**, `unit_number`: **204**
- **Requires Human Review:** Yes
- **Routing:** General Support

### Wizard Steps

**# Locked Down Permit Inquiry**

> Customer is asking about a locked-down permit. These permits show as 'Sold Out' because the property has locked down ALL permit purchases community-wide. CSRs CANNOT open these up — overrides are per-account and do NOT work for locked-down permits. Forward to Internal Managers.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Confirm the permits show as 'Sold Out' for the community
      - *Locked-down permits are community-wide restrictions set by the property. They are different from per-account overrides. A typical override will NOT open up locked-down permits.*
   3. **[Required]** Forward the WHOLE thread to Internal Managers
      - *CSRs do not have permission to open up locked-down permit types. Forward to internalmanagers@parkm.com and include:
- Customer email
- Property/community name
- What permit type they need
Let the customer know a manager will review their request.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Respond to the customer
      - *Let them know you've sent their request to a manager for review. Their leasing office may also need to approve the permit — suggest they contact their leasing office as well.*
   5. **[Required]** Set ticket status to Waiting/Escalated

   **Validation Checklist (on close):**
   - [ ] Did you forward to internalmanagers@parkm.com?
   - [ ] Did you NOT try to override or open up the permits yourself?
   - [ ] Did you respond to the customer?

   **Quick Response Templates:**
   - Locked Permit - Forwarded to Manager (`locked_permit_needs_approval.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #4: Customer Inquiring for Additional Permit

**Subject:** Need a second parking permit
**From:** tom.williams@gmail.com

**Email Body:**
> Hi there, I already have one permit for my Toyota but I just got a second car, a Honda Civic plate DEF3456. I live at Sunset Ridge apartment 112. Can I get an additional permit? What's the process and cost?

### Classification Results

- **Tags:** Customer Inquiring for Additional Permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **DEF3456**, `property_name`: **Sunset Ridge**, `unit_number`: **112**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**P Additional Permit Inquiry**

> Customer wants an additional permit added to their account. Some properties restrict extra permits and require an override/approval from the leasing office.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Check how many permits the customer currently has
      - *Look at Vehicles and Permits tab. Note how many active permits exist.*
   3. **[Required]** Check if the property allows additional permits
      - *Check Zoho CRM notes for the property. Some properties cap the number of permits per unit. If restricted, the leasing office must email to approve.*
   4. **[Required]** Is the additional permit approved?
      - **DECISION POINT** - Choose one:
        - Allowed or property approved - Help purchase/issue permit (action: `issue_additional`)
        - Needs property approval - Direct to leasing office (action: `direct_to_leasing`)
   5. **[Required]** If approved: Open permits/do override if needed, then help customer purchase
      - *If locked down, you may need to open up permits or change resident type first. Then either help them buy online or purchase on backend via Actions > Sale Permit.*
      - *(Only shown if action = `issue_additional`)*
   6. **[Required]** Send response to customer and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the property allows additional permits?
   - [ ] Did you respond to the customer?

   **Quick Response Templates:**
   - Additional Permit - Needs Approval (`additional_permit_needs_approval.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #5: Customer Rental Car

**Subject:** Rental car temporary permit needed
**From:** lisa.brown@outlook.com

**Email Body:**
> My car is in the shop and I have a rental car for the next two weeks. The rental plate is RENT789. I live at Creekside Village unit 305. How do I get a temporary permit so I don't get towed? My regular plate is GHI7890.

### Classification Results

- **Tags:** Customer Rental Car
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **RENT789**, `property_name`: **Creekside Village**, `unit_number`: **305**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**R Rental Car**

> Customer has a rental car (their car is in the shop, etc.) and needs a temporary permit. Issue a FREE temporary permit for the rental - do NOT modify their existing permit.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Confirm the customer has an existing active permit on their regular vehicle
      - *Their regular permit should stay in place. We do NOT want them to modify it because they often forget to switch back.*
   3. **[Required]** Ask how long they expect to have the rental
      - *If they say 2 weeks, issue for 4 weeks to allow buffer time. Never set it to 2055.*
   4. **[Required]** Issue a FREE temporary permit for the rental vehicle
      - *Actions > Sale Permit > Select community > Toggle 'Issue Free Permit' ON > Set expiration (double the expected rental time). Label it 'Temp permit' under custom permit number. Add rental vehicle info (plate, make, model, etc.). Do NOT enter a Next Recurring Date.*
   5. **[Required]** Send confirmation to customer with screenshot of the permit preview
      - Template: `rental_car_temp_permit.html`
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you issue a FREE temporary permit (not modify existing)?
   - [ ] Did you set a reasonable expiration date (not 2055)?
   - [ ] Did you confirm with the customer?

   **Quick Response Templates:**
   - Rental Car - Temp Permit Issued (`rental_car_temp_permit.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #6: Customer Double Charged or Extra Charges

**Subject:** Charged twice for my permit this month!
**From:** david.garcia@gmail.com

**Email Body:**
> I was charged $50 on March 1st and then another $50 on March 3rd for my parking permit at Willow Park. I should only have been charged once. My plate is JKL2345. Can you please look into this and refund the extra charge?

### Classification Results

- **Tags:** Customer Double Charged or Extra Charges
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **JKL2345**, `property_name`: **Willow Park**, `amount`: **50**
- **Requires Human Review:** No
- **Routing:** Accounting/Refunds

### Wizard Steps

**$ Double Charged / Extra Charges**

> Customer is reporting a billing issue - double charge, unexpected charge, or extra fees. Investigate in the Payments tab before responding.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Payments & Transactions tab
      - *Look for duplicate charges, unexpected amounts, failed payment retries, convenience fees, or credit card surcharges.*
   3. **[Required]** Confirm the license plate matches their account
      - *Extracted plate: JKL2345*
      - Entity `license_plate`: **JKL2345** (found in email)
   4. **[Required]** Determine the cause of the charge
      - *Common causes:
- Convenience fee / credit card surcharge (these are normal and disclosed)
- Permit renewed as expected (customer forgot)
- Actual duplicate charge (system error)
- NSF fee (non-sufficient funds)
- Taxes on the permit*
      - **DECISION POINT** - Choose one:
        - Legitimate charge - Explain to customer (action: `explain_charge`)
        - Duplicate/error - Forward to accounting for refund (action: `escalate_accounting`)
   5. **[Required]** If duplicate/error: Forward WHOLE thread to accounting@parkm.com
      - *Include: email on account, refund amount, reason, property name.
Then set ticket to 'Waiting on Accounting'.*
      - Email: mailto:accounting@parkm.com
      - *(Only shown if action = `escalate_accounting`)*
   6. **[Required]** If legitimate: Explain the charge clearly to the customer
      - *Be helpful and clear. Explain convenience fees, surcharges, or recurring permit charges as applicable.*
      - *(Only shown if action = `explain_charge`)*
   7. **[Required]** Send response and update ticket status

   **Validation Checklist (on close):**
   - [ ] Did you investigate the charge(s) in the Payments tab?
   - [ ] Did you either explain the charge OR forward to accounting?

   **Quick Response Templates:**
   - Payment Issue Follow-Up (`payment_issue_follow_up.html`)
   - Charge Explanation (`charge_explanation.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #7: Customer Guest Permit and Pricing Questions

**Subject:** Guest parking permit info
**From:** emily.wilson@gmail.com

**Email Body:**
> Hi, I'm having family visit me at Pine Valley Apartments next weekend. How do I get a guest parking permit? How much does it cost and how long is it valid? I'm in unit 401.

### Classification Results

- **Tags:** Customer Guest Permit and Pricing Questions
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** low
- **Language:** english
- **Key Entities:** `property_name`: **Pine Valley Apartments**, `unit_number`: **401**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**? Guest Permit & Pricing**

> Customer is asking about guest permits, pricing, or how guest permits work.

   1. Search parkm.app by customer email (if they have an account)
   2. **[Required]** Check the property's guest permit setup in parkm.app
      - *Go to the property > check guest permit types, pricing, duration limits, and any restrictions. Some properties have limits on guest permits.*
   3. **[Required]** Answer the customer's question about guest permits
      - *Key info:
- Guest permits are purchased by the RESIDENT for their guest's vehicle
- Multiple people can buy guest permits for the same vehicle
- Guest permits may have limits per property
- Guests can pre-purchase permits
- Residents can extend guest permits
- Direct them to: https://parkm.app/permit/community?forceChange=true*
   4. **[Required]** Send response and close ticket
      - Template: `guest_permit_info.html`

   **Validation Checklist (on close):**
   - [ ] Did you answer the customer's specific question about guest permits/pricing?

   **Quick Response Templates:**
   - Guest Permit Info (`guest_permit_info.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #8: Customer Miscellaneous Questions

**Subject:** General question about parking
**From:** chris.martinez@yahoo.com

**Email Body:**
> Hello, I just moved into Lakeside Terrace and I have a few questions about the parking situation. Is there assigned parking? Are there any visitor spots? What are the quiet hours for the parking garage? Thanks!

### Classification Results

- **Tags:** Customer Miscellaneous Questions
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** low
- **Language:** english
- **Key Entities:** `property_name`: **Lakeside Terrace**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**? Miscellaneous Question**

> General customer question that does not fit other categories. Read carefully and respond with a clear, helpful answer.

   1. **[Required]** Read the full email carefully
   2. Search parkm.app by customer email (if account-specific)
   3. **[Required]** Research the answer using Zoho CRM notes and parkm.app
      - *Check property notes in Zoho CRM for any special rules. If unsure, email internalmanagers@parkm.com for guidance.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Compose a clear, friendly, and informative response
      - *Remember: the goal is to give residents clear and informative answers, even if it means writing a more detailed email.*
      - Template: `general_inquiry_response.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you fully answer the customer's question?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)
   - FAQ Page Link (`faq_link.html`)

---

## Test #9: Customer Sending Money Order

**Subject:** Sending money order for parking permit
**From:** nancy.taylor@aol.com

**Email Body:**
> Hi, I don't have a credit card so I'd like to pay for my parking permit with a money order. I live at Brookfield Commons unit 210. Where do I mail the money order and who do I make it out to? The amount should be $45.

### Classification Results

- **Tags:** Customer Sending Money Order
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Brookfield Commons**, `amount`: **45**, `unit_number`: **210**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**$ Customer Money Order**

> Customer is paying by money order. Issue a free permit for the paid duration while waiting for the money order to be processed.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Confirm vehicle info and which property/permit type they need
      - *Extracted plate: [License Plate — Not Found in Email]*
      - Entity `license_plate`: *Not found in email*
   3. **[Required]** Issue a FREE permit for the duration they are paying for
      - *Actions > Sale Permit > Toggle 'Issue Free Permit' ON > Set expiration to match the period they paid for (e.g., 1 month). Label it with the money order reference if available.*
   4. **[Required]** Confirm the money order payment details
      - *Note: money orders are handled separately from online payments. The money order will be processed by accounting.*
   5. **[Required]** Send confirmation to customer and close ticket
      - Template: `money_order_received.html`

   **Validation Checklist (on close):**
   - [ ] Did you issue a free permit for the paid duration?
   - [ ] Did you confirm with the customer?

   **Quick Response Templates:**
   - Money Order Received (`money_order_received.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #10: Customer Need help buying a permit

**Subject:** How do I buy a parking permit?
**From:** kevin.anderson@gmail.com

**Email Body:**
> I just signed my lease at Harbor Point Apartments and the leasing office said I need to buy a parking permit online. I went to the website but I'm confused about which permit to select. I'm in building C, unit 108. Can you walk me through the process?

### Classification Results

- **Tags:** Customer Need help buying a permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Harbor Point Apartments**, `unit_number`: **108**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**P Help Buying a Permit**

> Customer needs help purchasing a permit for the first time.

   1. **[Required]** Search parkm.app by customer email - check if they have an account
   2. **[Required]** If no account: Direct them to create one
      - *Website: https://parkm.app/permit/community?forceChange=true
OR: https://www.parkm.com/*
   3. **[Required]** Identify the issue preventing purchase
      - *Common issues:
- Can't find their community
- Resident type is wrong (needs to be changed)
- Permits are locked down (needs override)
- Payment method issues
- Error message during checkout*
   4. If there's a system error preventing purchase: Issue a free temporary permit
      - *Issue a free permit for a few days/1 week while Internal Managers investigate the error. Email internalmanagers@parkm.com with details of the error.*
      - Email: mailto:internalmanagers@parkm.com
   5. **[Required]** If you can resolve it: Help them purchase or guide them through the process
      - *You can purchase on the backend: Actions > Sale Permit. Make sure they have a payment method on file and you have permission to charge it. Toggle OFF 'Issue Free Permit' and select their payment method.*
   6. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you help the customer purchase or explain how to?
   - [ ] If there was an error, did you issue a temp permit and escalate?

   **Quick Response Templates:**
   - How to Buy a Permit (`how_to_buy_permit.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #11: Customer Need Help Renewing Permit

**Subject:** Permit renewal issue
**From:** amanda.thomas@gmail.com

**Email Body:**
> My parking permit expired yesterday and I'm trying to renew it online but the system keeps giving me an error. I live at Elmwood Estates unit 502 and my plate is MNO4567. Can you help me renew my permit before I get towed?

### Classification Results

- **Tags:** Customer Need Help Renewing Permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **MNO4567**, `property_name`: **Elmwood Estates**, `unit_number`: **502**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**P Help Renewing Permit**

> Customer needs help renewing their existing permit.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Check the permit status and next recurring date
      - *Is it a recurring paid permit? Check the next recurring date and expiration date. Recurring permits auto-renew by pushing out the expiration date each charge cycle.*
   3. **[Required]** Identify the renewal issue
      - *Common issues:
- Payment method expired/declined
- Permit was accidentally canceled
- Need to change charge date
- Permit expired and needs reactivation*
      - **DECISION POINT** - Choose one:
        - Payment issue - Update payment method (action: `update_payment`)
        - Permit expired - Reactivate (action: `reactivate`)
        - Need to change charge date (action: `change_date`)
   4. **[Required]** Resolve the issue
      - *For payment: Have customer update card at https://parkm.app/account/login
For reactivation: May need to issue a new permit
For charge date: Actions > Move Next Recurring Date*
   5. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the permit status and resolve the renewal issue?
   - [ ] Did you respond to the customer?

   **Quick Response Templates:**
   - How to Update Payment (`how_to_update_payment.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #12: Customer Need Help Creating an Account

**Subject:** Can't create my ParkM account
**From:** jessica.lee@gmail.com

**Email Body:**
> Hi, I'm a new resident at Stonegate Apartments unit 301. The leasing office told me to create an account on ParkM but when I try to register it says my email is already in use. I've never used ParkM before. My email is jessica.lee@gmail.com. Please help.

### Classification Results

- **Tags:** Customer Need Help Creating an Account
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Stonegate Apartments**, `unit_number`: **301**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**+ Help Creating Account**

> Customer is having trouble creating a ParkM account.

   1. **[Required]** Check if an account already exists for this email
      - *Search parkm.app by email. The customer may already have an account and not realize it.*
   2. If account exists: Send them a password reset
      - *Click 'Reset Password' button on their account, or direct them to https://parkm.app/account/login > 'Forgot Password'*
   3. **[Required]** If no account: Guide them to create one
      - *Direct them to: https://parkm.app/permit/community?forceChange=true
They will need to search for their community and create an account.*
   4. If there's a technical error: Issue a free temp permit and escalate
      - *Issue a free permit for a few days/1 week. Email internalmanagers@parkm.com with the error details so they can investigate.*
      - Email: mailto:internalmanagers@parkm.com
   5. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you help the customer create an account or resolve their issue?

   **Quick Response Templates:**
   - How to Create Account (`how_to_create_account.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #13: Customer New Towing Legislation No Parking

**Subject:** New towing law question
**From:** ryan.clark@gmail.com

**Email Body:**
> I heard there's new legislation about towing in our area. I park at Ridgewood Community and I'm worried about how the new no-parking rules affect my vehicle. Can you explain what the new towing laws mean for residents? My plate is PQR6789.

### Classification Results

- **Tags:** Customer New Towing Legislation No Parking
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **PQR6789**, `property_name`: **Ridgewood Community**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**! Towing Legislation / No Parking**

> Customer has a paid permit but is complaining they have nowhere to park due to the new Colorado towing legislation (passed 2024). This law changed towing rules and may affect how parking is enforced at their community.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Verify the customer has an active paid permit
      - *Confirm they are paying for a permit and the permit is active. Note the community name.*
   3. **[Required]** Understand their complaint
      - *The customer is frustrated because they pay for a permit but cannot find available parking. This is often related to the new Colorado towing legislation (2024) which changed enforcement rules and may result in more unpermitted vehicles not being towed, taking up spots.*
   4. **[Required]** Remind the customer that ParkM sells permits, not parking spaces
      - *ParkM does not guarantee a specific parking spot (unless they have an assigned space). ParkM sells permits and does NOT tow, boot, or ticket vehicles.*
   5. **[Required]** Direct them to their leasing office for parking availability concerns
      - *The leasing office manages the property and parking rules. They can address concerns about parking availability and enforcement with their towing company.*
   6. If unsure how to respond: Escalate to Internal Managers
      - *Email internalmanagers@parkm.com with the thread and summary if the customer is persistent or the situation is unclear.*
      - Email: mailto:internalmanagers@parkm.com
   7. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the customer's permit is active?
   - [ ] Did you direct them to their leasing office for parking availability?
   - [ ] Did you clarify that ParkM does not tow or guarantee spots?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #14: Customer No Plate or Expired Tags

**Subject:** My car has expired tags - will I get towed?
**From:** michelle.lewis@yahoo.com

**Email Body:**
> Hi, I'm waiting for my new registration to come in the mail. My current tags on my car are expired. I live at Cedar Springs unit 115 and my plate is STU8901. Will I get towed or ticketed while I wait for my new tags? What should I do?

### Classification Results

- **Tags:** Customer No Plate or Expired Tags
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **STU8901**, `property_name`: **Cedar Springs**, `unit_number`: **115**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**! No Plate / Expired Tags**

> Customer's vehicle has no physical plates or expired registration tags. ParkM permits are tied to license plates, so they must resolve this first.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Explain that ParkM permits are tied to license plates
      - *The license plate must always be accurate on their permit to avoid towing/booting/ticketing issues.*
   3. **[Required]** Direct the customer to their leasing office
      - *They need to speak to their complex about the expired tags / no plates situation. In the meantime, they need to park OFF SITE since ParkM permits require valid plates.*
   4. **[Required]** Send response using template
      - Template: `no_plate_expired_tags.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you direct the customer to their leasing office?
   - [ ] Did you explain they need to park off site until resolved?

   **Quick Response Templates:**
   - No Plate / Expired Tags (`no_plate_expired_tags.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #15: Customer Someone is Parking in my Spot

**Subject:** Someone keeps parking in my assigned spot!
**From:** brian.walker@gmail.com

**Email Body:**
> There is a black SUV with plate VWX2345 that keeps parking in my assigned spot #42 at Fairview Apartments. This has happened three times this week. I've left notes but they keep doing it. What can be done about this? I'm in unit 208.

### Classification Results

- **Tags:** Customer Someone is Parking in my Spot
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **VWX2345**, `property_name`: **Fairview Apartments**, `unit_number`: **208**, `space_number`: **42**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**! Someone in My Spot**

> Customer is reporting that someone is parking in their assigned space.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Verify the customer's assigned space number
      - *Check their permit for the space number. Extracted space: [Space Number — Not Found in Email]*
      - Entity `space_number`: *Not found in email*
   3. **[Required]** Direct the customer to their leasing office
      - *ParkM does not enforce parking spaces or tow vehicles. The customer should contact their leasing office about the unauthorized vehicle. The leasing office can then contact the towing company if needed.*
   4. If we monitor the property: Forward to Brian McDonough
      - *Check Zoho CRM for 'ParkM Monitoring' checkmark. If we monitor: forward to Brian McDonough so monitors can be alerted. If we don't monitor: direct customer to their monitoring/towing company.*
   5. **[Required]** Send response and close ticket
      - Template: `someone_in_my_spot.html`

   **Validation Checklist (on close):**
   - [ ] Did you direct the customer to their leasing office?
   - [ ] Did you check if ParkM monitors the property?

   **Quick Response Templates:**
   - Someone in My Spot (`someone_in_my_spot.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #16: Customer Parking Space Not in Dropdown

**Subject:** My parking space isn't listed
**From:** jennifer.hall@gmail.com

**Email Body:**
> I'm trying to register my vehicle for space #167 at Highland Park Apartments but the space number isn't showing up in the dropdown menu on the website. I'm in unit 403. Can you add my space to the system?

### Classification Results

- **Tags:** Customer Parking Space Not in Dropdown
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Highland Park Apartments**, `unit_number`: **403**, `space_number`: **167**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**! Space Not in Dropdown**

> Customer's parking space number is not listed in the system dropdown when purchasing a permit.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Check the property's space list in parkm.app
      - *Go to the property and check if the space exists. It may need to be added.*
   3. **[Required]** If the space is missing: Escalate to Internal Managers
      - *Email internalmanagers@parkm.com and ask them to add the missing space to the property. Include the space number and property name.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Issue a free temporary permit while waiting
      - *Issue a free permit for a few days so the customer is covered. Actions > Sale Permit > Toggle 'Issue Free Permit' ON.*
   5. **[Required]** Send response and close/hold ticket

   **Validation Checklist (on close):**
   - [ ] Did you escalate the missing space to Internal Managers?
   - [ ] Did you issue a temp permit to cover the customer?

   **Quick Response Templates:**
   - Space Not Found - Working On It (`space_not_found.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #17: Customer Password Reset

**Subject:** Forgot my password
**From:** daniel.young@gmail.com

**Email Body:**
> I can't remember my password for my ParkM account. I've tried the reset link but I'm not getting the email. My account email is daniel.young@gmail.com. Can you send me a password reset or reset it for me?

### Classification Results

- **Tags:** Customer Password Reset
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** None extracted
- **Requires Human Review:** No
- **Routing:** Quick Updates

### Wizard Steps

**K Password Reset**

> Customer needs help resetting their password.

   1. **[Required]** Search parkm.app by customer email address
      - *Verify the account exists and the email matches.*
   2. **[Required]** Reset password using one of these methods
      - *Option 1: Direct them to https://parkm.app/account/login > 'Forgot Password'
Option 2: Find their account > click 'Reset Password' button
Option 3: Manual reset via Manage User > change password to 'Parking'*
   3. **[Required]** If manual reset, send login credentials
      - *Format:
Username: [their email]
Password: Parking
https://parkm.app/permit/community*
   4. **[Required]** Send response and close ticket
      - Template: `password_reset_sent.html`

   **Validation Checklist (on close):**
   - [ ] Did you reset the password or send instructions?
   - [ ] Did you confirm with the customer?

   **Quick Response Templates:**
   - Password Reset Sent (`password_reset_sent.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #18: Customer Towed Booted Ticketed

**Subject:** MY CAR WAS TOWED!! HELP!!
**From:** mark.king@gmail.com

**Email Body:**
> I came outside this morning and my car is GONE. It was towed from the parking lot at Westwood Apartments. I have a valid permit! My plate is YZA3456 and I'm in unit 510. This is an emergency, I need my car for work. Who towed it and how do I get it back??

### Classification Results

- **Tags:** Customer Towed Booted Ticketed
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **YZA3456**, `property_name`: **Westwood Apartments**, `unit_number`: **510**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**! Towed / Booted / Ticketed**

> Customer's vehicle was towed, booted, or ticketed. Be empathetic. ParkM does NOT tow/boot/ticket - we only sell permits. Offer a proof of permit if applicable.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Check if the vehicle had an active permit at the time of the tow/boot
      - *Extracted plate: YZA3456. Check the vehicle's permit history - was the permit active when the tow/boot occurred?*
      - Entity `license_plate`: **YZA3456** (found in email)
   3. **[Required]** Remind the customer that ParkM is NOT the towing company
      - *ParkM simply sells parking permits. We do not tow, boot, or ticket vehicles. Express empathy: 'I understand how frustrating being towed/booted can be...'*
   4. **[Required]** Determine if a proof of permit is applicable
      - *Only provide proof of permit if the vehicle appeared to have a permit at/around the time of the incident. Proof of permit covers the last 72 hours (3 days) only. If the incident was more than 72 hours ago, they need to work with the tow company using their original receipt.*
      - **DECISION POINT** - Choose one:
        - Vehicle was permitted - Generate Proof of Permit (action: `proof_of_permit`)
        - Vehicle was NOT permitted - Direct to tow company (action: `no_permit`)
   5. **[Required]** If permitted: Generate Proof of Permit
      - *Go to account > Actions > Proof of Permit. Either email it directly (add tow company email if known) or download the PDF and attach it to the thread. Check Zoho CRM for tow company email. After sending, STAY OUT OF IT - do not promise refunds or releases!*
      - *(Only shown if action = `proof_of_permit`)*
   6. **[Required]** If not permitted: Direct to towing company
      - *Look up the tow company for the property in Zoho CRM or in .app under the property's enforcement company. Share the tow company PHONE NUMBER (not email). If tow company is unknown, advise them to look for towing signs posted at the property.*
      - *(Only shown if action = `no_permit`)*
   7. **[Required]** NEVER promise a refund or release of the vehicle
      - *Tow/boot refunds are EXTREMELY rare and require Internal Manager approval. If the customer insists, forward to internalmanagers@parkm.com.*
      - Email: mailto:internalmanagers@parkm.com
   8. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you check the vehicle's permit status at the time of the incident?
   - [ ] Did you provide a proof of permit (if applicable)?
   - [ ] Did you remind the customer ParkM does not tow/boot/ticket?
   - [ ] Did you NOT promise a refund or vehicle release?

   **Quick Response Templates:**
   - Missing License Plate (`missing_license_plate.html`)
   - Tow/Boot Response - Had Permit (`tow_had_permit.html`)
   - Tow/Boot Response - No Permit (`tow_no_permit.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #19: Customer Warned or Tagged

**Subject:** Warning sticker on my car
**From:** stephanie.wright@gmail.com

**Email Body:**
> I found a warning tag on my windshield at Valley View Apartments. It says my vehicle will be towed if not resolved in 48 hours. I have a valid permit for space #23. My plate is BCD4567, unit 102. Why did I get warned?

### Classification Results

- **Tags:** Customer Warned or Tagged
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **BCD4567**, `property_name`: **Valley View Apartments**, `unit_number`: **102**, `space_number`: **23**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**! Warning / Tag**

> Customer received a warning sticker or tag on their vehicle. Tags are warnings with no fees. Focus on helping them get properly permitted.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Ask the customer to send a picture of the tag
      - *This helps identify the reason for the tag and who placed it. In Colorado, ParkM's tags are ORANGE. Other colors = not us.*
   3. **[Required]** Check the vehicle's permit status
      - *Extracted plate: BCD4567. Is the vehicle permitted? Was the plate correct? Check tow history/violations on the vehicle in .app.*
      - Entity `license_plate`: **BCD4567** (found in email)
   4. **[Required]** Determine why they were tagged
      - *Common reasons: no ParkM permit, expired permit, wrong plate on permit, parked in fire lane, parked in handicap spot without placard, parked in someone's assigned spot, expired vehicle tags.*
   5. **[Required]** Help them resolve the issue
      - *If not permitted: help them get a permit
If plate was wrong: update the plate
If other violation: explain and advise
Note: sticker removal is the customer's responsibility - ParkM cannot remove it.*
   6. **[Required]** Send response and close ticket
      - Template: `warning_tag_response.html`

   **Validation Checklist (on close):**
   - [ ] Did you identify why they were tagged?
   - [ ] Did you help them resolve the underlying issue?
   - [ ] Did you clarify that tags are warnings with no fees?

   **Quick Response Templates:**
   - Warning Tag Response (`warning_tag_response.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #20: Customer Payment Help

**Subject:** Payment not going through
**From:** jason.green@yahoo.com

**Email Body:**
> I'm trying to pay for my parking permit at Autumn Ridge but my credit card keeps getting declined. I've tried two different cards. I'm in unit 205. Is there something wrong with the payment system? Can I pay another way?

### Classification Results

- **Tags:** Customer Payment Help
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Autumn Ridge**, `unit_number`: **205**
- **Requires Human Review:** No
- **Routing:** General Support

### Wizard Steps

**$ Payment Help**

> Customer needs general help with payments - can't pay, payment failed, need to update card, etc.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Payments & Transactions tab
      - *Check for failed payments, expired cards, or missing payment methods.*
   3. **[Required]** Identify the payment issue
      - *Common issues:
- Credit/debit card expired or declined
- No payment method on file
- Wants to change payment method
- Bank account issues
- Convenience fee questions*
      - **DECISION POINT** - Choose one:
        - Card expired/declined - Guide to update (action: `update_card`)
        - No payment method - Help add one (action: `add_payment`)
        - Convenience fee question - Explain (action: `explain_fee`)
   4. **[Required]** Help resolve the payment issue
      - *For card updates: Direct them to https://parkm.app/account/login to update their payment method. Or you can delete the old method on backend: Payments tab > delete old card. Note: we can only delete payment methods, NOT add them on the backend.*
   5. If payment is stuck and they need to park tonight: Issue a free temp permit
      - *Issue for a few days while the payment issue is resolved.*
   6. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you identify and resolve the payment issue?
   - [ ] Did you respond to the customer?

   **Quick Response Templates:**
   - How to Update Payment (`how_to_update_payment.html`)
   - Payment Issue Follow-Up (`payment_issue_follow_up.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #21: Customer Update Vehicle Info

**Subject:** Need to update my license plate
**From:** laura.adams@gmail.com

**Email Body:**
> Hi, I just got a new car and need to update my license plate on my parking permit. Old plate: EFG5678, new plate: HIJ6789. I live at Magnolia Gardens unit 304. Can you update this for me?

### Classification Results

- **Tags:** Customer Update Vehicle Info
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **HIJ6789**, `property_name`: **Magnolia Gardens**, `unit_number`: **304**
- **Requires Human Review:** No
- **Routing:** Quick Updates

### Wizard Steps

**E Update Vehicle Info**

> Customer needs to update their vehicle information (license plate, make, model, etc.).

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Locate the vehicle they want to update
      - *Extracted plate: HIJ6789*
      - Entity `license_plate`: **HIJ6789** (found in email)
   3. **[Required]** Determine what needs to be updated
      - *LICENSE PLATE change: Actions > Modify License Plate > Enter new plate > Toggle 'Transfer All Active Permits' > Save
OTHER changes (make, model, VIN, color): Actions > Edit Vehicle > Make changes > Save*
   4. **[Required]** Make the update in parkm.app
   5. **[Required]** Verify the change saved correctly
      - *Refresh the page and confirm the update is reflected.*
   6. **[Required]** Send confirmation to customer
      - Template: `vehicle_update_confirmed.html`
   7. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the update saved correctly?
   - [ ] Did you use 'Modify License Plate' (not 'Edit Vehicle') for plate changes?
   - [ ] Did you transfer active permits to the new plate?

   **Quick Response Templates:**
   - Vehicle Update Confirmed (`vehicle_update_confirmed.html`)
   - Missing License Plate (`missing_license_plate.html`)

---

## Test #22: Customer Update Contact Info

**Subject:** Update my phone number and email
**From:** rachel.nelson@gmail.com

**Email Body:**
> Hi, I need to update my contact information on my ParkM account. My new phone number is 555-123-4567 and my new email is rachel.new@gmail.com. I live at Cypress Point unit 201. Thanks!

### Classification Results

- **Tags:** Customer Update Contact Info
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Cypress Point**, `unit_number`: **201**
- **Requires Human Review:** No
- **Routing:** Quick Updates

### Wizard Steps

**E Update Contact Info**

> Customer wants to update their email, phone, address, or unit number.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Identify what contact info needs updating
      - *Common updates: email address, phone number, unit number.*
   3. **[Required]** Update the info in parkm.app
      - *Go to the customer's account > Manage User or Edit to update email/phone/unit.*
   4. **[Required]** Verify the change saved correctly
   5. **[Required]** Send confirmation to customer
      - Template: `account_update_confirmed.html`
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the update saved?
   - [ ] Did you confirm with the customer?

   **Quick Response Templates:**
   - Account Update Confirmed (`account_update_confirmed.html`)

---

## Test #23: Property Changing Resident Type for Approved Permit

**Subject:** Change resident type for unit 305
**From:** leasing@birchwoodestates.com

**Email Body:**
> Hi, this is the leasing office at Birchwood Estates. We need to change the resident type for the tenant in unit 305 from 'Standard' to 'Premium' for their approved permit. The resident is John Smith, plate KLM7890. Please update accordingly.

### Classification Results

- **Tags:** Property Changing Resident Type for Approved Permit
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **KLM7890**, `property_name`: **Birchwood Estates**, `unit_number`: **305**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**B Property: Change Resident Type**

> Property manager is requesting a resident type change so a resident can purchase a specific permit type (e.g., carport, garage).

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Confirm which resident type the property is requesting
      - *Check the property notes in Zoho CRM. Example: at some properties, residents need to be 'Resident X' to get carport/garage permits.*
   3. **[Required]** Change the resident type
      - *Go to the resident's account > Edit > Change 'Customer Classification' to the requested type > Save.*
   4. **[Required]** Notify the property that the change has been made
      - *Let them know the resident can now purchase the approved permit type.*
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you change the resident type as requested?
   - [ ] Did you notify the property?

   **Quick Response Templates:**
   - Resident Type Changed (`resident_type_changed.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #24: Property Approving Grandfathered Permit

**Subject:** Approve grandfathered permit - unit 412
**From:** manager@oakridgemanor.com

**Email Body:**
> Hello ParkM team, this is the property manager at Oakridge Manor. We'd like to approve a grandfathered permit for our long-term resident in unit 412, Maria Gonzalez. Her plate is NOP8901. She's been here since 2020 and qualifies for the old rate.

### Classification Results

- **Tags:** Property Approving Grandfathered Permit
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **NOP8901**, `property_name`: **Oakridge Manor**, `unit_number`: **412**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**# Property: Approve Grandfathered Permit**

> Property is approving a grandfathered (free) permit for a resident. Issue a free permit.

   1. **[Required]** Search parkm.app by the resident's email or name (from property's email)
   2. **[Required]** Get the vehicle details from the property's email
      - *Need: license plate, make, model, year, color, state. If missing, ask the property.*
   3. **[Required]** Issue a free grandfathered permit
      - *Actions > Sale Permit > Select community > Toggle 'Issue Free Permit' ON > Set expiration to the date provided by property (if none given, default to 1 year and adjust later). Label permit 'Grandfathered'. Do NOT enter a Next Recurring Date.*
   4. **[Required]** Confirm with the property that the permit has been issued
      - Template: `grandfathered_permit_issued.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you issue the free permit and label it 'Grandfathered'?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Grandfathered Permit Issued (`grandfathered_permit_issued.html`)

---

## Test #25: Property Approving Override Additional Permit

**Subject:** Override approval for additional permit
**From:** frontdesk@pinecrestvillage.com

**Email Body:**
> Hi, this is Ashley from the front desk at Pinecrest Village. We're approving an override for an additional parking permit for unit 215, resident James Brown. His second vehicle plate is QRS9012. Please process this override.

### Classification Results

- **Tags:** Property Approving Override Additional Permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **QRS9012**, `property_name`: **Pinecrest Village**, `unit_number`: **215**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**P Property: Approve Override/Additional Permit**

> Property is approving an override so a resident can get an additional or restricted permit.

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Open up permits or change resident type as needed
      - *Depending on the property setup, you may need to:
- Change the resident's customer classification
- Do an override to allow additional permits
- Open up a specific permit type*
   3. **[Required]** Help the resident purchase or issue the permit
      - *Either guide the resident to purchase online, or purchase/issue on the backend via Actions > Sale Permit.*
   4. **[Required]** Confirm with the property
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you complete the override/permit issuance?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Override Complete (`override_complete.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #26: Property Extending Expiration Date on a Permit

**Subject:** Extend permit expiration for resident
**From:** office@lakeshorecommons.com

**Email Body:**
> Hello, this is the management office at Lakeshore Commons. We need to extend the permit expiration for resident in unit 608, Sarah Miller. Her current permit expires March 15th but her lease was extended through June 30th. Plate TUV1234.

### Classification Results

- **Tags:** Property Extending Expiration Date on a Permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **TUV1234**, `move_out_date`: **June 30th**, `property_name`: **Lakeshore Commons**, `unit_number`: **608**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**P Property: Extend Permit Expiration**

> Property is requesting an extension on a permit's expiration date.

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Locate the permit to extend
   3. **[Required]** Determine the permit type and use the correct method
      - *RECURRING PAID permits: The 'Extend Expiration Date' button does NOT work on these. Use 'Move Next Recurring Date' instead.
FREE or ONE-TIME permits: Use either 'Extend Expiration Date' or 'Delay Cancellation' - both work.*
   4. **[Required]** Extend the permit
      - *Actions > Extend Expiration Date (or Move Next Recurring Date for recurring). Set the new date as requested by the property.*
   5. **[Required]** Confirm with the property
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you use the correct method based on permit type?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Permit Extended (`permit_extended.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #27: Property Audits or Reports

**Subject:** Monthly parking audit report needed
**From:** pm@summithills.com

**Email Body:**
> Hi ParkM, this is the property manager at Summit Hills. We need the monthly parking audit report for February 2026. Specifically, we need the number of active permits, expired permits, and any violations issued. Please send it as a spreadsheet if possible.

### Classification Results

- **Tags:** Property Audits or Reports
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Summit Hills**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**R Property: Audit / Report Request**

> Property is requesting an audit, report, or parking statistics.

   1. **[Required]** Identify what type of report the property needs
      - *Common requests: permit list, vehicle list, payment history, space assignments, monitoring activity.*
   2. **[Required]** Check if the report can be generated from parkm.app
      - *Some reports can be pulled from the admin side. Check the property's data in .app.*
   3. **[Required]** If you cannot generate the report: Forward to Internal Managers
      - *Email internalmanagers@parkm.com with the property's request details.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Send the report or let the property know it's being prepared
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you provide the report or escalate to Internal Managers?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #28: Property Checking if a Vehicle is Permitted

**Subject:** Is this vehicle permitted?
**From:** maintenance@greenfieldapts.com

**Email Body:**
> Hi, this is maintenance at Greenfield Apartments. There's a red Ford F-150 with plate WXY2345 parked in lot B. Can you check if this vehicle has a valid permit? We want to verify before we call for a tow.

### Classification Results

- **Tags:** Property Checking if a Vehicle is Permitted
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **WXY2345**, `property_name`: **Greenfield Apartments**, `space_number`: **B**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**? Property: Check Vehicle Permit**

> Property is asking if a specific vehicle/plate is permitted. Provide COMPLETE information - not just 'yes' or 'no'.

   1. **[Required]** Search parkm.app by the license plate provided
      - *Extracted plate: WXY2345*
      - Entity `license_plate`: **WXY2345** (found in email)
   2. **[Required]** Check permit status and gather full details
      - *DO NOT just say 'yes'. Include ALL of:
- The date the permit became active on that plate
- The specific community the permit is for
- The type of permit (carport, garage, 1st car, open lot, etc.)
- Current status (active, expired, canceled)*
   3. **[Required]** Understand the context
      - *Properties often ask because a vehicle was tagged, booted, towed, or ticketed. A simple 'yes' can cause confusion - they may think the tow company made a mistake when the resident actually just updated their plate recently.*
   4. **[Required]** Send detailed response to the property
      - Template: `vehicle_permit_status.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you include the activation date, community, and permit type?
   - [ ] Did you NOT just say 'yes' or 'no'?

   **Quick Response Templates:**
   - Vehicle Permit Status (`vehicle_permit_status.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #29: Property Checking Who Has a Space Number

**Subject:** Who is assigned to space #55?
**From:** leasing@riverdaleth.com

**Email Body:**
> Hello, this is the leasing office at Riverdale Townhomes. We have a dispute about parking space #55. Can you tell us who is currently assigned to that space? We need to resolve this with our residents.

### Classification Results

- **Tags:** Property Checking Who Has a Space Number
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Riverdale Townhomes**, `space_number`: **55**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**? Property: Who Has This Space?**

> Property is asking who is assigned to a specific parking space number.

   1. **[Required]** Search parkm.app for the space number at the property
      - *Go to the property > check space assignments. Extracted space: [Space Number — Not Found in Email]*
      - Entity `space_number`: *Not found in email*
   2. **[Required]** Find who has a permit with that space number
   3. **[Required]** Respond with the resident's name and vehicle info for that space
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you provide the space assignment info to the property?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #30: Property Checking Who is in a Unit

**Subject:** Who is registered in unit 407?
**From:** manager@courtyardplace.com

**Email Body:**
> Hi ParkM, this is the property manager at Courtyard Place. We need to know which residents are registered and have parking permits in unit 407. We're doing a lease audit and need to verify the information matches our records.

### Classification Results

- **Tags:** Property Checking Who is in a Unit
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Courtyard Place**, `unit_number`: **407**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**? Property: Who is in This Unit?**

> Property is asking who is registered in a specific apartment unit.

   1. **[Required]** Search parkm.app by unit number at the property
      - *Extracted unit: [Unit Number — Not Found in Email]*
      - Entity `unit_number`: *Not found in email*
   2. **[Required]** Find residents registered for that unit
   3. **[Required]** Respond with the resident name(s) and vehicle info for the unit
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you provide the unit info to the property?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #31: Property Inquiring about a Tow Boot Ticket

**Subject:** Tow inquiry for our property
**From:** management@westgateapts.com

**Email Body:**
> Hello, this is management at Westgate Apartments. One of our residents is complaining that their car was towed from our lot last night. The vehicle is a blue Honda Civic plate ZAB3456. Can you provide details on why it was towed and which company performed the tow?

### Classification Results

- **Tags:** Property Inquiring about a Tow Boot Ticket
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **ZAB3456**, `property_name`: **Westgate Apartments**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**! Property: Tow/Boot/Ticket Inquiry**

> Property is asking about a tow, boot, or ticket at their community. ParkM does NOT tow/boot/ticket. Be helpful but stay within our means.

   1. **[Required]** Search parkm.app for the vehicle/plate in question
      - *Extracted plate: ZAB3456*
      - Entity `license_plate`: **ZAB3456** (found in email)
   2. **[Required]** Check permit status and tow history
      - *Click on the vehicle > scroll down to 'Tow History'. Also check the account 'Overview' tab for tow incidents.*
   3. **[Required]** Provide the property with the vehicle's permit status
      - *Include: permit active date, community, permit type, and any violations/tow history logged.*
   4. If property wants a tow/boot refunded: Forward to Internal Managers
      - *Tow/boot/ticket refunds are only handled by Internal Managers. Forward the thread to internalmanagers@parkm.com with a summary.*
      - Email: mailto:internalmanagers@parkm.com
   5. **[Required]** Direct the property to their towing company for tow-specific questions
      - *Check Zoho CRM or .app for the property's enforcement company. Share the tow company contact info with the property.*
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you provide permit status information?
   - [ ] If refund requested, did you forward to Internal Managers?

   **Quick Response Templates:**
   - Vehicle Permit Status (`vehicle_permit_status.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #32: Property Inquiring About a Warning Tag

**Subject:** Warning tag placed on resident vehicle
**From:** office@meadowbrookvillage.com

**Email Body:**
> Hi, this is the office at Meadowbrook Village. A resident in unit 103 received a warning tag on their vehicle, plate CDE4567. They're upset and came to us. Can you explain why the warning was issued and what steps the resident needs to take?

### Classification Results

- **Tags:** Property Inquiring About a Warning Tag
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **CDE4567**, `property_name`: **Meadowbrook Village**, `unit_number`: **103**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**! Property: Warning/Tag Inquiry**

> Property is asking about a warning tag placed on a vehicle.

   1. **[Required]** Check if ParkM monitors this property
      - *Check Zoho CRM for 'ParkM Monitoring' checkmark. In Colorado, ParkM monitoring uses ORANGE tags.*
   2. **[Required]** Search parkm.app for the vehicle/plate in question
      - *Check violations/tow history on the vehicle.*
   3. **[Required]** If ParkM monitors: Explain why the vehicle was tagged
      - *Check the violation log. Common reasons: no permit, expired permit, fire lane, handicap without placard, wrong spot, expired vehicle tags.*
   4. **[Required]** If ParkM does NOT monitor: Direct to their monitoring company
      - *Let them know ParkM did not place the tag. They should contact their monitoring/enforcement company.*
   5. If something seems incorrect about the tag: Report to Brian McDonough and Internal Managers
      - Email: mailto:internalmanagers@parkm.com
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you check if ParkM monitors the property?
   - [ ] Did you respond to the property?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #33: Property Monitor Request

**Subject:** Request parking lot monitoring
**From:** hoa@eagleridge.com

**Email Body:**
> Hello ParkM, this is the HOA president at Eagle Ridge. We've been having issues with unauthorized vehicles parking overnight in our guest lot. Can we set up monitoring for lot C, especially between 10 PM and 6 AM? We'd like to start enforcement next week.

### Classification Results

- **Tags:** Property Monitor Request
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Eagle Ridge**, `space_number`: **C**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**! Property: Monitor Request**

> Property is requesting monitoring, tagging, or patrol of their lot. This could be a request to tag/warn a specific vehicle, start monitoring their lot, or report an issue with current monitoring.

   1. **[Required]** Determine the type of monitoring request
      - *Is this a request to:
- Tag/warn a specific vehicle
- Start monitoring their lot
- Report an issue with current monitoring*
   2. **[Required]** If requesting a specific vehicle to be tagged/warned
      - *Check if ParkM monitors the property (Zoho CRM 'ParkM Monitoring' checkmark).
IF WE MONITOR: Tell property we'll let our monitors know, then forward thread to Brian McDonough.
IF WE DON'T MONITOR: Direct them to their monitoring/towing company.*
   3. **[Required]** If requesting to set up monitoring: CC the sales rep
      - *CC the property's ParkM sales rep and let them handle the monitoring setup discussion.*
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you check if ParkM monitors the property?
   - [ ] Did you forward to Brian if applicable?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #34: Property Leasing Staff Login

**Subject:** New leasing agent needs access
**From:** pm@silvercreekapts.com

**Email Body:**
> Hi, this is the property manager at Silver Creek Apartments. We have a new leasing agent, Brittany Cooper, who needs login access to the ParkM system. Her email is brittany.cooper@silvercreek.com. Can you set up her account?

### Classification Results

- **Tags:** Property Leasing Staff Login
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Silver Creek Apartments**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**K Property: Leasing Staff Login**

> Property manager or leasing office staff needs help with their login to the Property Manager Portal.

   1. **[Required]** Determine if this is a new setup or a password reset
      - **DECISION POINT** - Choose one:
        - New PM/leasing agent setup (action: `new_setup`)
        - Password reset for existing user (action: `reset`)
   2. **[Required]** If password reset: Find the user in Administration
      - *Go to Administration > Users > Paste their email > Toggle 'Show Tenant Users' ON. Click Actions > Reset Password (to send reset email) or Edit (to manually set password to 'Parking').*
      - *(Only shown if action = `reset`)*
   3. **[Required]** If new setup: Forward to Internal Managers
      - *New Property Manager portal setups should be handled by Internal Managers. Forward the request to internalmanagers@parkm.com.*
      - Email: mailto:internalmanagers@parkm.com
      - *(Only shown if action = `new_setup`)*
   4. **[Required]** Send login credentials if reset
      - *Format:
Username: [their email]
Password: Parking
Portal: [Property Manager Portal URL]*
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you resolve the login issue or escalate for new setup?

   **Quick Response Templates:**
   - Login Credentials (`login_credentials.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #35: Property Miscellaneous Questions

**Subject:** General parking questions for our property
**From:** newmanager@woodlandhills.com

**Email Body:**
> Hi ParkM, I'm the new property manager at Woodland Hills. I have a few general questions: How often do you patrol our lot? What's the process if we need to add more spaces? Do you provide signage? Can we get a copy of our current contract? Thanks.

### Classification Results

- **Tags:** Property Miscellaneous Questions
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** low
- **Language:** english
- **Key Entities:** `property_name`: **Woodland Hills**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**? Property: Misc Question**

> General question from a property manager that doesn't fit other categories.

   1. **[Required]** Read the full email carefully
   2. **[Required]** Check Zoho CRM for property notes and sales rep info
   3. If unsure: Email Internal Managers for guidance
      - *Email internalmanagers@parkm.com with the thread and a summary. They will reply with guidance.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Compose a clear, helpful response
      - *Be extra helpful with property managers. Give thorough, informative answers.*
      - Template: `general_inquiry_response.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you fully answer the property's question?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #36: Property Sending Money Order

**Subject:** Sending money order for resident permit
**From:** office@heritagepark.com

**Email Body:**
> Hello, this is the office at Heritage Park. One of our residents in unit 502 doesn't have a bank account and would like to pay for their permit via money order. The amount is $60. Where should we send the money order and who do we make it payable to?

### Classification Results

- **Tags:** Property Sending Money Order
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Heritage Park**, `amount`: **60**, `unit_number`: **502**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**$ Property: Money Order**

> Property is sending a money order payment on behalf of a resident.

   1. **[Required]** Get the resident's account info and vehicle details
   2. **[Required]** Issue a free permit for the paid duration
      - *Actions > Sale Permit > Toggle 'Issue Free Permit' ON > Set expiration to match the paid period.*
   3. **[Required]** Confirm with the property
      - Template: `money_order_received.html`
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you issue the free permit for the paid duration?

   **Quick Response Templates:**
   - Money Order Received (`money_order_received.html`)

---

## Test #37: Property Update or Register Employee Vehicles

**Subject:** Register employee vehicles
**From:** hr@cornerstonecommunities.com

**Email Body:**
> Hi ParkM, this is HR at Cornerstone Communities. We need to register vehicles for three new maintenance employees: 1) John, plate FGH5678, 2) Maria, plate IJK6789, 3) Sam, plate LMN7890. They all need permits for lot A starting immediately.

### Classification Results

- **Tags:** Property Update or Register Employee Vehicles
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Cornerstone Communities**, `space_number`: **lot A**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**E Property: Employee Vehicles**

> Property wants to add or update employee vehicles. Employee vehicles get free permits for life (set expiration to 2055).

   1. **[Required]** Get the employee vehicle details from the property
      - *Need: license plate, make, model, year, color, state, and employee name/email.*
   2. **[Required]** Search for the employee in parkm.app or create an account if needed
   3. **[Required]** Issue a free permit for life
      - *Actions > Sale Permit > Toggle 'Issue Free Permit' ON > Set expiration to year 2055. You can also add the vehicle to the property's 'Employee Car' list.*
   4. **[Required]** Confirm with the property
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you issue the free permit with 2055 expiration?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Employee Vehicle Permitted (`employee_vehicle_permitted.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #38: Property Update Resident Vehicle

**Subject:** Update resident vehicle info
**From:** leasing@springdalearpts.com

**Email Body:**
> Hi, leasing office at Springdale Apartments here. Our resident in unit 210, Michael Johnson, got a new car. Old plate: OPQ8901, new plate: RST9012. Can you update his parking permit with the new vehicle information?

### Classification Results

- **Tags:** Property Update Resident Vehicle
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **RST9012**, `property_name`: **Springdale Apartments**, `unit_number`: **210**
- **Requires Human Review:** No
- **Routing:** Quick Updates

### Wizard Steps

**E Property: Update Resident Vehicle**

> Property is requesting a vehicle update on behalf of a resident.

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Locate the vehicle to update
   3. **[Required]** Make the update
      - *LICENSE PLATE: Actions > Modify License Plate > Enter new plate > Transfer All Active Permits > Save
OTHER: Actions > Edit Vehicle > Update fields > Save*
   4. **[Required]** Confirm with the property
      - Template: `vehicle_update_confirmed.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the update saved?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Vehicle Update Confirmed (`vehicle_update_confirmed.html`)

---

## Test #39: Property Update Resident Contact Information

**Subject:** Update resident contact info
**From:** office@foxwoodapts.com

**Email Body:**
> Hello, this is the office at Foxwood Apartments. The resident in unit 318, Karen Davis, has a new phone number: 555-987-6543 and new email: karen.davis.new@gmail.com. Please update her ParkM account. Thanks!

### Classification Results

- **Tags:** Property Update Resident Contact Information
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Foxwood Apartments**, `unit_number`: **318**
- **Requires Human Review:** No
- **Routing:** Quick Updates

### Wizard Steps

**E Property: Update Resident Contact Info**

> Property is requesting a contact info update for a resident (email, phone, unit).

   1. **[Required]** Search parkm.app by the resident's current email or name
   2. **[Required]** Update the contact information as requested
      - *Go to the account > Manage User or Edit to update email, phone, or unit number.*
   3. **[Required]** Confirm with the property
      - Template: `account_update_confirmed.html`
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you update the info and confirm with the property?

   **Quick Response Templates:**
   - Account Update Confirmed (`account_update_confirmed.html`)

---

## Test #40: Property Update Resident Password

**Subject:** Reset password for resident
**From:** leasing@walnutcreekapts.com

**Email Body:**
> Hi ParkM, this is the leasing office at Walnut Creek Apartments. Our resident in unit 105, Robert Wilson, has been locked out of his ParkM account. He says he's tried the forgot password link multiple times with no luck. Can you manually reset his password? His email is robert.wilson@email.com.

### Classification Results

- **Tags:** Property Update Resident Password
- **Confidence:** 85%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Walnut Creek Apartments**, `unit_number`: **105**
- **Requires Human Review:** No
- **Routing:** Quick Updates

### Wizard Steps

**K Property: Reset Resident Password**

> Property is requesting a password reset on behalf of a resident.

   1. **[Required]** Search parkm.app by the resident's email
   2. **[Required]** Reset the password
      - *Option 1: Click 'Reset Password' button on the account
Option 2: Manage User > change password to 'Parking'
Option 3: Administration > Users > search email > Toggle 'Show Tenant Users' > Actions > Reset Password*
   3. **[Required]** Reply to the property with the resident's login info
      - *Format:
Username: [resident email]
Password: Parking
https://parkm.app/permit/community*
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you reset the password and provide login info?

   **Quick Response Templates:**
   - Password Reset Sent (`password_reset_sent.html`)

---

## Test #41: Property Register Resident Account for Them

**Subject:** Create account for elderly resident
**From:** office@sunflowersenior.com

**Email Body:**
> Hello, this is the office at Sunflower Senior Living. We have an elderly resident, Dorothy Thompson in unit 101, who is not tech-savvy and needs help creating her ParkM account. Her email is dorothy.t@gmail.com, phone 555-111-2222. Her vehicle is a silver Buick, plate UVW1234. Can you create her account for her?

### Classification Results

- **Tags:** Property Register Resident Account for Them
- **Confidence:** 85%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **UVW1234**, `property_name`: **Sunflower Senior Living**, `unit_number`: **101**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**+ Property: Register Resident Account**

> Property wants us to create a ParkM account for a resident.

   1. **[Required]** Get the resident's info from the property
      - *Need: name, email, phone, unit number, and vehicle details (plate, make, model, year, color, state).*
   2. **[Required]** Check if an account already exists for this email
   3. **[Required]** If no account: Create one in parkm.app
      - *Create the account with the resident's info and add their vehicle.*
   4. **[Required]** Confirm with the property and provide login credentials
      - *Format:
Username: [resident email]
Password: Parking
https://parkm.app/permit/community*
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you create the account and provide login info?

   **Quick Response Templates:**
   - Account Created (`account_created.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #42: Property Cancel Resident Account

**Subject:** Cancel resident account - moved out
**From:** leasing@riverwalkapts.com

**Email Body:**
> Hi ParkM, this is the leasing office at Riverwalk Apartments. Resident in unit 404, Thomas Lee, moved out on March 5th. Please cancel his parking permit and account. His plate was XYZ2345. Thanks.

### Classification Results

- **Tags:** Property Cancel Resident Account
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **XYZ2345**, `move_out_date`: **March 5th**, `property_name`: **Riverwalk Apartments**, `unit_number`: **404**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**X Property: Cancel Resident Account**

> Property is requesting cancellation of a resident's permit/account.

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Locate the active permit(s)
   3. **[Required]** Set the permit to Delay Cancel (1 week out)
      - *Do NOT cancel immediately. Use Actions > Cancel > Delay Cancellation > set to 1 week. Delete the 'Next Recurring Date' so they are not charged again.*
   4. If the property/resident also wants a refund: Follow refund process
      - *Forward to accounting@parkm.com with the required info.*
      - Email: mailto:accounting@parkm.com
   5. **[Required]** Confirm with the property
      - Template: `cancellation_confirmed.html`
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you delay cancel (not immediate cancel)?
   - [ ] Did you delete the Next Recurring Date?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Cancellation Confirmed (`cancellation_confirmed.html`)

---

## Test #43: Property Permitting PAID Resident Vehicle for Them

**Subject:** Process paid permit for resident
**From:** office@crestviewcondos.com

**Email Body:**
> Hi, the office at Crestview Condos here. We collected payment from our resident in unit 509, Angela Martinez, for a parking permit. Amount: $55. Her vehicle is a white Toyota Camry, plate ABC3456. Can you issue the permit on her behalf? She's already paid us directly.

### Classification Results

- **Tags:** Property Permitting PAID Resident Vehicle for Them
- **Confidence:** 85%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **ABC3456**, `property_name`: **Crestview Condos**, `amount`: **55**, `unit_number`: **509**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**P Property: Permit Paid Vehicle for Resident**

> Property wants us to purchase a PAID permit on behalf of a resident. Must have a payment method on file and permission to charge.

   1. **[Required]** Search parkm.app by the resident's email
   2. **[Required]** Verify the resident has a payment method on file
      - *Go to Payments & Transactions tab. If no payment method, the resident will need to add one at https://parkm.app/account/login first.*
   3. **[Required]** Confirm you have permission to charge the payment method
      - *The property or resident must explicitly give permission before you charge.*
   4. **[Required]** Purchase the permit on the backend
      - *Actions > Sale Permit > Select community and permit type > Toggle OFF 'Issue Free Permit' > Select vehicle > Select payment method (credit card) > Toggle OFF 'Do not send email receipt' (so resident gets receipt) > Save.*
   5. **[Required]** Confirm with the property
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify payment method on file?
   - [ ] Did you have permission to charge?
   - [ ] Did you send the receipt to the resident?

   **Quick Response Templates:**
   - Permit Purchased (`permit_purchased.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #44: Property Resident Payment Help

**Subject:** Resident having payment issues
**From:** manager@bayviewapts.com

**Email Body:**
> Hello, this is the property manager at Bayview Apartments. Our resident in unit 602, Steven Chen, is having trouble making a payment for his parking permit through the website. He says his card keeps getting declined but it works everywhere else. His email is steven.chen@email.com. Can you assist?

### Classification Results

- **Tags:** Property Resident Payment Help
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Bayview Apartments**, `unit_number`: **602**
- **Requires Human Review:** Yes
- **Routing:** Property Support

### Wizard Steps

**$ Property: Resident Payment Help**

> Property is helping a resident with a payment issue.

   1. **[Required]** Search parkm.app by the resident's email
   2. **[Required]** Check Payments & Transactions tab for issues
      - *Look for: failed payments, expired cards, missing payment methods, duplicate charges.*
   3. **[Required]** Identify and resolve the payment issue
      - *For card updates: Resident needs to update at https://parkm.app/account/login
For billing disputes: Check if charge is legitimate or needs refund
For failed payments: Check card expiry*
   4. If refund needed: Forward to accounting@parkm.com
      - Email: mailto:accounting@parkm.com
   5. **[Required]** Respond to the property with resolution
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you resolve or escalate the payment issue?

   **Quick Response Templates:**
   - Payment Issue Follow-Up (`payment_issue_follow_up.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #45: Property Guest Permits

**Subject:** Guest permit policy for our community
**From:** office@palmgardens.com

**Email Body:**
> Hi ParkM, this is the office at Palm Gardens. We're getting a lot of questions from residents about guest permits. Can you clarify: How many guest permits can each unit have? What's the cost? Is there a time limit? How do residents request them?

### Classification Results

- **Tags:** Property Guest Permits
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `property_name`: **Palm Gardens**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**P Property: Guest Permits**

> Property is asking about guest permit process, limits, or pricing.

   1. **[Required]** Check the property's guest permit setup in parkm.app
      - *Go to the property > check guest permit types, pricing, duration limits, and restrictions.*
   2. **[Required]** Answer the property's question
      - *Key info:
- Guest permits are purchased by the RESIDENT for their guest
- Some properties have limits on guest permits
- Guests can pre-purchase and extend permits
- Guest permits vs resident permits are different permit types*
   3. If the property wants to change guest permit settings: CC the sales rep
      - *CC the property's ParkM sales rep for configuration changes.*
   4. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you answer the property's guest permit question?

   **Quick Response Templates:**
   - Guest Permit Info (`guest_permit_info.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #46: Property Potential Leads

**Subject:** Interested in ParkM for our community
**From:** president@magnoliasquare.com

**Email Body:**
> Hello, I'm the HOA board president at Magnolia Square, a 200-unit apartment community. We're currently not using any parking management system and are interested in learning about ParkM's services. Can someone reach out to discuss pricing and setup? My direct number is 555-444-3333.

### Classification Results

- **Tags:** Property Potential Leads
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** low
- **Language:** english
- **Key Entities:** `property_name`: **Magnolia Square**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

**L Property: Potential Lead**

> A new property or complex is interested in ParkM services. Forward to the sales team.

   1. **[Required]** Gather the lead information
      - *Note: property name, contact name, email, phone, and what they're interested in.*
   2. **[Required]** Forward the thread to the sales team
      - *Forward to the appropriate sales channel. Check Zoho CRM for the territory/region.*
   3. **[Required]** Acknowledge the inquiry to the property
      - *Let them know a sales representative will be in touch shortly.*
      - Template: `lead_acknowledged.html`
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you forward to the sales team?
   - [ ] Did you acknowledge the inquiry?

   **Quick Response Templates:**
   - Lead Acknowledged (`lead_acknowledged.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #47: Sales Rep Asking for a Vehicle to be Released

**Subject:** Release vehicle from tow hold
**From:** jake@towingpartner.com

**Email Body:**
> Hey team, this is Jake from the towing division. We need to release the vehicle with plate DEF4567 that was flagged at Woodland Estates. The property manager confirmed it's a registered resident. Please release the hold so we can let it go.

### Classification Results

- **Tags:** Sales Rep Asking for a Vehicle to be Released
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **DEF4567**, `property_name`: **Woodland Estates**
- **Requires Human Review:** No
- **Routing:** Escalations

### Wizard Steps

**! Sales Rep: Vehicle Release Request**

> Sales rep is asking for a vehicle to be released from a tow/boot. Tow/boot refunds and releases require Internal Manager approval.

   1. **[Required]** Search parkm.app for the vehicle in question
   2. **[Required]** Check the vehicle's permit status at the time of the incident
   3. **[Required]** Forward to Internal Managers for review
      - *Let the sales rep know you'll send it to a manager to review. Forward the thread to internalmanagers@parkm.com with a summary.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Set ticket to waiting and close when resolved

   **Validation Checklist (on close):**
   - [ ] Did you forward to Internal Managers?
   - [ ] Did you NOT promise a release?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #48: Sales Rep Asking for a Vehicle to be Grandfathered

**Subject:** Grandfather this vehicle in
**From:** marcus@parkmsales.com

**Email Body:**
> Hi ParkM, this is Marcus from sales. The property at Hilltop Villas wants to grandfather in a vehicle for their long-term resident. Plate GHI5678, unit 201. The property confirmed they qualify under the old pricing. Can you process this?

### Classification Results

- **Tags:** Sales Rep Asking for a Vehicle to be Grandfathered
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Language:** english
- **Key Entities:** `license_plate`: **GHI5678**, `property_name`: **Hilltop Villas**, `unit_number`: **201**
- **Requires Human Review:** No
- **Routing:** Sales / Leads

### Wizard Steps

**# Sales Rep: Grandfather Request**

> Sales rep is requesting a grandfathered (free) permit for a vehicle.

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Get vehicle details
      - *Need: license plate, make, model, year, color, state.*
   3. **[Required]** Issue a free grandfathered permit
      - *Actions > Sale Permit > Toggle 'Issue Free Permit' ON > Set expiration (1 year default, or as specified). Label 'Grandfathered'. No Next Recurring Date.*
   4. **[Required]** Confirm with the sales rep
      - Template: `grandfathered_permit_issued.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you issue the grandfathered permit?
   - [ ] Did you confirm with the sales rep?

   **Quick Response Templates:**
   - Grandfathered Permit Issued (`grandfathered_permit_issued.html`)

---

## Test #49: Towing or Monitoring Leads

**Subject:** Parking enforcement services inquiry
**From:** info@downtownproperties.com

**Email Body:**
> Hi, I manage a commercial property complex in downtown. We're looking for a parking monitoring and towing enforcement partner. We have 3 buildings with about 500 parking spaces total. Would ParkM be able to provide monitoring and enforcement services? What's the process to get started?

### Classification Results

- **Tags:** Towing or Monitoring Leads
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** low
- **Language:** english
- **Key Entities:** None extracted
- **Requires Human Review:** No
- **Routing:** Sales / Leads

### Wizard Steps

**L Towing/Monitoring Lead**

> A towing, booting, ticketing, or monitoring company is reaching out. Forward to Brian McDonough (Enforcement Manager).

   1. **[Required]** Determine the nature of the inquiry
      - *Is this a tow company wanting to get set up? A property asking about getting a tow company? Questions about ParkM's towing/monitoring integration?*
   2. **[Required]** Forward to Brian McDonough
      - *Brian is our Enforcement Manager. He handles setting up tow/boot/ticket/monitoring companies on ParkM. Forward the thread to Brian.*
   3. If a property is asking about getting a tow company: CC the sales rep
      - *CC the property's sales rep and say: 'I've cc'd your ParkM sales representative, [Name], to assist in selecting a towing, booting, or ticketing company for your community.'*
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you forward to Brian McDonough?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Test #50: The Law Asking for Information

**Subject:** Law enforcement request for vehicle information
**From:** officer.johnson@metropd.gov

**Email Body:**
> This is Officer Johnson, badge #4521, with the Metro Police Department. We are investigating a case (Case #2026-1234) and need information about a vehicle registered in your system. The plate is JKL6789. We need the registered owner's name and address associated with this permit. Please respond as soon as possible.

### Classification Results

- **Tags:** The Law Asking for Information
- **Confidence:** 95%
- **Complexity:** simple
- **Urgency:** high
- **Language:** english
- **Key Entities:** `license_plate`: **JKL6789**
- **Requires Human Review:** Yes
- **Routing:** Escalations

### Wizard Steps

**! Law Enforcement Request**

> Law enforcement is requesting information. Escalate to Internal Managers immediately.

   1. **[Required]** Do NOT respond directly to law enforcement
      - *These requests must be handled by management.*
   2. **[Required]** Forward immediately to Internal Managers
      - *Forward the entire thread to internalmanagers@parkm.com with 'Law Enforcement Request' in the subject/summary.*
      - Email: mailto:internalmanagers@parkm.com
   3. **[Required]** Set ticket status to Escalated/Waiting

   **Validation Checklist (on close):**
   - [ ] Did you forward to Internal Managers?
   - [ ] Did you NOT respond directly to law enforcement?

---

# Part 2: Multi-Intent Test Cases (12)

These emails contain multiple issues that should result in multiple tags.
The wizard displays all tagged processes stacked (one per pill).

## Multi-Intent #1: Cancel Permit + Refund + Password Reset

**Subject:** Cancel permit, get refund, and can't log in
**From:** multi1@gmail.com

**Email Body:**
> Hi, I moved out of Riverside Apartments on Feb 28th 2026. I need to cancel my parking permit and get a refund. Also, I can't log into my account to see my charges - I forgot my password. My plate is MNO1234 and I was charged $65 last month. Please help with all of this.

### Classification Results

- **Tags (2):** Customer Canceling a Permit and Refunding; Customer Password Reset
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Key Entities:** `license_plate`: **MNO1234**, `move_out_date`: **Feb 28th 2026**, `property_name`: **Riverside Apartments**, `amount`: **$65**
- **Requires Human Review:** Yes
- **Routing:** Accounting/Refunds

### Wizard Steps

#### Intent 1: Customer Canceling a Permit and Refunding

**$ Cancel Permit + Refund**

> Customer wants to cancel their permit AND get a refund. Refund window is 30 days from the LAST charge date.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Vehicles and Permits tab
      - *Confirm the license plate and permit. Extracted plate: MNO1234*
      - Entity `license_plate`: **MNO1234** (found in email)
   3. **[Required]** Check if permit is already canceled
      - *If already canceled, note the cancellation date for eligibility calculation.*
   4. **[Required]** Open the Payments tab - find the last charge date and amount
      - *Refund window is 30 days from the LAST charge date.*
   5. **[Required]** Verify move-out date is within the 30-day refund window
      - *Move-out date from email: Feb 28th 2026. If not found, ask the customer.*
      - Entity `move_out_date`: **Feb 28th 2026** (found in email)
   6. **[Required]** Set permit to Delay Cancel (1 week out)
      - *Do NOT cancel immediately. Use Actions > Cancel > Delay Cancellation and set to 1 week. Delete the 'Next Recurring Date' so they are not charged again. Tell resident: 'Your permit is set to cancel on [date]. You will not be charged again.'*
   7. **[Required]** Determine refund eligibility
      - **DECISION POINT** - Choose one:
        - Eligible - Forward to Accounting (action: `submit_refund`) -> template: `refund_forward_accounting.html`
        - Deny - Outside 30-Day Window (action: `deny_outside_window`) -> template: `refund_denied_outside_window.html`
   8. **[Required]** If eligible: Forward WHOLE thread to accounting@parkm.com
      - *Include: customer email on account, refund amount, reason (e.g. 'Moved Out'), and property name. Format:
[email]
$[amount]
[reason]
[property name]
Then set ticket status to 'Waiting on Accounting'.*
      - Email: mailto:accounting@parkm.com
      - *(Only shown if action = `submit_refund`)*
   9. **[Required]** Send response email to customer
   10. **[Required]** Update ticket status (Waiting on Accounting or Closed)

   **Validation Checklist (on close):**
   - [ ] Did you verify the move-out date is within 30 days of the last charge?
   - [ ] Did you set the permit to delay cancel (not immediate)?
   - [ ] Did you delete the Next Recurring Date?
   - [ ] Did you forward to accounting@parkm.com (if eligible) OR send denial?

   **Quick Response Templates:**
   - Missing License Plate (`missing_license_plate.html`)
   - Missing Move-Out Date (`missing_move_out_date.html`)
   - Refund Approved (`refund_approved.html`)
   - Refund Denied - Outside Window (`refund_denied_outside_window.html`)
   - Cancellation Confirmed (`cancellation_confirmed.html`)

#### Intent 2: Customer Password Reset

**K Password Reset**

> Customer needs help resetting their password.

   1. **[Required]** Search parkm.app by customer email address
      - *Verify the account exists and the email matches.*
   2. **[Required]** Reset password using one of these methods
      - *Option 1: Direct them to https://parkm.app/account/login > 'Forgot Password'
Option 2: Find their account > click 'Reset Password' button
Option 3: Manual reset via Manage User > change password to 'Parking'*
   3. **[Required]** If manual reset, send login credentials
      - *Format:
Username: [their email]
Password: Parking
https://parkm.app/permit/community*
   4. **[Required]** Send response and close ticket
      - Template: `password_reset_sent.html`

   **Validation Checklist (on close):**
   - [ ] Did you reset the password or send instructions?
   - [ ] Did you confirm with the customer?

   **Quick Response Templates:**
   - Password Reset Sent (`password_reset_sent.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #2: Double Charged + Cancel Permit

**Subject:** Charged twice AND I'm moving out
**From:** multi2@gmail.com

**Email Body:**
> I was charged $50 twice on March 1st for my permit at Willow Creek. That needs to be fixed. Also, I'm moving out on March 15th so I need to cancel my permit entirely. Plate: PQR2345, unit 303. This is really frustrating.

### Classification Results

- **Tags (2):** Customer Canceling a Permit and Refunding; Customer Double Charged or Extra Charges
- **Confidence:** 85%
- **Complexity:** complex
- **Urgency:** high
- **Key Entities:** `license_plate`: **PQR2345**, `move_out_date`: **March 15th**, `property_name`: **Willow Creek**, `amount`: **50**, `unit_number`: **303**
- **Requires Human Review:** Yes
- **Routing:** Escalations

### Wizard Steps

#### Intent 1: Customer Canceling a Permit and Refunding

**$ Cancel Permit + Refund**

> Customer wants to cancel their permit AND get a refund. Refund window is 30 days from the LAST charge date.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Vehicles and Permits tab
      - *Confirm the license plate and permit. Extracted plate: PQR2345*
      - Entity `license_plate`: **PQR2345** (found in email)
   3. **[Required]** Check if permit is already canceled
      - *If already canceled, note the cancellation date for eligibility calculation.*
   4. **[Required]** Open the Payments tab - find the last charge date and amount
      - *Refund window is 30 days from the LAST charge date.*
   5. **[Required]** Verify move-out date is within the 30-day refund window
      - *Move-out date from email: March 15th. If not found, ask the customer.*
      - Entity `move_out_date`: **March 15th** (found in email)
   6. **[Required]** Set permit to Delay Cancel (1 week out)
      - *Do NOT cancel immediately. Use Actions > Cancel > Delay Cancellation and set to 1 week. Delete the 'Next Recurring Date' so they are not charged again. Tell resident: 'Your permit is set to cancel on [date]. You will not be charged again.'*
   7. **[Required]** Determine refund eligibility
      - **DECISION POINT** - Choose one:
        - Eligible - Forward to Accounting (action: `submit_refund`) -> template: `refund_forward_accounting.html`
        - Deny - Outside 30-Day Window (action: `deny_outside_window`) -> template: `refund_denied_outside_window.html`
   8. **[Required]** If eligible: Forward WHOLE thread to accounting@parkm.com
      - *Include: customer email on account, refund amount, reason (e.g. 'Moved Out'), and property name. Format:
[email]
$[amount]
[reason]
[property name]
Then set ticket status to 'Waiting on Accounting'.*
      - Email: mailto:accounting@parkm.com
      - *(Only shown if action = `submit_refund`)*
   9. **[Required]** Send response email to customer
   10. **[Required]** Update ticket status (Waiting on Accounting or Closed)

   **Validation Checklist (on close):**
   - [ ] Did you verify the move-out date is within 30 days of the last charge?
   - [ ] Did you set the permit to delay cancel (not immediate)?
   - [ ] Did you delete the Next Recurring Date?
   - [ ] Did you forward to accounting@parkm.com (if eligible) OR send denial?

   **Quick Response Templates:**
   - Missing License Plate (`missing_license_plate.html`)
   - Missing Move-Out Date (`missing_move_out_date.html`)
   - Refund Approved (`refund_approved.html`)
   - Refund Denied - Outside Window (`refund_denied_outside_window.html`)
   - Cancellation Confirmed (`cancellation_confirmed.html`)

#### Intent 2: Customer Double Charged or Extra Charges

**$ Double Charged / Extra Charges**

> Customer is reporting a billing issue - double charge, unexpected charge, or extra fees. Investigate in the Payments tab before responding.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Payments & Transactions tab
      - *Look for duplicate charges, unexpected amounts, failed payment retries, convenience fees, or credit card surcharges.*
   3. **[Required]** Confirm the license plate matches their account
      - *Extracted plate: PQR2345*
      - Entity `license_plate`: **PQR2345** (found in email)
   4. **[Required]** Determine the cause of the charge
      - *Common causes:
- Convenience fee / credit card surcharge (these are normal and disclosed)
- Permit renewed as expected (customer forgot)
- Actual duplicate charge (system error)
- NSF fee (non-sufficient funds)
- Taxes on the permit*
      - **DECISION POINT** - Choose one:
        - Legitimate charge - Explain to customer (action: `explain_charge`)
        - Duplicate/error - Forward to accounting for refund (action: `escalate_accounting`)
   5. **[Required]** If duplicate/error: Forward WHOLE thread to accounting@parkm.com
      - *Include: email on account, refund amount, reason, property name.
Then set ticket to 'Waiting on Accounting'.*
      - Email: mailto:accounting@parkm.com
      - *(Only shown if action = `escalate_accounting`)*
   6. **[Required]** If legitimate: Explain the charge clearly to the customer
      - *Be helpful and clear. Explain convenience fees, surcharges, or recurring permit charges as applicable.*
      - *(Only shown if action = `explain_charge`)*
   7. **[Required]** Send response and update ticket status

   **Validation Checklist (on close):**
   - [ ] Did you investigate the charge(s) in the Payments tab?
   - [ ] Did you either explain the charge OR forward to accounting?

   **Quick Response Templates:**
   - Payment Issue Follow-Up (`payment_issue_follow_up.html`)
   - Charge Explanation (`charge_explanation.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #3: Update Vehicle + Renew Permit

**Subject:** New car - need to update plate and renew
**From:** multi3@gmail.com

**Email Body:**
> Hey, I just got a new car and my permit is about to expire. I need to update my plate from STU3456 to VWX4567 AND renew my parking permit at Summit Apartments unit 210. Can we do both at once?

### Classification Results

- **Tags (2):** Customer Update Vehicle Info; Customer Need Help Renewing Permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Key Entities:** `license_plate`: **VWX4567**, `property_name`: **Summit Apartments**, `unit_number`: **210**
- **Requires Human Review:** No
- **Routing:** Quick Updates

### Wizard Steps

#### Intent 1: Customer Update Vehicle Info

**E Update Vehicle Info**

> Customer needs to update their vehicle information (license plate, make, model, etc.).

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Locate the vehicle they want to update
      - *Extracted plate: VWX4567*
      - Entity `license_plate`: **VWX4567** (found in email)
   3. **[Required]** Determine what needs to be updated
      - *LICENSE PLATE change: Actions > Modify License Plate > Enter new plate > Toggle 'Transfer All Active Permits' > Save
OTHER changes (make, model, VIN, color): Actions > Edit Vehicle > Make changes > Save*
   4. **[Required]** Make the update in parkm.app
   5. **[Required]** Verify the change saved correctly
      - *Refresh the page and confirm the update is reflected.*
   6. **[Required]** Send confirmation to customer
      - Template: `vehicle_update_confirmed.html`
   7. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the update saved correctly?
   - [ ] Did you use 'Modify License Plate' (not 'Edit Vehicle') for plate changes?
   - [ ] Did you transfer active permits to the new plate?

   **Quick Response Templates:**
   - Vehicle Update Confirmed (`vehicle_update_confirmed.html`)
   - Missing License Plate (`missing_license_plate.html`)

#### Intent 2: Customer Need Help Renewing Permit

**P Help Renewing Permit**

> Customer needs help renewing their existing permit.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Check the permit status and next recurring date
      - *Is it a recurring paid permit? Check the next recurring date and expiration date. Recurring permits auto-renew by pushing out the expiration date each charge cycle.*
   3. **[Required]** Identify the renewal issue
      - *Common issues:
- Payment method expired/declined
- Permit was accidentally canceled
- Need to change charge date
- Permit expired and needs reactivation*
      - **DECISION POINT** - Choose one:
        - Payment issue - Update payment method (action: `update_payment`)
        - Permit expired - Reactivate (action: `reactivate`)
        - Need to change charge date (action: `change_date`)
   4. **[Required]** Resolve the issue
      - *For payment: Have customer update card at https://parkm.app/account/login
For reactivation: May need to issue a new permit
For charge date: Actions > Move Next Recurring Date*
   5. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the permit status and resolve the renewal issue?
   - [ ] Did you respond to the customer?

   **Quick Response Templates:**
   - How to Update Payment (`how_to_update_payment.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #4: Towed + Refund Request

**Subject:** Car towed but I had a permit! I want a refund!
**From:** multi4@gmail.com

**Email Body:**
> MY CAR WAS TOWED from Oakdale Apartments even though I have a valid permit!! Plate YZA5678, space #15, unit 404. I had to pay $250 to get my car back. I want a refund for the tow AND I want a refund on my parking permit because clearly it doesn't work. This is unacceptable!

### Classification Results

- **Tags (2):** Customer Towed Booted Ticketed; Customer Canceling a Permit and Refunding
- **Confidence:** 85%
- **Complexity:** complex
- **Urgency:** high
- **Key Entities:** `license_plate`: **YZA5678**, `property_name`: **Oakdale Apartments**, `amount`: **250**, `unit_number`: **404**, `space_number`: **15**
- **Requires Human Review:** Yes
- **Routing:** Escalations

### Wizard Steps

#### Intent 1: Customer Towed Booted Ticketed

**! Towed / Booted / Ticketed**

> Customer's vehicle was towed, booted, or ticketed. Be empathetic. ParkM does NOT tow/boot/ticket - we only sell permits. Offer a proof of permit if applicable.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Check if the vehicle had an active permit at the time of the tow/boot
      - *Extracted plate: YZA5678. Check the vehicle's permit history - was the permit active when the tow/boot occurred?*
      - Entity `license_plate`: **YZA5678** (found in email)
   3. **[Required]** Remind the customer that ParkM is NOT the towing company
      - *ParkM simply sells parking permits. We do not tow, boot, or ticket vehicles. Express empathy: 'I understand how frustrating being towed/booted can be...'*
   4. **[Required]** Determine if a proof of permit is applicable
      - *Only provide proof of permit if the vehicle appeared to have a permit at/around the time of the incident. Proof of permit covers the last 72 hours (3 days) only. If the incident was more than 72 hours ago, they need to work with the tow company using their original receipt.*
      - **DECISION POINT** - Choose one:
        - Vehicle was permitted - Generate Proof of Permit (action: `proof_of_permit`)
        - Vehicle was NOT permitted - Direct to tow company (action: `no_permit`)
   5. **[Required]** If permitted: Generate Proof of Permit
      - *Go to account > Actions > Proof of Permit. Either email it directly (add tow company email if known) or download the PDF and attach it to the thread. Check Zoho CRM for tow company email. After sending, STAY OUT OF IT - do not promise refunds or releases!*
      - *(Only shown if action = `proof_of_permit`)*
   6. **[Required]** If not permitted: Direct to towing company
      - *Look up the tow company for the property in Zoho CRM or in .app under the property's enforcement company. Share the tow company PHONE NUMBER (not email). If tow company is unknown, advise them to look for towing signs posted at the property.*
      - *(Only shown if action = `no_permit`)*
   7. **[Required]** NEVER promise a refund or release of the vehicle
      - *Tow/boot refunds are EXTREMELY rare and require Internal Manager approval. If the customer insists, forward to internalmanagers@parkm.com.*
      - Email: mailto:internalmanagers@parkm.com
   8. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you check the vehicle's permit status at the time of the incident?
   - [ ] Did you provide a proof of permit (if applicable)?
   - [ ] Did you remind the customer ParkM does not tow/boot/ticket?
   - [ ] Did you NOT promise a refund or vehicle release?

   **Quick Response Templates:**
   - Missing License Plate (`missing_license_plate.html`)
   - Tow/Boot Response - Had Permit (`tow_had_permit.html`)
   - Tow/Boot Response - No Permit (`tow_no_permit.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Customer Canceling a Permit and Refunding

**$ Cancel Permit + Refund**

> Customer wants to cancel their permit AND get a refund. Refund window is 30 days from the LAST charge date.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Vehicles and Permits tab
      - *Confirm the license plate and permit. Extracted plate: YZA5678*
      - Entity `license_plate`: **YZA5678** (found in email)
   3. **[Required]** Check if permit is already canceled
      - *If already canceled, note the cancellation date for eligibility calculation.*
   4. **[Required]** Open the Payments tab - find the last charge date and amount
      - *Refund window is 30 days from the LAST charge date.*
   5. **[Required]** Verify move-out date is within the 30-day refund window
      - *Move-out date from email: [Move Out Date — Not Found in Email]. If not found, ask the customer.*
      - Entity `move_out_date`: *Not found in email*
      - Missing action: Send **"Request Move-Out Date"** template (`missing_move_out_date.html`)
   6. **[Required]** Set permit to Delay Cancel (1 week out)
      - *Do NOT cancel immediately. Use Actions > Cancel > Delay Cancellation and set to 1 week. Delete the 'Next Recurring Date' so they are not charged again. Tell resident: 'Your permit is set to cancel on [date]. You will not be charged again.'*
   7. **[Required]** Determine refund eligibility
      - **DECISION POINT** - Choose one:
        - Eligible - Forward to Accounting (action: `submit_refund`) -> template: `refund_forward_accounting.html`
        - Deny - Outside 30-Day Window (action: `deny_outside_window`) -> template: `refund_denied_outside_window.html`
   8. **[Required]** If eligible: Forward WHOLE thread to accounting@parkm.com
      - *Include: customer email on account, refund amount, reason (e.g. 'Moved Out'), and property name. Format:
[email]
$[amount]
[reason]
[property name]
Then set ticket status to 'Waiting on Accounting'.*
      - Email: mailto:accounting@parkm.com
      - *(Only shown if action = `submit_refund`)*
   9. **[Required]** Send response email to customer
   10. **[Required]** Update ticket status (Waiting on Accounting or Closed)

   **Validation Checklist (on close):**
   - [ ] Did you verify the move-out date is within 30 days of the last charge?
   - [ ] Did you set the permit to delay cancel (not immediate)?
   - [ ] Did you delete the Next Recurring Date?
   - [ ] Did you forward to accounting@parkm.com (if eligible) OR send denial?

   **Quick Response Templates:**
   - Missing License Plate (`missing_license_plate.html`)
   - Missing Move-Out Date (`missing_move_out_date.html`)
   - Refund Approved (`refund_approved.html`)
   - Refund Denied - Outside Window (`refund_denied_outside_window.html`)
   - Cancellation Confirmed (`cancellation_confirmed.html`)

---

## Multi-Intent #5: Property: Check Vehicle + Check Unit

**Subject:** Vehicle check and unit verification
**From:** leasing@brooksidemanor.com

**Email Body:**
> Hi ParkM, this is the leasing office at Brookside Manor. Can you check two things: 1) Is the vehicle with plate BCD6789 permitted in our lot? And 2) Who is currently registered in unit 512? We're doing an end-of-month audit. Thanks!

### Classification Results

- **Tags (3):** Property Checking if a Vehicle is Permitted; Property Checking Who is in a Unit; Property Audits or Reports
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Key Entities:** `license_plate`: **BCD6789**, `property_name`: **Brookside Manor**, `unit_number`: **512**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

#### Intent 1: Property Checking if a Vehicle is Permitted

**? Property: Check Vehicle Permit**

> Property is asking if a specific vehicle/plate is permitted. Provide COMPLETE information - not just 'yes' or 'no'.

   1. **[Required]** Search parkm.app by the license plate provided
      - *Extracted plate: BCD6789*
      - Entity `license_plate`: **BCD6789** (found in email)
   2. **[Required]** Check permit status and gather full details
      - *DO NOT just say 'yes'. Include ALL of:
- The date the permit became active on that plate
- The specific community the permit is for
- The type of permit (carport, garage, 1st car, open lot, etc.)
- Current status (active, expired, canceled)*
   3. **[Required]** Understand the context
      - *Properties often ask because a vehicle was tagged, booted, towed, or ticketed. A simple 'yes' can cause confusion - they may think the tow company made a mistake when the resident actually just updated their plate recently.*
   4. **[Required]** Send detailed response to the property
      - Template: `vehicle_permit_status.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you include the activation date, community, and permit type?
   - [ ] Did you NOT just say 'yes' or 'no'?

   **Quick Response Templates:**
   - Vehicle Permit Status (`vehicle_permit_status.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Property Checking Who is in a Unit

**? Property: Who is in This Unit?**

> Property is asking who is registered in a specific apartment unit.

   1. **[Required]** Search parkm.app by unit number at the property
      - *Extracted unit: [Unit Number — Not Found in Email]*
      - Entity `unit_number`: *Not found in email*
   2. **[Required]** Find residents registered for that unit
   3. **[Required]** Respond with the resident name(s) and vehicle info for the unit
   4. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you provide the unit info to the property?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 3: Property Audits or Reports

**R Property: Audit / Report Request**

> Property is requesting an audit, report, or parking statistics.

   1. **[Required]** Identify what type of report the property needs
      - *Common requests: permit list, vehicle list, payment history, space assignments, monitoring activity.*
   2. **[Required]** Check if the report can be generated from parkm.app
      - *Some reports can be pulled from the admin side. Check the property's data in .app.*
   3. **[Required]** If you cannot generate the report: Forward to Internal Managers
      - *Email internalmanagers@parkm.com with the property's request details.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Send the report or let the property know it's being prepared
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you provide the report or escalate to Internal Managers?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #6: Guest Permit + Someone in My Spot

**Subject:** Guest permit and someone in my spot
**From:** multi6@gmail.com

**Email Body:**
> Two issues: First, my parents are visiting this weekend and I need a guest permit for them at Meadow Lakes unit 207. Second, there's been a silver Honda with plate EFG7890 parking in my assigned spot #31 every day this week. Can you handle both?

### Classification Results

- **Tags (2):** Customer Guest Permit and Pricing Questions; Customer Someone is Parking in my Spot
- **Confidence:** 85%
- **Complexity:** complex
- **Urgency:** medium
- **Key Entities:** `license_plate`: **EFG7890**, `property_name`: **Meadow Lakes**, `unit_number`: **207**, `space_number`: **31**
- **Requires Human Review:** Yes
- **Routing:** Escalations

### Wizard Steps

#### Intent 1: Customer Guest Permit and Pricing Questions

**? Guest Permit & Pricing**

> Customer is asking about guest permits, pricing, or how guest permits work.

   1. Search parkm.app by customer email (if they have an account)
   2. **[Required]** Check the property's guest permit setup in parkm.app
      - *Go to the property > check guest permit types, pricing, duration limits, and any restrictions. Some properties have limits on guest permits.*
   3. **[Required]** Answer the customer's question about guest permits
      - *Key info:
- Guest permits are purchased by the RESIDENT for their guest's vehicle
- Multiple people can buy guest permits for the same vehicle
- Guest permits may have limits per property
- Guests can pre-purchase permits
- Residents can extend guest permits
- Direct them to: https://parkm.app/permit/community?forceChange=true*
   4. **[Required]** Send response and close ticket
      - Template: `guest_permit_info.html`

   **Validation Checklist (on close):**
   - [ ] Did you answer the customer's specific question about guest permits/pricing?

   **Quick Response Templates:**
   - Guest Permit Info (`guest_permit_info.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Customer Someone is Parking in my Spot

**! Someone in My Spot**

> Customer is reporting that someone is parking in their assigned space.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Verify the customer's assigned space number
      - *Check their permit for the space number. Extracted space: [Space Number — Not Found in Email]*
      - Entity `space_number`: *Not found in email*
   3. **[Required]** Direct the customer to their leasing office
      - *ParkM does not enforce parking spaces or tow vehicles. The customer should contact their leasing office about the unauthorized vehicle. The leasing office can then contact the towing company if needed.*
   4. If we monitor the property: Forward to Brian McDonough
      - *Check Zoho CRM for 'ParkM Monitoring' checkmark. If we monitor: forward to Brian McDonough so monitors can be alerted. If we don't monitor: direct customer to their monitoring/towing company.*
   5. **[Required]** Send response and close ticket
      - Template: `someone_in_my_spot.html`

   **Validation Checklist (on close):**
   - [ ] Did you direct the customer to their leasing office?
   - [ ] Did you check if ParkM monitors the property?

   **Quick Response Templates:**
   - Someone in My Spot (`someone_in_my_spot.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #7: Property: Register Account + Permit Payment

**Subject:** New resident needs account and permit
**From:** office@cedarpoint.com

**Email Body:**
> Hello, this is the office at Cedar Point. We have a new move-in, Patricia Holmes, unit 603. She needs a ParkM account created (email: patricia.h@email.com, phone: 555-222-3333) AND we collected her permit payment of $45. Her vehicle is a blue Honda Accord plate HIJ8901. Please set up her account and issue the permit.

### Classification Results

- **Tags (2):** Property Register Resident Account for Them; Property Permitting PAID Resident Vehicle for Them
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Key Entities:** `license_plate`: **HIJ8901**, `property_name`: **Cedar Point**, `amount`: **45**, `unit_number`: **603**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

#### Intent 1: Property Register Resident Account for Them

**+ Property: Register Resident Account**

> Property wants us to create a ParkM account for a resident.

   1. **[Required]** Get the resident's info from the property
      - *Need: name, email, phone, unit number, and vehicle details (plate, make, model, year, color, state).*
   2. **[Required]** Check if an account already exists for this email
   3. **[Required]** If no account: Create one in parkm.app
      - *Create the account with the resident's info and add their vehicle.*
   4. **[Required]** Confirm with the property and provide login credentials
      - *Format:
Username: [resident email]
Password: Parking
https://parkm.app/permit/community*
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you create the account and provide login info?

   **Quick Response Templates:**
   - Account Created (`account_created.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Property Permitting PAID Resident Vehicle for Them

**P Property: Permit Paid Vehicle for Resident**

> Property wants us to purchase a PAID permit on behalf of a resident. Must have a payment method on file and permission to charge.

   1. **[Required]** Search parkm.app by the resident's email
   2. **[Required]** Verify the resident has a payment method on file
      - *Go to Payments & Transactions tab. If no payment method, the resident will need to add one at https://parkm.app/account/login first.*
   3. **[Required]** Confirm you have permission to charge the payment method
      - *The property or resident must explicitly give permission before you charge.*
   4. **[Required]** Purchase the permit on the backend
      - *Actions > Sale Permit > Select community and permit type > Toggle OFF 'Issue Free Permit' > Select vehicle > Select payment method (credit card) > Toggle OFF 'Do not send email receipt' (so resident gets receipt) > Save.*
   5. **[Required]** Confirm with the property
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify payment method on file?
   - [ ] Did you have permission to charge?
   - [ ] Did you send the receipt to the resident?

   **Quick Response Templates:**
   - Permit Purchased (`permit_purchased.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #8: Warning Tag + No Plate/Expired Tags

**Subject:** Got a warning but my tags are being renewed
**From:** multi8@gmail.com

**Email Body:**
> I got a warning tag on my car at Sunridge Apartments. The warning says my tags are expired, which they are, but I've already submitted my renewal to the DMV and I'm waiting for the new stickers. My plate is KLM9012, unit 108, space #22. What do I do so I don't get towed while I wait?

### Classification Results

- **Tags (2):** Customer No Plate or Expired Tags; Customer Warned or Tagged
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** high
- **Key Entities:** `license_plate`: **KLM9012**, `property_name`: **Sunridge Apartments**, `unit_number`: **108**, `space_number`: **22**
- **Requires Human Review:** Yes
- **Routing:** Escalations

### Wizard Steps

#### Intent 1: Customer No Plate or Expired Tags

**! No Plate / Expired Tags**

> Customer's vehicle has no physical plates or expired registration tags. ParkM permits are tied to license plates, so they must resolve this first.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Explain that ParkM permits are tied to license plates
      - *The license plate must always be accurate on their permit to avoid towing/booting/ticketing issues.*
   3. **[Required]** Direct the customer to their leasing office
      - *They need to speak to their complex about the expired tags / no plates situation. In the meantime, they need to park OFF SITE since ParkM permits require valid plates.*
   4. **[Required]** Send response using template
      - Template: `no_plate_expired_tags.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you direct the customer to their leasing office?
   - [ ] Did you explain they need to park off site until resolved?

   **Quick Response Templates:**
   - No Plate / Expired Tags (`no_plate_expired_tags.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Customer Warned or Tagged

**! Warning / Tag**

> Customer received a warning sticker or tag on their vehicle. Tags are warnings with no fees. Focus on helping them get properly permitted.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Ask the customer to send a picture of the tag
      - *This helps identify the reason for the tag and who placed it. In Colorado, ParkM's tags are ORANGE. Other colors = not us.*
   3. **[Required]** Check the vehicle's permit status
      - *Extracted plate: KLM9012. Is the vehicle permitted? Was the plate correct? Check tow history/violations on the vehicle in .app.*
      - Entity `license_plate`: **KLM9012** (found in email)
   4. **[Required]** Determine why they were tagged
      - *Common reasons: no ParkM permit, expired permit, wrong plate on permit, parked in fire lane, parked in handicap spot without placard, parked in someone's assigned spot, expired vehicle tags.*
   5. **[Required]** Help them resolve the issue
      - *If not permitted: help them get a permit
If plate was wrong: update the plate
If other violation: explain and advise
Note: sticker removal is the customer's responsibility - ParkM cannot remove it.*
   6. **[Required]** Send response and close ticket
      - Template: `warning_tag_response.html`

   **Validation Checklist (on close):**
   - [ ] Did you identify why they were tagged?
   - [ ] Did you help them resolve the underlying issue?
   - [ ] Did you clarify that tags are warnings with no fees?

   **Quick Response Templates:**
   - Warning Tag Response (`warning_tag_response.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #9: Property: Employee Vehicles + Leasing Staff Login

**Subject:** New staff setup - vehicles and system access
**From:** hr@grandviewproperties.com

**Email Body:**
> Hi ParkM, this is HR at Grandview Properties. We have two new employees starting Monday. They both need: 1) Their vehicles registered for staff parking (John - plate NOP0123, Sarah - plate QRS1234), and 2) Login access to the ParkM management system. John's email: john@grandview.com, Sarah's email: sarah@grandview.com.

### Classification Results

- **Tags (2):** Property Update or Register Employee Vehicles; Property Leasing Staff Login
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Key Entities:** `license_plate`: **NOP0123, QRS1234**, `property_name`: **Grandview Properties**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

#### Intent 1: Property Update or Register Employee Vehicles

**E Property: Employee Vehicles**

> Property wants to add or update employee vehicles. Employee vehicles get free permits for life (set expiration to 2055).

   1. **[Required]** Get the employee vehicle details from the property
      - *Need: license plate, make, model, year, color, state, and employee name/email.*
   2. **[Required]** Search for the employee in parkm.app or create an account if needed
   3. **[Required]** Issue a free permit for life
      - *Actions > Sale Permit > Toggle 'Issue Free Permit' ON > Set expiration to year 2055. You can also add the vehicle to the property's 'Employee Car' list.*
   4. **[Required]** Confirm with the property
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you issue the free permit with 2055 expiration?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Employee Vehicle Permitted (`employee_vehicle_permitted.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Property Leasing Staff Login

**K Property: Leasing Staff Login**

> Property manager or leasing office staff needs help with their login to the Property Manager Portal.

   1. **[Required]** Determine if this is a new setup or a password reset
      - **DECISION POINT** - Choose one:
        - New PM/leasing agent setup (action: `new_setup`)
        - Password reset for existing user (action: `reset`)
   2. **[Required]** If password reset: Find the user in Administration
      - *Go to Administration > Users > Paste their email > Toggle 'Show Tenant Users' ON. Click Actions > Reset Password (to send reset email) or Edit (to manually set password to 'Parking').*
      - *(Only shown if action = `reset`)*
   3. **[Required]** If new setup: Forward to Internal Managers
      - *New Property Manager portal setups should be handled by Internal Managers. Forward the request to internalmanagers@parkm.com.*
      - Email: mailto:internalmanagers@parkm.com
      - *(Only shown if action = `new_setup`)*
   4. **[Required]** Send login credentials if reset
      - *Format:
Username: [their email]
Password: Parking
Portal: [Property Manager Portal URL]*
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you resolve the login issue or escalate for new setup?

   **Quick Response Templates:**
   - Login Credentials (`login_credentials.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #10: Create Account + Buy Permit + Payment Help

**Subject:** New here - can't figure anything out
**From:** multi10@gmail.com

**Email Body:**
> Hi, I just moved into Lakeview Terrace unit 401 and I'm completely lost. I need to create a ParkM account, buy a parking permit, and I'm not sure what payment methods you accept. I tried to go to the website but I don't even know where to start. My car is a red Nissan plate TUV2345. Help!!

### Classification Results

- **Tags (3):** Customer Need Help Creating an Account; Customer Need help buying a permit; Customer Payment Help
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Key Entities:** `license_plate`: **TUV2345**, `property_name`: **Lakeview Terrace**, `unit_number`: **401**
- **Requires Human Review:** Yes
- **Routing:** General Support

### Wizard Steps

#### Intent 1: Customer Need Help Creating an Account

**+ Help Creating Account**

> Customer is having trouble creating a ParkM account.

   1. **[Required]** Check if an account already exists for this email
      - *Search parkm.app by email. The customer may already have an account and not realize it.*
   2. If account exists: Send them a password reset
      - *Click 'Reset Password' button on their account, or direct them to https://parkm.app/account/login > 'Forgot Password'*
   3. **[Required]** If no account: Guide them to create one
      - *Direct them to: https://parkm.app/permit/community?forceChange=true
They will need to search for their community and create an account.*
   4. If there's a technical error: Issue a free temp permit and escalate
      - *Issue a free permit for a few days/1 week. Email internalmanagers@parkm.com with the error details so they can investigate.*
      - Email: mailto:internalmanagers@parkm.com
   5. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you help the customer create an account or resolve their issue?

   **Quick Response Templates:**
   - How to Create Account (`how_to_create_account.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Customer Need help buying a permit

**P Help Buying a Permit**

> Customer needs help purchasing a permit for the first time.

   1. **[Required]** Search parkm.app by customer email - check if they have an account
   2. **[Required]** If no account: Direct them to create one
      - *Website: https://parkm.app/permit/community?forceChange=true
OR: https://www.parkm.com/*
   3. **[Required]** Identify the issue preventing purchase
      - *Common issues:
- Can't find their community
- Resident type is wrong (needs to be changed)
- Permits are locked down (needs override)
- Payment method issues
- Error message during checkout*
   4. If there's a system error preventing purchase: Issue a free temporary permit
      - *Issue a free permit for a few days/1 week while Internal Managers investigate the error. Email internalmanagers@parkm.com with details of the error.*
      - Email: mailto:internalmanagers@parkm.com
   5. **[Required]** If you can resolve it: Help them purchase or guide them through the process
      - *You can purchase on the backend: Actions > Sale Permit. Make sure they have a payment method on file and you have permission to charge it. Toggle OFF 'Issue Free Permit' and select their payment method.*
   6. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you help the customer purchase or explain how to?
   - [ ] If there was an error, did you issue a temp permit and escalate?

   **Quick Response Templates:**
   - How to Buy a Permit (`how_to_buy_permit.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 3: Customer Payment Help

**$ Payment Help**

> Customer needs general help with payments - can't pay, payment failed, need to update card, etc.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Payments & Transactions tab
      - *Check for failed payments, expired cards, or missing payment methods.*
   3. **[Required]** Identify the payment issue
      - *Common issues:
- Credit/debit card expired or declined
- No payment method on file
- Wants to change payment method
- Bank account issues
- Convenience fee questions*
      - **DECISION POINT** - Choose one:
        - Card expired/declined - Guide to update (action: `update_card`)
        - No payment method - Help add one (action: `add_payment`)
        - Convenience fee question - Explain (action: `explain_fee`)
   4. **[Required]** Help resolve the payment issue
      - *For card updates: Direct them to https://parkm.app/account/login to update their payment method. Or you can delete the old method on backend: Payments tab > delete old card. Note: we can only delete payment methods, NOT add them on the backend.*
   5. If payment is stuck and they need to park tonight: Issue a free temp permit
      - *Issue for a few days while the payment issue is resolved.*
   6. **[Required]** Send response and close ticket

   **Validation Checklist (on close):**
   - [ ] Did you identify and resolve the payment issue?
   - [ ] Did you respond to the customer?

   **Quick Response Templates:**
   - How to Update Payment (`how_to_update_payment.html`)
   - Payment Issue Follow-Up (`payment_issue_follow_up.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #11: Property: Extend Permit + Change Resident Type

**Subject:** Lease renewal - extend permit and change type
**From:** management@ivycourt.com

**Email Body:**
> Hello ParkM, this is management at Ivy Court. Resident in unit 208, James White, renewed his lease and is upgrading from Standard to Premium parking. We need to: 1) Extend his permit expiration from March 31st to September 30th, and 2) Change his resident type to Premium. Plate WXY3456. Thanks!

### Classification Results

- **Tags (2):** Property Extending Expiration Date on a Permit; Property Changing Resident Type for Approved Permit
- **Confidence:** 90%
- **Complexity:** simple
- **Urgency:** medium
- **Key Entities:** `license_plate`: **WXY3456**, `property_name`: **Ivy Court**, `unit_number`: **208**
- **Requires Human Review:** No
- **Routing:** Property Support

### Wizard Steps

#### Intent 1: Property Extending Expiration Date on a Permit

**P Property: Extend Permit Expiration**

> Property is requesting an extension on a permit's expiration date.

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Locate the permit to extend
   3. **[Required]** Determine the permit type and use the correct method
      - *RECURRING PAID permits: The 'Extend Expiration Date' button does NOT work on these. Use 'Move Next Recurring Date' instead.
FREE or ONE-TIME permits: Use either 'Extend Expiration Date' or 'Delay Cancellation' - both work.*
   4. **[Required]** Extend the permit
      - *Actions > Extend Expiration Date (or Move Next Recurring Date for recurring). Set the new date as requested by the property.*
   5. **[Required]** Confirm with the property
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you use the correct method based on permit type?
   - [ ] Did you confirm with the property?

   **Quick Response Templates:**
   - Permit Extended (`permit_extended.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

#### Intent 2: Property Changing Resident Type for Approved Permit

**B Property: Change Resident Type**

> Property manager is requesting a resident type change so a resident can purchase a specific permit type (e.g., carport, garage).

   1. **[Required]** Search parkm.app by the resident's email or name
   2. **[Required]** Confirm which resident type the property is requesting
      - *Check the property notes in Zoho CRM. Example: at some properties, residents need to be 'Resident X' to get carport/garage permits.*
   3. **[Required]** Change the resident type
      - *Go to the resident's account > Edit > Change 'Customer Classification' to the requested type > Save.*
   4. **[Required]** Notify the property that the change has been made
      - *Let them know the resident can now purchase the approved permit type.*
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you change the resident type as requested?
   - [ ] Did you notify the property?

   **Quick Response Templates:**
   - Resident Type Changed (`resident_type_changed.html`)
   - General Inquiry Response (`general_inquiry_response.html`)

---

## Multi-Intent #12: Refund + Update Contact Info + Miscellaneous

**Subject:** Moving out - refund, update info, and questions
**From:** multi12@gmail.com

**Email Body:**
> Hi, I'm moving out of Parkside Heights on March 20th. A few things: 1) I need a refund on my remaining permit balance - I was charged $70 on March 1st. 2) My new email will be jane.newemail@gmail.com and phone 555-999-8888, please update that. 3) Also, do I need to return any parking stickers or key fobs? Plate ZAB4567, unit 506.

### Classification Results

- **Tags (3):** Customer Canceling a Permit and Refunding; Customer Update Contact Info; Customer Miscellaneous Questions
- **Confidence:** 85%
- **Complexity:** moderate
- **Urgency:** medium
- **Key Entities:** `license_plate`: **ZAB4567**, `move_out_date`: **March 20th**, `property_name`: **Parkside Heights**, `amount`: **70**, `unit_number`: **506**
- **Requires Human Review:** Yes
- **Routing:** Accounting/Refunds

### Wizard Steps

#### Intent 1: Customer Canceling a Permit and Refunding

**$ Cancel Permit + Refund**

> Customer wants to cancel their permit AND get a refund. Refund window is 30 days from the LAST charge date.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Open the Vehicles and Permits tab
      - *Confirm the license plate and permit. Extracted plate: ZAB4567*
      - Entity `license_plate`: **ZAB4567** (found in email)
   3. **[Required]** Check if permit is already canceled
      - *If already canceled, note the cancellation date for eligibility calculation.*
   4. **[Required]** Open the Payments tab - find the last charge date and amount
      - *Refund window is 30 days from the LAST charge date.*
   5. **[Required]** Verify move-out date is within the 30-day refund window
      - *Move-out date from email: March 20th. If not found, ask the customer.*
      - Entity `move_out_date`: **March 20th** (found in email)
   6. **[Required]** Set permit to Delay Cancel (1 week out)
      - *Do NOT cancel immediately. Use Actions > Cancel > Delay Cancellation and set to 1 week. Delete the 'Next Recurring Date' so they are not charged again. Tell resident: 'Your permit is set to cancel on [date]. You will not be charged again.'*
   7. **[Required]** Determine refund eligibility
      - **DECISION POINT** - Choose one:
        - Eligible - Forward to Accounting (action: `submit_refund`) -> template: `refund_forward_accounting.html`
        - Deny - Outside 30-Day Window (action: `deny_outside_window`) -> template: `refund_denied_outside_window.html`
   8. **[Required]** If eligible: Forward WHOLE thread to accounting@parkm.com
      - *Include: customer email on account, refund amount, reason (e.g. 'Moved Out'), and property name. Format:
[email]
$[amount]
[reason]
[property name]
Then set ticket status to 'Waiting on Accounting'.*
      - Email: mailto:accounting@parkm.com
      - *(Only shown if action = `submit_refund`)*
   9. **[Required]** Send response email to customer
   10. **[Required]** Update ticket status (Waiting on Accounting or Closed)

   **Validation Checklist (on close):**
   - [ ] Did you verify the move-out date is within 30 days of the last charge?
   - [ ] Did you set the permit to delay cancel (not immediate)?
   - [ ] Did you delete the Next Recurring Date?
   - [ ] Did you forward to accounting@parkm.com (if eligible) OR send denial?

   **Quick Response Templates:**
   - Missing License Plate (`missing_license_plate.html`)
   - Missing Move-Out Date (`missing_move_out_date.html`)
   - Refund Approved (`refund_approved.html`)
   - Refund Denied - Outside Window (`refund_denied_outside_window.html`)
   - Cancellation Confirmed (`cancellation_confirmed.html`)

#### Intent 2: Customer Update Contact Info

**E Update Contact Info**

> Customer wants to update their email, phone, address, or unit number.

   1. **[Required]** Search parkm.app by customer email address
   2. **[Required]** Identify what contact info needs updating
      - *Common updates: email address, phone number, unit number.*
   3. **[Required]** Update the info in parkm.app
      - *Go to the customer's account > Manage User or Edit to update email/phone/unit.*
   4. **[Required]** Verify the change saved correctly
   5. **[Required]** Send confirmation to customer
      - Template: `account_update_confirmed.html`
   6. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you verify the update saved?
   - [ ] Did you confirm with the customer?

   **Quick Response Templates:**
   - Account Update Confirmed (`account_update_confirmed.html`)

#### Intent 3: Customer Miscellaneous Questions

**? Miscellaneous Question**

> General customer question that does not fit other categories. Read carefully and respond with a clear, helpful answer.

   1. **[Required]** Read the full email carefully
   2. Search parkm.app by customer email (if account-specific)
   3. **[Required]** Research the answer using Zoho CRM notes and parkm.app
      - *Check property notes in Zoho CRM for any special rules. If unsure, email internalmanagers@parkm.com for guidance.*
      - Email: mailto:internalmanagers@parkm.com
   4. **[Required]** Compose a clear, friendly, and informative response
      - *Remember: the goal is to give residents clear and informative answers, even if it means writing a more detailed email.*
      - Template: `general_inquiry_response.html`
   5. **[Required]** Close ticket

   **Validation Checklist (on close):**
   - [ ] Did you fully answer the customer's question?

   **Quick Response Templates:**
   - General Inquiry Response (`general_inquiry_response.html`)
   - FAQ Page Link (`faq_link.html`)

---

# Summary

- **Total single-intent tests:** 50
- **Total multi-intent tests:** 12
- **Total classifications run:** 62
- **Generated on:** March 12, 2026

Please review each test case and note any corrections needed.
Send feedback to Eli and the team.