"""
Wizard Service
Loads wizard step definitions from wizard_content.json and resolves
entity placeholders using ticket classification data.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

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


def get_wizard_for_intent(
    intent: str,
    classification: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Return the wizard definition for a given intent, with entity placeholders
    filled in from the classification data where available.

    Args:
        intent: One of the 9 intent values (e.g. 'refund_request')
        classification: Full classification dict from EmailClassifier (optional)

    Returns:
        Wizard definition dict with steps and templates
    """
    data = _load_wizard_data()

    if intent not in data or intent.startswith("_"):
        logger.warning(f"Unknown intent '{intent}', falling back to 'unclear'")
        intent = "unclear"

    wizard = json.loads(json.dumps(data[intent]))  # deep copy

    # Extract entities for placeholder substitution
    entities: Dict[str, str] = {}
    if classification:
        extracted = classification.get("extracted_entities") or {}
        if extracted.get("license_plate"):
            entities["license_plate"] = extracted["license_plate"]
        if extracted.get("move_out_date"):
            entities["move_out_date"] = extracted["move_out_date"]
        if extracted.get("amount"):
            entities["amount"] = str(extracted["amount"])

    # Substitute {{entity}} placeholders in step substeps
    for step in wizard.get("steps", []):
        if "substep" in step:
            step["substep"] = _fill_placeholders(step["substep"], entities)
        # Mark whether entity was actually found
        entity_field = step.get("entity_field")
        if entity_field:
            step["entity_value"] = entities.get(entity_field)
            step["entity_found"] = entity_field in entities

    # Attach confidence + intent from classification
    if classification:
        wizard["ai_confidence"] = classification.get("confidence")
        wizard["ai_intent"] = intent
        wizard["requires_human_review"] = classification.get("requires_human_review", False)
        wizard["extracted_entities"] = entities

    return wizard


def get_template_html(template_filename: str) -> Optional[str]:
    """
    Return the raw HTML content of a response template.

    Args:
        template_filename: e.g. 'refund_approved.html'

    Returns:
        HTML string or None if not found
    """
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
    """Return all supported intent keys."""
    data = _load_wizard_data()
    return [k for k in data.keys() if not k.startswith("_")]


def _fill_placeholders(text: str, entities: Dict[str, str]) -> str:
    """Replace {{key}} placeholders with entity values or a 'not found' fallback."""
    for key, value in entities.items():
        text = text.replace("{{" + key + "}}", value)
    # Replace any remaining unfilled placeholders with a clear indicator
    import re
    text = re.sub(
        r"\{\{(\w+)\}\}",
        lambda m: f"[{m.group(1).replace('_', ' ').title()} — Not Found in Email]",
        text
    )
    return text
