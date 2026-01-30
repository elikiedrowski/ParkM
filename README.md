# ParkM Zoho Desk AI Integration

## Project Overview
AI-powered email classification and workflow assistance for ParkM's customer support team using OpenAI GPT-4o to automatically classify, tag, and route support tickets in Zoho Desk.

**Current Status:** ✅ Week 2 - Custom field integration complete and tested in sandbox

## Features

✅ **Implemented & Tested:**
- AI-powered email classification (95% confidence)
- 10-point classification schema (intent, complexity, language, urgency, etc.)
- Automatic custom field population in Zoho Desk
- Entity extraction (license plates, move-out dates, amounts)
- Internal comment generation with classification details
- Routing recommendations (6 specialized queues)
- FastAPI webhook server with test endpoints

🚧 **In Progress:**
- Webhook automation (requires ngrok + Zoho configuration)
- Queue routing implementation
- Monitoring dashboard

## Architecture

### Email Triage & Classification System
- **Input**: New tickets created in Zoho Desk
- **Process**: AI classification using GPT-4o (2-3 second processing)
- **Output**: 10 custom fields populated + routing recommendation

### Components
1. **FastAPI Webhook Server** (`main.py`) - Receives ticket notifications
2. **Email Classifier** (`src/services/classifier.py`) - GPT-4o classification engine
3. **Auto-Tagger** (`src/services/tagger.py`) - Updates Zoho custom fields via API
4. **Zoho API Client** (`src/api/zoho_client.py`) - Async API wrapper
5. **Webhook Processor** (`src/api/webhooks.py`) - Background task handler

## Tech Stack
- **Backend**: Python 3.11, FastAPI 0.128.0, Uvicorn (ASGI)
- **AI**: OpenAI GPT-4o (gpt-4o model)
- **Integration**: Zoho Desk API v1 (OAuth 2.0)
- **Async HTTP**: httpx
- **Environment**: Sandbox Org 856336669, Production Org 854251057

## Getting Started

### Prerequisites
- Python 3.11+
- Zoho Desk account with admin access
- OpenAI API key (GPT-4o access)
- Zoho OAuth credentials (Client ID, Secret, Refresh Token)

### Installation

```bash
# Clone repository
git clone https://github.com/elikiedrowski/ParkM.git
cd ParmM_Zoho

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
# - ZOHO_ORG_ID (sandbox: 856336669, production: 854251057)
# - ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET
# - OPENAI_API_KEY

# Run OAuth setup (generates refresh token)
python3 oauth_setup.py

# Start development server
python3 -m uvicorn main:app --reload --port 8000
```

### Custom Field Setup

Before testing, create 10 custom fields in Zoho Desk:

```bash
# Follow the detailed checklist:
cat SETUP-CUSTOM-FIELDS-CHECKLIST.md
```

**Required Custom Fields:**
1. AI Intent (dropdown, 9 options)
2. AI Complexity (dropdown: simple/moderate/complex)
3. AI Language (dropdown: english/spanish/mixed/other)
4. AI Urgency (dropdown: high/medium/low)
5. AI Confidence (number, 0-100)
6. Requires Refund (checkbox)
7. Requires Human Review (checkbox)
8. License Plate (text, max 20 chars)
9. Move Out Date (date, YYYY-MM-DD)
10. Routing Queue (text, max 50 chars)

### Testing

```bash
# Create a test ticket in sandbox
python3 create_test_ticket.py

# Test AI classification and tagging
curl -X POST http://localhost:8000/test-tagging/{TICKET_ID}

# View results in Zoho Desk sandbox:
# https://desk.zoho.com/agent/parkmllc1719353334134/testing/tickets
```

## Project Structure

```
ParmM_Zoho/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── webhooks.py         # Zoho webhook handlers
│   │   └── zoho_client.py      # Zoho API wrapper
│   ├── services/
│   │   ├── classifier.py       # Email classification logic
│   │   ├── tagger.py           # Auto-tagging service
│   │   └── router.py           # Queue routing logic
│   ├── models/
│   │   ├── ticket.py           # Ticket data models
│   │   └── classification.py   # Classification schemas
│   └── config.py               # Configuration management
├── tests/
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

## Development Phases

### Priority 1: Email Classification System (Current - Week 2)
- [x] Set up Zoho API connection (OAuth 2.0)
- [x] Create webhook receiver (FastAPI endpoints)
- [x] Implement AI classifier (GPT-4o, 95% confidence)
- [x] Auto-tag tickets (10 custom fields)
- [x] Test with sample emails (7 scenarios validated)
- [x] Custom field integration tested in sandbox
- [ ] Configure production webhook (ngrok + Zoho setup)
- [ ] Implement queue routing automation
- [ ] Build monitoring dashboard

### Priority 2: Refund Process Automation (Planned)
- [ ] Move-out date validation (30-day window)
- [ ] Refund amount calculation
- [ ] Accounting handoff workflow
- [ ] Missing information detection

### Priority 3: Workflow Guidance (Planned)
- [ ] In-ticket checklist overlay
- [ ] Step-by-step refund process guide
- [ ] Real-time validation

### Priority 4: Unified Agent Desktop (Future)
- [ ] Custom Zoho extension
- [ ] App platform integration
- [ ] Single-pane view

### Priority 5: Progressive Automation (Future)
- [ ] Phase 1: Auto-fill responses (CSR approval)
- [ ] Phase 2: Auto-responses (CSR review)
- [ ] Phase 3: Full automation with monitoring

## Hosting & Cost

### Production Deployment Options

**AI Processing Cost (OpenAI GPT-4o):**
- ~$0.003 per ticket
- 2,500 tickets/month: $7.50
- 5,000 tickets/month: $15.00

**Recommended Hosting:**

| Platform | Cost/Month | Best For | Total (5K tickets) |
|----------|------------|----------|-------------------|
| **DigitalOcean App Platform** | $12-25 | Production (recommended) | $27-40 |
| Railway.app | $5-20 | Dev/Testing | $20-35 |
| AWS Lightsail | $3.50-10 | Enterprise | $18.50-25 |
| Heroku | $7-25 | Rapid deployment | $22-40 |
| Self-hosted VPS | $4-12 | Cost-sensitive | $19-27 |

**Why DigitalOcean App Platform:**
- Zero DevOps maintenance
- Auto-scaling included
- Built-in HTTPS (no ngrok in production)
- Deploy from GitHub in 5 minutes
- Free SSL certificates

**Total Production Cost (5,000 tickets/month): $27-40/month**

## Configuration

See `.env.example` for required environment variables.

## License

Proprietary - CRM Wizards & ParkM
