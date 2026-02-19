# P1: AI Email Classification — Call Prep for Katie

## The Problem

CSRs manually read every incoming Zoho Desk ticket, figure out what the customer wants, and route it. This is slow, inconsistent, and doesn't scale.

## The Solution

An AI classifier that **automatically reads every incoming ticket, categorizes it, extracts key info, and writes it back to Zoho** — all in ~5 seconds, before a CSR even opens it.

---

## What the AI Classifies (10 fields per ticket)

| Field | What It Does |
|-------|-------------|
| **Intent** | 9 categories: refund_request, permit_cancellation, account_update, permit_inquiry, payment_issue, technical_issue, move_out, general_question, unclear |
| **Complexity** | simple / moderate / complex |
| **Language** | english / spanish / mixed / other |
| **Urgency** | high / medium / low |
| **Confidence** | 0-100% with calibrated scoring rules (not just 95% on everything) |
| **Requires Refund** | Yes/No flag |
| **Requires Human Review** | Yes/No flag |
| **License Plate** | Extracted if mentioned |
| **Move-Out Date** | Extracted and parsed to YYYY-MM-DD |
| **Routing Queue** | Suggested queue label (see Routing section below) |

## What Happens When a Ticket Comes In

1. Zoho webhook fires on new ticket
2. System fetches full ticket details via Zoho API
3. GPT-4o classifies the email (~2-3 sec)
4. **10 custom fields** written back to the ticket in Zoho
5. **Internal comment** added with full classification breakdown
6. Everything logged for analytics

## Key Design Decisions

- **Confidence calibration** — Strict scoring rules with mandatory deductions (empty body = max 55%, missing entities = -5% each). Prevents the AI from being overconfident.
- **Intent disambiguation** — Detailed rules for overlapping intents (e.g., "I moved out, refund me" = refund_request, not move_out)
- **7 few-shot examples** baked into the prompt for edge cases
- **Entity extraction** — License plates, dates, amounts, property names pulled automatically

## Routing Recommendation

Each ticket gets a suggested queue label written to `cf_routing_queue` as a custom field:

| Condition | Label |
|-----------|-------|
| Simple refund | Auto-Resolution Queue |
| Refund/payment (not simple) | Accounting/Refunds |
| Simple cancel or account update | Quick Updates |
| Complex or high urgency | Escalations |
| Everything else | General Support |

> **Note:** This is a recommendation only — no tickets are moved automatically today. The `move_to_department()` API method exists and is ready to wire up, but actual auto-routing would need Katie's input on department structure and whether they want tickets moved without CSR review. This is a natural Phase 2 enhancement once the classification accuracy is validated in production.

## What's Written to Zoho (per ticket)

- `cf_ai_intent` — dropdown
- `cf_ai_complexity` — dropdown
- `cf_ai_language` — dropdown
- `cf_ai_urgency` — dropdown
- `cf_ai_confidence` — number (0-100)
- `cf_requires_refund` — boolean
- `cf_requires_human_review` — boolean
- `cf_license_plate` — text
- `cf_move_out_date` — date
- `cf_routing_queue` — text
- Plus an internal comment with the full breakdown

## Correction Feedback Loop

- CSRs can set `cf_agent_corrected_intent` if the AI was wrong
- A webhook catches the update and logs the correction
- Corrections feed the analytics dashboard (confusion matrix, accuracy tracking)
- These will be used to improve the prompt over time

## Current Stats (sandbox)

- **94 tickets classified**, 0 errors
- **80% avg confidence** (calibrated, not inflated)
- **~5s avg processing time** per ticket
- **100% tagging success** — every classification written back to Zoho
- **Live webhook** — new tickets auto-classify in ~5 seconds

## What's Live Right Now

- API running on Railway: `parkm-production.up.railway.app`
- Sandbox org connected and tested (org: 856336669)
- Webhook registered — new tickets auto-classify
- Analytics dashboard tracking everything: `parkm-production.up.railway.app/analytics/dashboard`

## Demo Flow

1. Create a new ticket in the sandbox (any subject/body)
2. Wait ~5 seconds
3. Open the ticket — all 10 custom fields populated + internal comment
4. Show the analytics dashboard updating in real-time

## What's Next for Production

1. Create the same 10 custom fields in production Zoho Desk
2. Swap sandbox credentials for production org in Railway env vars
3. Register the webhook URL in Zoho Desk production
4. Then it's live — every new ticket auto-classifies
