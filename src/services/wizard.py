"""
Wizard Service
Loads wizard step definitions from wizard_content.json and resolves
entity placeholders using ticket classification data.

Supports lookup by both tag name (e.g. "Customer Password Reset")
and legacy intent key (e.g. "password_reset").
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_WIZARD_PATH = Path(__file__).parent.parent / "wizard" / "wizard_content.json"
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_wizard_data: Optional[Dict[str, Any]] = None


def _load_wizard_data() -> Dict[str, Any]:
    global _wizard_data
    if _wizard_data is None:
        with open(_WIZARD_PATH, encoding="utf-8") as f:
            _wizard_data = json.load(f)
    return _wizard_data


def _normalize_tag_key(tag: str) -> str:
    """Convert a tag name to the wizard_content.json key format.
    e.g. 'Customer Password Reset' → 'customer_password_reset'
    """
    return re.sub(r'[^a-z0-9]+', '_', tag.lower()).strip('_')


def get_wizard_for_intent(
    intent: str,
    classification: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Return the wizard definition for a given intent/tag, with entity
    placeholders filled in from the classification data.

    Args:
        intent: Either a tag name ("Customer Password Reset") or
                a legacy key ("password_reset")
        classification: Full classification dict from EmailClassifier (optional)

    Returns:
        Wizard definition dict with steps and templates
    """
    data = _load_wizard_data()

    # Try direct lookup first (legacy key), then normalized tag key
    key = intent
    if key not in data or key.startswith("_"):
        key = _normalize_tag_key(intent)
    if key not in data or key.startswith("_"):
        logger.warning(f"No wizard for '{intent}' (key='{key}'), falling back to 'unclear'")
        # Return a generic placeholder wizard
        return _placeholder_wizard(intent, classification)

    wizard = json.loads(json.dumps(data[key]))  # deep copy

    # Extract entities for placeholder substitution
    entities: Dict[str, str] = {}
    if classification:
        extracted = classification.get("key_entities") or classification.get("extracted_entities") or {}
        if extracted.get("license_plate"):
            val = extracted["license_plate"]
            entities["license_plate"] = ", ".join(val) if isinstance(val, list) else str(val)
        if extracted.get("move_out_date"):
            val = extracted["move_out_date"]
            entities["move_out_date"] = ", ".join(val) if isinstance(val, list) else str(val)
        if extracted.get("amount"):
            val = extracted["amount"]
            entities["amount"] = ", ".join(str(v) for v in val) if isinstance(val, list) else str(val)

    # Substitute {{entity}} placeholders in step substeps
    for step in wizard.get("steps", []):
        if "substep" in step:
            step["substep"] = _fill_placeholders(step["substep"], entities)
        entity_field = step.get("entity_field")
        if entity_field:
            step["entity_value"] = entities.get(entity_field)
            step["entity_found"] = entity_field in entities

    # Attach classification metadata
    if classification:
        wizard["ai_confidence"] = classification.get("confidence")
        wizard["ai_intent"] = intent
        wizard["requires_human_review"] = classification.get("requires_human_review", False)
        wizard["extracted_entities"] = entities

    return wizard


_TAG_ICONS: Dict[str, str] = {
    "cancel": "🚫", "refund": "💰", "password": "🔑", "update": "✏️",
    "payment": "💳", "double charged": "💳", "extra charges": "💳",
    "towed": "🚗", "booted": "🚗", "ticketed": "🚗",
    "permit": "🅿️", "parking": "🅿️", "spot": "🅿️",
    "move": "🏠", "property": "🏢", "sales": "📊",
    "enforce": "⚖️", "citation": "⚖️", "appeal": "⚖️",
    "grandfathered": "📋", "inquir": "❓", "question": "❓",
    "needs tag": "⚠️",
}


def _icon_for_tag(tag: str) -> str:
    """Pick an emoji icon based on keywords in the tag name."""
    tag_lower = tag.lower()
    for keyword, icon in _TAG_ICONS.items():
        if keyword in tag_lower:
            return icon
    return "📋"


def _placeholder_wizard(tag: str, classification: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a generic wizard for tags that don't have a full definition yet."""
    wizard = {
        "label": tag,
        "icon": _icon_for_tag(tag),
        "color": "#607d8b",
        "intro": f"Wizard steps for \"{tag}\" are being developed. Follow your standard process.",
        "steps": [
            {"id": "1", "text": "Review the ticket and identify the customer's request", "required": True},
            {"id": "2", "text": "Follow the standard process for this type of request"},
            {"id": "3", "text": "Send appropriate response to customer"},
            {"id": "4", "text": "Update ticket status"},
        ],
        "validation_on_close": [
            "Did you respond to the customer?",
            "Did you complete all required actions?"
        ],
        "quick_templates": []
    }
    if classification:
        wizard["ai_confidence"] = classification.get("confidence")
        wizard["ai_intent"] = tag
        wizard["requires_human_review"] = classification.get("requires_human_review", False)
        wizard["extracted_entities"] = {}
    return wizard


def get_template_html(template_filename: str) -> Optional[str]:
    """Return the raw HTML content of a response template."""
    path = _TEMPLATES_DIR / template_filename
    if not path.exists():
        logger.error(f"Template not found: {template_filename}")
        return None
    return path.read_text(encoding="utf-8")


def list_templates() -> list:
    """Return all available template filenames."""
    if not _TEMPLATES_DIR.exists():
        return []
    return sorted(p.name for p in _TEMPLATES_DIR.glob("*.html"))


def list_intents() -> list:
    """Return all supported intent/tag keys."""
    data = _load_wizard_data()
    return [k for k in data.keys() if not k.startswith("_")]


def _fill_placeholders(text: str, entities: Dict[str, str]) -> str:
    """Replace {{key}} placeholders with entity values or a 'not found' fallback."""
    for key, value in entities.items():
        text = text.replace("{{" + key + "}}", value)
    text = re.sub(
        r"\{\{(\w+)\}\}",
        lambda m: f"[{m.group(1).replace('_', ' ').title()} — Not Found in Email]",
        text
    )
    return text
