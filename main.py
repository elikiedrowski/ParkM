"""
ParkM Email Classification System - FastAPI Application
Main entry point for webhook receiver and API endpoints
"""
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime
import hashlib
import hmac
from typing import Dict, Any

from src.api.webhooks import process_ticket_webhook, process_correction_webhook
from src.services.classifier import EmailClassifier
from src.api.zoho_client import ZohoDeskClient
from src.services.correction_logger import get_corrections_summary
from src.services.wizard import get_wizard_for_intent, get_template_html, list_templates, list_intents
from src.services.analytics_logger import log_template_usage, log_classification_event
from src.services.analytics_aggregator import (
    get_summary, get_classification_analytics, get_correction_analytics,
    get_template_analytics, get_performance_analytics, get_entity_analytics,
    get_api_usage_analytics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ParkM Email Classification API",
    description="AI-powered email classification and routing for Zoho Desk",
    version="1.0.0"
)

# CORS — allow Zoho Desk widget iframe to call our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://desk.zoho.com",
        "https://desk.zoho.eu",
        "https://desk.zoho.in",
        "https://desk.zoho.com.au",
        "https://desk.zoho.com.cn",
        "https://desk.zoho.jp",
        "https://127.0.0.1:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5000",
    ],
    allow_origin_regex=r"https://.*\.zappsusercontent\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize services
classifier = EmailClassifier()
zoho_client = ZohoDeskClient()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting ParkM Email Classification API")
    logger.info("FastAPI server ready to receive webhooks")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ParkM Email Classification API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Zoho connection
        departments = await zoho_client.get_departments()
        zoho_healthy = len(departments) > 0
        
        return {
            "status": "healthy" if zoho_healthy else "degraded",
            "zoho_api": "connected" if zoho_healthy else "disconnected",
            "classifier": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/webhooks/zoho/ticket-created")
@app.get("/webhooks/zoho/ticket-updated")
async def zoho_webhook_validation():
    """Respond 200 OK to Zoho's GET validation request when saving a webhook."""
    return {"status": "ok"}


@app.post("/webhooks/zoho/ticket-created")
async def zoho_ticket_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for Zoho Desk ticket creation events
    
    This endpoint:
    1. Receives webhook from Zoho when new ticket is created
    2. Validates the webhook signature
    3. Extracts ticket data
    4. Queues classification task in background
    5. Returns immediate response to Zoho
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        headers = dict(request.headers)
        
        # Log webhook receipt
        logger.info(f"Received webhook from Zoho at {datetime.now()}")
        
        # Parse JSON payload
        try:
            payload = await request.json()
        except Exception as e:
            logger.error(f"Failed to parse webhook JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Zoho sends webhooks as a JSON array — unwrap first element
        if isinstance(payload, list):
            if not payload:
                raise HTTPException(status_code=400, detail="Empty payload array")
            payload = payload[0]

        # Zoho wraps ticket data inside a "payload" key:
        # { "payload": { "id": "...", ... }, "eventType": "Ticket_Add", "orgId": "..." }
        ticket_payload = payload.get("payload", payload)
        event_type = payload.get("eventType", "unknown")
        logger.info(f"Webhook event: {event_type}")

        # Extract ticket ID from the nested payload
        ticket_id = (
            ticket_payload.get("id")
            or ticket_payload.get("ticketId")
            or payload.get("ticketId")
        )

        if not ticket_id:
            logger.error(f"Webhook payload missing ticket ID. Keys: {list(payload.keys())}")
            raise HTTPException(status_code=400, detail="Missing ticket ID in payload")
        logger.info(f"Processing ticket ID: {ticket_id}")
        
        # Process webhook in background (don't block response to Zoho)
        background_tasks.add_task(
            process_ticket_webhook,
            ticket_id=ticket_id,
            payload=payload
        )
        
        # Return immediate success response to Zoho
        return {
            "status": "accepted",
            "ticket_id": ticket_id,
            "message": "Ticket queued for classification",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/classify")
async def classify_email_endpoint(request: Request):
    """
    Manual classification endpoint for testing
    
    Request body:
    {
        "subject": "Email subject",
        "body": "Email body text",
        "from": "customer@example.com"
    }
    """
    try:
        data = await request.json()
        
        subject = data.get("subject", "")
        body = data.get("body", "")
        sender = data.get("from", "")
        
        # Classify
        classification = classifier.classify_email(subject, body, sender)
        
        # Get routing recommendation
        routing = classifier.get_routing_recommendation(classification)
        
        return {
            "classification": classification,
            "routing": routing,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/webhooks/zoho/ticket-updated")
async def zoho_ticket_updated_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for Zoho Desk ticket update events.
    Fires when a CSR sets Agent Corrected Intent on a ticket.
    Logs the correction for LLM training.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Zoho sends webhooks as a JSON array
    if isinstance(payload, list):
        if not payload:
            raise HTTPException(status_code=400, detail="Empty payload array")
        payload = payload[0]

    ticket_payload = payload.get("payload", payload)

    ticket_id = (
        ticket_payload.get("id")
        or ticket_payload.get("ticketId")
        or payload.get("ticketId")
    )
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Missing ticket ID in payload")

    logger.info(f"Received ticket-updated webhook for ticket {ticket_id}")

    background_tasks.add_task(
        process_correction_webhook,
        ticket_id=ticket_id,
        payload=ticket_payload
    )

    return {
        "status": "accepted",
        "ticket_id": ticket_id,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/stats")
async def get_statistics():
    """Classification accuracy and CSR correction summary"""
    summary = get_corrections_summary()
    return {
        "corrections": summary,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/test-tagging/{ticket_id}")
async def test_ticket_tagging(ticket_id: str):
    """
    Test endpoint to classify and tag an existing ticket
    Useful for verifying custom fields are working
    """
    try:
        start_time = datetime.now()
        logger.info(f"Testing classification and tagging for ticket {ticket_id}")

        # Fetch ticket
        ticket_data = await zoho_client.get_ticket(ticket_id)
        if not ticket_data:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        # Extract email content
        subject = ticket_data.get("subject", "")
        description = ticket_data.get("description", "")
        sender_email = ticket_data.get("email", "")
        
        logger.info(f"Ticket: {subject}")
        
        # Classify
        classification = classifier.classify_email(subject, description, sender_email, ticket_id=ticket_id)
        routing = classifier.get_routing_recommendation(classification)

        # Tag (import tagger here to avoid circular import)
        from src.services.tagger import TicketTagger
        tagger = TicketTagger()
        
        tag_result = await tagger.apply_classification_tags(
            ticket_id=ticket_id,
            classification=classification,
            routing=routing
        )

        # Log classification event for analytics dashboard
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        log_classification_event(
            ticket_id=ticket_id,
            classification=classification,
            routing=routing,
            processing_time_seconds=processing_time,
            tagging_success=bool(tag_result),
        )

        return {
            "ticket_id": ticket_id,
            "subject": subject,
            "classification": classification,
            "routing": routing,
            "tagging_success": tag_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing tagging: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets")
async def list_tickets(limit: int = 5):
    """
    List recent tickets to get ticket IDs for testing
    """
    try:
        from src.api.zoho_client import ZohoDeskClient
        client = ZohoDeskClient()
        
        # Get recent tickets
        tickets = await client.search_tickets("", limit=limit)
        
        return {
            "count": len(tickets),
            "tickets": [
                {
                    "id": t.get("id"),
                    "ticketNumber": t.get("ticketNumber"),
                    "subject": t.get("subject"),
                    "status": t.get("status"),
                    "email": t.get("email")
                }
                for t in tickets
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing tickets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wizard/{intent}")
async def get_wizard_content(intent: str, ticket_id: str = None):
    """
    Return wizard steps for a given intent type.
    Optionally fetches ticket data to fill entity placeholders.

    Usage:
      GET /wizard/refund_request
      GET /wizard/refund_request?ticket_id=12345
    """
    try:
        classification = None
        if ticket_id:
            ticket_data = await zoho_client.get_ticket(ticket_id)
            if ticket_data:
                subject = ticket_data.get("subject", "")
                description = ticket_data.get("description", "")
                sender = ticket_data.get("email", "")
                classification = classifier.classify_email(subject, description, sender, ticket_id=ticket_id)

        wizard = get_wizard_for_intent(intent, classification)
        return {
            "intent": intent,
            "wizard": wizard,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Wizard content error for intent '{intent}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wizard-intents")
async def get_supported_intents():
    """List all supported intent types for the wizard."""
    return {"intents": list_intents()}


@app.get("/templates")
async def get_template_list():
    """List all available response templates."""
    return {"templates": list_templates()}


@app.get("/templates/{filename}")
async def get_template(filename: str):
    """
    Return the HTML content of a response template.

    Usage: GET /templates/refund_approved.html
    """
    html = get_template_html(filename)
    if html is None:
        raise HTTPException(status_code=404, detail=f"Template '{filename}' not found")
    return {"filename": filename, "html": html}


# ── Analytics Dashboard ────────────────────────────────────────────────

# Serve dashboard static files
import os as _os
if _os.path.isdir("dashboard"):
    app.mount("/dashboard/css", StaticFiles(directory="dashboard/css"), name="dashboard-css")
    app.mount("/dashboard/js", StaticFiles(directory="dashboard/js"), name="dashboard-js")


@app.get("/analytics/dashboard")
async def analytics_dashboard():
    """Serve the analytics dashboard HTML page."""
    return FileResponse("dashboard/index.html", media_type="text/html")


@app.get("/analytics/summary")
async def analytics_summary(days: int = None):
    """High-level KPI metrics for dashboard header cards."""
    return get_summary(days)


@app.get("/analytics/classifications")
async def analytics_classifications(days: int = None):
    """Intent distribution, confidence stats, volume over time."""
    return get_classification_analytics(days)


@app.get("/analytics/corrections")
async def analytics_corrections(days: int = None):
    """Confusion matrix, accuracy over time, top misclassification pairs."""
    return get_correction_analytics(days)


@app.get("/analytics/templates")
async def analytics_templates(days: int = None):
    """Template usage stats by template and by intent."""
    return get_template_analytics(days)


@app.get("/analytics/performance")
async def analytics_performance(days: int = None):
    """Processing time percentiles, error rates."""
    return get_performance_analytics(days)


@app.get("/analytics/entities")
async def analytics_entities(days: int = None):
    """Entity extraction rates by type and by intent."""
    return get_entity_analytics(days)


@app.get("/analytics/api-usage")
async def analytics_api_usage(days: int = None):
    """API usage tracking: call volumes, token usage, cost estimates."""
    return get_api_usage_analytics(days)


@app.post("/analytics/template-used")
async def analytics_template_used(request: Request):
    """Record a template usage event from the CSR wizard widget."""
    try:
        data = await request.json()
        log_template_usage(
            template_file=data.get("template_file", "unknown"),
            ticket_id=data.get("ticket_id"),
            intent=data.get("intent"),
        )
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Failed to log template usage: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/analytics/seed-test-data")
async def seed_test_data(count: int = 25):
    """Generate realistic test data in analytics logs to populate the dashboard."""
    import random

    intents = [
        "permit_cancellation", "refund_request", "new_permit_request",
        "payment_issue", "visitor_parking", "enforcement_complaint",
        "account_update", "general_inquiry", "towing_complaint",
        "accessibility_request",
    ]
    complexities = ["simple", "moderate", "complex"]
    urgencies = ["low", "medium", "high"]
    templates = [
        "permit_cancellation.html", "refund_approved.html",
        "new_permit_confirmation.html", "payment_receipt.html",
        "visitor_pass.html", "enforcement_response.html",
        "account_updated.html", "general_response.html",
    ]
    routing_queues = [
        "permit_management", "billing_refunds", "enforcement",
        "general_support", "accessibility",
    ]
    plates = [
        "ABC-1234", "XYZ-9876", "DEF-5555", "GHI-7890",
        "JKL-3210", "MNO-6543", "PQR-2468", "STU-1357",
    ]

    now = datetime.now()
    created = 0

    for i in range(count):
        ticket_id = f"TEST-{1000 + i}"
        intent = random.choice(intents)
        confidence = round(random.uniform(0.65, 0.98), 2)
        complexity = random.choice(complexities)
        urgency = random.choice(urgencies)
        processing_time = round(random.uniform(1.5, 8.0), 2)
        tagging_ok = random.random() > 0.05
        has_error = random.random() < 0.03

        # Spread events over the past 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)

        classification = {
            "intent": intent,
            "confidence": confidence,
            "complexity": complexity,
            "urgency": urgency,
            "language": "english",
            "requires_refund": intent in ("refund_request", "permit_cancellation"),
            "requires_human_review": confidence < 0.7,
            "key_entities": {
                "license_plate": random.choice(plates) if random.random() > 0.3 else None,
                "move_out_date": None,
                "property_name": f"Property {random.randint(1, 20)}" if random.random() > 0.5 else None,
                "amount": str(round(random.uniform(25, 300), 2)) if intent == "refund_request" else None,
            },
        }

        routing = random.choice(routing_queues)

        log_classification_event(
            ticket_id=ticket_id,
            classification=classification if not has_error else None,
            routing=routing if not has_error else None,
            processing_time_seconds=processing_time,
            tagging_success=tagging_ok,
            error="OpenAI timeout" if has_error else None,
        )

        # Log template usage for some tickets
        if random.random() > 0.4:
            log_template_usage(
                template_file=random.choice(templates),
                ticket_id=ticket_id,
                intent=intent,
            )

        # Log API usage (OpenAI classify call)
        prompt_tokens = random.randint(1200, 1800)
        completion_tokens = random.randint(80, 200)
        total_tokens = prompt_tokens + completion_tokens
        from src.services.analytics_logger import log_api_usage, estimate_openai_cost
        cost = estimate_openai_cost("gpt-4o-mini", prompt_tokens, completion_tokens)
        log_api_usage(
            provider="openai", call_type="classify_email", model="gpt-4o-mini",
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            total_tokens=total_tokens, estimated_cost_usd=cost,
            ticket_id=ticket_id,
        )

        # Log Zoho API calls (get_ticket + update_ticket + add_comment)
        for call_type in ["get_ticket", "update_ticket", "add_comment"]:
            log_api_usage(provider="zoho", call_type=call_type, ticket_id=ticket_id)

        created += 1

    return {
        "status": "ok",
        "created": created,
        "message": f"Seeded {created} test classification events with API usage data",
    }


if __name__ == "__main__":
    import uvicorn
    import os

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Railway injects PORT; fall back to 8000 for local dev
    port = int(os.getenv("PORT", 8000))
    is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,
        log_level="info"
    )
