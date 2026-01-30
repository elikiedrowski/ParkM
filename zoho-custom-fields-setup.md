# Zoho Desk Custom Fields Setup Guide

## Overview
This guide provides step-by-step instructions for creating custom fields in Zoho Desk to support the AI classification system.

**Estimated Time:** 15-20 minutes  
**Required Access:** Zoho Desk Administrator

---

## Custom Fields to Create

### 1. AI Intent
- **Field Name:** `AI Intent`
- **API Name:** `cf_ai_intent`
- **Type:** Dropdown (Single Select)
- **Description:** AI-detected customer intent
- **Options:**
  1. refund_request
  2. permit_cancellation
  3. account_update
  4. payment_issue
  5. permit_inquiry
  6. move_out
  7. technical_issue
  8. general_question
  9. unclear

### 2. AI Complexity
- **Field Name:** `AI Complexity`
- **API Name:** `cf_ai_complexity`
- **Type:** Dropdown (Single Select)
- **Description:** Complexity level of the request
- **Options:**
  1. simple
  2. moderate
  3. complex

### 3. AI Language
- **Field Name:** `AI Language`
- **API Name:** `cf_ai_language`
- **Type:** Dropdown (Single Select)
- **Description:** Detected language of the email
- **Options:**
  1. english
  2. spanish
  3. mixed
  4. other

### 4. AI Urgency
- **Field Name:** `AI Urgency`
- **API Name:** `cf_ai_urgency`
- **Type:** Dropdown (Single Select)
- **Description:** Urgency level based on tone and content
- **Options:**
  1. high
  2. medium
  3. low

### 5. AI Confidence
- **Field Name:** `AI Confidence`
- **API Name:** `cf_ai_confidence`
- **Type:** Number (Integer)
- **Description:** Classification confidence percentage (0-100)
- **Default Value:** 0
- **Validation:** Min: 0, Max: 100

### 6. Requires Refund
- **Field Name:** `Requires Refund`
- **API Name:** `cf_requires_refund`
- **Type:** Checkbox (Boolean)
- **Description:** AI detected refund request
- **Default Value:** Unchecked

### 7. Requires Human Review
- **Field Name:** `Requires Human Review`
- **API Name:** `cf_requires_human_review`
- **Type:** Checkbox (Boolean)
- **Description:** Flagged for human review (low confidence or complex)
- **Default Value:** Unchecked

### 8. License Plate
- **Field Name:** `License Plate`
- **API Name:** `cf_license_plate`
- **Type:** Single Line (Text)
- **Description:** Extracted vehicle license plate number
- **Max Length:** 20 characters

### 9. Move Out Date
- **Field Name:** `Move Out Date`
- **API Name:** `cf_move_out_date`
- **Type:** Date
- **Description:** Extracted customer move-out date (for refund eligibility)
- **Format:** YYYY-MM-DD

### 10. Routing Queue
- **Field Name:** `Routing Queue`
- **API Name:** `cf_routing_queue`
- **Type:** Single Line (Text)
- **Description:** AI-recommended queue for routing
- **Max Length:** 50 characters

---

## Step-by-Step Creation Process

### Access Custom Fields Settings

1. Log in to **Zoho Desk** (sandbox: https://desk.zoho.com)
2. Click the **Settings** icon (gear icon) in the top-right
3. Navigate to: **Customization → Layouts and Fields → Tickets**
4. Click on **Fields** tab
5. Click **+ New Field** button

### For Each Field Above:

1. **Enter Field Label** (e.g., "AI Intent")
2. **Select Field Type** (Dropdown, Number, Checkbox, etc.)
3. **Add Description** (copy from above)
4. **Configure Options** (for dropdown fields):
   - Click "Add Option"
   - Enter each option exactly as listed
   - Do NOT change the option values
5. **Set Default Value** (if specified)
6. **Add Validation Rules** (for Number fields: min 0, max 100)
7. **Click Save**
8. **Note the API Name** - Zoho will auto-generate (usually `cf_<field_name>`)

### Verify API Names

After creating all fields:

1. Go to **Setup → Developer Space → APIs → Fields**
2. Find each custom field in the list
3. Note the actual API name (e.g., `cf_ai_intent`)
4. **IMPORTANT:** If Zoho generates different API names, update `src/services/tagger.py`:

```python
self.custom_fields = {
    "intent": "cf_ai_intent",  # Replace with actual API name from Zoho
    "complexity": "cf_ai_complexity",
    "language": "cf_ai_language",
    # ... etc
}
```

---

## Testing Custom Fields

After creating all fields:

### 1. Manual Test
1. Create a test ticket manually in Zoho Desk
2. Open the ticket
3. Verify all 10 new custom fields appear in the ticket details
4. Try setting values manually to ensure fields work

### 2. API Test
Run this Python script to test API access to custom fields:

```python
import httpx
from src.config import get_settings

settings = get_settings()

async def test_custom_fields():
    # Get a test ticket
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.zoho_base_url}/tickets",
            headers={
                "Authorization": f"Zoho-oauthtoken {settings.zoho_api_token}",
                "orgId": settings.zoho_org_id
            },
            params={"limit": 1}
        )
        
        tickets = response.json().get("data", [])
        if tickets:
            ticket = tickets[0]
            print("Custom fields in ticket:")
            for key, value in ticket.items():
                if key.startswith("cf_"):
                    print(f"  {key}: {value}")

# Run test
import asyncio
asyncio.run(test_custom_fields())
```

---

## Webhook Configuration

After custom fields are created:

### 1. Configure Webhook in Zoho Desk

1. Go to **Setup → Developer Space → Webhooks**
2. Click **+ New Webhook**
3. **Webhook Name:** `AI Classification - Ticket Created`
4. **Description:** `Triggers AI classification when new ticket is created`
5. **Webhook URL:** `https://<your-public-url>/webhooks/zoho/ticket-created`
   - For testing, use ngrok: `https://abc123.ngrok.io/webhooks/zoho/ticket-created`
   - For production, use your server URL
6. **Method:** POST
7. **Event:** Ticket Created
8. **Format:** JSON
9. **Include:** Ticket ID, Subject, Description, Email, Status
10. Click **Save**

### 2. Set Up Public URL (for testing)

Using **ngrok**:
```bash
# Install ngrok (if not installed)
# Download from https://ngrok.com/download

# Start ngrok tunnel to local server
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Use this URL in Zoho webhook configuration
```

Using **CloudFlare Tunnel** (alternative):
```bash
# Install cloudflared
# Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

# Start tunnel
cloudflared tunnel --url http://localhost:8000

# Copy the HTTPS URL provided
# Use this URL in Zoho webhook configuration
```

### 3. Test Webhook Delivery

1. Create a test ticket in Zoho Desk
2. Check webhook logs: `tail -f logs/webhook.log`
3. Verify webhook received and processed
4. Check ticket in Zoho - custom fields should be populated

---

## Validation Checklist

- [ ] All 10 custom fields created in Zoho Desk
- [ ] Fields appear in ticket detail view
- [ ] API names documented in `src/services/tagger.py`
- [ ] Manual field update test successful
- [ ] Webhook configured in Zoho
- [ ] Public URL accessible (ngrok or server)
- [ ] Test ticket created and webhook triggered
- [ ] Classification ran successfully
- [ ] Custom fields populated with AI data
- [ ] Logs show successful tagging

---

## Troubleshooting

### Custom Fields Not Appearing in API Response
- Check field visibility settings (ensure "API Enabled")
- Verify field is added to the ticket layout
- Try refreshing the Zoho session

### Webhook Not Firing
- Verify webhook is enabled in Zoho settings
- Check webhook URL is accessible (test with curl)
- Ensure event filter matches (Ticket Created)
- Check Zoho webhook logs in Settings → Webhooks → View Logs

### Tagging Fails (401 Unauthorized)
- OAuth token may have expired
- Check token refresh mechanism in `src/api/zoho_client.py`
- Manually refresh token using `oauth_setup.py`

### Tagging Fails (400 Bad Request)
- API field name mismatch
- Verify actual API names in Zoho match `tagger.py`
- Check field value format (e.g., date format, number range)

---

## Next Steps

After completing this setup:

1. ✅ Custom fields created
2. ✅ Webhook configured
3. → Proceed to Week 2 Day 5: Integration Testing
4. → Test end-to-end flow with various email types
5. → Monitor performance and accuracy
6. → Proceed to Week 3: Queue routing and monitoring

---

**Estimated Setup Time:** 15-20 minutes  
**Prerequisites:** Zoho Desk Admin access, API credentials configured  
**Support:** Check `priority-1-progress.md` for current status
