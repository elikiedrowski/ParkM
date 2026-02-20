"""
Analytics Logger Service
Logs classification, template, API usage, and error events.

Primary storage: PostgreSQL via SQLAlchemy (when DATABASE_URL is set).
Fallback storage: JSONL files in logs/ directory.
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# JSONL fallback paths
CLASSIFICATIONS_LOG = "logs/classifications.jsonl"
TEMPLATE_USAGE_LOG = "logs/template_usage.jsonl"
API_USAGE_LOG = "logs/api_usage.jsonl"
ERRORS_LOG = "logs/errors.jsonl"

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


# ── Classification events ─────────────────────────────────────────────────

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
    Log a classification event to DB (primary) or JSONL (fallback).
    """
    # Build the common entry dict
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

    # Try DB first
    try:
        from src.db.database import get_engine, classifications
        engine = get_engine()
        if engine:
            with engine.connect() as conn:
                conn.execute(classifications.insert().values(
                    timestamp=datetime.utcnow(),
                    ticket_id=ticket_id,
                    department_id=department_id,
                    intent=entry["intent"],
                    confidence=entry["confidence"],
                    complexity=entry["complexity"],
                    urgency=entry["urgency"],
                    language=entry["language"],
                    requires_refund=entry["requires_refund"],
                    requires_human_review=entry["requires_human_review"],
                    routing_queue=entry["routing_queue"],
                    entities_json=json.dumps(entry["entities"]) if entry["entities"] else None,
                    processing_time_seconds=entry["processing_time_seconds"],
                    tagging_success=entry["tagging_success"],
                    error=entry["error"],
                ))
                conn.commit()
            logger.info(f"[{ticket_id}] Classification event written to DB")
            return True
    except Exception as e:
        logger.warning(f"[{ticket_id}] DB write failed ({e}), falling back to JSONL")

    # JSONL fallback
    try:
        os.makedirs("logs", exist_ok=True)
        with open(CLASSIFICATIONS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"[{ticket_id}] Classification event logged to JSONL")
        return True
    except Exception as e:
        logger.error(f"[{ticket_id}] Failed to log classification event: {e}")
        return False


# ── Template usage ────────────────────────────────────────────────────────

def log_template_usage(
    template_file: str,
    ticket_id: Optional[str] = None,
    intent: Optional[str] = None
) -> bool:
    """Log a template usage event to DB (primary) or JSONL (fallback)."""
    # Try DB first
    try:
        from src.db.database import get_engine, template_usage
        engine = get_engine()
        if engine:
            with engine.connect() as conn:
                conn.execute(template_usage.insert().values(
                    timestamp=datetime.utcnow(),
                    template_file=template_file,
                    ticket_id=ticket_id,
                    intent=intent,
                ))
                conn.commit()
            logger.info(f"Template usage written to DB: {template_file}")
            return True
    except Exception as e:
        logger.warning(f"DB write failed for template usage ({e}), falling back to JSONL")

    # JSONL fallback
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
        logger.info(f"Template usage logged to JSONL: {template_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to log template usage: {e}")
        return False


# ── API usage ─────────────────────────────────────────────────────────────

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
    """Log an API usage event to DB (primary) or JSONL (fallback)."""
    # Try DB first
    try:
        from src.db.database import get_engine, api_usage
        engine = get_engine()
        if engine:
            with engine.connect() as conn:
                conn.execute(api_usage.insert().values(
                    timestamp=datetime.utcnow(),
                    provider=provider,
                    call_type=call_type,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=round(estimated_cost_usd, 6) if estimated_cost_usd else None,
                    ticket_id=ticket_id,
                    success=success,
                    error=error,
                ))
                conn.commit()
            return True
    except Exception as e:
        logger.warning(f"DB write failed for api_usage ({e}), falling back to JSONL")

    # JSONL fallback
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


# ── Error logs ────────────────────────────────────────────────────────────

def log_error(
    level: str,
    component: str,
    message: str,
    ticket_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Log an application error to DB (primary) or JSONL (fallback).

    Args:
        level: "ERROR", "WARNING", or "CRITICAL"
        component: Module/service name (e.g. "webhooks", "classifier")
        message: Human-readable error description
        ticket_id: Associated Zoho ticket ID (optional)
        details: Additional structured data (optional)
    """
    # Try DB first
    try:
        from src.db.database import get_engine, error_logs
        engine = get_engine()
        if engine:
            with engine.connect() as conn:
                conn.execute(error_logs.insert().values(
                    timestamp=datetime.utcnow(),
                    level=level.upper(),
                    component=component,
                    ticket_id=ticket_id,
                    message=message,
                    details=json.dumps(details) if details else None,
                ))
                conn.commit()
            return True
    except Exception as e:
        logger.warning(f"DB write failed for error_log ({e}), falling back to JSONL")

    # JSONL fallback
    try:
        os.makedirs("logs", exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "component": component,
            "ticket_id": ticket_id,
            "message": message,
            "details": details,
        }
        with open(ERRORS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to log error event: {e}")
        return False
