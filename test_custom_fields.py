"""
Test custom fields using async httpx (same as FastAPI server)
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_fields():
    # Use the settings from our working config
    from src.config import get_settings
    settings = get_settings()
    
    print("=" * 70)
    print("Testing Custom Fields")
    print("=" * 70)
    print(f"Org ID: {settings.zoho_org_id}")
    print(f"Base URL: {settings.zoho_base_url}")
    print()
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {settings.zoho_api_token or settings.zoho_refresh_token}",
        "orgId": settings.zoho_org_id
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get tickets
        print("1. Fetching tickets...")
        response = await client.get(
            f"{settings.zoho_base_url}/tickets",
            headers=headers,
            params={"limit": 1}
        )
        
        if response.status_code != 200:
            print(f"✗ Failed: {response.status_code}")
            print(response.text)
            return
        
        tickets = response.json().get("data", [])
        if not tickets:
            print("⚠ No tickets found")
            return
        
        ticket_id = tickets[0]["id"]
        print(f"✓ Found ticket: {ticket_id}")
        
        # Get full ticket
        print(f"\n2. Getting ticket details...")
        response = await client.get(
            f"{settings.zoho_base_url}/tickets/{ticket_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"✗ Failed: {response.status_code}")
            return
        
        ticket = response.json()
        print(f"✓ Got ticket details")
        
        # Check custom fields
        print("\n3. Custom fields found:")
        print("-" * 70)
        
        cf_found = []
        for key, value in ticket.items():
            if key.startswith("cf_"):
                cf_found.append(key)
                print(f"   ✓ {key}: {value}")
        
        if not cf_found:
            print("   ⚠ No custom fields (cf_*) found")
        
        print("-" * 70)
        print(f"\nTotal custom fields: {len(cf_found)}")
        
        # Check expected
        expected = [
            "cf_ai_intent", "cf_ai_complexity", "cf_ai_language",
            "cf_ai_urgency", "cf_ai_confidence", "cf_requires_refund",
            "cf_requires_human_review", "cf_license_plate",
            "cf_move_out_date", "cf_routing_queue"
        ]
        
        missing = [f for f in expected if f not in ticket]
        
        print(f"\nExpected: {len(expected)}")
        print(f"Found: {len(expected) - len(missing)}")
        print(f"Missing: {len(missing)}")
        
        if missing:
            print("\n⚠ Missing fields:")
            for f in missing:
                print(f"   - {f}")
        else:
            print("\n✓ All fields present!")

if __name__ == "__main__":
    asyncio.run(test_fields())
