"""
ParkM Email Classification System - FastAPI Application
Main entry point for webhook receiver and API endpoints
"""
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import asyncio
import logging
import os
from datetime import datetime
import hashlib
import hmac
from typing import Dict, Any

from src.api.webhooks import process_ticket_webhook, process_correction_webhook
from src.services.classifier import EmailClassifier
from src.api.zoho_client import ZohoDeskClient
from src.services.correction_logger import get_corrections_summary
from src.services.wizard import get_wizard_for_intent, get_template_html, list_templates, list_intents
from src.services.parkm_client import ParkMClient
from src.services.refund_service import RefundService
from src.services.analytics_logger import log_template_usage, log_classification_event
from src.services.analytics_aggregator import (
    get_summary, get_classification_analytics, get_correction_analytics,
    get_template_analytics, get_performance_analytics, get_entity_analytics,
    get_api_usage_analytics, get_error_logs
)
from src.services.analytics_logger import log_error

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

# Session middleware — powers the analytics dashboard login
# https_only=False works on Railway because TLS is terminated at the edge proxy;
# the signed cookie (itsdangerous) is still tamper-proof.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "change-me-before-deploying"),
    session_cookie="parkm_session",
    max_age=86400,       # 24-hour sessions
    same_site="lax",
    https_only=False,    # Railway terminates TLS at edge; app sees plain HTTP internally
)

# ── Dashboard auth ────────────────────────────────────────────────────────

_DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
_DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")


async def require_auth(request: Request):
    """FastAPI dependency — raises 401/307 if the dashboard session is missing."""
    if not request.session.get("authenticated"):
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            raise HTTPException(
                status_code=307,
                headers={"Location": "/analytics/login"},
                detail="Login required"
            )
        raise HTTPException(status_code=401, detail="Not authenticated")

# Initialize services
classifier = EmailClassifier()
zoho_client = ZohoDeskClient()
parkm_client = ParkMClient()
refund_service = RefundService()

# Concurrency limiter — prevents webhook flood from overwhelming OpenAI/Zoho APIs
_webhook_semaphore = asyncio.Semaphore(3)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting ParkM Email Classification API")
    # Initialize database (creates tables if DATABASE_URL is set)
    from src.db.database import init_db
    db_ready = init_db()
    if db_ready:
        logger.info("Persistent database storage active")
    else:
        logger.info("No DATABASE_URL — analytics stored in JSONL files (ephemeral)")
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
        
        # Process webhook in background with concurrency limit
        async def _throttled_process(tid, pl):
            async with _webhook_semaphore:
                await process_ticket_webhook(ticket_id=tid, payload=pl)

        background_tasks.add_task(_throttled_process, ticket_id, payload)
        
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

    async def _throttled_correction(tid, pl):
        async with _webhook_semaphore:
            await process_correction_webhook(ticket_id=tid, payload=pl)

    background_tasks.add_task(_throttled_correction, ticket_id, ticket_payload)

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
        dept_id_for_llm = ticket_data.get("departmentId", "")

        logger.info(f"Ticket: {subject}")

        # Classify
        classification = classifier.classify_email(subject, description, sender_email, ticket_id=ticket_id, department_id=dept_id_for_llm)
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
        department_id = ticket_data.get("departmentId", "")
        log_classification_event(
            ticket_id=ticket_id,
            classification=classification,
            routing=routing,
            processing_time_seconds=processing_time,
            tagging_success=bool(tag_result),
            department_id=department_id,
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
async def list_tickets(limit: int = 25):
    """List recent tickets from Zoho Desk."""
    try:
        tickets = await zoho_client.list_tickets(limit=limit)
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


@app.post("/batch-classify")
async def batch_classify(limit: int = 25):
    """
    Classify multiple real Zoho tickets at once.
    Lists recent tickets, classifies each, tags them, and logs analytics.
    """
    from src.services.tagger import TicketTagger
    tagger = TicketTagger()
    results = []
    errors = []

    try:
        tickets = await zoho_client.list_tickets(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tickets: {e}")

    for t in tickets:
        ticket_id = t.get("id")
        if not ticket_id:
            continue
        try:
            start_time = datetime.now()
            ticket_data = await zoho_client.get_ticket(ticket_id)
            if not ticket_data:
                continue

            subject = ticket_data.get("subject", "")
            description = ticket_data.get("description", "")
            sender_email = ticket_data.get("email", "")

            classification = classifier.classify_email(
                subject, description, sender_email, ticket_id=ticket_id,
                department_id=ticket_data.get("departmentId", ""),
            )
            routing = classifier.get_routing_recommendation(classification)

            tag_result = await tagger.apply_classification_tags(
                ticket_id=ticket_id,
                classification=classification,
                routing=routing,
            )

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            dept_id = ticket_data.get("departmentId", "")
            log_classification_event(
                ticket_id=ticket_id,
                classification=classification,
                routing=routing,
                processing_time_seconds=processing_time,
                tagging_success=bool(tag_result),
                department_id=dept_id,
            )

            results.append({
                "ticket_id": ticket_id,
                "subject": subject,
                "intent": classification.get("intent"),
                "confidence": classification.get("confidence"),
                "tagged": bool(tag_result),
            })
        except Exception as e:
            logger.error(f"Batch classify error for {ticket_id}: {e}")
            errors.append({"ticket_id": ticket_id, "error": str(e)})

    return {
        "classified": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/batch-reclassify")
async def batch_reclassify(
    limit: int = 100,
    delay: float = 2.0,
    background_tasks: BackgroundTasks = None,
):
    """
    Rate-limited reclassification of all tickets.
    Fetches tickets in pages, classifies each with a delay between calls
    to avoid OpenAI 429 rate limits and Zoho connection timeouts.

    Query params:
        limit: Max tickets to process (default 100, max 500)
        delay: Seconds between each classification call (default 2.0)
    """
    from src.services.tagger import TicketTagger

    limit = min(limit, 500)
    tagger = TicketTagger()
    results = []
    errors = []

    # Paginate through all tickets (Zoho max 50 per page)
    all_tickets = []
    page_size = 50
    offset = 0
    while len(all_tickets) < limit:
        try:
            batch = await zoho_client.list_tickets(
                limit=min(page_size, limit - len(all_tickets)),
                _from=offset,
            )
            if not batch:
                break
            all_tickets.extend(batch)
            offset += len(batch)
            if len(batch) < page_size:
                break
        except Exception as e:
            logger.error(f"Failed to fetch tickets at offset {offset}: {e}")
            break

    logger.info(f"Batch reclassify: {len(all_tickets)} tickets to process (delay={delay}s)")

    for i, t in enumerate(all_tickets):
        ticket_id = t.get("id")
        if not ticket_id:
            continue

        try:
            start_time = datetime.now()
            ticket_data = await zoho_client.get_ticket(ticket_id)
            if not ticket_data:
                continue

            subject = ticket_data.get("subject", "")
            description = ticket_data.get("description", "")
            sender_email = ticket_data.get("email", "")

            classification = classifier.classify_email(
                subject, description, sender_email, ticket_id=ticket_id,
                department_id=ticket_data.get("departmentId", ""),
            )
            routing = classifier.get_routing_recommendation(classification)

            tag_result = await tagger.apply_classification_tags(
                ticket_id=ticket_id,
                classification=classification,
                routing=routing,
            )

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            dept_id = ticket_data.get("departmentId", "")
            log_classification_event(
                ticket_id=ticket_id,
                classification=classification,
                routing=routing,
                processing_time_seconds=processing_time,
                tagging_success=bool(tag_result),
                department_id=dept_id,
            )

            results.append({
                "ticket_id": ticket_id,
                "subject": subject,
                "intent": classification.get("intent"),
                "confidence": classification.get("confidence"),
                "tagged": bool(tag_result),
            })
            logger.info(
                f"[{i+1}/{len(all_tickets)}] {ticket_id} → "
                f"{classification.get('intent')} ({classification.get('confidence')})"
            )

        except Exception as e:
            logger.error(f"Batch reclassify error for {ticket_id}: {e}")
            errors.append({"ticket_id": ticket_id, "error": str(e)})

        # Rate-limit delay between tickets (skip after the last one)
        if i < len(all_tickets) - 1:
            await asyncio.sleep(delay)

    return {
        "classified": len(results),
        "errors": len(errors),
        "total_tickets": len(all_tickets),
        "delay_seconds": delay,
        "results": results,
        "error_details": errors,
        "timestamp": datetime.now().isoformat(),
    }


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
        ticket_data = None
        if ticket_id:
            ticket_data = await zoho_client.get_ticket(ticket_id)
            if ticket_data:
                # Read entities from custom fields instead of re-classifying
                cf = ticket_data.get("cf", ticket_data.get("customFields", {})) or {}
                classification = {
                    "confidence": cf.get("cf_ai_confidence"),
                    "requires_human_review": cf.get("cf_requires_human_review") == "true",
                    "key_entities": {
                        "license_plate": cf.get("cf_license_plate"),
                        "move_out_date": cf.get("cf_move_out_date"),
                    }
                }

        # Extract contact email from ticket for widget pre-population
        contact_email = ""
        if ticket_data:
            contact_email = ticket_data.get("email", "") or ""

        wizard = get_wizard_for_intent(intent, classification)
        return {
            "intent": intent,
            "wizard": wizard,
            "contact_email": contact_email,
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


# ── ParkM API / Refund Automation ──────────────────────────────────────

import re as _re
_PARKM_API_KEY = os.getenv("PARKM_API_KEY", "")

async def require_parkm_auth(request: Request):
    """Verify API key for destructive ParkM endpoints."""
    if not _PARKM_API_KEY:
        return  # No key configured — skip auth (dev/sandbox mode)
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if key != _PARKM_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

def _validate_email(email: str) -> str:
    """Basic email format validation. Returns cleaned email or raises 400."""
    email = (email or "").strip()
    if not email or not _re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        raise HTTPException(status_code=400, detail="Valid email address is required")
    return email

@app.get("/parkm/health")
async def parkm_health():
    """Check ParkM API connectivity."""
    try:
        info = await parkm_client.health_check()
        return {"status": "connected", **info}
    except Exception as e:
        logger.error(f"ParkM health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "disconnected", "error": str(e)})


@app.get("/parkm/debug/apis")
async def parkm_debug_apis(email: str):
    """Temporary debug endpoint to test ParkM API responses."""
    try:
        customer = await parkm_client.get_customer_by_email(email)
        if not customer:
            return {"error": "customer not found"}
        cid = customer["id"]
        balance = await parkm_client.get_customer_balance(cid)
        txns = await parkm_client.get_customer_transactions(cid)
        subs = await parkm_client.get_customer_subscriptions(cid)
        try:
            all_permits = await parkm_client.get_all_permits(cid)
        except Exception as ap_err:
            all_permits = {"error": str(ap_err)}
        return {
            "customer_id": cid,
            "balance_permits": balance,
            "transactions_count": len(txns),
            "transactions_sample": txns[:5],
            "subscriptions": subs,
            "all_permits": all_permits,
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/parkm/customer")
async def parkm_customer_lookup(email: str, _auth=Depends(require_parkm_auth)):
    """Look up a customer in ParkM by email.

    Returns customer info, active permits, vehicles, and transactions.
    Usage: GET /parkm/customer?email=john@example.com
    """
    try:
        email = _validate_email(email)
        result = await refund_service.lookup_customer(email)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer lookup failed for {email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/parkm/customer/search")
async def parkm_customer_search(q: str, _auth=Depends(require_parkm_auth)):
    """Search for customers in ParkM by name or email.

    Returns a list of matching customers with basic info.
    Usage: GET /parkm/customer/search?q=John+Smith
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

    try:
        from src.services.parkm_client import ParkMClient
        parkm = ParkMClient()
        customers = await parkm.search_customers(q.strip(), max_results=10)
        results = []
        for c in customers:
            results.append({
                "id": c.get("id"),
                "name": f'{c.get("firstName", "")} {c.get("lastName", "")}'.strip(),
                "email": c.get("primaryEmailAddress", ""),
                "phone": c.get("mobilePhone") or c.get("homePhone") or "",
                "unit_number": c.get("unitNumber", ""),
                "account_id": c.get("accountId", ""),
            })
        return {"query": q, "count": len(results), "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer search failed for '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/parkm/search/plate")
async def parkm_search_plate(q: str, _auth=Depends(require_parkm_auth)):
    """Search vehicles by license plate.

    Returns list of vehicles with plate, customer name, community, vehicle desc.
    customerId is null in the response — call /parkm/customer/search?q={name}
    after CSR picks a result to look up the actual customer record.
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Plate query must be at least 2 characters")
    try:
        from src.services.parkm_client import ParkMClient
        parkm = ParkMClient()
        items = await parkm.search_vehicles_by_plate(q.strip(), max_results=15)
        results = []
        seen_keys = set()
        for item in items:
            v = item.get("vehicle", {}) or {}
            plate = v.get("licensePlate") or ""
            customer_name = item.get("customerName") or ""
            community = item.get("community") or ""
            # Dedupe by (plate, customer_name) since search returns close matches
            key = (plate.lower(), customer_name.lower())
            if key in seen_keys:
                continue
            seen_keys.add(key)
            results.append({
                "plate": plate,
                "plate_state": item.get("plateState") or "",
                "vehicle_description": (item.get("description") or "").strip(),
                "customer_name": customer_name,
                "community": community,
                "community_id": item.get("communityId"),
            })
        return {"query": q, "count": len(results), "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plate search failed for '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/parkm/search/unit")
async def parkm_search_unit(q: str, _auth=Depends(require_parkm_auth)):
    """Search units by unit number.

    Returns list of units, each with embedded customer records.
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Unit query must be at least 2 characters")
    try:
        from src.services.parkm_client import ParkMClient
        parkm = ParkMClient()
        items = await parkm.search_units(q.strip(), max_results=15)
        results = []
        for item in items:
            unit = item.get("unit", {}) or {}
            customer_entries = item.get("customers", []) or []
            customers = []
            for ce in customer_entries:
                c = ce.get("customer", ce) or {}
                email = c.get("primaryEmailAddress") or ""
                # Filter placeholder fake.com emails
                if "@fake.com" in email.lower():
                    email = ""
                customers.append({
                    "id": c.get("id"),
                    "name": f'{c.get("firstName", "")} {c.get("lastName", "")}'.strip(),
                    "email": email,
                    "phone": c.get("mobilePhone") or c.get("homePhone") or "",
                    "account_id": c.get("accountId"),
                })
            results.append({
                "unit_id": unit.get("id"),
                "unit_number": unit.get("unitNumber"),
                "address": unit.get("primaryAddress") or "",
                "city": unit.get("city") or "",
                "state": unit.get("state") or "",
                "customers": customers,
            })
        return {"query": q, "count": len(results), "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unit search failed for '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/parkm/customer/by-id/{customer_id}")
async def parkm_customer_by_id(customer_id: str, _auth=Depends(require_parkm_auth)):
    """Fetch full customer + permits by ParkM customer ID.

    Used after CSR picks a result from plate/unit/name search to load
    customer details and permits into the refund panel.
    """
    try:
        result = await refund_service.lookup_customer_by_id(customer_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer lookup by id failed for {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parkm/refund/evaluate")
async def parkm_evaluate_refund(request: Request, _auth=Depends(require_parkm_auth)):
    """Evaluate refund eligibility for a customer.

    Request body:
    {
        "customer_email": "john@example.com",
        "permit_id": "optional-uuid",
        "reason": "Customer moved out",
        "ticket_id": "12345"
    }

    Returns customer info, permit details, eligibility assessment,
    and a pre-built accounting email if eligible.
    Does NOT cancel the permit or process the refund — CSR must confirm.
    """
    try:
        data = await request.json()
        email = _validate_email(data.get("customer_email", ""))
        result = await refund_service.process_refund_request(
            customer_email=email,
            permit_id=data.get("permit_id"),
            reason=data.get("reason", "Customer requested cancellation/refund"),
            ticket_id=data.get("ticket_id", ""),
            auto_cancel=False,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refund evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parkm/refund/process")
async def parkm_process_refund(request: Request, _auth=Depends(require_parkm_auth)):
    """Cancel permit and prepare accounting email.

    Request body:
    {
        "customer_email": "john@example.com",
        "permit_id": "uuid-of-permit-to-cancel",
        "reason": "Customer moved out",
        "ticket_id": "12345",
        "cancel_date": null  // optional ISO-8601 datetime for delayed cancellation
    }

    This WILL cancel the permit in ParkM. CSR should confirm before calling.
    If cancel_date is provided, schedules a delayed cancellation instead of
    cancelling immediately.
    """
    try:
        data = await request.json()
        permit_id = data.get("permit_id")
        if not permit_id:
            raise HTTPException(status_code=400, detail="permit_id is required")
        email = _validate_email(data.get("customer_email", ""))

        result = await refund_service.process_refund_request(
            customer_email=email,
            permit_id=permit_id,
            reason=data.get("reason", "Customer requested cancellation/refund"),
            ticket_id=data.get("ticket_id", ""),
            auto_cancel=True,
            cancel_date=data.get("cancel_date"),
        )

        # Ticket status is NOT auto-changed — CSR decides manually (per Apr 16 feedback).
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refund processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/parkm/permit/cancel")
async def parkm_cancel_permit(request: Request, _auth=Depends(require_parkm_auth)):
    """Cancel a specific permit in ParkM (immediate or delayed).

    Request body:
    {
        "permit_id": "uuid",
        "send_notice": true,
        "cancel_date": null  // optional ISO-8601 datetime for delayed cancellation
    }
    """
    try:
        data = await request.json()
        permit_id = data.get("permit_id")
        if not permit_id:
            raise HTTPException(status_code=400, detail="permit_id is required")

        result = await refund_service.cancel_permit(
            permit_id=permit_id,
            send_notice=data.get("send_notice", True),
            cancel_date=data.get("cancel_date"),
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Permit cancellation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Widget Access Control ──────────────────────────────────────────────

# Comma-separated list of agent emails allowed to use the widget.
# Empty string = all agents allowed (no restriction).
WIDGET_ALLOWED_AGENTS = os.getenv("WIDGET_ALLOWED_AGENTS", "")


@app.get("/widget/access")
async def widget_access_check(email: str = ""):
    """Check if an agent is allowed to use the CSR Wizard widget.

    Query params:
        email: The agent's Zoho Desk email address

    Returns:
        {"allowed": bool}
    """
    if not WIDGET_ALLOWED_AGENTS:
        return {"allowed": True}

    allowed_list = [e.strip().lower() for e in WIDGET_ALLOWED_AGENTS.split(",") if e.strip()]
    return {"allowed": email.strip().lower() in allowed_list}


# ── Analytics Dashboard ────────────────────────────────────────────────

# Department filter for analytics — defaults to Testing department
import os as _os
ANALYTICS_DEPARTMENT_ID = _os.getenv("ANALYTICS_DEPARTMENT_ID", "1004699000001888029")

# Serve dashboard static files
if _os.path.isdir("dashboard"):
    app.mount("/dashboard/css", StaticFiles(directory="dashboard/css"), name="dashboard-css")
    app.mount("/dashboard/js", StaticFiles(directory="dashboard/js"), name="dashboard-js")
    app.mount("/dashboard/img", StaticFiles(directory="dashboard/img"), name="dashboard-img")


# ── Auth routes (public — no require_auth dependency) ────────────────────

@app.get("/analytics/login")
async def analytics_login_page():
    """Serve the login form."""
    return FileResponse("dashboard/login.html", media_type="text/html")


@app.post("/analytics/login")
async def analytics_login_post(request: Request):
    """Process login form submission."""
    form = await request.form()
    username = (form.get("username") or "").strip()
    password = (form.get("password") or "").strip()

    if not _DASHBOARD_PASSWORD:
        # No password configured — block access with a clear message
        return FileResponse("dashboard/login.html", status_code=503)

    if username == _DASHBOARD_USERNAME and password == _DASHBOARD_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse(url="/analytics/dashboard", status_code=303)
    return RedirectResponse(url="/analytics/login?error=1", status_code=303)


@app.get("/analytics/logout")
async def analytics_logout(request: Request):
    """Clear session and redirect to login."""
    request.session.clear()
    return RedirectResponse(url="/analytics/login", status_code=303)


# ── Protected analytics routes ────────────────────────────────────────────

@app.get("/analytics/dashboard")
async def analytics_dashboard(_: None = Depends(require_auth)):
    """Serve the analytics dashboard HTML page."""
    return FileResponse("dashboard/index.html", media_type="text/html")


@app.get("/analytics/ai-usage")
async def analytics_ai_usage_page(_: None = Depends(require_auth)):
    """Serve the dedicated AI Usage page."""
    return FileResponse("dashboard/ai-usage.html", media_type="text/html")


@app.get("/analytics/summary")
async def analytics_summary(days: int = None, _: None = Depends(require_auth)):
    """High-level KPI metrics for dashboard header cards."""
    return get_summary(days, department_id=ANALYTICS_DEPARTMENT_ID)


@app.get("/analytics/classifications")
async def analytics_classifications(days: int = None, _: None = Depends(require_auth)):
    """Intent distribution, confidence stats, volume over time."""
    return get_classification_analytics(days, department_id=ANALYTICS_DEPARTMENT_ID)


@app.get("/analytics/corrections")
async def analytics_corrections(days: int = None, _: None = Depends(require_auth)):
    """Confusion matrix, accuracy over time, top misclassification pairs."""
    return get_correction_analytics(days, department_id=ANALYTICS_DEPARTMENT_ID)


@app.get("/analytics/templates")
async def analytics_templates(days: int = None, _: None = Depends(require_auth)):
    """Template usage stats by template and by intent."""
    return get_template_analytics(days)


@app.get("/analytics/performance")
async def analytics_performance(days: int = None, _: None = Depends(require_auth)):
    """Processing time percentiles, error rates."""
    return get_performance_analytics(days, department_id=ANALYTICS_DEPARTMENT_ID)


@app.get("/analytics/entities")
async def analytics_entities(days: int = None, _: None = Depends(require_auth)):
    """Entity extraction rates by type and by intent."""
    return get_entity_analytics(days, department_id=ANALYTICS_DEPARTMENT_ID)


@app.get("/analytics/api-usage")
async def analytics_api_usage(days: int = None, _: None = Depends(require_auth)):
    """API usage tracking: call volumes, token usage, cost estimates."""
    return get_api_usage_analytics(days)


@app.get("/analytics/errors")
async def analytics_errors(days: int = 7, level: str = None, limit: int = 200, _: None = Depends(require_auth)):
    """Recent application error logs from DB or JSONL."""
    return get_error_logs(days=days, level=level, limit=limit)


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
    import json as _json
    import random
    from datetime import timedelta

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

    _os.makedirs("logs", exist_ok=True)
    now = datetime.utcnow()
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
        ts = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        timestamp = ts.isoformat() + "Z"

        routing = random.choice(routing_queues)
        entities = {
            "license_plate": random.choice(plates) if random.random() > 0.3 else None,
            "move_out_date": None,
            "property_name": f"Property {random.randint(1, 20)}" if random.random() > 0.5 else None,
            "amount": str(round(random.uniform(25, 300), 2)) if intent == "refund_request" else None,
        }

        # Write classification entry with custom timestamp
        cls_entry = {
            "timestamp": timestamp,
            "ticket_id": ticket_id,
            "department_id": ANALYTICS_DEPARTMENT_ID,
            "intent": intent if not has_error else None,
            "confidence": confidence if not has_error else None,
            "complexity": complexity if not has_error else None,
            "urgency": urgency if not has_error else None,
            "language": "english",
            "requires_refund": intent in ("refund_request", "permit_cancellation"),
            "requires_human_review": confidence < 0.7,
            "routing_queue": routing if not has_error else None,
            "entities": entities if not has_error else {},
            "processing_time_seconds": processing_time,
            "tagging_success": tagging_ok,
            "error": "OpenAI timeout" if has_error else None,
        }
        with open("logs/classifications.jsonl", "a") as f:
            f.write(_json.dumps(cls_entry) + "\n")

        # Template usage for some tickets
        if random.random() > 0.4:
            tpl_entry = {
                "timestamp": timestamp,
                "template_file": random.choice(templates),
                "ticket_id": ticket_id,
                "intent": intent,
            }
            with open("logs/template_usage.jsonl", "a") as f:
                f.write(_json.dumps(tpl_entry) + "\n")

        # API usage: OpenAI classify call
        prompt_tokens = random.randint(1200, 1800)
        completion_tokens = random.randint(80, 200)
        total_tokens = prompt_tokens + completion_tokens
        from src.services.analytics_logger import estimate_openai_cost
        cost = estimate_openai_cost("gpt-4o-mini", prompt_tokens, completion_tokens)
        api_entry = {
            "timestamp": timestamp,
            "provider": "openai", "call_type": "classify_email",
            "model": "gpt-4o-mini",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(cost, 6),
            "ticket_id": ticket_id, "success": True, "error": None,
        }
        with open("logs/api_usage.jsonl", "a") as f:
            f.write(_json.dumps(api_entry) + "\n")

        # Zoho API calls
        for call_type in ["get_ticket", "update_ticket", "add_comment"]:
            zoho_entry = {
                "timestamp": timestamp,
                "provider": "zoho", "call_type": call_type,
                "model": None, "prompt_tokens": None,
                "completion_tokens": None, "total_tokens": None,
                "estimated_cost_usd": None,
                "ticket_id": ticket_id, "success": True, "error": None,
            }
            with open("logs/api_usage.jsonl", "a") as f:
                f.write(_json.dumps(zoho_entry) + "\n")

        # Corrections: ~30% of tickets get a CSR correction
        if not has_error and random.random() < 0.30:
            # Pick a different intent as the "correct" one
            other_intents = [x for x in intents if x != intent]
            corrected = random.choice(other_intents)
            corr_entry = {
                "timestamp": timestamp,
                "ticket_id": ticket_id,
                "department_id": ANALYTICS_DEPARTMENT_ID,
                "original_intent": intent,
                "corrected_intent": corrected,
                "confidence": int(confidence * 100),
                "is_misclassification": True,
            }
            with open("logs/corrections.jsonl", "a") as f:
                f.write(_json.dumps(corr_entry) + "\n")

        created += 1

    return {
        "status": "ok",
        "created": created,
        "message": f"Seeded {created} test events with corrections spread across 30 days",
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
