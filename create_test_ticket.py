#!/usr/bin/env python3
"""
Get departments from Zoho Desk and create test ticket
"""
import os
import requests
from dotenv import load_dotenv

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
        return None

print("=" * 70)
print("Creating Test Ticket in Zoho Desk Sandbox")
print("=" * 70)
print()

# Get access token
print("1. Getting access token...")
access_token = get_access_token()
if not access_token:
    print("✗ Failed to get access token")
    exit(1)
print("✓ Got access token")

# Set up headers
org_id = os.getenv('ZOHO_ORG_ID')
headers = {
    'Authorization': f'Zoho-oauthtoken {access_token}',
    'orgId': org_id
}
base_url = os.getenv('ZOHO_BASE_URL')

# Use Testing department
print("\n2. Using Testing department...")
department_id = "1004699000001888029"
print(f"✓ Department ID: {department_id}")

# Get or create contact
print(f"\n3. Checking for contacts...")
response = requests.get(f"{base_url}/contacts?limit=5", headers=headers)
if response.status_code == 200:
    contacts = response.json().get('data', [])
    if contacts:
        contact_id = contacts[0]['id']
        print(f"✓ Using existing contact (ID: {contact_id}, {contacts[0].get('firstName', '')} {contacts[0].get('lastName', '')})")
    else:
        contact_id = None
        print("⚠ No contacts found")
elif response.status_code == 204:
    contact_id = None
    print("⚠ No contacts in system")
else:
    print(f"✗ Failed to get contacts: {response.status_code}")
    exit(1)

# Create test ticket - try with or without contact
print(f"\n4. Creating test ticket...")

if contact_id:
    test_ticket = {
        "subject": "Refund Request - Moved Out Last Month",
        "description": "Hi, I moved out on January 1st, 2026 but I got charged on January 15th for my parking permit. My license plate is ABC-1234. I need a refund for this charge as I already canceled my lease and moved to a different property. Please process this refund within 5 business days. Thank you!",
        "contactId": str(contact_id),
        "departmentId": str(department_id)
    }
else:
    # Try creating with email, first name, last name
    test_ticket = {
        "subject": "Refund Request - Moved Out Last Month",
        "description": "Hi, I moved out on January 1st, 2026 but I got charged on January 15th for my parking permit. My license plate is ABC-1234. I need a refund for this charge as I already canceled my lease and moved to a different property. Please process this refund within 5 business days. Thank you!",
        "contact": {
            "firstName": "John",
            "lastName": "TestCustomer",
            "email": "john.test@example.com"
        },
        "departmentId": str(department_id),
        "channel": "Email"
    }

headers['Content-Type'] = 'application/json'

response = requests.post(
    f"{base_url}/tickets",
    headers=headers,
    json=test_ticket
)

if response.status_code in [200, 201]:
    ticket = response.json()
    ticket_id = ticket.get('id')
    ticket_number = ticket.get('ticketNumber')
    
    print(f"✓ Created ticket successfully!")
    print()
    print("=" * 70)
    print("✅ Test Ticket Created")
    print("=" * 70)
    print(f"Ticket ID: {ticket_id}")
    print(f"Ticket Number: #{ticket_number}")
    print(f"Subject: {test_ticket['subject']}")
    print()
    print("=" * 70)
    print("🔍 View in Zoho Desk")
    print("=" * 70)
    print(f"https://desk.zoho.com/support/parkmllc1719353334134/ShowHomePage.do#Cases/dv/{ticket_id}")
    print()
    print("=" * 70)
    print("🤖 Test AI Classification & Tagging")
    print("=" * 70)
    print(f"curl -X POST http://localhost:8000/test-tagging/{ticket_id}")
    print()
    print("This will:")
    print("  • Classify the email using AI")
    print("  • Populate all 10 custom fields")
    print("  • Add internal comment with classification details")
    print()
    print("=" * 70)
    print("✓ Expected Classification Results")
    print("=" * 70)
    print("  • AI Intent: refund_request")
    print("  • AI Complexity: simple")
    print("  • AI Language: english")
    print("  • AI Urgency: medium")
    print("  • AI Confidence: 95%")
    print("  • Requires Refund: Yes ✓")
    print("  • Requires Human Review: No")
    print("  • License Plate: ABC-1234")
    print("  • Move Out Date: 2026-01-01")
    print("  • Routing Queue: Accounting/Refunds Queue")
    print()
    print("=" * 70)
    print("📋 Visual Verification Steps")
    print("=" * 70)
    print("1. Run the curl command above")
    print("2. Refresh the ticket in Zoho Desk")
    print("3. Scroll down to see all 10 custom fields populated")
    print("4. Check the internal comment for classification details")
    print()
    
    # Save ticket ID
    with open('.last_ticket_id.txt', 'w') as f:
        f.write(ticket_id)
    
    print(f"✓ Ticket ID saved to .last_ticket_id.txt")
    print()
    
else:
    print(f"✗ Failed to create ticket: {response.status_code}")
    print(response.text)
    exit(1)
