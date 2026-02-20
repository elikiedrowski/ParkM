"""
Correction Logger Service
Logs CSR corrections when they override an AI misclassification.
These corrections build a training dataset for prompt improvement over time.

Primary storage: PostgreSQL via SQLAlchemy (when DATABASE_URL is set).
Fallback storage: logs/corrections.jsonl
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

CORRECTIONS_LOG = "logs/corrections.jsonl"


def log_correction(
    ticket_id: str,
    original_intent: str,
    corrected_intent: str,
    confidence: Optional[int] = None,
    department_id: Optional[str] = None
) -> bool:
    """
    Append a CSR correction to DB (primary) or JSONL (fallback).

    Args:
        ticket_id: Zoho Desk ticket ID
        original_intent: What the AI classified it as (cf_ai_intent)
        corrected_intent: What the CSR says it should be (cf_agent_corrected_intent)
        confidence: AI confidence score at time of classification (0-100)
        department_id: Zoho department ID

    Returns:
        True if logged successfully, False otherwise
    """
    is_misclassification = corrected_intent != "correct" and corrected_intent != original_intent

    # Try DB first
    try:
        from src.db.database import get_engine, corrections
        engine = get_engine()
        if engine:
            with engine.connect() as conn:
                conn.execute(corrections.insert().values(
                    timestamp=datetime.utcnow(),
                    ticket_id=ticket_id,
                    department_id=department_id,
                    original_intent=original_intent,
                    corrected_intent=corrected_intent,
                    confidence=confidence,
                    is_misclassification=is_misclassification,
                ))
                conn.commit()
            logger.info(
                f"[{ticket_id}] Correction written to DB: {original_intent} → {corrected_intent} "
                f"(confidence was {confidence}%)"
            )
            return True
    except Exception as e:
        logger.warning(f"[{ticket_id}] DB write failed ({e}), falling back to JSONL")

    # JSONL fallback
    try:
        os.makedirs("logs", exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ticket_id": ticket_id,
            "department_id": department_id,
            "original_intent": original_intent,
            "corrected_intent": corrected_intent,
            "confidence": confidence,
            "is_misclassification": is_misclassification,
        }
        with open(CORRECTIONS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(
            f"[{ticket_id}] Correction logged to JSONL: {original_intent} → {corrected_intent} "
            f"(confidence was {confidence}%)"
        )
        return True
    except Exception as e:
        logger.error(f"[{ticket_id}] Failed to log correction: {e}")
        return False


def get_corrections_summary() -> dict:
    """
    Summarize logged corrections to identify top misclassification patterns.

    Returns:
        dict with confusion pairs ranked by frequency
    """
    entries = _fetch_all_corrections()

    if not entries:
        return {"total": 0, "misclassifications": 0, "confusion_pairs": []}

    misclassifications = [e for e in entries if e.get("is_misclassification")]

    confusion_counts: dict = {}
    for e in misclassifications:
        pair = f"{e['original_intent']} → {e['corrected_intent']}"
        confusion_counts[pair] = confusion_counts.get(pair, 0) + 1

    sorted_pairs = sorted(confusion_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "total": len(entries),
        "misclassifications": len(misclassifications),
        "accuracy_rate": round((len(entries) - len(misclassifications)) / len(entries) * 100, 1) if entries else 0,
        "confusion_pairs": [{"pair": p, "count": c} for p, c in sorted_pairs]
    }


def _fetch_all_corrections() -> list:
    """Fetch all correction records from DB or JSONL."""
    try:
        from src.db.database import get_engine, read_corrections
        engine = get_engine()
        if engine:
            return read_corrections(engine)
    except Exception as e:
        logger.warning(f"DB read failed for corrections ({e}), falling back to JSONL")

    # JSONL fallback
    if not os.path.exists(CORRECTIONS_LOG):
        return []
    entries = []
    with open(CORRECTIONS_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries
