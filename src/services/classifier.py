"""
Email Classification Service using OpenAI
Classifies support emails with granular tags and multi-intent support.
Tags align with the Zoho Desk 'Tagging' picklist values.
"""
import json
import os
from typing import Dict, Any, List
from openai import OpenAI
from src.config import get_settings


# Load tag values from the canonical source
_TAG_VALUES_PATH = os.path.join(os.path.dirname(__file__), "..", "wizard", "tagging_values.json")
with open(_TAG_VALUES_PATH) as _f:
    VALID_TAGS: List[str] = json.load(_f)["values"]


class EmailClassifier:
    """Classifies support emails using AI"""

    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.ai_model

    def classify_email(self, subject: str, body: str, from_email: str = "", ticket_id: str = "") -> Dict[str, Any]:
        """
        Classify an email and return structured classification data.

        Returns a dict with "tags" (list of 1+ tag strings) plus complexity,
        language, urgency, confidence, key_entities, and other metadata.
        """
        prompt = self._build_classification_prompt(subject, body)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert customer support email classifier for ParkM, "
                        "a virtual parking permit provider. ParkM manages parking permits "
                        "for apartment communities. Emails come from three groups: "
                        "Customers (residents), Property managers/staff, and Sales reps. "
                        "Analyze support emails and classify them with one or more granular tags."
                    )
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

        result = json.loads(response.choices[0].message.content)

        # Validate tags against allowed values
        raw_tags = result.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        result["tags"] = [t for t in raw_tags if t in VALID_TAGS] or ["Needs Tag"]

        # Backwards compat: set "intent" to primary (first) tag for routing/logging
        result["intent"] = result["tags"][0]

        return result

    def _build_classification_prompt(self, subject: str, body: str) -> str:
        """Build the classification prompt with granular tags"""
        return f"""Analyze this customer support email and classify it.

EMAIL:
Subject: {subject}
Body: {body}

Provide your classification in JSON format with these fields:

1. "tags" - A JSON array of one or more tags that apply. Choose from EXACTLY these values:

   CUSTOMER TAGS (resident/end-user emails):
   - "Customer Canceling a Permit and Refunding" — wants to cancel AND get money back
   - "Customer Inquiring for Grandfathered Permit" — asking about a grandfathered permit
   - "Customer Inquiring for Locked Down Permit" — asking about a locked/restricted permit
   - "Customer Inquiring for Additional Permit" — wants another permit added to their account
   - "Customer Rental Car" — has a rental car, needs temporary permit or update
   - "Customer Double Charged or Extra Charges" — billing dispute, charged twice, unexpected charges
   - "Customer Guest Permit and Pricing Questions" — questions about guest passes or pricing
   - "Customer Miscellaneous Questions" — general questions that don't fit other categories
   - "Customer Sending Money Order" — paying by money order
   - "Customer Need help buying a permit" — first-time buyer needs help purchasing
   - "Customer Need Help Renewing Permit" — existing customer needs help with renewal
   - "Customer Need Help Creating an Account" — can't create an account, signup issues
   - "Customer New Towing Legislation No Parking" — asking about towing laws or no-parking rules
   - "Customer No Plate or Expired Tags" — vehicle has no plate or expired registration
   - "Customer Someone is Parking in my Spot" — reporting unauthorized vehicle in their space
   - "Customer Parking Space Not in Dropdown" — their parking space isn't listed in the system
   - "Customer Password Reset" — forgot password, locked out, needs reset
   - "Customer Towed Booted Ticketed" — vehicle was towed, booted, or ticketed
   - "Customer Warned or Tagged" — vehicle received a warning sticker or tag
   - "Customer Payment Help" — general payment issues, can't pay, payment failed
   - "Customer Update Vehicle Info" — changing license plate or vehicle details
   - "Customer Update Contact Info" — changing email, phone, address, unit number

   PROPERTY TAGS (property manager/staff emails):
   - "Property Changing Resident Type for Approved Permit" — changing resident status on a permit
   - "Property Approving Grandfathered Permit" — property approving a grandfathered permit
   - "Property Approving Override Additional Permit" — property overriding to allow extra permit
   - "Property Extending Expiration Date on a Permit" — extending a permit's expiration
   - "Property Audits or Reports" — requesting audit data, reports, or parking stats
   - "Property Checking if a Vehicle is Permitted" — verifying a vehicle has a permit
   - "Property Checking Who Has a Space Number" — looking up who is assigned a space
   - "Property Checking Who is in a Unit" — looking up who lives in a unit
   - "Property Inquiring about a Tow Boot Ticket" — property asking about a tow/boot/ticket
   - "Property Inquiring About a Warning Tag" — property asking about a warning tag
   - "Property Monitor Request" — requesting parking lot monitoring/patrol
   - "Property Leasing Staff Login" — leasing office staff needs login help
   - "Property Miscellaneous Questions" — general property manager questions
   - "Property Sending Money Order" — property sending payment by money order
   - "Property Update or Register Employee Vehicles" — adding/updating staff vehicles
   - "Property Update Resident Vehicle" — property updating a resident's vehicle info
   - "Property Update Resident Contact Information" — property updating resident contact info
   - "Property Update Resident Password" — property resetting a resident's password
   - "Property Register Resident Account for Them" — property creating a resident account
   - "Property Cancel Resident Account" — property canceling a resident's account
   - "Property Permitting PAID Resident Vehicle for Them" — property permitting a vehicle on behalf of resident
   - "Property Resident Payment Help" — property helping a resident with payment issues
   - "Property Guest Permits" — property asking about guest permit process
   - "Property Potential Leads" — new property interested in ParkM services

   OTHER TAGS:
   - "Sales Rep Asking for a Vehicle to be Released" — sales rep requesting vehicle release
   - "Sales Rep Asking for a Vehicle to be Grandfathered" — sales rep requesting grandfathered status
   - "Towing or Monitoring Leads" — potential towing/monitoring business leads
   - "The Law Asking for Information" — law enforcement requesting information
   - "Needs Tag" — ONLY if the email is completely unintelligible or empty

   MULTI-INTENT RULES:
   - If the email covers MULTIPLE distinct issues, include ALL applicable tags.
   - Order tags by importance: the primary issue first, secondary issues after.
   - Most emails will have 1 tag. Some will have 2-3. Rarely more than 3.
   - Example: customer says "I need to update my plate AND my car was warned" → ["Customer Update Vehicle Info", "Customer Warned or Tagged"]

   SENDER DETECTION:
   - If the email is from a property manager or leasing office → use "Property ..." tags
   - If the email is from a resident/customer → use "Customer ..." tags
   - If the email mentions "on behalf of" a resident → still use "Property ..." tags
   - Clues for property: mentions "resident", "unit", "leasing office", property company name, "our community"
   - Clues for customer: mentions "my permit", "my car", "I moved out", "I need help"

2. "complexity" - How difficult to resolve (choose ONE):
   - "simple" - Clear request, straightforward resolution
   - "moderate" - Some ambiguity, may need follow-up
   - "complex" - Multiple issues, edge cases, unclear

3. "language" - Detected language:
   - "english", "spanish", "other", or "mixed"

4. "urgency" - How urgent (choose ONE):
   - "high" - Angry customer, immediate need, legal threat, tow/boot situation
   - "medium" - Normal request timing
   - "low" - General inquiry, no rush

5. "confidence" - Your confidence in this classification (0.0 to 1.0).
   STRICT scoring rules:
   - 0.90-1.00: Crystal clear intent, all key entities present. Rare.
   - 0.75-0.89: Clear intent, missing one or more entities.
   - 0.60-0.74: Ambiguous, could be multiple categories, vague language.
   - 0.40-0.59: Very unclear, short, contradictory.
   - Below 0.40: Cannot determine (gibberish, empty, off-topic).

   MANDATORY deductions:
   - Empty body (subject only) → max 0.55
   - Forwarded/reply chain with noise → deduct 0.10
   - Multiple possible tags with no clear primary → deduct 0.10
   - Missing license plate when relevant → deduct 0.05
   - Third party writing → deduct 0.05

6. "key_entities" - Extract important information:
   - "license_plate": null or plate number
   - "move_out_date": null or date mentioned
   - "property_name": null or property/community name
   - "amount": null or dollar amount
   - "unit_number": null or unit/apartment number
   - "space_number": null or parking space number

7. "requires_refund" - Boolean: Does this email mention wanting money back?

8. "requires_human_review" - Boolean: Should a human review this?

9. "suggested_response_type":
   - "auto_resolve" - Can be fully automated
   - "auto_draft" - Generate draft for CSR approval
   - "manual" - Needs full human handling

10. "notes" - Brief explanation of your classification (1 sentence)

EXAMPLES:

Example 1 — Customer cancel + refund:
Subject: "Cancel and refund"
Body: "I moved out Jan 1. Plate ABC-1234. Please cancel my permit and refund the $45."
→ tags: ["Customer Canceling a Permit and Refunding"], confidence: 0.95

Example 2 — Someone parking in their spot:
Subject: "Unauthorized car"
Body: "Someone is parking in my assigned spot #204. License plate XYZ-789."
→ tags: ["Customer Someone is Parking in my Spot"], confidence: 0.90

Example 3 — Property checking a vehicle:
Subject: "Is this car permitted?"
Body: "Hi, can you check if plate DEF-456 is registered in our system? This is from Sunset Apartments leasing office."
→ tags: ["Property Checking if a Vehicle is Permitted"], confidence: 0.90

Example 4 — Multi-intent:
Subject: "Payment issue and password"
Body: "I was double charged this month AND I can't log in to check my account. Please help."
→ tags: ["Customer Double Charged or Extra Charges", "Customer Password Reset"], confidence: 0.80

Example 5 — Customer towed and wants refund:
Subject: "TOWED!!"
Body: "My car was towed but I have a valid permit! I want it released AND a refund for the tow fee!"
→ tags: ["Customer Towed Booted Ticketed"], confidence: 0.85

Example 6 — Empty email:
Subject: "(No Subject)"
Body: ""
→ tags: ["Needs Tag"], confidence: 0.30

Respond ONLY with valid JSON, no other text."""

    def get_routing_recommendation(self, classification: Dict[str, Any]) -> str:
        """
        Recommend which department/queue to route to based on classification.
        Uses the primary tag (first in the tags list).
        """
        tags = classification.get("tags", [])
        primary_tag = tags[0] if tags else "Needs Tag"
        complexity = classification.get("complexity")
        urgency = classification.get("urgency")

        # Escalation cases
        if urgency == "high" or complexity == "complex":
            return "Escalations"

        # Tow/boot situations
        if primary_tag in [
            "Customer Towed Booted Ticketed",
            "Customer New Towing Legislation No Parking",
            "Property Inquiring about a Tow Boot Ticket",
        ]:
            return "Escalations"

        # Refund / billing
        if primary_tag in [
            "Customer Canceling a Permit and Refunding",
            "Customer Double Charged or Extra Charges",
        ]:
            return "Accounting/Refunds"

        # Quick resolution items
        if primary_tag in [
            "Customer Password Reset",
            "Customer Update Vehicle Info",
            "Customer Update Contact Info",
            "Customer Warned or Tagged",
            "Property Update Resident Vehicle",
            "Property Update Resident Contact Information",
            "Property Update Resident Password",
        ] and complexity == "simple":
            return "Quick Updates"

        # Property requests
        if primary_tag.startswith("Property "):
            return "Property Support"

        # Sales / leads
        if primary_tag in [
            "Sales Rep Asking for a Vehicle to be Released",
            "Sales Rep Asking for a Vehicle to be Grandfathered",
            "Towing or Monitoring Leads",
            "Property Potential Leads",
        ]:
            return "Sales / Leads"

        # Law enforcement
        if primary_tag == "The Law Asking for Information":
            return "Escalations"

        return "General Support"
