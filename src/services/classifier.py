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
    
    def classify_email(self, subject: str, body: str, from_email: str = "", ticket_id: str = "") -> Dict[str, Any]:
        """
        Classify an email and return structured classification data

        Args:
            subject: Email subject line
            body: Email body content
            from_email: Sender email address
            ticket_id: Optional ticket ID for analytics tracking

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

        # Log OpenAI token usage and estimated cost
        usage = response.usage
        if usage:
            try:
                from src.services.analytics_logger import log_api_usage, estimate_openai_cost
                cost = estimate_openai_cost(self.model, usage.prompt_tokens, usage.completion_tokens)
                log_api_usage(
                    provider="openai",
                    call_type="classify_email",
                    model=self.model,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    estimated_cost_usd=cost,
                    ticket_id=ticket_id or None,
                )
            except Exception:
                pass  # Never let logging break classification

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
   - "refund_request" - Customer wants money back (refund, reimbursement, credit). Use this whenever the customer explicitly asks for a refund, even if combined with a charge dispute or cancellation.
   - "permit_cancellation" - Customer wants to CANCEL their parking permit but does NOT mention a refund or wanting money back.
   - "account_update" - Update vehicle info, license plate, contact details, unit number, etc.
   - "permit_inquiry" - Questions about permits, status, pricing, how permits work.
   - "payment_issue" - Billing problems, charge disputes, failed payments, unauthorized charges where customer does NOT ask for a refund.
   - "technical_issue" - App/website problems, login issues, error messages.
   - "move_out" - Customer says they are moving out or have moved out, but does NOT explicitly request a refund or cancellation. They are notifying us.
   - "general_question" - Other questions that don't fit above categories.
   - "unclear" - Cannot determine intent at all (very short, gibberish, completely off-topic).

   IMPORTANT distinctions:
   - If customer mentions BOTH moving out AND wanting a refund → "refund_request" (refund is the actionable intent)
   - If customer mentions BOTH moving out AND wanting to cancel permit (no refund) → "permit_cancellation"
   - If customer just says "I'm moving out, what do I do?" with no specific request → "move_out"
   - If customer disputes a charge AND asks for money back → "refund_request"
   - If customer disputes a charge but does NOT ask for money back → "payment_issue"
   - If BOTH subject AND body are empty/meaningless (e.g. "(No Subject)" with no body) → "unclear"
   - "Renew", "Renewal", "Expiring Permit" without further context → "permit_inquiry", NOT "refund_request"

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

5. "confidence" - Your confidence in this classification (0.0 to 1.0).
   STRICT scoring rules — follow these exactly:
   - 0.90-1.00: ONLY when intent is crystal clear AND all key entities are present (plate, date, amount where applicable). Very few emails deserve this.
   - 0.75-0.89: Clear intent, but missing one or more entities (no plate, no date, no amount).
   - 0.60-0.74: Ambiguous — could be multiple intents, vague language, or conflicting signals.
   - 0.40-0.59: Very unclear, rambling, contradictory, or extremely short with no context.
   - Below 0.40: Cannot determine intent at all (gibberish, off-topic, empty).

   MANDATORY deductions — apply ALL that apply:
   - Email body is empty or near-empty (subject only) → max 0.55
   - Email is a forwarded/reply chain with noise → deduct 0.10
   - Multiple possible intents with no clear winner → max 0.70
   - Missing license plate when relevant → deduct 0.05
   - Missing move-out date when relevant → deduct 0.05
   - Third party writing on behalf of someone → deduct 0.05

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

EXAMPLES for calibration:

Example 1 — Clear refund with all entities:
Subject: "Refund for parking"
Body: "I moved out on Jan 1. Plate ABC-1234. Refund me the $45 charge."
→ intent: "refund_request", confidence: 0.95

Example 2 — Cancel permit, no refund:
Subject: "Cancel parking permit"
Body: "I'd like to cancel my parking permit effective immediately. Plate DEF-5678."
→ intent: "permit_cancellation", confidence: 0.90

Example 3 — Moving out notification (no action requested):
Subject: "Moving out"
Body: "I'm moving out next month. What do I need to do about parking?"
→ intent: "move_out", confidence: 0.80 (no specific date, no plate)

Example 4 — Vague/empty body:
Subject: "Refund"
Body: ""
→ intent: "refund_request", confidence: 0.50 (subject-only, no details)

Example 5 — Angry charge dispute wanting money back:
Subject: "UNAUTHORIZED CHARGE"
Body: "You charged me $45 without authorization after I moved out. Refund immediately or I'm calling my lawyer!"
→ intent: "refund_request", confidence: 0.90 (explicit refund demand, has amount, urgency: high)

Example 6 — No subject, no body (zero signal):
Subject: "(No Subject)"
Body: ""
→ intent: "unclear", confidence: 0.35 (absolutely no information to classify)

Example 7 — Renewal inquiry (NOT a refund):
Subject: "Renew"
Body: ""
→ intent: "permit_inquiry", confidence: 0.50 (subject suggests renewal, no body)

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
        elif intent == "permit_cancellation" and complexity == "simple":
            return "Quick Updates"
        elif intent == "account_update" and complexity == "simple":
            return "Quick Updates"
        elif complexity == "complex" or classification.get("urgency") == "high":
            return "Escalations"
        else:
            return "General Support"
