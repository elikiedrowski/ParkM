"""
Email Classification Service using OpenAI
Classifies support emails with granular tags and multi-intent support.
Tags align with the Zoho Desk 'Tagging' picklist values.
"""
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional
from openai import OpenAI
from src.config import get_settings

logger = logging.getLogger(__name__)


# Load tag values from the canonical source
_TAG_VALUES_PATH = os.path.join(os.path.dirname(__file__), "..", "wizard", "tagging_values.json")
with open(_TAG_VALUES_PATH) as _f:
    VALID_TAGS: List[str] = json.load(_f)["values"]

# Load corrected-examples few-shot block (built from human review of 31 mistagged tickets)
_CORRECTED_EXAMPLES_PATH = os.path.join(os.path.dirname(__file__), "..", "wizard", "corrected_examples.txt")
try:
    with open(_CORRECTED_EXAMPLES_PATH) as _f:
        CORRECTED_EXAMPLES: str = _f.read()
except FileNotFoundError:
    CORRECTED_EXAMPLES = ""


# ── Live-learning cache (per-department) ────────────────────────────────────
# Rebuilt from the `corrections` table every LIVE_LEARNING_TTL seconds.
_LIVE_LEARNING_CACHE: Dict[str, Dict[str, Any]] = {}
LIVE_LEARNING_TTL = 600  # 10 minutes
LIVE_LEARNING_LIMIT = 20


def _build_live_learning_block(department_id: Optional[str]) -> str:
    """Fetch the most recent CSR corrections for this department and format
    them as a few-shot block to inject into the classifier prompt.

    Cached per-department for LIVE_LEARNING_TTL seconds. Returns empty string
    on any failure — this path must never break classification.
    """
    if os.environ.get("LIVE_LEARNING_ENABLED", "true").lower() in ("0", "false", "no"):
        return ""

    cache_key = f"corrections:{department_id or 'default'}"
    entry = _LIVE_LEARNING_CACHE.get(cache_key)
    if entry and (time.time() - entry["ts"]) < LIVE_LEARNING_TTL:
        return entry["block"]

    try:
        from src.db.database import get_engine, read_recent_corrections
        engine = get_engine()
        if not engine:
            return ""
        rows = read_recent_corrections(engine, department_id=department_id, limit=LIVE_LEARNING_LIMIT)
    except Exception as e:
        logger.warning(f"Live-learning DB read failed ({e}); skipping injection")
        return ""

    # Only keep corrections with real content AND canonical tags — older legacy
    # rows may have empty subject/body or obsolete tag names.
    usable = []
    for r in rows:
        subj = (r.get("subject") or "").strip()
        snippet = (r.get("description_snippet") or "").strip()
        if not subj and not snippet:
            continue
        correct = r["corrected_tags"] or ([] if not r.get("corrected_intent") else [r["corrected_intent"]])
        if not any(t in VALID_TAGS for t in correct):
            continue
        usable.append(r)

    if not usable:
        _LIVE_LEARNING_CACHE[cache_key] = {"ts": time.time(), "block": ""}
        return ""

    lines = [
        "LIVE CSR CORRECTIONS (most recent first — your team has overridden these classifications):",
        "",
    ]
    for i, r in enumerate(usable, 1):
        ai = "; ".join(r["original_tags"]) or r.get("original_intent") or "?"
        correct = "; ".join(r["corrected_tags"]) or r.get("corrected_intent") or "?"
        subj = (r.get("subject") or "").strip()
        snippet = (r.get("description_snippet") or "").strip()
        lines.append(f"[L{i}] Subject: \"{subj[:120]}\"")
        if snippet:
            lines.append(f"      Body: \"{snippet[:250]}\"")
        lines.append(f"      AI picked: {ai}  →  CSR corrected to: {correct}")
        lines.append("")
    block = "\n".join(lines)
    _LIVE_LEARNING_CACHE[cache_key] = {"ts": time.time(), "block": block}
    return block


class EmailClassifier:
    """Classifies support emails using AI"""

    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.ai_model

    def classify_email(self, subject: str, body: str, from_email: str = "", ticket_id: str = "", department_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify an email and return structured classification data.

        Returns a dict with "tags" (list of 1+ tag strings) plus complexity,
        language, urgency, confidence, key_entities, and other metadata.
        """
        prompt = self._build_classification_prompt(subject, body, from_email, department_id=department_id)

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

    def _build_classification_prompt(self, subject: str, body: str, from_email: str = "", department_id: Optional[str] = None) -> str:
        """Build the classification prompt with granular tags"""
        email_line = f"\nFrom: {from_email}" if from_email else ""
        LIVE_LEARNING_BLOCK = _build_live_learning_block(department_id)
        return f"""Analyze this customer support email and classify it.

EMAIL:{email_line}
Subject: {subject}
Body: {body}

Provide your classification in JSON format with these fields:

1. "tags" - A JSON array of one or more tags that apply. Choose from EXACTLY these values:

   CUSTOMER TAGS (resident/end-user emails):
   - "Customer Canceling a Permit and Refunding" — wants to cancel AND get money back
   - "Customer Inquiring for Grandfathered Permit" — asking about a grandfathered permit
   - "Customer Inquiring for Locked Down Permit" — permits show as 'Sold Out', community-wide lockdown
   - "Customer Inquiring for Additional Permit" — wants another permit added to their account
   - "Customer Rental Car" — has a rental car, needs temporary permit or update
   - "Customer Double Charged or Extra Charges" — billing dispute, charged twice, unexpected charges
   - "Customer Guest Permit and Pricing Questions" — questions about guest passes or pricing
   - "Customer Miscellaneous Questions" — general questions that don't fit other categories
   - "Customer Sending Money Order" — paying by money order
   - "Customer Need help buying a permit" — first-time buyer needs help purchasing
   - "Customer Need Help Renewing Permit" — existing customer needs help with renewal
   - "Customer Need Help Creating an Account" — can't create an account, signup issues
   - "Customer New Towing Legislation No Parking" — pays for permit but no parking available, mentions new towing law
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

   PRIORITY RULES (avoid common misclassifications — derived from human review):

   RULE 1 — Cancel + refund dominates context:
   If the email contains explicit cancel + refund language ("cancel my permit",
   "refund me", "stop charging me", "I moved out, please refund", "cancel and
   reimburse"), tag as "Customer Canceling a Permit and Refunding" — even if
   the email ALSO mentions a license plate, contact info change, or a charge
   dispute as supporting context. The cancel+refund intent dominates secondary
   topics.

   RULE 2 — "Customer Double Charged or Extra Charges" is reserved for actual
   duplicate or unexpected charges. Do NOT use for:
     - General billing complaints (use "Customer Payment Help")
     - Renewal billing questions (use "Customer Need Help Renewing Permit")
     - Cancel+refund requests (use "Customer Canceling a Permit and Refunding")
     - Grandfathered permit billing (use "Customer Inquiring for Grandfathered Permit")
   Trigger phrases for valid use: "charged twice", "two charges", "duplicate
   charge", "extra charge I didn't authorize", "charged for something I didn't buy".

   RULE 3 — "Customer Update Vehicle Info" requires that updating the vehicle
   is the PRIMARY ask. Do NOT use just because the email mentions a vehicle.
   If the customer says "cancel the permit on my Honda", the intent is cancel,
   not update. Trigger phrases for valid use: "I got a new car", "please update
   my plate to", "I changed vehicles", "new license plate is".

   RULE 4 — "Customer Update Contact Info" requires that updating contact
   information is the PRIMARY ask. Do NOT use just because the email contains
   a new email address in the signature or mentions an address change in passing.
   Trigger phrases for valid use: "please update my email to", "new phone
   number", "I changed my address", "update my unit number".

   RULE 5 — "Customer Miscellaneous Questions" is a LAST RESORT. Always prefer
   a specific tag. Before tagging miscellaneous, check whether the email matches
   any of: Need Help Buying, Need Help Renewing, Payment Help, Update Contact
   Info, Password Reset, Guest Permit Questions. Only use miscellaneous if no
   specific tag fits.

   RULE 6 — "Customer Towed Booted Ticketed" requires an ACTUAL tow, boot, or
   ticket event on the customer's vehicle. Do NOT use for general questions
   about parking enforcement, complaints about other cars, or property
   inquiries. Trigger phrases for valid use: "my car was towed", "got booted",
   "received a ticket", "found a tow notice".

   RULE 7 — "Customer Need help buying a permit" recognition. Triggers include:
   "how do I get a permit", "I just moved in", "I'm trying to buy a permit",
   "trying to register", "trying to sign up", "new resident need permit",
   "how do I purchase". First-time-buyer intent — they don't have a permit yet
   and want one.

   RULE 8 — "Customer Inquiring for Locked Down Permit" recognition. Triggers
   include: "permits show as Sold Out", "can't purchase a permit", "permit
   page won't let me buy", "system says no permits available", "community is
   full", "lockdown". This is a community-wide availability issue, NOT a
   customer trying to add an extra permit (which is "Additional Permit").

   SENDER DETECTION:
   The "From" email address is a critical signal for determining sender type.

   EMAIL DOMAIN RULES (highest priority):
   - @parkm.com → ParkM internal staff / Sales Rep → use "Sales Rep ..." tags
   - Personal email domains (@gmail.com, @yahoo.com, @hotmail.com, @outlook.com, @aol.com, @icloud.com, @live.com, @comcast.net, @att.net, @verizon.net, etc.) → almost always a Customer → use "Customer ..." tags
   - KNOWN Property management domains (high confidence): @greystar.com, @redpeak.com, @udr.com → use "Property ..." tags
   - Other corporate/business email domains that are NOT @parkm.com (e.g., @lincolnapts.com, @[propertyname].com) → likely Property manager/staff → use "Property ..." tags

   CONTENT RULES (use to confirm or override domain signal):
   - If the email is from a property manager or leasing office → use "Property ..." tags
   - If the email is from a resident/customer → use "Customer ..." tags
   - If the email mentions "on behalf of" a resident → still use "Property ..." tags
   - Clues for property: mentions "resident", "unit", "leasing office", property company name, "our community", "our property"
   - Clues for customer: mentions "my permit", "my car", "I moved out", "I need help", "my account"
   - Clues for sales rep: mentions ParkM internally, sales context, references being a ParkM employee

   COMBINING SIGNALS:
   - When the email domain and content agree, use high confidence
   - When a corporate domain sends customer-like language (e.g., "my permit"), trust the content — they may be a resident with a work email
   - When a personal email sends property-like language (e.g., "our resident needs"), trust the content — they may be a property manager using personal email
   - @parkm.com senders should almost always get "Sales Rep ..." tags unless content clearly indicates otherwise

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

{CORRECTED_EXAMPLES}
{LIVE_LEARNING_BLOCK}
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
