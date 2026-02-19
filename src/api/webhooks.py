"""
Webhook processing module
Handles incoming Zoho Desk webhooks and triggers classification
"""
import logging
from datetime import datetime
from typing import Dict, Any

from src.services.classifier import EmailClassifier
from src.services.tagger import TicketTagger
from src.api.zoho_client import ZohoDeskClient
from src.services.correction_logger import log_correction
from src.services.analytics_logger import log_classification_event

logger = logging.getLogger(__name__)

# Initialize services
classifier = EmailClassifier()
tagger = TicketTagger()
zoho_client = ZohoDeskClient()


async def process_ticket_webhook(ticket_id: str, payload: Dict[str, Any]):
    """
    Process a ticket creation webhook from Zoho Desk
    
    Workflow:
    1. Fetch full ticket details from Zoho API
    2. Extract email content (subject + body)
    3. Classify email using AI
    4. Apply classification tags to ticket
    5. Log results
    
    Args:
        ticket_id: Zoho Desk ticket ID
        payload: Webhook payload from Zoho
    """
    try:
        start_time = datetime.now()
        logger.info(f"[{ticket_id}] Starting webhook processing")
        
        # Step 1: Fetch full ticket details from Zoho
        logger.info(f"[{ticket_id}] Fetching ticket details from Zoho API")
        ticket_data = await zoho_client.get_ticket(ticket_id)
        
        if not ticket_data:
            logger.error(f"[{ticket_id}] Failed to fetch ticket data")
            return
        
        # Step 2: Extract email content
        subject = ticket_data.get("subject", "")
        description = ticket_data.get("description", "")
        sender_email = ticket_data.get("email", "")
        department_id = ticket_data.get("departmentId", "")
        
        logger.info(f"[{ticket_id}] Ticket from: {sender_email}")
        logger.info(f"[{ticket_id}] Subject: {subject}")
        
        # Step 3: Classify email
        logger.info(f"[{ticket_id}] Classifying email with AI")
        classification = classifier.classify_email(subject, description, sender_email, ticket_id=ticket_id)
        
        logger.info(f"[{ticket_id}] Classification result:")
        logger.info(f"  - Intent: {classification.get('intent')}")
        logger.info(f"  - Complexity: {classification.get('complexity')}")
        logger.info(f"  - Language: {classification.get('language')}")
        logger.info(f"  - Urgency: {classification.get('urgency')}")
        logger.info(f"  - Confidence: {classification.get('confidence')}")
        
        # Get routing recommendation (returns a string)
        routing = classifier.get_routing_recommendation(classification)
        logger.info(f"[{ticket_id}] Routing recommendation: {routing}")
        
        # Step 4: Apply classification tags to ticket
        logger.info(f"[{ticket_id}] Applying tags to ticket in Zoho")
        tag_result = await tagger.apply_classification_tags(
            ticket_id=ticket_id,
            classification=classification,
            routing=routing
        )
        
        if tag_result:
            logger.info(f"[{ticket_id}] Tags applied successfully")
        else:
            logger.error(f"[{ticket_id}] Failed to apply tags")
        
        # Step 5: Log completion metrics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"[{ticket_id}] Processing complete in {processing_time:.2f} seconds")

        # Log structured classification event for analytics dashboard
        log_classification_event(
            ticket_id=ticket_id,
            classification=classification,
            routing=routing,
            processing_time_seconds=processing_time,
            tagging_success=bool(tag_result),
            department_id=department_id,
        )

    except Exception as e:
        logger.error(f"[{ticket_id}] Error processing webhook: {e}", exc_info=True)
        log_classification_event(
            ticket_id=ticket_id,
            classification=None,
            routing=None,
            processing_time_seconds=None,
            tagging_success=False,
            error=str(e),
        )


async def process_correction_webhook(ticket_id: str, payload: Dict[str, Any]):
    """
    Process a ticket-updated webhook when a CSR sets Agent Corrected Intent.

    Workflow:
    1. Extract the corrected intent from the webhook payload
    2. Fetch the ticket to get the original AI intent and confidence
    3. Log the correction for LLM training
    4. Skip logging if no correction was made (field blank or set to "correct")

    Args:
        ticket_id: Zoho Desk ticket ID
        payload: Webhook payload from Zoho (ticket updated event)
    """
    try:
        logger.info(f"[{ticket_id}] Processing correction webhook")

        # Pull corrected intent directly from payload if Zoho includes it
        corrected_intent = (
            payload.get("cf_agent_corrected_intent")
            or payload.get("cf", {}).get("cf_agent_corrected_intent")
        )

        if not corrected_intent:
            logger.info(f"[{ticket_id}] No corrected intent in payload — skipping")
            return

        # Fetch ticket to get original AI classification fields
        ticket_data = await zoho_client.get_ticket(ticket_id)
        if not ticket_data:
            logger.error(f"[{ticket_id}] Could not fetch ticket for correction logging")
            return

        cf = ticket_data.get("cf", {})
        original_intent = cf.get("cf_ai_intent", "unknown")
        confidence_raw = cf.get("cf_ai_confidence")
        confidence = int(confidence_raw) if confidence_raw is not None else None
        department_id = ticket_data.get("departmentId", "")

        log_correction(
            ticket_id=ticket_id,
            original_intent=original_intent,
            corrected_intent=corrected_intent,
            confidence=confidence,
            department_id=department_id
        )

    except Exception as e:
        logger.error(f"[{ticket_id}] Error processing correction webhook: {e}", exc_info=True)
