"""
Build classifier few-shot examples from Sadie's 31 mistagged tickets.

Joins:
  - Sandbox ticket # (Sadie's review identifies #72211 etc.)
  - sandbox_import_map.json → original production ticket # (e.g. 59218)
  - production_tickets.json → subject + description for that original

Output: corrected_tickets.json with ai_tag, correct_tag, subject, description.
"""
import json
import re
from pathlib import Path

CORRECTIONS = [
    ("72211", "Customer Miscellaneous Questions", "Customer Need help buying a permit"),
    ("72405", "Customer Update Vehicle Info", "Customer Canceling a Permit and Refunding"),
    ("72395", "Customer Update Contact Info", "Customer Canceling a Permit and Refunding"),
    ("72385", "Needs Tag", "Customer Need help buying a permit"),
    ("72378", "Customer Double Charged or Extra Charges", "Customer Need Help Renewing Permit"),
    ("72370", "Customer Update Vehicle Info", "Customer Payment Help"),
    ("72368", "Customer Update Vehicle Info", "Customer Inquiring for Locked Down Permit"),
    ("72356", "Customer Double Charged or Extra Charges", "Customer Inquiring for Grandfathered Permit"),
    ("72341", "Property Update Resident Vehicle", "Customer Rental Car"),
    ("72338", "Customer Double Charged or Extra Charges", "Customer Canceling a Permit and Refunding"),
    ("72326", "Property Permitting PAID Resident Vehicle for Them", "Property Update Resident Contact Information"),
    ("72319", "Property Permitting PAID Resident Vehicle for Them", "Property Changing Resident Type for Approved Permit"),
    ("72301", "Customer Inquiring for Additional Permit", "Customer Inquiring for Locked Down Permit"),
    ("72298", "Customer Parking Space Not in Dropdown", "Customer Miscellaneous Questions"),
    ("72296", "Customer Towed Booted Ticketed", "Property Checking if a Vehicle is Permitted"),
    ("72213", "Customer Miscellaneous Questions", "Customer Payment Help"),
    ("72218", "Customer Towed Booted Ticketed", "Customer Need help buying a permit"),
    ("72244", "Customer Towed Booted Ticketed", "Customer Guest Permit and Pricing Questions"),
    ("72249", "Customer Update Contact Info", "Customer Canceling a Permit and Refunding"),
    ("72253", "Customer Parking Space Not in Dropdown", "Customer Need help buying a permit"),
    ("72256", "Customer Update Contact Info", "Customer Canceling a Permit and Refunding"),
    ("72264", "Customer Update Vehicle Info", "Customer Canceling a Permit and Refunding"),
    ("72267", "Customer Miscellaneous Questions", "Customer Need help buying a permit"),
    ("72268", "Customer Double Charged or Extra Charges", "Customer Canceling a Permit and Refunding"),
    ("72272", "Sales Rep Asking for a Vehicle to be Released", "Needs Tag"),
    ("72276", "Needs Tag", "Customer Miscellaneous Questions"),
    ("72281", "Customer Need help buying a permit", "Customer Inquiring for Locked Down Permit"),
    ("72283", "Customer Update Vehicle Info", "Customer Need help buying a permit"),
    ("72288", "Customer Miscellaneous Questions", "Customer Need Help Renewing Permit"),
    ("72291", "Property Miscellaneous Questions", "Property Cancel Resident Account"),
    ("72294", "Customer Double Charged or Extra Charges", "Customer Payment Help"),
]


def strip_html(s: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"&lt;", "<", s)
    s = re.sub(r"&gt;", ">", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main():
    sandbox_map = json.load(open("sandbox_import_map.json"))["results"]
    sandbox_to_original = {r["ticket_number"]: r["original"] for r in sandbox_map}

    prod = json.load(open("production_tickets.json"))
    prod_by_num = {str(t["ticketNumber"]): t for t in prod}

    # batch_test_enriched.json has the full first_message body (production_tickets has null description)
    enriched = json.load(open("batch_test_enriched.json"))
    enriched_by_num = {str(t["original_ticket_number"]): t for t in enriched}

    out = []
    for sandbox_num, ai_tag, correct_tag in CORRECTIONS:
        original_num = sandbox_to_original.get(sandbox_num)
        if not original_num:
            print(f"#{sandbox_num}: no sandbox→original mapping")
            out.append({
                "sandbox_ticket_number": sandbox_num,
                "original_ticket_number": None,
                "ai_tag": ai_tag,
                "correct_tag": correct_tag,
                "subject": None,
                "description": None,
                "from_email": None,
            })
            continue
        prod_ticket = prod_by_num.get(str(original_num))
        if not prod_ticket:
            print(f"#{sandbox_num} (orig #{original_num}): not in production_tickets.json")
            out.append({
                "sandbox_ticket_number": sandbox_num,
                "original_ticket_number": original_num,
                "ai_tag": ai_tag,
                "correct_tag": correct_tag,
                "subject": None,
                "description": None,
                "from_email": None,
            })
            continue
        enriched_ticket = enriched_by_num.get(str(original_num), {})
        body = enriched_ticket.get("first_message") or prod_ticket.get("description") or ""
        out.append({
            "sandbox_ticket_number": sandbox_num,
            "original_ticket_number": original_num,
            "ai_tag": ai_tag,
            "correct_tag": correct_tag,
            "subject": prod_ticket.get("subject", ""),
            "description": strip_html(body)[:1500],
            "from_email": prod_ticket.get("email", ""),
        })

    Path("corrected_tickets.json").write_text(json.dumps(out, indent=2))
    found = sum(1 for x in out if x.get("subject"))
    print(f"\nResolved {found}/{len(out)} tickets → corrected_tickets.json")
    if found < len(out):
        print("Missing originals:", [x["sandbox_ticket_number"] for x in out if not x.get("subject")])


if __name__ == "__main__":
    main()
