#!/usr/bin/env python3
"""
Test Zoho Desk API Connection
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
        print(f"Error getting access token: {response.status_code}")
        print(response.text)
        return None

def test_zoho_connection():
    """Test connection to Zoho Desk API"""
    print("=" * 60)
    print("Testing Zoho Desk API Connection")
    print("=" * 60)
    print()
    
    # Get access token
    print("Getting access token...")
    access_token = get_access_token()
    
    if not access_token:
        print("✗ Failed to get access token")
        return
    
    print(f"✓ Access token obtained: {access_token[:20]}...")
    print()
    
    # Test API call - get organization info
    print("Testing API call (fetching organization info)...")
    
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'orgId': os.getenv('ZOHO_ORG_ID')
    }
    
    # Try to get departments
    response = requests.get(
        f"{os.getenv('ZOHO_BASE_URL')}/departments",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Successfully connected to Zoho Desk!")
        print()
        print("Departments:")
        for dept in data.get('data', []):
            print(f"  - {dept.get('name')} (ID: {dept.get('id')})")
    else:
        print(f"✗ API call failed: {response.status_code}")
        print(response.text)
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    test_zoho_connection()
