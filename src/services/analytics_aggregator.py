"""
Analytics Aggregator Service
Reads JSONL log files and computes dashboard-ready aggregates.
"""
import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CLASSIFICATIONS_LOG = "logs/classifications.jsonl"
CORRECTIONS_LOG = "logs/corrections.jsonl"
TEMPLATE_USAGE_LOG = "logs/template_usage.jsonl"
API_USAGE_LOG = "logs/api_usage.jsonl"


def _read_jsonl(filepath: str, days: Optional[int] = None) -> List[Dict[str, Any]]:
    """Read a JSONL file and optionally filter by time range."""
    if not os.path.exists(filepath):
        return []

    cutoff = None
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

    entries = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if cutoff and entry.get("timestamp", "") < cutoff:
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def get_summary(days: Optional[int] = None) -> dict:
    """High-level metrics for dashboard header cards."""
    classifications = _read_jsonl(CLASSIFICATIONS_LOG, days)
    corrections = _read_jsonl(CORRECTIONS_LOG, days)
    templates = _read_jsonl(TEMPLATE_USAGE_LOG, days)

    total = len(classifications)
    errors = sum(1 for c in classifications if c.get("error"))
    successful = total - errors

    confidences = [c["confidence"] for c in classifications if c.get("confidence") is not None]
    times = [c["processing_time_seconds"] for c in classifications if c.get("processing_time_seconds") is not None]

    misclass = sum(1 for c in corrections if c.get("is_misclassification"))
    total_corrections = len(corrections)

    # Accuracy: if we have corrections, calculate from those
    # Otherwise report as N/A
    accuracy = None
    if total_corrections > 0:
        accuracy = round((total_corrections - misclass) / total_corrections * 100, 1)

    return {
        "total_classifications": total,
        "successful_classifications": successful,
        "accuracy_rate": accuracy,
        "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else None,
        "avg_processing_time_seconds": round(sum(times) / len(times), 2) if times else None,
        "total_corrections": total_corrections,
        "total_misclassifications": misclass,
        "templates_used": len(templates),
        "error_rate": round(errors / total * 100, 1) if total else 0,
    }


def get_classification_analytics(days: Optional[int] = None) -> dict:
    """Intent distribution, confidence stats, volume over time."""
    entries = _read_jsonl(CLASSIFICATIONS_LOG, days)
    successful = [e for e in entries if not e.get("error")]

    # Intent distribution
    intent_counts = defaultdict(int)
    for e in successful:
        intent_counts[e.get("intent", "unknown")] += 1

    total = len(successful)
    intent_dist = sorted(
        [{"intent": k, "count": v, "percentage": round(v / total * 100, 1) if total else 0}
         for k, v in intent_counts.items()],
        key=lambda x: x["count"], reverse=True
    )

    # Confidence by intent
    conf_by_intent = defaultdict(list)
    for e in successful:
        if e.get("confidence") is not None:
            conf_by_intent[e.get("intent", "unknown")].append(e["confidence"])

    confidence_stats = []
    for intent, confs in sorted(conf_by_intent.items()):
        confidence_stats.append({
            "intent": intent,
            "avg_confidence": round(sum(confs) / len(confs), 3),
            "min": round(min(confs), 3),
            "max": round(max(confs), 3),
            "count": len(confs),
        })

    # Volume over time (daily)
    daily_counts = defaultdict(int)
    for e in successful:
        date = e.get("timestamp", "")[:10]
        if date:
            daily_counts[date] += 1

    volume_over_time = [{"date": d, "count": c} for d, c in sorted(daily_counts.items())]

    # Complexity, urgency, language distributions
    complexity_dist = defaultdict(int)
    urgency_dist = defaultdict(int)
    language_dist = defaultdict(int)
    for e in successful:
        if e.get("complexity"):
            complexity_dist[e["complexity"]] += 1
        if e.get("urgency"):
            urgency_dist[e["urgency"]] += 1
        if e.get("language"):
            language_dist[e["language"]] += 1

    return {
        "intent_distribution": intent_dist,
        "confidence_by_intent": confidence_stats,
        "volume_over_time": volume_over_time,
        "complexity_distribution": dict(complexity_dist),
        "urgency_distribution": dict(urgency_dist),
        "language_distribution": dict(language_dist),
    }


def get_correction_analytics(days: Optional[int] = None) -> dict:
    """Confusion matrix, accuracy over time, top misclassification pairs."""
    entries = _read_jsonl(CORRECTIONS_LOG, days)

    misclassifications = [e for e in entries if e.get("is_misclassification")]

    # Confusion matrix
    matrix = defaultdict(lambda: defaultdict(int))
    for e in misclassifications:
        matrix[e["original_intent"]][e["corrected_intent"]] += 1

    # Convert to serializable dict
    confusion_matrix = {k: dict(v) for k, v in matrix.items()}

    # Top confusion pairs
    pair_counts = defaultdict(int)
    for e in misclassifications:
        pair_counts[(e["original_intent"], e["corrected_intent"])] += 1

    confusion_pairs = sorted(
        [{"original": k[0], "corrected": k[1], "count": v} for k, v in pair_counts.items()],
        key=lambda x: x["count"], reverse=True
    )

    # Accuracy over time (weekly)
    weekly = defaultdict(lambda: {"total": 0, "correct": 0})
    for e in entries:
        ts = e.get("timestamp", "")
        if len(ts) >= 10:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                week = dt.strftime("%Y-W%W")
                weekly[week]["total"] += 1
                if not e.get("is_misclassification"):
                    weekly[week]["correct"] += 1
            except (ValueError, TypeError):
                continue

    accuracy_over_time = []
    for week, data in sorted(weekly.items()):
        accuracy_over_time.append({
            "week": week,
            "total": data["total"],
            "correct": data["correct"],
            "accuracy": round(data["correct"] / data["total"] * 100, 1) if data["total"] else 0,
        })

    return {
        "total_corrections": len(entries),
        "misclassifications": len(misclassifications),
        "accuracy_rate": round((len(entries) - len(misclassifications)) / len(entries) * 100, 1) if entries else None,
        "confusion_matrix": confusion_matrix,
        "confusion_pairs": confusion_pairs,
        "accuracy_over_time": accuracy_over_time,
    }


def get_template_analytics(days: Optional[int] = None) -> dict:
    """Template usage by template and by intent."""
    entries = _read_jsonl(TEMPLATE_USAGE_LOG, days)

    # By template
    template_counts = defaultdict(int)
    for e in entries:
        template_counts[e.get("template_file", "unknown")] += 1

    total = len(entries)
    by_template = sorted(
        [{"template": k, "count": v, "percentage": round(v / total * 100, 1) if total else 0}
         for k, v in template_counts.items()],
        key=lambda x: x["count"], reverse=True
    )

    # By intent
    intent_template = defaultdict(lambda: defaultdict(int))
    for e in entries:
        intent_template[e.get("intent", "unknown")][e.get("template_file", "unknown")] += 1

    by_intent = []
    for intent, templates in sorted(intent_template.items()):
        by_intent.append({
            "intent": intent,
            "templates": sorted(
                [{"template": t, "count": c} for t, c in templates.items()],
                key=lambda x: x["count"], reverse=True
            )
        })

    # Usage over time (daily)
    daily = defaultdict(int)
    for e in entries:
        date = e.get("timestamp", "")[:10]
        if date:
            daily[date] += 1

    return {
        "total_uses": total,
        "by_template": by_template,
        "by_intent": by_intent,
        "usage_over_time": [{"date": d, "count": c} for d, c in sorted(daily.items())],
    }


def get_performance_analytics(days: Optional[int] = None) -> dict:
    """Processing time percentiles, error rates, tagging success."""
    entries = _read_jsonl(CLASSIFICATIONS_LOG, days)

    times = sorted([e["processing_time_seconds"] for e in entries if e.get("processing_time_seconds") is not None])
    total = len(entries)
    errors = [e for e in entries if e.get("error")]
    tagging_ok = sum(1 for e in entries if e.get("tagging_success"))

    def percentile(sorted_list, p):
        if not sorted_list:
            return None
        idx = int(len(sorted_list) * p / 100)
        idx = min(idx, len(sorted_list) - 1)
        return round(sorted_list[idx], 2)

    # Error breakdown
    error_types = defaultdict(int)
    for e in errors:
        err_msg = e.get("error", "Unknown")
        # Truncate long error messages to a category
        if "rate limit" in err_msg.lower() or "429" in err_msg:
            error_types["Rate limit (429)"] += 1
        elif "timeout" in err_msg.lower():
            error_types["Timeout"] += 1
        elif "zoho" in err_msg.lower():
            error_types["Zoho API error"] += 1
        else:
            error_types["Other"] += 1

    return {
        "processing_time": {
            "avg_seconds": round(sum(times) / len(times), 2) if times else None,
            "p50_seconds": percentile(times, 50),
            "p95_seconds": percentile(times, 95),
            "p99_seconds": percentile(times, 99),
            "max_seconds": round(max(times), 2) if times else None,
        },
        "total_processed": total,
        "total_errors": len(errors),
        "error_rate": round(len(errors) / total * 100, 1) if total else 0,
        "tagging_success_rate": round(tagging_ok / total * 100, 1) if total else 0,
        "errors_by_type": [{"error": k, "count": v} for k, v in sorted(error_types.items(), key=lambda x: x[1], reverse=True)],
    }


def get_entity_analytics(days: Optional[int] = None) -> dict:
    """Entity extraction rates by type and by intent."""
    entries = _read_jsonl(CLASSIFICATIONS_LOG, days)
    successful = [e for e in entries if not e.get("error") and e.get("entities")]

    entity_fields = ["license_plate", "move_out_date", "property_name", "amount"]

    # Overall extraction rates
    overall = {}
    for field in entity_fields:
        found = sum(1 for e in successful if e.get("entities", {}).get(field))
        total = len(successful)
        overall[field] = {
            "found": found,
            "missing": total - found,
            "rate": round(found / total * 100, 1) if total else 0,
        }

    # By intent
    by_intent = defaultdict(lambda: defaultdict(lambda: {"found": 0, "total": 0}))
    for e in successful:
        intent = e.get("intent", "unknown")
        for field in entity_fields:
            by_intent[intent][field]["total"] += 1
            if e.get("entities", {}).get(field):
                by_intent[intent][field]["found"] += 1

    by_intent_result = {}
    for intent, fields in by_intent.items():
        by_intent_result[intent] = {}
        for field, data in fields.items():
            by_intent_result[intent][field] = {
                "found": data["found"],
                "missing": data["total"] - data["found"],
                "rate": round(data["found"] / data["total"] * 100, 1) if data["total"] else 0,
            }

    return {
        "extraction_rates": overall,
        "by_intent": by_intent_result,
    }


def get_api_usage_analytics(days: Optional[int] = None) -> dict:
    """API usage stats: call counts, token usage, cost tracking."""
    entries = _read_jsonl(API_USAGE_LOG, days)

    openai_entries = [e for e in entries if e.get("provider") == "openai"]
    zoho_entries = [e for e in entries if e.get("provider") == "zoho"]

    total_calls = len(entries)
    total_openai_calls = len(openai_entries)
    total_zoho_calls = len(zoho_entries)

    total_prompt_tokens = sum(e.get("prompt_tokens", 0) or 0 for e in openai_entries)
    total_completion_tokens = sum(e.get("completion_tokens", 0) or 0 for e in openai_entries)
    total_tokens = sum(e.get("total_tokens", 0) or 0 for e in openai_entries)
    total_cost = sum(e.get("estimated_cost_usd", 0) or 0 for e in openai_entries)

    tickets_with_openai = set(e.get("ticket_id") for e in openai_entries if e.get("ticket_id"))
    avg_cost_per_ticket = round(total_cost / len(tickets_with_openai), 6) if tickets_with_openai else 0

    # Cost over time (daily)
    daily_cost = defaultdict(float)
    daily_calls = defaultdict(int)
    for e in openai_entries:
        date = e.get("timestamp", "")[:10]
        if date:
            daily_cost[date] += e.get("estimated_cost_usd", 0) or 0
            daily_calls[date] += 1

    cost_over_time = [
        {"date": d, "cost": round(c, 6), "calls": daily_calls[d]}
        for d, c in sorted(daily_cost.items())
    ]

    # API calls by type (prefixed with provider)
    call_type_counts = defaultdict(int)
    for e in entries:
        label = e.get("provider", "unknown") + ":" + e.get("call_type", "unknown")
        call_type_counts[label] += 1

    calls_by_type = sorted(
        [{"call_type": k, "count": v} for k, v in call_type_counts.items()],
        key=lambda x: x["count"], reverse=True
    )

    # Zoho call distribution
    zoho_type_counts = defaultdict(int)
    for e in zoho_entries:
        zoho_type_counts[e.get("call_type", "unknown")] += 1

    zoho_distribution = sorted(
        [{"call_type": k, "count": v} for k, v in zoho_type_counts.items()],
        key=lambda x: x["count"], reverse=True
    )

    # Error rate
    failed = sum(1 for e in entries if not e.get("success", True))

    return {
        "total_api_calls": total_calls,
        "total_openai_calls": total_openai_calls,
        "total_zoho_calls": total_zoho_calls,
        "total_cost_usd": round(total_cost, 4),
        "avg_cost_per_ticket": round(avg_cost_per_ticket, 6),
        "token_breakdown": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
        },
        "cost_over_time": cost_over_time,
        "calls_by_type": calls_by_type,
        "zoho_distribution": zoho_distribution,
        "failed_calls": failed,
        "error_rate": round(failed / total_calls * 100, 1) if total_calls else 0,
    }
