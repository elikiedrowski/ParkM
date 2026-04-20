"""
Append 'survey link has been sent' to every 'Closed' status suggestion
across all wizard_content.json tags. (Task A1 from Apr 16 feedback.)

Matches any suggestion whose text starts with either:
  - Closed (...
  - 'Closed' (...
And inserts ", survey link has been sent" before the final ").".
"""
import json
import re
from pathlib import Path

SUFFIX = ", survey link has been sent"


def patch_suggestion(s: str) -> tuple[str, bool]:
    # Already has the suffix — skip
    if "survey link has been sent" in s.lower():
        return s, False
    # Must start with Closed or 'Closed'
    if not (s.startswith("Closed ") or s.startswith("Closed(") or s.startswith("'Closed'") or s.startswith('"Closed"')):
        return s, False
    # Find the last ")." and insert suffix before it
    m = re.search(r"\)\.\s*$", s)
    if not m:
        return s, False
    insert_at = m.start()
    patched = s[:insert_at] + SUFFIX + s[insert_at:]
    return patched, True


def main():
    path = Path("src/wizard/wizard_content.json")
    data = json.loads(path.read_text())
    changed_tags = []
    for tag_key, tag_val in data.items():
        if tag_key.startswith("_"):
            continue
        for step in tag_val.get("steps", []):
            suggestions = step.get("suggestions", [])
            for i, s in enumerate(suggestions):
                patched, did = patch_suggestion(s)
                if did:
                    suggestions[i] = patched
                    changed_tags.append((tag_key, s, patched))
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Patched {len(changed_tags)} Closed suggestions across tags:")
    seen = set()
    for k, orig, new in changed_tags:
        if k not in seen:
            print(f"  {k}")
            seen.add(k)
    print(f"\nUnique tags patched: {len(seen)}")


if __name__ == "__main__":
    main()
