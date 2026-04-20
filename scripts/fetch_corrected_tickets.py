"""
Fetch the 31 mistagged production tickets identified by Sadie's Apr 16 review.
Uses /tickets list endpoint (no search scope needed) — paginates until all
target ticket numbers are found.

Output → corrected_tickets.json for use as classifier few-shot examples.
"""
import asyncio
import json
import os
from pathlib import Path

import httpx

PRODUCTION_ORG_ID = "854251057"
PRODUCTION_REFRESH_TOKEN = Path(".production_refresh_token").read_text().strip()

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

TARGET_NUMBERS = {tn for tn, _, _ in CORRECTIONS}
CORRECTION_LOOKUP = {tn: (ai, correct) for tn, ai, correct in CORRECTIONS}


async def get_access_token() -> str:
    client_id = os.environ["ZOHO_CLIENT_ID"]
    client_secret = os.environ["ZOHO_CLIENT_SECRET"]
    data_center = os.environ.get("ZOHO_DATA_CENTER", "com")
    url = f"https://accounts.zoho.{data_center}/oauth/v2/token"
    async with httpx.AsyncClient() as c:
        r = await c.post(url, data={
            "refresh_token": PRODUCTION_REFRESH_TOKEN,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        })
        r.raise_for_status()
        return r.json()["access_token"]


async def list_tickets(client: httpx.AsyncClient, headers: dict, from_idx: int, limit: int = 100) -> list:
    base = os.environ.get("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
    r = await client.get(f"{base}/tickets", headers=headers, params={
        "from": from_idx,
        "limit": limit,
        "sortBy": "-createdTime",
        "fields": "id,ticketNumber,subject,description,email,createdTime",
    })
    if r.status_code != 200:
        print(f"  list failed: {r.status_code} {r.text[:200]}")
        return []
    return r.json().get("data", [])


async def get_ticket_full(client: httpx.AsyncClient, headers: dict, ticket_id: str) -> dict | None:
    base = os.environ.get("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
    r = await client.get(f"{base}/tickets/{ticket_id}", headers=headers)
    if r.status_code != 200:
        return None
    return r.json()


async def main():
    os.environ["ZOHO_ORG_ID"] = PRODUCTION_ORG_ID
    token = await get_access_token()
    print(f"Got production access token (length {len(token)})")
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "orgId": PRODUCTION_ORG_ID,
    }

    found_tickets = {}  # ticket_number → ticket dict
    remaining = set(TARGET_NUMBERS)
    page_size = 100
    max_pages = 50  # cap at 5000 tickets

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page in range(max_pages):
            from_idx = 1 + (page * page_size)
            print(f"\nPage {page+1} (from={from_idx})")
            batch = await list_tickets(client, headers, from_idx, page_size)
            if not batch:
                print("  empty batch, stopping")
                break
            min_num = min(int(t["ticketNumber"]) for t in batch if t.get("ticketNumber"))
            max_num = max(int(t["ticketNumber"]) for t in batch if t.get("ticketNumber"))
            print(f"  batch range #{min_num} - #{max_num} ({len(batch)} tickets)")
            for t in batch:
                tn = str(t.get("ticketNumber"))
                if tn in remaining:
                    found_tickets[tn] = t
                    remaining.discard(tn)
                    print(f"  ✓ found #{tn}")
            if not remaining:
                print("  all targets found")
                break
            # If we've gone past all target numbers, stop
            if max_num < min(int(n) for n in TARGET_NUMBERS):
                print(f"  past all target numbers, stopping")
                break

        # Now fetch full details (description) for each found ticket
        out = []
        for tn in sorted(TARGET_NUMBERS):
            ai_tag, correct_tag = CORRECTION_LOOKUP[tn]
            t = found_tickets.get(tn)
            if not t:
                print(f"NOT FOUND: #{tn}")
                out.append({
                    "ticket_number": tn, "ai_tag": ai_tag, "correct_tag": correct_tag,
                    "subject": None, "description": None, "from_email": None,
                })
                continue
            full = await get_ticket_full(client, headers, t["id"])
            description = (full or {}).get("description") or t.get("description") or ""
            out.append({
                "ticket_number": tn,
                "ticket_id": t["id"],
                "ai_tag": ai_tag,
                "correct_tag": correct_tag,
                "subject": (full or {}).get("subject", t.get("subject", "")),
                "description": description[:2000],
                "from_email": (full or {}).get("email") or t.get("email") or "",
                "createdTime": (full or {}).get("createdTime") or t.get("createdTime"),
            })

    Path("corrected_tickets.json").write_text(json.dumps(out, indent=2))
    found = sum(1 for x in out if x.get("subject"))
    print(f"\nFetched {found}/{len(out)} tickets → corrected_tickets.json")
    if remaining:
        print(f"NOT FOUND: {sorted(remaining)}")


if __name__ == "__main__":
    asyncio.run(main())
