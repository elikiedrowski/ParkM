"""
Analytics Logger Service
Logs classification events and template usage to JSONL files for dashboard analytics.
Follows the same pattern as correction_logger.py.
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CLASSIFICATIONS_LOG = "logs/classifications.jsonl"
TEMPLATE_USAGE_LOG = "logs/template_usage.jsonl"
API_USAGE_LOG = "logs/api_usage.jsonl"

# Pricing per 1M tokens (update when model changes)
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def estimate_openai_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated cost in USD based on model pricing."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def log_classification_event(
    ticket_id: str,
    classification: Optional[Dict[str, Any]],
    routing: Optional[str],
    processing_time_seconds: Optional[float],
    tagging_success: bool,
    error: Optional[str] = None,
    department_id: Optional[str] = None
) -> bool:
    """
    Append a classification event to the classifications log.

    Args:
        ticket_id: Zoho Desk ticket ID
        classification: Full classification dict from EmailClassifier (or None on error)
        routing: Routing recommendation string
        processing_time_seconds: Time taken to process the ticket
        tagging_success: Whether Zoho custom fields were updated successfully
        error: Error message if classification failed

    Returns:
        True if logged successfully
    """
    try:
        os.makedirs("logs", exist_ok=True)

        if classification:
            entities = classification.get("key_entities") or classification.get("extracted_entities") or {}
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "ticket_id": ticket_id,
                "department_id": department_id,
                "intent": classification.get("intent"),
                "confidence": classification.get("confidence"),
                "complexity": classification.get("complexity"),
                "urgency": classification.get("urgency"),
                "language": classification.get("language"),
                "requires_refund": classification.get("requires_refund", False),
                "requires_human_review": classification.get("requires_human_review", False),
                "routing_queue": routing,
                "entities": {
                    "license_plate": entities.get("license_plate"),
                    "move_out_date": entities.get("move_out_date"),
                    "property_name": entities.get("property_name"),
                    "amount": str(entities["amount"]) if entities.get("amount") else None,
                },
                "processing_time_seconds": round(processing_time_seconds, 2) if processing_time_seconds else None,
                "tagging_success": tagging_success,
                "error": None,
            }
        else:
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "ticket_id": ticket_id,
                "department_id": department_id,
                "intent": None,
                "confidence": None,
                "complexity": None,
                "urgency": None,
                "language": None,
                "requires_refund": False,
                "requires_human_review": False,
                "routing_queue": None,
                "entities": {},
                "processing_time_seconds": round(processing_time_seconds, 2) if processing_time_seconds else None,
                "tagging_success": False,
                "error": error,
            }

        with open(CLASSIFICATIONS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.info(f"[{ticket_id}] Classification event logged")
        return True

    except Exception as e:
        logger.error(f"[{ticket_id}] Failed to log classification event: {e}")
        return False


def log_template_usage(
    template_file: str,
    ticket_id: Optional[str] = None,
    intent: Optional[str] = None
) -> bool:
    """
    Append a template usage event to the template usage log.

    Args:
        template_file: Template filename (e.g. 'refund_approved.html')
        ticket_id: Zoho Desk ticket ID (optional)
        intent: Current intent when template was used (optional)

    Returns:
        True if logged successfully
    """
    try:
        os.makedirs("logs", exist_ok=True)

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "template_file": template_file,
            "ticket_id": ticket_id,
            "intent": intent,
        }

        with open(TEMPLATE_USAGE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.info(f"Template usage logged: {template_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to log template usage: {e}")
        return False


def log_api_usage(
    provider: str,
    call_type: str,
    model: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    estimated_cost_usd: Optional[float] = None,
    ticket_id: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> bool:
    """
    Append an API usage event to the api_usage log.

    Args:
        provider: "openai" or "zoho"
        call_type: Function name (e.g. "classify_email", "get_ticket")
        model: Model name for OpenAI calls
        prompt_tokens: Input tokens (OpenAI only)
        completion_tokens: Output tokens (OpenAI only)
        total_tokens: Total tokens (OpenAI only)
        estimated_cost_usd: Estimated cost in USD (OpenAI only)
        ticket_id: Associated ticket ID if applicable
        success: Whether the API call succeeded
        error: Error message if call failed

    Returns:
        True if logged successfully
    """
    try:
        os.makedirs("logs", exist_ok=True)

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "provider": provider,
            "call_type": call_type,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost_usd, 6) if estimated_cost_usd else None,
            "ticket_id": ticket_id,
            "success": success,
            "error": error,
        }

        with open(API_USAGE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return True

    except Exception as e:
        logger.error(f"Failed to log API usage: {e}")
        return False
