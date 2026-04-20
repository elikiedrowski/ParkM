"""
Import the uncommon-tag batch tickets (fetched by fetch_uncommon_tag_tickets.py)
into the sandbox org so they trigger classification via the webhook pipeline.

Mirrors the logic in import_to_sandbox.py but reads from
uncommon_batch_tickets.json and writes to uncommon_batch_import_map.json.
"""
import asyncio
import json
import os
import time
from pathlib import Path

import httpx

SANDBOX_ORG_ID = "856336669"
SANDBOX_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN")
ZOHO_BASE = os.environ.get("ZOHO_BASE_URL", "https://desk.zoho.com/api/v1")
TARGET_DEPT = "Testing"
RATE_DELAY = 0.75  # seconds between creates


async def get_access_token(refresh_token: str) -> str:
    client_id = os.environ["ZOHO_CLIENT_ID"]
    client_secret = os.environ["ZOHO_CLIENT_SECRET"]
    data_center = os.environ.get("ZOHO_DATA_CENTER", "com")
    url = f"https://accounts.zoho.{data_center}/oauth/v2/token"
    async with httpx.AsyncClient() as c:
        r = await c.post(url, data={
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        })
        r.raise_for_status()
        return r.json()["access_token"]


async def get_departments(token: str) -> list:
    hdrs = {"orgId": SANDBOX_ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{ZOHO_BASE}/departments", headers=hdrs)
        r.raise_for_status()
    return r.json().get("data", [])


async def get_default_contact_id(token: str) -> str:
    hdrs = {"orgId": SANDBOX_ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{ZOHO_BASE}/tickets", headers=hdrs,
                        params={"limit": 10, "sortBy": "createdTime"})
        r.raise_for_status()
    for ticket in r.json().get("data", []):
        cid = ticket.get("contactId")
        if cid:
            return cid
    raise RuntimeError("No existing sandbox tickets/contacts found")


async def create_sandbox_ticket(token: str, dept_id: str, contact_id: str,
                                 subject: str, description: str) -> dict:
    hdrs = {
        "orgId": SANDBOX_ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "subject": subject or "(No Subject)",
        "departmentId": dept_id,
        "description": description or "",
        "status": "Open",
        "channel": "Web",
        "contactId": contact_id,
    }
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{ZOHO_BASE}/tickets", headers=hdrs, json=payload)
        return r.json()


async def main():
    source = Path("uncommon_batch_tickets.json")
    if not source.exists():
        print(f"ERROR: {source} not found. Run fetch_uncommon_tag_tickets.py first.")
        return
    tickets = json.loads(source.read_text())
    print(f"Loaded {len(tickets)} tickets from {source}")

    sandbox_token = await get_access_token(SANDBOX_REFRESH_TOKEN)
    depts = await get_departments(sandbox_token)
    dept = next((d for d in depts if TARGET_DEPT.lower() in d["name"].lower()), depts[0])
    print(f"Using sandbox department: {dept['name']} ({dept['id']})")

    contact_id = await get_default_contact_id(sandbox_token)
    print(f"Using shared contact: {contact_id}\n")

    results = []
    errors = []
    start = time.time()
    for i, t in enumerate(tickets):
        try:
            res = await create_sandbox_ticket(
                sandbox_token, dept["id"], contact_id,
                t.get("subject") or "(No Subject)",
                t.get("description") or "",
            )
            sid = res.get("id")
            if sid:
                results.append({
                    "sandbox_ticket_id": sid,
                    "sandbox_ticket_number": res.get("ticketNumber"),
                    "prod_ticket_id": t.get("id"),
                    "prod_ticket_number": t.get("ticketNumber"),
                    "manual_tag": t.get("manual_tag"),
                    "subject": t.get("subject"),
                })
                print(f"  [{i+1}/{len(tickets)}] ✓ #{res.get('ticketNumber')} ← prod #{t.get('ticketNumber')} ({t.get('manual_tag')})")
            else:
                errors.append({"ticket": t, "error": res})
                print(f"  [{i+1}/{len(tickets)}] ✗ unexpected response: {res}")
        except Exception as e:
            errors.append({"ticket": t, "error": str(e)})
            print(f"  [{i+1}/{len(tickets)}] ✗ {e}")
        await asyncio.sleep(RATE_DELAY)

    elapsed = time.time() - start
    Path("uncommon_batch_import_map.json").write_text(json.dumps({
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sandbox_department_id": dept["id"],
        "sandbox_department_name": dept["name"],
        "count_success": len(results),
        "count_error": len(errors),
        "results": results,
        "errors": errors,
    }, indent=2))
    print(f"\nDone in {elapsed:.0f}s. Imported {len(results)}/{len(tickets)} successfully.")
    print("→ uncommon_batch_import_map.json")


if __name__ == "__main__":
    asyncio.run(main())
