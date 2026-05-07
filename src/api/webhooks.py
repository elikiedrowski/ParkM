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
from src.services.parker_handler import prepare_parker_ticket

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
    3. Classify email using AI (returns multi-intent tags)
    4. Apply classification tags to ticket
    5. Log results
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

        # Step 1b: Skip if this ticket has already been classified successfully.
        # The same Ticket_Add can hit us twice — once from the API-subscription
        # webhook and once from the synchronous workflow-rule webhook. We treat
        # "Needs Tag" as not-yet-successfully-classified so retries still work.
        existing_tags = (ticket_data.get("cf") or {}).get("cf_ai_tags") or ""
        if existing_tags and existing_tags != "Needs Tag":
            logger.info(
                f"[{ticket_id}] Already classified ({existing_tags!r}); skipping duplicate webhook"
            )
            return

        # Step 2: Extract email content
        subject = ticket_data.get("subject", "")
        description = ticket_data.get("description", "")
        sender_email = ticket_data.get("email", "")
        department_id = ticket_data.get("departmentId", "")

        logger.info(f"[{ticket_id}] Ticket from: {sender_email}")
        logger.info(f"[{ticket_id}] Subject: {subject}")

        # Step 2b: If this came from Parker (Chat channel), the description is
        # empty — the real content is in the incoming chat thread. Parse it and
        # use the transcript as the body for classification.
        parker_ctx = await prepare_parker_ticket(zoho_client, ticket_data)
        if parker_ctx.is_parker and parker_ctx.transcript_text:
            description = (
                "[Chat transcript from Parker the Parking Bot — ParkM's website "
                "intake chatbot. Lines prefixed with [Parker, the Parking Bot] are "
                "bot messages; other lines are the resident's responses.]\n\n"
                + parker_ctx.transcript_text
            )

        # Step 3: Classify email
        logger.info(f"[{ticket_id}] Classifying email with AI")
        classification = classifier.classify_email(subject, description, sender_email, ticket_id=ticket_id, department_id=department_id)

        # Step 3b: For Parker tickets where the menu selection deterministically
        # implies a tag, override the LLM's tag output. The LLM is still useful
        # for entity extraction, complexity, urgency, and language — but the
        # tag itself is more reliable from the menu mapping.
        if parker_ctx.is_parker and parker_ctx.deterministic_tag:
            classification["tags"] = [parker_ctx.deterministic_tag]
            classification["intent"] = parker_ctx.deterministic_tag
            classification["confidence"] = max(classification.get("confidence", 0) or 0, 0.95)
            classification["requires_human_review"] = False
            logger.info(
                f"[{ticket_id}] Parker deterministic tag applied: {parker_ctx.deterministic_tag}"
            )

        logger.info(f"[{ticket_id}] Classification result:")
        logger.info(f"  - Tags: {classification.get('tags')}")
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
    Process a ticket-updated webhook when a CSR sets Agent Corrected Tags.

    Reads cf_agent_corrected_tags (semicolon-separated multi-select) and
    compares against cf_ai_tags to log corrections.
    """
    try:
        logger.info(f"[{ticket_id}] Processing correction webhook")

        # Pull corrected tags from payload
        corrected_tags = (
            payload.get("cf_agent_corrected_tags")
            or payload.get("cf", {}).get("cf_agent_corrected_tags")
        )

        if not corrected_tags:
            logger.info(f"[{ticket_id}] No corrected tags in payload — skipping")
            return

        # Fetch ticket to get original AI classification fields
        ticket_data = await zoho_client.get_ticket(ticket_id)
        if not ticket_data:
            logger.error(f"[{ticket_id}] Could not fetch ticket for correction logging")
            return

        cf = ticket_data.get("cf", {})
        original_tags = cf.get("cf_ai_tags", "Needs Tag")
        confidence_raw = cf.get("cf_ai_confidence")
        confidence = int(confidence_raw) if confidence_raw is not None else None
        department_id = ticket_data.get("departmentId", "")
        subject = ticket_data.get("subject") or ""
        description = ticket_data.get("description") or ""

        log_correction(
            ticket_id=ticket_id,
            original_intent=original_tags,
            corrected_intent=corrected_tags,
            confidence=confidence,
            department_id=department_id,
            subject=subject,
            description_snippet=description[:500] if description else None,
        )

    except Exception as e:
        logger.error(f"[{ticket_id}] Error processing correction webhook: {e}", exc_info=True)
