#!/usr/bin/env python3
"""
Phase 1.3 — Batch Classification Testing
Pulls tickets from Zoho Desk, classifies each one, and generates an analysis report.

Usage:
    python batch_test.py                    # Test all sandbox tickets
    python batch_test.py --limit 50         # Limit number of tickets
    python batch_test.py --synthetic        # Also run synthetic edge cases
"""
import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter, defaultdict
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.classifier import EmailClassifier
from src.api.zoho_client import ZohoDeskClient


# ── Synthetic edge-case emails (ParkM-specific) ─────────────────────────────
SYNTHETIC_EMAILS = [
    # 1. Refund + cancel combo (multi-intent)
    {
        "subject": "Cancel permit and refund",
        "body": "I want to cancel my permit and get a refund. I moved out February 1st. Plate XYZ-9876.",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.80, 1.0),
        "tag": "multi-intent",
    },
    # 2. Vague one-liner
    {
        "subject": "Help",
        "body": "I need help with my account",
        "expected_intent": "unclear",
        "expected_confidence_range": (0.35, 0.60),
        "tag": "vague",
    },
    # 3. Spanish refund request
    {
        "subject": "Reembolso",
        "body": "Hola, me mude el 15 de enero y me cobraron el 20 de enero. Mi placa es ABC-1234. Necesito un reembolso por favor.",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.80, 1.0),
        "tag": "spanish",
    },
    # 4. Angry customer with legal threat
    {
        "subject": "UNAUTHORIZED CHARGE - LEGAL ACTION",
        "body": "You charged my card $45 without authorization! I moved out 3 months ago and you're STILL charging me! I'm going to file a complaint with the BBB and my attorney if this isn't refunded immediately!!! This is FRAUD!",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.85, 1.0),
        "tag": "angry-legal-threat",
    },
    # 5. Permit cancellation without refund mention
    {
        "subject": "Cancel parking permit",
        "body": "Hi, I'd like to cancel my parking permit effective immediately. I no longer need it. Plate: DEF-5678.",
        "expected_intent": "permit_cancellation",
        "expected_confidence_range": (0.85, 1.0),
        "tag": "cancel-no-refund",
    },
    # 6. Ambiguous cancel vs refund
    {
        "subject": "Moving out",
        "body": "I'm moving out next month. What do I need to do about my parking permit?",
        "expected_intent": "move_out",
        "expected_confidence_range": (0.60, 0.85),
        "tag": "ambiguous-cancel-refund",
    },
    # 7. Multiple vehicles / complex account update
    {
        "subject": "Update vehicles on my account",
        "body": "I need to remove my old car (plate AAA-1111) and add two new vehicles. New plates are BBB-2222 and CCC-3333. Also my apartment number changed from 204 to 308.",
        "expected_intent": "account_update",
        "expected_confidence_range": (0.80, 1.0),
        "tag": "multi-vehicle-complex",
    },
    # 8. Payment failed — can't tell if it's technical or billing
    {
        "subject": "Payment not going through",
        "body": "I've been trying to pay for my parking permit but the payment keeps failing. I've tried three different cards. Can someone help?",
        "expected_intent": "payment_issue",
        "expected_confidence_range": (0.60, 0.85),
        "tag": "payment-vs-technical",
    },
    # 9. Completely off-topic
    {
        "subject": "Pizza delivery",
        "body": "Hi, I'd like to order a large pepperoni pizza for delivery to unit 305. Thanks!",
        "expected_intent": "unclear",
        "expected_confidence_range": (0.30, 0.60),
        "tag": "off-topic",
    },
    # 10. Date in unusual format
    {
        "subject": "Refund for February",
        "body": "I moved out on the 25th of February and was charged on 2/28. Plate GHI-7890. Please refund.",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.80, 1.0),
        "tag": "date-format-edge",
    },
    # 11. Mixed language (Spanglish)
    {
        "subject": "Refund por favor",
        "body": "Hi, necesito un refund because I already moved out on January 15. My plate es JKL-4567. Gracias!",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.75, 1.0),
        "tag": "mixed-language",
    },
    # 12. Long rambling email with buried intent
    {
        "subject": "Question about my account",
        "body": """Hi there, I hope this email finds you well. I've been a resident at Oakwood Apartments
for about 3 years now and have always had a good experience with the parking. However, last month
my wife's car broke down and we had to get a new one. The old car was a blue Honda Civic with plate
MNO-1234 and the new one is a red Toyota Camry with plate PQR-5678. I was wondering if you could
update my account to reflect the new vehicle. Also, I noticed that I was charged twice in January,
once on the 1st and once on the 15th. Is that normal? I thought the permit was monthly. Anyway,
please update the vehicle info when you get a chance. Thanks so much!""",
        "expected_intent": "account_update",
        "expected_confidence_range": (0.60, 0.85),
        "tag": "rambling-multi-issue",
    },
    # 13. Technical issue - app login
    {
        "subject": "Can't log in to parkm app",
        "body": "I keep getting an error when I try to log in to the parkm.app website. It says 'invalid credentials' but I know my password is correct. I've tried resetting it twice.",
        "expected_intent": "technical_issue",
        "expected_confidence_range": (0.85, 1.0),
        "tag": "technical-login",
    },
    # 14. Permit inquiry about pricing
    {
        "subject": "Parking permit cost",
        "body": "How much does a monthly parking permit cost at Riverside Commons? Do you have any visitor passes available?",
        "expected_intent": "permit_inquiry",
        "expected_confidence_range": (0.85, 1.0),
        "tag": "pricing-inquiry",
    },
    # 15. Refund request missing all entities
    {
        "subject": "I want my money back",
        "body": "Give me a refund. I already moved out.",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.60, 0.80),
        "tag": "refund-no-entities",
    },
    # 16. Forward / reply chain (noisy email)
    {
        "subject": "RE: RE: FWD: Parking Permit Issue",
        "body": """---------- Forwarded message ----------
From: jane@example.com
Date: Feb 10, 2026

Hi, I originally emailed about canceling my permit back in January but never heard back.
My plate is STU-9012 and I moved out on January 5th. I need this resolved ASAP.

> On Jan 5, 2026, parking@parkm.com wrote:
> Thank you for contacting ParkM support. We'll get back to you within 24 hours.
""",
        "expected_intent": "permit_cancellation",
        "expected_confidence_range": (0.65, 0.90),
        "tag": "noisy-reply-chain",
    },
    # 17. Resident asking on behalf of someone else
    {
        "subject": "My mom's parking permit",
        "body": "Hi, my mother lives at unit 412 and she doesn't know how to use email. She wants to cancel her parking permit. Her plate is VWX-3456. She moved out last week.",
        "expected_intent": "permit_cancellation",
        "expected_confidence_range": (0.70, 0.90),
        "tag": "third-party",
    },
    # 18. Dispute — claims they never signed up (asks for reversal = refund)
    {
        "subject": "I never signed up for parking",
        "body": "I just noticed a $35 charge from ParkM on my credit card statement. I never signed up for any parking permit. This is an unauthorized charge and I want it reversed immediately.",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.75, 0.95),
        "tag": "unauthorized-charge",
    },
    # 19. Move-out with future date + explicit cancel request
    {
        "subject": "Moving out next month",
        "body": "Hi, I will be moving out of my apartment on March 15th, 2026. I want to make sure my parking permit is canceled on that date so I don't get charged again. My plate is YZA-7890.",
        "expected_intent": "permit_cancellation",
        "expected_confidence_range": (0.85, 1.0),
        "tag": "future-move-out",
    },
    # 20. Empty body
    {
        "subject": "Refund",
        "body": "",
        "expected_intent": "refund_request",
        "expected_confidence_range": (0.35, 0.65),
        "tag": "empty-body",
    },
]


async def fetch_zoho_tickets(limit: int = 100) -> List[Dict[str, Any]]:
    """Pull tickets from Zoho Desk using the list endpoint (not search)."""
    client = ZohoDeskClient()
    headers = await client._build_headers()

    all_tickets = []
    offset = 0
    page_size = min(limit, 100)  # Zoho max per page is 100

    import httpx
    async with httpx.AsyncClient() as http:
        while len(all_tickets) < limit:
            response = await http.get(
                f"{client.base_url}/tickets",
                headers=headers,
                params={
                    "limit": page_size,
                    "from": offset,
                    "sortBy": "createdTime",
                    "include": "contacts",
                },
            )
            if response.status_code == 204:
                # No more tickets
                break
            response.raise_for_status()
            data = response.json().get("data", [])
            if not data:
                break
            all_tickets.extend(data)
            offset += len(data)
            if len(data) < page_size:
                break

    return all_tickets[:limit]


def classify_single(classifier: EmailClassifier, subject: str, body: str) -> Dict[str, Any]:
    """Classify a single email and return result."""
    try:
        return classifier.classify_email(subject, body)
    except Exception as e:
        return {"error": str(e)}


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze batch classification results and identify edge cases."""
    intent_counts = Counter()
    complexity_counts = Counter()
    language_counts = Counter()
    urgency_counts = Counter()
    confidence_buckets = {"high (0.90+)": 0, "good (0.75-0.89)": 0, "medium (0.60-0.74)": 0, "low (<0.60)": 0}
    low_confidence = []
    human_review_needed = []
    entity_extraction = {"license_plate": 0, "move_out_date": 0, "property_name": 0, "amount": 0}
    errors = []

    for r in results:
        cls = r.get("classification", {})
        if "error" in cls:
            errors.append(r)
            continue

        intent = cls.get("intent", "unknown")
        intent_counts[intent] += 1
        complexity_counts[cls.get("complexity", "unknown")] += 1
        language_counts[cls.get("language", "unknown")] += 1
        urgency_counts[cls.get("urgency", "unknown")] += 1

        conf = cls.get("confidence", 0)
        if conf >= 0.90:
            confidence_buckets["high (0.90+)"] += 1
        elif conf >= 0.75:
            confidence_buckets["good (0.75-0.89)"] += 1
        elif conf >= 0.60:
            confidence_buckets["medium (0.60-0.74)"] += 1
        else:
            confidence_buckets["low (<0.60)"] += 1

        if conf < 0.70:
            low_confidence.append({
                "subject": r.get("subject", ""),
                "intent": intent,
                "confidence": conf,
                "notes": cls.get("notes", ""),
                "tag": r.get("tag", ""),
            })

        if cls.get("requires_human_review"):
            human_review_needed.append({
                "subject": r.get("subject", ""),
                "intent": intent,
                "confidence": conf,
            })

        entities = cls.get("key_entities", {})
        for key in entity_extraction:
            if entities.get(key):
                entity_extraction[key] += 1

    return {
        "total": len(results),
        "errors": len(errors),
        "intent_distribution": dict(intent_counts.most_common()),
        "complexity_distribution": dict(complexity_counts.most_common()),
        "language_distribution": dict(language_counts.most_common()),
        "urgency_distribution": dict(urgency_counts.most_common()),
        "confidence_buckets": confidence_buckets,
        "low_confidence_tickets": low_confidence,
        "human_review_flagged": human_review_needed,
        "entity_extraction_counts": entity_extraction,
        "error_details": [{"subject": e.get("subject"), "error": e["classification"].get("error")} for e in errors],
    }


def check_synthetic_accuracy(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Check synthetic emails against expected results."""
    correct = 0
    wrong = []
    confidence_misses = []

    for r in results:
        cls = r.get("classification", {})
        if "error" in cls:
            wrong.append({"tag": r.get("tag"), "error": cls["error"]})
            continue

        expected_intent = r.get("expected_intent")
        actual_intent = cls.get("intent")
        conf = cls.get("confidence", 0)
        expected_range = r.get("expected_confidence_range", (0, 1))

        intent_match = actual_intent == expected_intent
        conf_in_range = expected_range[0] <= conf <= expected_range[1]

        if intent_match:
            correct += 1
        else:
            wrong.append({
                "tag": r.get("tag"),
                "subject": r.get("subject"),
                "expected": expected_intent,
                "got": actual_intent,
                "confidence": conf,
                "notes": cls.get("notes", ""),
            })

        if not conf_in_range:
            confidence_misses.append({
                "tag": r.get("tag"),
                "expected_range": f"{expected_range[0]:.2f}-{expected_range[1]:.2f}",
                "actual": f"{conf:.2f}",
                "intent": actual_intent,
            })

    return {
        "total": len(results),
        "correct_intent": correct,
        "accuracy": f"{correct / len(results) * 100:.1f}%" if results else "N/A",
        "wrong_intents": wrong,
        "confidence_misses": confidence_misses,
    }


async def main():
    parser = argparse.ArgumentParser(description="Phase 1.3 — Batch Classification Testing")
    parser.add_argument("--limit", type=int, default=100, help="Max Zoho tickets to pull")
    parser.add_argument("--synthetic", action="store_true", help="Also run synthetic edge cases")
    parser.add_argument("--synthetic-only", action="store_true", help="Only run synthetic edge cases")
    parser.add_argument("--output", type=str, default="batch_test_results.json", help="Output file")
    args = parser.parse_args()

    classifier = EmailClassifier()
    report = {"timestamp": datetime.now().isoformat(), "zoho_results": None, "synthetic_results": None}

    # ── Zoho tickets ─────────────────────────────────────────────────────
    if not args.synthetic_only:
        print("=" * 70)
        print("Phase 1.3 — Batch Classification Testing")
        print("=" * 70)
        print(f"\n1. Fetching tickets from Zoho Desk (limit={args.limit})...")

        tickets = await fetch_zoho_tickets(args.limit)
        print(f"   Pulled {len(tickets)} tickets")

        print(f"\n2. Classifying {len(tickets)} tickets with AI...")
        zoho_results = []
        for i, ticket in enumerate(tickets):
            subject = ticket.get("subject", "")
            description = ticket.get("description", "")
            ticket_id = ticket.get("id", "")
            ticket_number = ticket.get("ticketNumber", "")

            # Strip HTML from description
            import re
            description_text = re.sub(r"<[^>]+>", " ", description) if description else ""

            result = classify_single(classifier, subject, description_text)
            zoho_results.append({
                "ticket_id": ticket_id,
                "ticket_number": ticket_number,
                "subject": subject,
                "classification": result,
            })

            conf = result.get("confidence", 0)
            intent = result.get("intent", "err")
            marker = "!" if conf < 0.70 else " "
            print(f"   [{i+1:3d}/{len(tickets)}]{marker} #{ticket_number} — {intent} ({conf:.0%}) — {subject[:50]}")

        analysis = analyze_results(zoho_results)
        report["zoho_results"] = {"tickets": zoho_results, "analysis": analysis}

        print(f"\n3. Zoho Analysis:")
        print(f"   Total classified: {analysis['total']}")
        print(f"   Errors: {analysis['errors']}")
        print(f"\n   Intent distribution:")
        for intent, count in analysis["intent_distribution"].items():
            print(f"     {intent}: {count}")
        print(f"\n   Confidence distribution:")
        for bucket, count in analysis["confidence_buckets"].items():
            print(f"     {bucket}: {count}")
        if analysis["low_confidence_tickets"]:
            print(f"\n   Low confidence tickets ({len(analysis['low_confidence_tickets'])}):")
            for t in analysis["low_confidence_tickets"]:
                print(f"     - [{t['confidence']:.0%}] {t['intent']} — {t['subject'][:50]}")
                if t.get("notes"):
                    print(f"       Notes: {t['notes']}")

    # ── Synthetic edge cases ─────────────────────────────────────────────
    if args.synthetic or args.synthetic_only:
        print(f"\n{'=' * 70}")
        print("Synthetic Edge Case Testing")
        print("=" * 70)
        print(f"\nRunning {len(SYNTHETIC_EMAILS)} synthetic emails...")

        synthetic_results = []
        for i, email in enumerate(SYNTHETIC_EMAILS):
            result = classify_single(classifier, email["subject"], email["body"])
            synthetic_results.append({
                "tag": email["tag"],
                "subject": email["subject"],
                "expected_intent": email["expected_intent"],
                "expected_confidence_range": email["expected_confidence_range"],
                "classification": result,
            })

            conf = result.get("confidence", 0)
            intent = result.get("intent", "err")
            expected = email["expected_intent"]
            match = "OK" if intent == expected else "MISS"
            print(f"   [{i+1:3d}/{len(SYNTHETIC_EMAILS)}] {match:4s} [{email['tag']}] — got {intent} (expected {expected}) conf={conf:.0%}")

        accuracy = check_synthetic_accuracy(synthetic_results)
        report["synthetic_results"] = {"emails": synthetic_results, "accuracy": accuracy}

        print(f"\n   Accuracy: {accuracy['accuracy']}")
        if accuracy["wrong_intents"]:
            print(f"\n   Wrong intents ({len(accuracy['wrong_intents'])}):")
            for w in accuracy["wrong_intents"]:
                print(f"     - [{w.get('tag')}] Expected {w.get('expected')}, got {w.get('got')} (conf={w.get('confidence', 0):.0%})")
                if w.get("notes"):
                    print(f"       Notes: {w['notes']}")
        if accuracy["confidence_misses"]:
            print(f"\n   Confidence out of expected range ({len(accuracy['confidence_misses'])}):")
            for c in accuracy["confidence_misses"]:
                print(f"     - [{c['tag']}] Expected {c['expected_range']}, got {c['actual']} (intent: {c['intent']})")

    # ── Save full report ─────────────────────────────────────────────────
    # Make results JSON-serializable (convert tuples)
    def make_serializable(obj):
        if isinstance(obj, tuple):
            return list(obj)
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [make_serializable(i) for i in obj]
        return obj

    report = make_serializable(report)

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
