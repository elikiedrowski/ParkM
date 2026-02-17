"""
Verify custom fields are accessible via Zoho Desk API
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

print("=" * 70)
print("Verifying Custom Fields in Zoho Desk")
print("=" * 70)
print()

# Get fresh access token
print("1. Getting fresh access token...")
token_response = requests.post(
    "https://accounts.zoho.com/oauth/v2/token",
    params={
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    },
    timeout=10
)

if token_response.status_code != 200:
    print(f"✗ Failed to get access token: {token_response.text}")
    exit(1)

access_token = token_response.json().get("access_token")
print(f"✓ Got access token")

# Set up API client
base_url = "https://desk.zoho.com/api/v1"
headers = {
    "Authorization": f"Zoho-oauthtoken {access_token}",
    "orgId": org_id
}

# Get tickets to see custom fields
print("\n2. Fetching recent tickets to verify custom fields...")
response = requests.get(
    f"{base_url}/tickets",
    headers=headers,
    params={"limit": 1, "sortBy": "createdTime"}
)

if response.status_code != 200:
    print(f"✗ Failed to fetch tickets: {response.status_code}")
    print(response.text)
    exit(1)

tickets = response.json().get("data", [])

if not tickets:
    print("⚠ No tickets found. Creating a test ticket...")
    # Create a test ticket
    test_ticket = {
        "subject": "Test ticket for custom fields verification",
        "description": "This is a test ticket to verify custom fields are working",
        "email": "test@parkm.com",
        "departmentId": None  # Will use default
    }
    
    create_response = requests.post(
        f"{base_url}/tickets",
        headers=headers,
        json=test_ticket
    )
    
    if create_response.status_code in [200, 201]:
        ticket = create_response.json()
        ticket_id = ticket.get("id")
        print(f"✓ Created test ticket: {ticket_id}")
    else:
        print(f"✗ Failed to create test ticket: {create_response.text}")
        exit(1)
else:
    ticket = tickets[0]
    ticket_id = ticket.get("id")
    print(f"✓ Found ticket: {ticket_id}")

# Get full ticket details
print(f"\n3. Getting detailed ticket info...")
response = requests.get(
    f"{base_url}/tickets/{ticket_id}",
    headers=headers
)

if response.status_code != 200:
    print(f"✗ Failed to get ticket details: {response.status_code}")
    exit(1)

ticket_details = response.json()

# Find all custom fields
print("\n4. Checking for custom fields (cf_*)...")
print("-" * 70)

custom_fields_found = {}
for key, value in ticket_details.items():
    if key.startswith("cf_"):
        custom_fields_found[key] = value
        print(f"   ✓ {key}: {value}")

if not custom_fields_found:
    print("   ⚠ No custom fields found (cf_* prefix)")
    print("\n   Showing all ticket fields:")
    for key, value in ticket_details.items():
        if not key.startswith("_") and key not in ["description", "threadCount"]:
            print(f"      {key}: {type(value).__name__}")

print()
print("-" * 70)

# Check for expected custom fields
expected_fields = [
    "cf_ai_intent",
    "cf_ai_complexity", 
    "cf_ai_language",
    "cf_ai_urgency",
    "cf_ai_confidence",
    "cf_requires_refund",
    "cf_requires_human_review",
    "cf_license_plate",
    "cf_move_out_date",
    "cf_routing_queue"
]

print("\n5. Verifying expected custom fields...")
missing_fields = []
found_fields = []

for field_name in expected_fields:
    if field_name in custom_fields_found or field_name in ticket_details:
        found_fields.append(field_name)
        print(f"   ✓ {field_name}")
    else:
        missing_fields.append(field_name)
        print(f"   ✗ {field_name} - NOT FOUND")

print()
print("=" * 70)
print("Summary")
print("=" * 70)
print(f"Expected fields: {len(expected_fields)}")
print(f"Found: {len(found_fields)}")
print(f"Missing: {len(missing_fields)}")

if missing_fields:
    print(f"\n⚠ Missing fields:")
    for field in missing_fields:
        print(f"   - {field}")
    print("\nNote: Fields might use different API names.")
    print("Check actual field names in Zoho Desk:")
    print("Settings → Developer Space → APIs → Fields")
    print("\nAll custom fields present (any cf_* prefix):")
    for key in custom_fields_found.keys():
        print(f"   - {key}")
else:
    print("\n✓ All expected custom fields found!")
    print("\nNext steps:")
    print("1. Test classification and tagging")
    print("2. Configure webhook")
    print("3. Test end-to-end flow")

print()
