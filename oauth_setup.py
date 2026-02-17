#!/usr/bin/env python3
"""
OAuth Authorization Flow for Zoho Desk
This script handles the OAuth flow to get a refresh token
"""
import os
import webbrowser
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI")
DATA_CENTER = os.getenv("ZOHO_DATA_CENTER", "com")

# Scopes needed for Zoho Desk
SCOPES = "Desk.tickets.ALL,Desk.contacts.READ,Desk.settings.ALL"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    """Handles the OAuth callback"""
    
    def do_GET(self):
        global auth_code
        
        # Parse the authorization code from the callback URL
        query = parse_qs(self.path.split('?')[1])
        
        if 'code' in query:
            auth_code = query['code'][0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>No authorization code received.</p>
                </body>
                </html>
            """)
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass


def get_authorization_url():
    """Generate the authorization URL"""
    params = {
        'client_id': CLIENT_ID,
        'scope': SCOPES,
        'response_type': 'code',
        'access_type': 'offline',
        'redirect_uri': REDIRECT_URI,
        'prompt': 'consent'
    }
    base_url = f"https://accounts.zoho.{DATA_CENTER}/oauth/v2/auth"
    return f"{base_url}?{urlencode(params)}"


def exchange_code_for_token(code):
    """Exchange authorization code for access and refresh tokens"""
    token_url = f"https://accounts.zoho.{DATA_CENTER}/oauth/v2/token"
    
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def update_env_file(refresh_token):
    """Update .env file with the refresh token"""
    env_path = '.env'
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('ZOHO_REFRESH_TOKEN='):
                f.write(f'ZOHO_REFRESH_TOKEN={refresh_token}\n')
            else:
                f.write(line)


def main():
    print("=" * 60)
    print("Zoho Desk OAuth Authorization")
    print("=" * 60)
    print()
    
    # Generate and open authorization URL
    auth_url = get_authorization_url()
    print("Opening browser for authorization...")
    print(f"If browser doesn't open, visit this URL:\n{auth_url}\n")
    
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    print("Starting local server to receive authorization code...")
    print("Waiting for authorization...\n")
    
    server = HTTPServer(('localhost', 8080), CallbackHandler)
    server.handle_request()  # Handle one request then stop
    
    if auth_code:
        print("✓ Authorization code received!")
        print("Exchanging code for tokens...\n")
        
        tokens = exchange_code_for_token(auth_code)
        
        if tokens and 'refresh_token' in tokens:
            refresh_token = tokens['refresh_token']
            print("✓ Tokens received successfully!")
            print(f"Access Token: {tokens['access_token'][:20]}...")
            print(f"Refresh Token: {refresh_token[:20]}...")
            print(f"Expires in: {tokens.get('expires_in', 'N/A')} seconds\n")
            
            # Update .env file
            update_env_file(refresh_token)
            print("✓ .env file updated with refresh token!")
            print("\nSetup complete! You can now run the application.")
        else:
            print("✗ Failed to get tokens")
            if tokens:
                print(f"Response: {tokens}")
    else:
        print("✗ No authorization code received")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
