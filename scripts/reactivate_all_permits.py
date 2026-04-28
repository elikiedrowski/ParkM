#!/usr/bin/env python3
"""
Reactivate all permits for a ParkM customer.

Handles two cases that block permits from being "active":
  1. Fully cancelled (isCancelled=true) — reactivate via Permits/ReActivatePermit
  2. Scheduled to be cancelled (delayCancellationDate set) — clear the field
     via Permits/CreateOrEdit

Usage:
  python scripts/reactivate_all_permits.py                       # sandbox default customer
  python scripts/reactivate_all_permits.py --email eli@...       # by email
  python scripts/reactivate_all_permits.py --customer-id <uuid>  # by id
"""
import argparse
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

PARKM_BASE = os.getenv("PARKM_API_URL", "https://app-api-dev-parkm.azurewebsites.net")
# Sandbox fallback creds — same pattern as scripts/e2e_refund_test.py
PARKM_USER = os.getenv("PARKM_API_USERNAME") or "eli@thecrmwizards.com"
PARKM_PASS = os.getenv("PARKM_API_PASSWORD") or 'J4$wQz8#mXvP2@kRnL6!'
PARKM_TENANT = os.getenv("PARKM_API_TENANT_ID", "0")

SANDBOX_DEFAULT_CUSTOMER_ID = "1c03c9e7-1706-4ff0-9ab4-00451bfd12fe"


def get_token():
    r = httpx.post(
        f"{PARKM_BASE}/api/TokenAuth/Authenticate",
        json={"userNameOrEmailAddress": PARKM_USER, "password": PARKM_PASS},
        headers={"Content-Type": "application/json", "X-TenantId": PARKM_TENANT},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["result"]["accessToken"]


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-TenantId": PARKM_TENANT,
    }


def resolve_customer_id(token, email):
    r = httpx.post(
        f"{PARKM_BASE}/api/services/app/PermitPortal/GetCustomerFromEmail",
        json={"primaryEmailAddress": email},
        headers=headers(token),
        timeout=20,
    )
    r.raise_for_status()
    result = r.json().get("result") or {}
    cid = result.get("id")
    if not cid:
        sys.exit(f"No ParkM customer found for {email}")
    print(f"Customer: {result.get('fullName') or email}  ({cid})")
    return cid


def clear_delay_cancellation(token, permit_id):
    """GET the permit DTO, null out delayCancellationDate, POST back."""
    r = httpx.get(
        f"{PARKM_BASE}/api/services/app/Permits/GetPermitForEdit",
        params={"Id": permit_id},
        headers=headers(token),
        timeout=20,
    )
    r.raise_for_status()
    result = r.json().get("result") or {}
    dto = result.get("permit") or result
    if not dto or not dto.get("id"):
        return False, "could not load permit DTO"

    dto["delayCancellationDate"] = None

    r = httpx.post(
        f"{PARKM_BASE}/api/services/app/Permits/CreateOrEdit",
        json=dto,
        headers=headers(token),
        timeout=20,
    )
    if r.status_code != 200:
        return False, f"CreateOrEdit {r.status_code}: {r.text[:200]}"
    return True, "cleared"


def reactivate(token, permit_id):
    r = httpx.post(
        f"{PARKM_BASE}/api/services/app/Permits/ReActivatePermit",
        params={"Id": permit_id},
        headers=headers(token),
        timeout=15,
    )
    if r.status_code != 200:
        return False, f"ReActivatePermit {r.status_code}: {r.text[:200]}"
    return True, "reactivated"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", help="Customer email (falls back to sandbox default)")
    ap.add_argument("--customer-id", help="ParkM customer UUID")
    args = ap.parse_args()

    if not PARKM_USER or not PARKM_PASS:
        sys.exit("PARKM_API_USERNAME / PARKM_API_PASSWORD not set in .env")

    token = get_token()
    print(f"Authed against {PARKM_BASE}")

    if args.customer_id:
        customer_id = args.customer_id
    elif args.email:
        customer_id = resolve_customer_id(token, args.email)
    else:
        customer_id = SANDBOX_DEFAULT_CUSTOMER_ID
        print(f"Using sandbox default customer ({customer_id})")

    r = httpx.get(
        f"{PARKM_BASE}/api/services/app/Permits/GetAll",
        params={"CustomerIdFilter": customer_id},
        headers=headers(token),
        timeout=30,
    )
    r.raise_for_status()
    result = r.json().get("result") or {}
    items = result.get("items", []) if isinstance(result, dict) else result
    print(f"Found {len(items)} permits\n")

    scheduled = 0
    cancelled = 0
    errors = 0

    for item in items:
        p = item.get("permit", item)
        pid = p.get("id")
        name = item.get("permitTypeName") or p.get("permitTypeName") or "?"
        is_cancelled = p.get("isCancelled", False)

        # Permits/GetAll omits delayCancellationDate in its summary — fetch the
        # authoritative DTO via GetPermitForEdit to see if one is scheduled.
        dto_resp = httpx.get(
            f"{PARKM_BASE}/api/services/app/Permits/GetPermitForEdit",
            params={"Id": pid},
            headers=headers(token),
            timeout=20,
        )
        dto = (dto_resp.json().get("result") or {}).get("permit") or dto_resp.json().get("result") or {}
        delay_date = dto.get("delayCancellationDate")

        if delay_date:
            ok, msg = clear_delay_cancellation(token, pid)
            if ok:
                scheduled += 1
                print(f"  ✓ Cleared scheduled cancellation: {name}  (was {delay_date})")
            else:
                errors += 1
                print(f"  ✗ Failed to clear delay on {name}: {msg}")

        if is_cancelled:
            ok, msg = reactivate(token, pid)
            if ok:
                cancelled += 1
                print(f"  ✓ Reactivated cancelled permit: {name}")
            else:
                errors += 1
                print(f"  ✗ Failed to reactivate {name}: {msg}")

    print(
        f"\nDone. Cleared {scheduled} scheduled cancellation(s), "
        f"reactivated {cancelled} cancelled permit(s), {errors} error(s)."
    )


if __name__ == "__main__":
    main()
