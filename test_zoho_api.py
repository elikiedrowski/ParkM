"""
Test script to explore Zoho Desk API endpoints
"""
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Get credentials
org_id = os.getenv("ZOHO_ORG_ID")
refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
client_id = os.getenv("ZOHO_CLIENT_ID")
client_secret = os.getenv("ZOHO_CLIENT_SECRET")

# First, get a fresh access token
print("Getting fresh access token...")
token_response = requests.post(
    "https://accounts.zoho.com/oauth/v2/token",
    params={
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
)

if token_response.status_code == 200:
    access_token = token_response.json().get("access_token")
    print(f"✓ Got access token: {access_token[:20]}...")
else:
    print(f"✗ Failed to get access token: {token_response.text}")
    exit(1)

# Test various API endpoints to find custom fields
base_url = "https://desk.zoho.com/api/v1"
headers = {
    "Authorization": f"Zoho-oauthtoken {access_token}",
    "orgId": org_id
}

print("\nTesting API endpoints...")
print("=" * 70)

# Try to get departments (we know this works)
print("\n1. Testing /departments (known working endpoint)...")
response = requests.get(f"{base_url}/departments", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    depts = response.json().get("data", [])
    print(f"   ✓ Found {len(depts)} departments")

# Try to get a ticket to see what fields exist
print("\n2. Getting a sample ticket to see existing fields...")
response = requests.get(f"{base_url}/tickets", headers=headers, params={"limit": 1})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    tickets = response.json().get("data", [])
    if tickets:
        ticket = tickets[0]
        print(f"   ✓ Got ticket #{ticket.get('ticketNumber')}")
        print(f"\n   Custom fields (cf_*) in ticket:")
        for key, value in ticket.items():
            if key.startswith("cf_"):
                print(f"      {key}: {value}")
        
        if not any(k.startswith("cf_") for k in ticket.keys()):
            print("      No custom fields found yet")

# Try different custom field endpoints
endpoints_to_test = [
    "/customFields",
    "/fields",
    "/ticketFields",
    "/layouts",
    "/settings/fields"
]

print("\n3. Testing potential custom field endpoints...")
for endpoint in endpoints_to_test:
    response = requests.get(f"{base_url}{endpoint}", headers=headers)
    print(f"   {endpoint}: {response.status_code}", end="")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f" ✓ (found {len(data.get('data', []))} items)")
        except:
            print(" ✓ (valid response)")
    elif response.status_code == 404:
        print(" (not found)")
    elif response.status_code == 403:
        print(" (forbidden - may need admin access)")
    else:
        print(f" ({response.text[:50]})")

print("\n" + "=" * 70)
print("\nConclusion:")
print("If no /customFields or /fields endpoint works, custom fields must be")
print("created manually through the Zoho Desk UI:")
print("  Settings → Customization → Layouts and Fields → Tickets → Fields")
print("\nSee zoho-custom-fields-setup.md for detailed instructions.")
