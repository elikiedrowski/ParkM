"""
Email Classification Service using OpenAI
Classifies support emails by intent, complexity, language, and urgency
"""
import os
from typing import Dict, Any
from openai import OpenAI
from src.config import get_settings


class EmailClassifier:
    """Classifies support emails using AI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.ai_model
    
    def classify_email(self, subject: str, body: str, from_email: str = "") -> Dict[str, Any]:
        """
        Classify an email and return structured classification data
        
        Args:
            subject: Email subject line
            body: Email body content
            from_email: Sender email address
        
        Returns:
            Dictionary with classification results
        """
        
        prompt = self._build_classification_prompt(subject, body)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert customer support email classifier for ParkM, 
                    a virtual parking permit provider. Analyze support emails and classify them 
                    accurately to help route them to the right team and set expectations."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def _build_classification_prompt(self, subject: str, body: str) -> str:
        """Build the classification prompt"""
        return f"""Analyze this customer support email and classify it with the following categories:

EMAIL:
Subject: {subject}
Body: {body}

Provide your classification in JSON format with these fields:

1. "intent" - Primary intent (choose ONE):
   - "refund_request" - Customer requesting a refund
   - "account_update" - Update vehicle info, license plate, etc.
   - "permit_inquiry" - Questions about permits, status, pricing
   - "payment_issue" - Billing problems, charge disputes
   - "technical_issue" - App/website problems
   - "move_out" - Moving out notification
   - "general_question" - Other questions
   - "unclear" - Cannot determine intent

2. "complexity" - How difficult to resolve (choose ONE):
   - "simple" - Clear request, straightforward resolution, one permit/vehicle
   - "moderate" - Some ambiguity, may need follow-up, multiple items
   - "complex" - Unclear request, multiple issues, edge cases, conflicts

3. "language" - Detected language:
   - "english"
   - "spanish"
   - "other"
   - "mixed"

4. "urgency" - How urgent (choose ONE):
   - "high" - Angry customer, immediate need, legal threat
   - "medium" - Normal request timing
   - "low" - General inquiry, no rush

5. "confidence" - Your confidence in this classification (0.0 to 1.0)

6. "key_entities" - Extract important information as an object:
   - "license_plate": null or the plate number if mentioned
   - "move_out_date": null or date mentioned
   - "property_name": null or property/community name
   - "amount": null or dollar amount mentioned

7. "requires_refund" - Boolean: Does this email mention wanting money back?

8. "requires_human_review" - Boolean: Should a human review this before any automation?

9. "suggested_response_type" - How should we respond:
   - "auto_resolve" - Can be fully automated
   - "auto_draft" - Generate draft for CSR approval
   - "manual" - Needs full human handling

10. "notes" - Brief explanation of your classification (1 sentence)

Respond ONLY with valid JSON, no other text."""
    
    def get_routing_recommendation(self, classification: Dict[str, Any]) -> str:
        """
        Recommend which department/queue to route to based on classification
        
        Args:
            classification: Result from classify_email()
        
        Returns:
            Department name recommendation
        """
        intent = classification.get("intent")
        complexity = classification.get("complexity")
        
        # Simple routing logic (can be enhanced)
        if intent == "refund_request" and complexity == "simple":
            return "Auto-Resolution Queue"
        elif intent in ["refund_request", "payment_issue"]:
            return "Accounting/Refunds"
        elif intent == "account_update" and complexity == "simple":
            return "Quick Updates"
        elif complexity == "complex" or classification.get("urgency") == "high":
            return "Escalations"
        else:
            return "General Support"
