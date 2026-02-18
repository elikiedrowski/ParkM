"""
ParkM Email Classification System - FastAPI Application
Main entry point for webhook receiver and API endpoints
"""
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
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

        logger.info(f"Webhook payload keys: {list(payload.keys()) if isinstance(payload, dict) else type(payload)}")

        # Extract ticket ID — Zoho may use "ticketId", "id", or nested "ticket.id"
        ticket_id = (
            payload.get("ticketId")
            or payload.get("id")
            or payload.get("ticket", {}).get("id")
        )

        if not ticket_id:
            logger.error(f"Webhook payload missing ticketId. Full payload: {payload}")
            raise HTTPException(status_code=400, detail="Missing ticketId in payload")
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

    ticket_id = (
        payload.get("ticketId")
        or payload.get("id")
        or payload.get("ticket", {}).get("id")
    )
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Missing ticketId in payload")

    logger.info(f"Received ticket-updated webhook for ticket {ticket_id}")

    background_tasks.add_task(
        process_correction_webhook,
        ticket_id=ticket_id,
        payload=payload
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
        classification = classifier.classify_email(subject, description, sender_email)
        routing = classifier.get_routing_recommendation(classification)
        
        # Tag (import tagger here to avoid circular import)
        from src.services.tagger import TicketTagger
        tagger = TicketTagger()
        
        tag_result = await tagger.apply_classification_tags(
            ticket_id=ticket_id,
            classification=classification,
            routing=routing
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
                classification = classifier.classify_email(subject, description, sender)

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
