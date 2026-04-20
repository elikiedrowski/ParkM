"""
Sanity-check validation: re-classify the 31 corrected tickets with the new
prompt and report accuracy.

NOTE: This is a sanity check — the tickets themselves appear verbatim in the
prompt as few-shots, so high accuracy here just proves the prompt is loaded
correctly. True generalization is measured on a fresh test batch (task F).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.services.classifier import EmailClassifier


def main():
    data = json.load(open("corrected_tickets.json"))
    classifier = EmailClassifier()
    results = []
    matches = 0
    for i, t in enumerate(data, 1):
        subject = t["subject"]
        body = t["description"] or ""
        expected = t["correct_tag"]
        from_email = t.get("from_email", "")
        try:
            result = classifier.classify_email(subject, body, from_email, ticket_id=f"validate_{t['sandbox_ticket_number']}")
            got_tags = result.get("tags", [])
            got_primary = got_tags[0] if got_tags else "None"
            match = expected in got_tags
            if match:
                matches += 1
            results.append({
                "sandbox_ticket_number": t["sandbox_ticket_number"],
                "subject": subject,
                "expected": expected,
                "got_tags": got_tags,
                "match": match,
            })
            mark = "✓" if match else "✗"
            print(f"[{i:2d}/31] {mark} #{t['sandbox_ticket_number']} expected={expected!r} got={got_tags}")
        except Exception as e:
            print(f"[{i:2d}/31] ERR #{t['sandbox_ticket_number']}: {e}")
            results.append({
                "sandbox_ticket_number": t["sandbox_ticket_number"],
                "subject": subject,
                "expected": expected,
                "error": str(e),
                "match": False,
            })

    print(f"\n=== Accuracy: {matches}/{len(data)} = {matches/len(data)*100:.1f}% ===")
    Path("validate_results.json").write_text(json.dumps(results, indent=2))
    misses = [r for r in results if not r.get("match")]
    if misses:
        print("\nMisses:")
        for r in misses:
            print(f"  #{r['sandbox_ticket_number']}: expected={r['expected']!r} got={r.get('got_tags') or 'ERR'}")


if __name__ == "__main__":
    main()
