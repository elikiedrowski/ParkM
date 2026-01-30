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
        ticket_data = zoho_client.get_ticket(ticket_id)
        
        if not ticket_data:
            logger.error(f"[{ticket_id}] Failed to fetch ticket data")
            return
        
        # Step 2: Extract email content
        subject = ticket_data.get("subject", "")
        description = ticket_data.get("description", "")
        sender_email = ticket_data.get("email", "")
        
        logger.info(f"[{ticket_id}] Ticket from: {sender_email}")
        logger.info(f"[{ticket_id}] Subject: {subject}")
        
        # Step 3: Classify email
        logger.info(f"[{ticket_id}] Classifying email with AI")
        classification = classifier.classify_email(subject, description, sender_email)
        
        logger.info(f"[{ticket_id}] Classification result:")
        logger.info(f"  - Intent: {classification.get('intent')}")
        logger.info(f"  - Complexity: {classification.get('complexity')}")
        logger.info(f"  - Language: {classification.get('language')}")
        logger.info(f"  - Urgency: {classification.get('urgency')}")
        logger.info(f"  - Confidence: {classification.get('confidence')}")
        
        # Get routing recommendation
        routing = classifier.get_routing_recommendation(classification)
        logger.info(f"[{ticket_id}] Routing recommendation: {routing.get('queue')}")
        
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
        
        # TODO: Store metrics in database for dashboard (Week 3)
        
    except Exception as e:
        logger.error(f"[{ticket_id}] Error processing webhook: {e}", exc_info=True)
        # Don't raise - we don't want to return error to Zoho
        # Log the error and move on
