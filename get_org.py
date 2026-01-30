#!/usr/bin/env python3
"""
Get organization ID from Zoho account
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

def get_organizations():
    """Get available organizations"""
    access_token = get_access_token()
    
    if not access_token:
        print("Failed to get access token")
        return
    
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}'
    }
    
    # Try to get organizations
    response = requests.get(
        f"{os.getenv('ZOHO_BASE_URL')}/organizations",
        headers=headers
    )
    
    print("Response status:", response.status_code)
    print("Response:", response.text)

if __name__ == "__main__":
    get_organizations()
