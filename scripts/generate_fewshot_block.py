"""
Generate the few-shot example block to inject into the classifier prompt.
Reads corrected_tickets.json, outputs the formatted text to stdout.
"""
import json
import re
from pathlib import Path

# Concise "lesson" phrasing for each pattern the 31 tickets surface.
# Keyed by (ai_tag, correct_tag) — if missing, fall back to generic.
LESSON_MAP = {
    ("Customer Update Vehicle Info", "Customer Canceling a Permit and Refunding"):
        '"moved out / remove plate from billing" is cancel+refund, not plate-update.',
    ("Customer Update Contact Info", "Customer Canceling a Permit and Refunding"):
        '"no longer live here / stop billing me" is cancel+refund, not contact-update.',
    ("Customer Double Charged or Extra Charges", "Customer Canceling a Permit and Refunding"):
        '"moved out, stop charging me, refund" is cancel+refund, not a double-charge dispute.',
    ("Customer Double Charged or Extra Charges", "Customer Need Help Renewing Permit"):
        'Confusion about a renewal reminder ≠ double charge. Customer sees an existing payment and a renewal notice.',
    ("Customer Double Charged or Extra Charges", "Customer Inquiring for Grandfathered Permit"):
        'Billing question tied to a grandfathered-permit context is its own tag.',
    ("Customer Double Charged or Extra Charges", "Customer Payment Help"):
        'Payment failure / method issue is Payment Help — NOT double charge.',
    ("Customer Miscellaneous Questions", "Customer Need help buying a permit"):
        'First-time buyer ("purchased but no confirmation", "just moved in, how do I permit") = Need Help Buying.',
    ("Customer Miscellaneous Questions", "Customer Payment Help"):
        'Any payment-method or billing question → Payment Help, not Miscellaneous.',
    ("Customer Miscellaneous Questions", "Customer Need Help Renewing Permit"):
        'Existing-customer renewal confusion → Renewing, not Miscellaneous.',
    ("Customer Towed Booted Ticketed", "Customer Need help buying a permit"):
        '"Towed because I didn\'t have a permit, help me get one" = Need Help Buying, NOT Towed. Tow/boot is a PAST event; the asked-for resolution is buying.',
    ("Customer Towed Booted Ticketed", "Customer Guest Permit and Pricing Questions"):
        'Tow involving a guest vehicle → Guest Permit Questions.',
    ("Customer Towed Booted Ticketed", "Property Checking if a Vehicle is Permitted"):
        'Property asking about a vehicle + tow context → Property Checking if Vehicle is Permitted, not Customer Towed.',
    ("Customer Parking Space Not in Dropdown", "Customer Miscellaneous Questions"):
        'Reserve "Space Not in Dropdown" for actual missing-space signups; general questions → Miscellaneous.',
    ("Customer Parking Space Not in Dropdown", "Customer Need help buying a permit"):
        'New resident not finding their space in the signup dropdown is "Need Help Buying" — the space-dropdown tag is rare.',
    ("Customer Update Vehicle Info", "Customer Payment Help"):
        'Payment-method issues are Payment Help even if the email also mentions vehicle details.',
    ("Customer Update Vehicle Info", "Customer Inquiring for Locked Down Permit"):
        '"My permit stopped working / shows sold out" signals community lockdown, not a vehicle-info update.',
    ("Customer Update Vehicle Info", "Customer Need help buying a permit"):
        '"I have a new car and need a permit" from a first-time buyer = Need Help Buying.',
    ("Property Update Resident Vehicle", "Customer Rental Car"):
        'Rental car replacement on a resident permit is "Customer Rental Car", distinct from routine property updates.',
    ("Property Permitting PAID Resident Vehicle for Them", "Property Update Resident Contact Information"):
        'Property correcting a resident\'s email/phone/address → Update Resident Contact, not Permitting Vehicle.',
    ("Property Permitting PAID Resident Vehicle for Them", "Property Changing Resident Type for Approved Permit"):
        'Changing resident TYPE (tenant → owner etc.) on an approved permit is its own tag.',
    ("Customer Inquiring for Additional Permit", "Customer Inquiring for Locked Down Permit"):
        '"Can\'t buy a second permit" usually = Locked Down (community cap), NOT Additional Permit which implies they\'re allowed another.',
    ("Customer Need help buying a permit", "Customer Inquiring for Locked Down Permit"):
        'First-time-buyer who is blocked by a community cap/lockdown → Locked Down, not Need Help Buying.',
    ("Needs Tag", "Customer Need help buying a permit"):
        'Don\'t default to Needs Tag when a concrete "I want to buy a permit" signal is present — even if sparse.',
    ("Needs Tag", "Customer Miscellaneous Questions"):
        'Short / sparse emails with a question but no specific category → Miscellaneous, not Needs Tag. Reserve Needs Tag for unintelligible content.',
    ("Sales Rep Asking for a Vehicle to be Released", "Needs Tag"):
        'Only use Sales Rep tags when the SENDER is a ParkM sales rep and the content matches. Otherwise → Needs Tag.',
    ("Property Miscellaneous Questions", "Property Cancel Resident Account"):
        'Property asking to close/remove a resident account → Property Cancel Resident Account, not Miscellaneous.',
    ("Customer Update Contact Info", "Customer Canceling a Permit and Refunding"):
        '"Stop emailing me, I moved" with billing context = cancel+refund, not contact-update.',
}


def truncate(text: str, n: int = 300) -> str:
    text = text or ""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > n:
        text = text[:n].rsplit(" ", 1)[0] + "..."
    return text


def build_block():
    data = json.load(open("corrected_tickets.json"))
    lines = [
        "CORRECTED EXAMPLES — 31 real misclassifications from human review. Match these patterns:",
        "",
    ]
    for i, d in enumerate(data, 1):
        subject = (d.get("subject") or "").strip()
        body = truncate(d.get("description"), 300)
        ai = d["ai_tag"]
        correct = d["correct_tag"]
        lesson = LESSON_MAP.get((ai, correct)) or f"AI picked {ai!r}, correct is {correct!r}."
        lines.append(f'[{i}] Subject: "{subject}"')
        if body:
            lines.append(f'    Body: "{body}"')
        lines.append(f"    → correct: {correct} (NOT {ai})")
        lines.append(f"    Lesson: {lesson}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(build_block())
