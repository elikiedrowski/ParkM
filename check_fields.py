#!/usr/bin/env python3
"""
Verify custom fields in Zoho Desk
"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def get_access_token():
    """Get access token using refresh token"""
    token_url = f"https://accounts.zoho.{os.getenv('ZOHO_DATA_CENTER')}/oauth/v2/token"
    
    data = {
        'refresh_token': os.getenv('ZOHO_REFRESH_TOKEN'),
        'client_id': os.getenv('ZOHO_CLIENT_ID'),
        'client_secret': os.getenv('ZOHO_CLIENT_SECRET'),
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Failed to get access token: {response.text}")
        return None

print("=" * 70)
print("Verifying Custom Fields in Zoho Desk")
print("=" * 70)
print()

# Get access token
print("1. Getting access token...")
access_token = get_access_token()
if not access_token:
    exit(1)
print("✓ Got access token")

# Set up headers
org_id = os.getenv('ZOHO_ORG_ID')
headers = {
    'Authorization': f'Zoho-oauthtoken {access_token}',
    'orgId': org_id
}
base_url = os.getenv('ZOHO_BASE_URL')

# Get a ticket to check custom fields
print("\n2. Fetching recent tickets...")
response = requests.get(
    f"{base_url}/tickets",
    headers=headers,
    params={'limit': 1, 'sortBy': 'createdTime'}
)

if response.status_code != 200:
    print(f"✗ Failed to get tickets: {response.status_code}")
    print(response.text)
    exit(1)

tickets_data = response.json()
tickets = tickets_data.get('data', [])

if not tickets:
    print("⚠ No tickets found. Please create a test ticket in Zoho Desk first.")
    print("Then run this script again.")
    exit(0)

ticket_id = tickets[0]['id']
ticket_number = tickets[0].get('ticketNumber', 'N/A')
print(f"✓ Found ticket #{ticket_number} (ID: {ticket_id})")

# Get full ticket details
print(f"\n3. Getting ticket details...")
response = requests.get(
    f"{base_url}/tickets/{ticket_id}",
    headers=headers
)

if response.status_code != 200:
    print(f"✗ Failed to get ticket details: {response.status_code}")
    exit(1)

ticket = response.json()
print(f"✓ Got ticket details")

# Find custom fields
print("\n4. Checking for custom fields...")
print("-" * 70)

custom_fields = {}
for key, value in ticket.items():
    if key.startswith('cf_'):
        custom_fields[key] = value

if custom_fields:
    print(f"Found {len(custom_fields)} custom fields:")
    for key, value in custom_fields.items():
        print(f"   ✓ {key}: {value}")
else:
    print("   ⚠ No custom fields found with 'cf_' prefix")

print("-" * 70)

# Check for expected fields
expected_fields = [
    'cf_ai_intent',
    'cf_ai_complexity',
    'cf_ai_language',
    'cf_ai_urgency',
    'cf_ai_confidence',
    'cf_requires_refund',
    'cf_requires_human_review',
    'cf_license_plate',
    'cf_move_out_date',
    'cf_routing_queue'
]

print("\n5. Verifying expected custom fields...")
found = []
missing = []

for field in expected_fields:
    if field in ticket:
        found.append(field)
        print(f"   ✓ {field}")
    else:
        missing.append(field)
        print(f"   ✗ {field} - NOT FOUND")

print()
print("=" * 70)
print("Summary")
print("=" * 70)
print(f"Expected: {len(expected_fields)}")
print(f"Found: {len(found)}")
print(f"Missing: {len(missing)}")
print()

if missing:
    print("⚠ Missing fields:")
    for field in missing:
        print(f"   - {field}")
    print()
    print("Possible reasons:")
    print("1. Fields not added to ticket layout")
    print("2. Different API names used")
    print("3. Fields not saved properly")
    print()
    print("To check actual field names:")
    print("  Settings → Developer Space → APIs")
    print()
    if custom_fields:
        print("Found these custom fields instead:")
        for key in custom_fields.keys():
            print(f"   - {key}")
else:
    print("✓ SUCCESS! All custom fields found and accessible!")
    print()
    print("Next steps:")
    print("1. Test classification and auto-tagging")
    print("2. Configure webhook in Zoho")
    print("3. Test end-to-end flow")
print()
