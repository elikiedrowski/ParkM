"""
Fetch production tickets for Sadie's next-batch test (~105 tickets, uncommon tags).

Per Apr 16 call: 7 tickets each of 13 uncommon tags, plus 14 of 'Customer Inquiring
for Locked Down Permit' (Sadie's list had that tag duplicated).

Paginates through recent production tickets (desc createdTime), filters by Zoho
'Tagging' picklist value, fills quotas, and stops when all quotas are met.

Output: uncommon_batch_tickets.json  — same shape as production_tickets.json so
the existing scripts/import_to_sandbox.py can pick it up.
"""
import asyncio
import json
import os
from pathlib import Path

import httpx

PRODUCTION_ORG_ID = "854251057"
PRODUCTION_REFRESH_TOKEN = Path(".production_refresh_token").read_text().strip()

# Sadie's target tags (canonical names). Qty per tag.
QUOTAS: dict[str, int] = {
    "Customer Update Vehicle Info": 7,
    "Customer Update Contact Info": 7,
    "Customer Double Charged or Extra Charges": 7,
    "Property Update Resident Vehicle": 7,
    "Property Permitting PAID Resident Vehicle for Them": 7,
    "Property Update Resident Contact Information": 7,
    "Property Changing Resident Type for Approved Permit": 7,
    "Customer Inquiring for Additional Permit": 7,
    "Customer Inquiring for Locked Down Permit": 14,  # duplicated in Sadie's email
    "Customer Parking Space Not in Dropdown": 7,
    "Property Checking if a Vehicle is Permitted": 7,
    "Property Cancel Resident Account": 7,
}

MAX_PAGES = int(os.environ.get("MAX_PAGES", "100"))  # cap — at 100/page = 10k tickets max


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


async def list_tickets(client, headers, from_idx, limit=100):
    """List tickets WITH cf_tag_testing included — no per-ticket detail fetch needed."""
    base = os.environ.get("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
    r = await client.get(f"{base}/tickets", headers=headers, params={
        "from": from_idx,
        "limit": limit,
        "sortBy": "-createdTime",
        "fields": "id,ticketNumber,subject,description,email,createdTime,closedTime,cf_tag_testing",
    })
    if r.status_code != 200:
        print(f"  list failed: {r.status_code} {r.text[:150]}")
        return []
    return r.json().get("data", [])


def extract_manual_tag(ticket):
    """Get the production 'Tagging' custom field value."""
    cf = (ticket or {}).get("cf") or {}
    return cf.get("cf_tag_testing") or cf.get("cf_tagging")


async def main():
    os.environ["ZOHO_ORG_ID"] = PRODUCTION_ORG_ID
    token = await get_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "orgId": PRODUCTION_ORG_ID,
    }
    collected: dict[str, list] = {tag: [] for tag in QUOTAS}

    def remaining():
        return sum(QUOTAS[t] - len(collected[t]) for t in QUOTAS)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page in range(MAX_PAGES):
            from_idx = 1 + (page * 100)
            batch = await list_tickets(client, headers, from_idx)
            if not batch:
                print(f"page {page+1}: empty, stopping")
                break
            first_num = batch[0].get("ticketNumber")
            last_num = batch[-1].get("ticketNumber")
            print(f"page {page+1} (from={from_idx}) #{first_num}-#{last_num}  remaining: {remaining()}")

            for t in batch:
                if remaining() == 0:
                    break
                tag = extract_manual_tag(t)
                if not tag or tag not in QUOTAS:
                    continue
                if len(collected[tag]) >= QUOTAS[tag]:
                    continue
                collected[tag].append({
                    "id": t["id"],
                    "ticketNumber": t["ticketNumber"],
                    "subject": t.get("subject"),
                    "description": t.get("description"),
                    "email": t.get("email"),
                    "contact_name": (t.get("contact") or {}).get("firstName", "") + " " +
                                    (t.get("contact") or {}).get("lastName", ""),
                    "manual_tag": tag,
                    "createdTime": t.get("createdTime"),
                    "closedTime": t.get("closedTime"),
                })
                print(f"  ✓ {tag}: {len(collected[tag])}/{QUOTAS[tag]}")
            if remaining() == 0:
                print("all quotas met")
                break

    all_tickets = [t for lst in collected.values() for t in lst]
    Path("uncommon_batch_tickets.json").write_text(json.dumps(all_tickets, indent=2))
    print(f"\nTotal fetched: {len(all_tickets)} tickets → uncommon_batch_tickets.json")
    print("Quota fill:")
    for tag in QUOTAS:
        print(f"  {len(collected[tag]):3d}/{QUOTAS[tag]:3d}  {tag}")


if __name__ == "__main__":
    asyncio.run(main())
