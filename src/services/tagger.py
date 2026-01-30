"""
Ticket Tagging Service
Applies AI classification results to Zoho Desk tickets via custom fields
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.api.zoho_client import ZohoDeskClient

logger = logging.getLogger(__name__)


class TicketTagger:
    """Service for applying classification tags to Zoho Desk tickets"""
    
    def __init__(self):
        self.zoho_client = ZohoDeskClient()
        
        # Custom field mappings (API names)
        # These will be created in Zoho Desk during setup
        self.custom_fields = {
            "intent": "cf_ai_intent",
            "complexity": "cf_ai_complexity",
            "language": "cf_ai_language",
            "urgency": "cf_ai_urgency",
            "confidence": "cf_ai_confidence",
            "requires_refund": "cf_requires_refund",
            "requires_human_review": "cf_requires_human_review",
            "license_plate": "cf_license_plate",
            "move_out_date": "cf_move_out_date",
            "routing_queue": "cf_routing_queue",
        }
    
    async def apply_classification_tags(
        self,
        ticket_id: str,
        classification: Dict[str, Any],
        routing: Dict[str, Any]
    ) -> bool:
        """
        Apply classification results to a ticket via custom fields
        
        Args:
            ticket_id: Zoho Desk ticket ID
            classification: Classification result from EmailClassifier
            routing: Routing recommendation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"[{ticket_id}] Building custom field updates")
            
            # Build custom field update payload
            custom_field_data = {}
            
            # Map classification data to custom fields
            if "intent" in classification:
                custom_field_data[self.custom_fields["intent"]] = classification["intent"]
            
            if "complexity" in classification:
                custom_field_data[self.custom_fields["complexity"]] = classification["complexity"]
            
            if "language" in classification:
                custom_field_data[self.custom_fields["language"]] = classification["language"]
            
            if "urgency" in classification:
                custom_field_data[self.custom_fields["urgency"]] = classification["urgency"]
            
            if "confidence" in classification:
                # Convert to percentage for display
                confidence_pct = int(classification["confidence"] * 100)
                custom_field_data[self.custom_fields["confidence"]] = confidence_pct
            
            if "requires_refund" in classification:
                custom_field_data[self.custom_fields["requires_refund"]] = classification["requires_refund"]
            
            if "requires_human_review" in classification:
                custom_field_data[self.custom_fields["requires_human_review"]] = classification["requires_human_review"]
            
            # Extract entities
            key_entities = classification.get("key_entities", {})
            
            if "license_plate" in key_entities and key_entities["license_plate"]:
                custom_field_data[self.custom_fields["license_plate"]] = key_entities["license_plate"]
            
            if "move_out_date" in key_entities and key_entities["move_out_date"]:
                custom_field_data[self.custom_fields["move_out_date"]] = key_entities["move_out_date"]
            
            # Add routing recommendation
            if "queue" in routing:
                custom_field_data[self.custom_fields["routing_queue"]] = routing["queue"]
            
            logger.info(f"[{ticket_id}] Custom fields to update: {len(custom_field_data)}")
            
            # Update ticket via Zoho API
            # Note: This will fail if custom fields don't exist in Zoho yet
            # We'll create them in the setup phase
            result = self.zoho_client.update_ticket(ticket_id, {
                "customFields": custom_field_data
            })
            
            if result:
                logger.info(f"[{ticket_id}] Custom fields updated successfully")
                
                # Also add an internal comment with classification details
                comment = self._build_classification_comment(classification, routing)
                self.zoho_client.add_comment(
                    ticket_id,
                    comment,
                    is_public=False  # Internal note only
                )
                
                return True
            else:
                logger.error(f"[{ticket_id}] Failed to update custom fields")
                return False
                
        except Exception as e:
            logger.error(f"[{ticket_id}] Error applying tags: {e}", exc_info=True)
            return False
    
    def _build_classification_comment(
        self,
        classification: Dict[str, Any],
        routing: Dict[str, Any]
    ) -> str:
        """
        Build an internal comment with classification details
        
        Args:
            classification: Classification result
            routing: Routing recommendation
            
        Returns:
            str: Formatted comment text
        """
        comment_lines = [
            "🤖 AI Classification Results",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Intent: {classification.get('intent', 'unknown')}",
            f"Complexity: {classification.get('complexity', 'unknown')}",
            f"Language: {classification.get('language', 'unknown')}",
            f"Urgency: {classification.get('urgency', 'unknown')}",
            f"Confidence: {int(classification.get('confidence', 0) * 100)}%",
            "",
            f"Requires Refund: {'Yes' if classification.get('requires_refund') else 'No'}",
            f"Requires Human Review: {'Yes' if classification.get('requires_human_review') else 'No'}",
            "",
            f"Recommended Queue: {routing.get('queue', 'unknown')}",
            f"Routing Reason: {routing.get('reason', 'N/A')}",
        ]
        
        # Add extracted entities
        key_entities = classification.get("key_entities", {})
        if key_entities:
            comment_lines.append("")
            comment_lines.append("Extracted Information:")
            if key_entities.get("license_plate"):
                comment_lines.append(f"  • License Plate: {key_entities['license_plate']}")
            if key_entities.get("move_out_date"):
                comment_lines.append(f"  • Move-Out Date: {key_entities['move_out_date']}")
            if key_entities.get("property_name"):
                comment_lines.append(f"  • Property: {key_entities['property_name']}")
            if key_entities.get("amount"):
                comment_lines.append(f"  • Amount: ${key_entities['amount']}")
        
        # Add notes
        if classification.get("notes"):
            comment_lines.append("")
            comment_lines.append(f"Notes: {classification['notes']}")
        
        return "\n".join(comment_lines)
    
    def create_custom_fields_in_zoho(self) -> Dict[str, Any]:
        """
        Helper method to create custom fields in Zoho Desk
        This should be run once during initial setup
        
        Returns:
            dict: Results of field creation
        """
        # Note: This requires admin API access
        # Custom fields in Zoho Desk are typically created via UI
        # This is a placeholder for the manual setup instructions
        
        logger.info("Custom fields should be created manually in Zoho Desk")
        logger.info("Required custom fields:")
        
        fields_to_create = [
            {
                "name": "AI Intent",
                "api_name": "cf_ai_intent",
                "type": "dropdown",
                "options": [
                    "refund_request",
                    "permit_cancellation",
                    "account_update",
                    "payment_issue",
                    "permit_inquiry",
                    "move_out",
                    "technical_issue",
                    "general_question",
                    "unclear"
                ]
            },
            {
                "name": "AI Complexity",
                "api_name": "cf_ai_complexity",
                "type": "dropdown",
                "options": ["simple", "moderate", "complex"]
            },
            {
                "name": "AI Language",
                "api_name": "cf_ai_language",
                "type": "dropdown",
                "options": ["english", "spanish", "mixed", "other"]
            },
            {
                "name": "AI Urgency",
                "api_name": "cf_ai_urgency",
                "type": "dropdown",
                "options": ["high", "medium", "low"]
            },
            {
                "name": "AI Confidence",
                "api_name": "cf_ai_confidence",
                "type": "number",
                "description": "Classification confidence (0-100%)"
            },
            {
                "name": "Requires Refund",
                "api_name": "cf_requires_refund",
                "type": "boolean"
            },
            {
                "name": "Requires Human Review",
                "api_name": "cf_requires_human_review",
                "type": "boolean"
            },
            {
                "name": "License Plate",
                "api_name": "cf_license_plate",
                "type": "text"
            },
            {
                "name": "Move Out Date",
                "api_name": "cf_move_out_date",
                "type": "date"
            },
            {
                "name": "Routing Queue",
                "api_name": "cf_routing_queue",
                "type": "text"
            }
        ]
        
        for field in fields_to_create:
            logger.info(f"  - {field['name']} ({field['api_name']}) - {field['type']}")
        
        return {
            "status": "manual_setup_required",
            "fields": fields_to_create,
            "instructions": "Create these fields in Zoho Desk Settings > Customize > Modules > Tickets > Fields"
        }
