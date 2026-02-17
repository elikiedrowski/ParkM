"""
Correction Logger Service
Logs CSR corrections when they override an AI misclassification.
These corrections build a training dataset for prompt improvement over time.
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
    confidence: Optional[int] = None
) -> bool:
    """
    Append a CSR correction to the corrections log.

    Args:
        ticket_id: Zoho Desk ticket ID
        original_intent: What the AI classified it as (cf_ai_intent)
        corrected_intent: What the CSR says it should be (cf_agent_corrected_intent)
        confidence: AI confidence score at time of classification (0-100)

    Returns:
        True if logged successfully, False otherwise
    """
    try:
        os.makedirs("logs", exist_ok=True)

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ticket_id": ticket_id,
            "original_intent": original_intent,
            "corrected_intent": corrected_intent,
            "confidence": confidence,
            # True = AI was wrong, False = CSR confirmed it was correct
            "is_misclassification": corrected_intent != "correct" and corrected_intent != original_intent
        }

        with open(CORRECTIONS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.info(
            f"[{ticket_id}] Correction logged: {original_intent} → {corrected_intent} "
            f"(confidence was {confidence}%)"
        )
        return True

    except Exception as e:
        logger.error(f"[{ticket_id}] Failed to log correction: {e}")
        return False


def get_corrections_summary() -> dict:
    """
    Summarize logged corrections to identify top misclassification patterns.
    Used during prompt engineering to add few-shot examples.

    Returns:
        dict with confusion pairs ranked by frequency
    """
    if not os.path.exists(CORRECTIONS_LOG):
        return {"total": 0, "misclassifications": 0, "confusion_pairs": []}

    entries = []
    with open(CORRECTIONS_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    misclassifications = [e for e in entries if e.get("is_misclassification")]

    # Count confusion pairs: what did AI say → what should it have been
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
