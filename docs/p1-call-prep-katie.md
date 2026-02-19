# P1: AI Email Classification

## The Problem

CSRs manually read every incoming Zoho Desk ticket, figure out what the customer wants, and route it. This is slow, inconsistent, and doesn't scale.

## The Solution

An AI classifier that **automatically reads every incoming ticket, categorizes it, extracts key info, and writes it back to Zoho** — all in ~5 seconds, before a CSR even opens it.

---

## System Architecture

```mermaid
graph LR
    A[Customer Email] --> B[Zoho Desk]
    B -->|Webhook| C[ParkM API<br/>Railway.app]
    C --> D[GPT-4o<br/>Classifier]
    D --> C
    C -->|Write 10 Fields<br/>+ Internal Comment| B
    C --> E[Analytics<br/>Dashboard]

    style A fill:#FFC107,stroke:#003060,color:#003060
    style B fill:#046bd2,stroke:#003060,color:#fff
    style C fill:#003060,stroke:#024985,color:#fff
    style D fill:#024985,stroke:#003060,color:#fff
    style E fill:#046bd2,stroke:#003060,color:#fff
```

## End-to-End Flow

```mermaid
sequenceDiagram
    participant Customer
    participant Zoho as Zoho Desk
    participant API as ParkM API
    participant AI as GPT-4o
    participant Dashboard as Analytics

    Customer->>Zoho: Sends email
    Zoho->>Zoho: Creates ticket
    Zoho->>API: Webhook (ticket_created)
    API->>Zoho: Fetch full ticket details
    Zoho-->>API: Subject + body + metadata
    API->>AI: Classify email
    AI-->>API: Intent, confidence, entities, etc.
    API->>Zoho: Write 10 custom fields
    API->>Zoho: Add internal comment
    API->>Dashboard: Log classification event
    Note over Zoho: CSR opens ticket —<br/>all fields pre-populated
```

## What the AI Classifies (10 fields per ticket)

| Field | Type | Values |
|-------|------|--------|
| **Intent** | Dropdown | refund_request, permit_cancellation, account_update, permit_inquiry, payment_issue, technical_issue, move_out, general_question, unclear |
| **Complexity** | Dropdown | simple, moderate, complex |
| **Language** | Dropdown | english, spanish, mixed, other |
| **Urgency** | Dropdown | high, medium, low |
| **Confidence** | Number | 0-100% (calibrated with mandatory deductions) |
| **Requires Refund** | Boolean | Yes / No |
| **Requires Human Review** | Boolean | Yes / No |
| **License Plate** | Text | Extracted from email body |
| **Move-Out Date** | Date | Parsed to YYYY-MM-DD |
| **Routing Queue** | Text | Suggested department (see below) |

## Intent Classification Logic

```mermaid
flowchart TD
    A[Incoming Email] --> B{Mentions refund<br/>or money back?}
    B -->|Yes| C[refund_request]
    B -->|No| D{Wants to cancel<br/>permit?}
    D -->|Yes| E[permit_cancellation]
    D -->|No| F{Update account<br/>info?}
    F -->|Yes| G[account_update]
    F -->|No| H{Billing or<br/>charge issue?}
    H -->|Yes| I[payment_issue]
    H -->|No| J{App or login<br/>problem?}
    J -->|Yes| K[technical_issue]
    J -->|No| L{Moving out<br/>notification?}
    L -->|Yes| M[move_out]
    L -->|No| N{Question about<br/>permits?}
    N -->|Yes| O[permit_inquiry]
    N -->|No| P{Can determine<br/>intent?}
    P -->|Yes| Q[general_question]
    P -->|No| R[unclear]

    style C fill:#003060,color:#fff
    style E fill:#046bd2,color:#fff
    style G fill:#024985,color:#fff
    style I fill:#FFC107,color:#003060
    style K fill:#046bd2,color:#fff
    style M fill:#003060,color:#fff
    style O fill:#024985,color:#fff
    style Q fill:#046bd2,color:#fff
    style R fill:#dc2626,color:#fff
```

## Confidence Calibration

The AI doesn't just say "95% confident" on everything. We enforce strict scoring:

| Score Range | Meaning | Rule |
|-------------|---------|------|
| **90-100%** | Crystal clear intent + all key entities present | Very few emails qualify |
| **75-89%** | Clear intent, missing some entities | No plate, no date, no amount |
| **60-74%** | Ambiguous — could be multiple intents | Vague language, conflicting signals |
| **40-59%** | Very unclear, short, contradictory | Subject-only emails cap at 55% |
| **Below 40%** | Cannot determine intent | Gibberish, empty, off-topic |

**Mandatory deductions:**
- Empty body (subject only) → max 55%
- Forwarded/reply chain noise → -10%
- Multiple possible intents → max 70%
- Missing license plate → -5%
- Missing move-out date → -5%

## Routing Recommendation

```mermaid
flowchart LR
    A[Classification] --> B{Intent + Complexity}
    B -->|Simple refund| C[Auto-Resolution Queue]
    B -->|Refund/payment<br/>not simple| D[Accounting / Refunds]
    B -->|Simple cancel<br/>or account update| E[Quick Updates]
    B -->|Complex or<br/>high urgency| F[Escalations]
    B -->|Everything else| G[General Support]

    style C fill:#046bd2,color:#fff
    style D fill:#FFC107,color:#003060
    style E fill:#024985,color:#fff
    style F fill:#dc2626,color:#fff
    style G fill:#003060,color:#fff
```

> **Note:** This is a recommendation label only — no tickets are moved automatically today. The `move_to_department()` API method exists and is ready to wire up, but actual auto-routing needs Katie's input on department structure and whether tickets should move without CSR review. This is a natural Phase 2 enhancement once classification accuracy is validated in production.

## Correction Feedback Loop

```mermaid
flowchart LR
    A[AI classifies ticket] --> B[CSR reviews classification]
    B -->|Correct| C[No action needed]
    B -->|Wrong| D[CSR sets<br/>cf_agent_corrected_intent]
    D --> E[Webhook fires]
    E --> F[Correction logged<br/>to JSONL]
    F --> G[Analytics Dashboard<br/>Confusion Matrix]
    G --> H[Prompt improvement<br/>over time]

    style D fill:#FFC107,color:#003060
    style F fill:#046bd2,color:#fff
    style G fill:#003060,color:#fff
    style H fill:#024985,color:#fff
```

## Current Stats (Sandbox)

- **94 tickets classified**, 0 errors
- **80% avg confidence** (calibrated, not inflated)
- **~5s avg processing time** per ticket
- **100% tagging success** — every classification written back to Zoho
- **Live webhook** — new tickets auto-classify within seconds

## What's Live Right Now

| Component | Status | URL |
|-----------|--------|-----|
| ParkM API | Healthy | `parkm-production.up.railway.app` |
| Zoho Sandbox | Connected | Org: 856336669 |
| Webhook | Active | Auto-classifies on ticket creation |
| Analytics Dashboard | Live | `parkm-production.up.railway.app/analytics/dashboard` |

## Demo Flow

1. Create a new ticket in the sandbox (any subject/body)
2. Wait ~5 seconds
3. Open the ticket — all 10 custom fields populated + internal comment
4. Show the analytics dashboard updating in real-time

## Production Rollout Steps

```mermaid
flowchart LR
    A[Create 10 custom<br/>fields in prod Zoho] --> B[Swap credentials<br/>in Railway env vars]
    B --> C[Register webhook<br/>URL in prod Zoho]
    C --> D[Live — every new<br/>ticket auto-classifies]

    style A fill:#FFC107,color:#003060
    style B fill:#046bd2,color:#fff
    style C fill:#024985,color:#fff
    style D fill:#003060,color:#fff
```

1. Create the same 10 custom fields in production Zoho Desk
2. Swap sandbox credentials for production org in Railway env vars
3. Register the webhook URL in Zoho Desk production
4. Live — every new ticket auto-classifies
