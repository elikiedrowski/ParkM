# ✅ Zoho Desk Custom Fields - Quick Setup Checklist

**Time Required:** 15-20 minutes  
**Current Status:** Ready to create fields manually

---

## 📋 Step-by-Step Instructions

### 1. Access Zoho Desk Settings
- [ ] Log in to https://desk.zoho.com
- [ ] Click **Settings** (⚙️ gear icon in top-right)
- [ ] Navigate to: **Customization** → **Layouts and Fields** → **Tickets**
- [ ] Click the **Fields** tab
- [ ] Click **+ New Field** button

---

## 📝 Fields to Create (10 total)

### Field 1 of 10: AI Intent ⭐
```
Field Label: AI Intent
Field Type: Dropdown (Single Select)
Description: AI-detected customer intent
Options (add exactly as shown):
  - refund_request
  - permit_cancellation
  - account_update
  - payment_issue
  - permit_inquiry
  - move_out
  - technical_issue
  - general_question
  - unclear
```
- [ ] Created

---

### Field 2 of 10: AI Complexity
```
Field Label: AI Complexity
Field Type: Dropdown (Single Select)
Description: Complexity level of the request
Options:
  - simple
  - moderate
  - complex
```
- [ ] Created

---

### Field 3 of 10: AI Language
```
Field Label: AI Language
Field Type: Dropdown (Single Select)
Description: Detected language of the email
Options:
  - english
  - spanish
  - mixed
  - other
```
- [ ] Created

---

### Field 4 of 10: AI Urgency
```
Field Label: AI Urgency
Field Type: Dropdown (Single Select)
Description: Urgency level based on tone and content
Options:
  - high
  - medium
  - low
```
- [ ] Created

---

### Field 5 of 10: AI Confidence
```
Field Label: AI Confidence
Field Type: Number
Description: Classification confidence percentage (0-100)
Default Value: 0
Min Value: 0
Max Value: 100
```
- [ ] Created

---

### Field 6 of 10: Requires Refund
```
Field Label: Requires Refund
Field Type: Checkbox (Boolean)
Description: AI detected refund request
Default Value: Unchecked
```
- [ ] Created

---

### Field 7 of 10: Requires Human Review
```
Field Label: Requires Human Review
Field Type: Checkbox (Boolean)
Description: Flagged for human review (low confidence or complex)
Default Value: Unchecked
```
- [ ] Created

---

### Field 8 of 10: License Plate
```
Field Label: License Plate
Field Type: Single Line (Text)
Description: Extracted vehicle license plate number
Max Length: 20 characters
```
- [ ] Created

---

### Field 9 of 10: Move Out Date
```
Field Label: Move Out Date
Field Type: Date
Description: Extracted customer move-out date (for refund eligibility)
Date Format: YYYY-MM-DD
```
- [ ] Created

---

### Field 10 of 10: Routing Queue
```
Field Label: Routing Queue
Field Type: Single Line (Text)
Description: AI-recommended queue for routing
Max Length: 50 characters
```
- [ ] Created

---

## ✅ Verification Steps

### After Creating All Fields:

1. **Verify in Ticket Layout**
   - [ ] Go to Settings → Customization → Layouts and Fields → Tickets
   - [ ] Click on your layout (usually "Standard")
   - [ ] Confirm all 10 new fields appear in the layout
   - [ ] If missing, drag them from "Available Fields" to the layout

2. **Get API Names**
   - [ ] Go to Settings → Developer Space → APIs
   - [ ] Look for "Fields" or create a test ticket to see field names
   - [ ] Note the actual API names (should be cf_ai_intent, cf_ai_complexity, etc.)

3. **Test Manually**
   - [ ] Create a test ticket
   - [ ] Open the ticket
   - [ ] Verify all 10 custom fields are visible
   - [ ] Try setting values manually to ensure they work

---

## 🔧 Next: Update Tagger Configuration

After creating fields, if Zoho generated different API names:

```bash
# Edit this file:
nano src/services/tagger.py

# Update the custom_fields mapping around line 20:
self.custom_fields = {
    "intent": "cf_ai_intent",           # ← Replace with actual API name
    "complexity": "cf_ai_complexity",    # ← Replace with actual API name
    "language": "cf_ai_language",        # ← Replace with actual API name
    # ... etc
}
```

---

## 🎯 Quick Reference Card

**Dropdown Fields (4):**
- AI Intent (9 options)
- AI Complexity (3 options)
- AI Language (4 options)  
- AI Urgency (3 options)

**Checkbox Fields (2):**
- Requires Refund
- Requires Human Review

**Text Fields (2):**
- License Plate (max 20 chars)
- Routing Queue (max 50 chars)

**Number Field (1):**
- AI Confidence (0-100)

**Date Field (1):**
- Move Out Date

**TOTAL: 10 fields**

---

## 🚨 Common Issues

**Issue:** Field doesn't appear in ticket
- **Fix:** Check layout configuration, drag field from "Available" section

**Issue:** Can't find API name
- **Fix:** Create a test ticket and check the JSON response via API

**Issue:** Dropdown options not saving
- **Fix:** Make sure to click "Add" after typing each option

---

## ✅ Completion Checklist

- [ ] All 10 fields created in Zoho Desk
- [ ] Fields added to ticket layout
- [ ] API names verified (cf_ai_intent, cf_ai_complexity, etc.)
- [ ] Test ticket created successfully
- [ ] Manual field update test passed

**When done, proceed to:** [Week 2 Day 3: Webhook Configuration](zoho-custom-fields-setup.md#webhook-configuration)

---

**Estimated Time:** 2 minutes per field = 20 minutes total  
**Status:** ⏳ Awaiting manual creation  
**Next Step:** Webhook configuration + integration testing
