#!/usr/bin/env python3
"""
Pull production tickets from Zoho Desk for Phase 1.3 Round 3 testing.

Step 1: Run this script — it opens a browser for OAuth
Step 2: Select the PRODUCTION org when Zoho asks
Step 3: Script pulls tickets and saves to production_tickets.json
Step 4: Run batch_test.py against the saved tickets

Usage:
    python pull_production_tickets.py                # Full OAuth flow + pull
    python pull_production_tickets.py --token TOKEN  # Skip OAuth, use existing token
    python pull_production_tickets.py --limit 500    # Pull 500 tickets (default: 500)
"""
import os
import sys
import json
import argparse
import requests
import webbrowser
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI", "http://localhost:8080/callback")
DATA_CENTER = os.getenv("ZOHO_DATA_CENTER", "com")
PRODUCTION_ORG_ID = "854251057"

SCOPES = "Desk.tickets.ALL,Desk.contacts.READ,Desk.settings.ALL"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        if "?" in self.path:
            query = parse_qs(self.path.split("?")[1])
            if "code" in query:
                auth_code = query["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Authorization successful! Return to terminal.</h1>")
                return
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Authorization failed</h1>")

    def log_message(self, format, *args):
        pass


def get_production_token():
    """Run OAuth flow and return an access token for the production org."""
    global auth_code

    params = {
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "response_type": "code",
        "access_type": "offline",
        "redirect_uri": REDIRECT_URI,
        "prompt": "consent",
    }
    auth_url = f"https://accounts.zoho.{DATA_CENTER}/oauth/v2/auth?{urlencode(params)}"

    print("=" * 70)
    print("Zoho Production OAuth — Step 1")
    print("=" * 70)
    print()
    print("Opening browser for authorization...")
    print("IMPORTANT: When Zoho asks, select the PRODUCTION organization")
    print(f"           (NOT the sandbox)")
    print()
    print(f"If browser doesn't open, visit:\n{auth_url}\n")

    webbrowser.open(auth_url)

    print("Waiting for authorization callback on localhost:8080...")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()

    if not auth_code:
        print("ERROR: No authorization code received")
        sys.exit(1)

    print("Got authorization code, exchanging for token...")

    token_url = f"https://accounts.zoho.{DATA_CENTER}/oauth/v2/token"
    resp = requests.post(token_url, data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code,
    })

    if resp.status_code != 200:
        print(f"ERROR: Token exchange failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    tokens = resp.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        print(f"ERROR: No access token in response: {tokens}")
        sys.exit(1)

    print(f"Got access token: {access_token[:20]}...")
    if refresh_token:
        print(f"Got refresh token: {refresh_token[:20]}...")
        # Save refresh token for future use (don't overwrite main .env)
        with open(".production_refresh_token", "w") as f:
            f.write(refresh_token)
        print("Saved production refresh token to .production_refresh_token")

    return access_token


def refresh_production_token():
    """Get a fresh access token using a saved production refresh token."""
    token_file = ".production_refresh_token"
    if not os.path.exists(token_file):
        return None

    with open(token_file) as f:
        refresh_token = f.read().strip()

    if not refresh_token:
        return None

    token_url = f"https://accounts.zoho.{DATA_CENTER}/oauth/v2/token"
    resp = requests.post(token_url, data={
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
    })

    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def pull_tickets(access_token: str, limit: int = 500) -> list:
    """Pull tickets from the production Zoho Desk org."""
    base_url = f"https://desk.zoho.{DATA_CENTER}/api/v1"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "orgId": PRODUCTION_ORG_ID,
        "Content-Type": "application/json",
    }

    all_tickets = []
    offset = 0
    page_size = 100  # Zoho max per page

    print(f"\nPulling up to {limit} tickets from production org ({PRODUCTION_ORG_ID})...")

    while len(all_tickets) < limit:
        resp = requests.get(
            f"{base_url}/tickets",
            headers=headers,
            params={
                "limit": min(page_size, limit - len(all_tickets)),
                "from": offset,
                "sortBy": "createdTime",
            },
        )

        if resp.status_code == 204:
            print(f"  No more tickets (got {len(all_tickets)} total)")
            break
        elif resp.status_code == 403:
            print(f"  ERROR 403: {resp.json().get('message', resp.text)}")
            print("  Make sure you selected the PRODUCTION org during OAuth")
            break
        elif resp.status_code != 200:
            print(f"  ERROR {resp.status_code}: {resp.text[:200]}")
            break

        data = resp.json().get("data", [])
        if not data:
            break

        all_tickets.extend(data)
        offset += len(data)
        print(f"  Pulled {len(all_tickets)} tickets so far...")

        if len(data) < page_size:
            break

    return all_tickets[:limit]


def fetch_ticket_details(access_token: str, ticket_id: str) -> dict:
    """Fetch full ticket details including description."""
    base_url = f"https://desk.zoho.{DATA_CENTER}/api/v1"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "orgId": PRODUCTION_ORG_ID,
    }
    resp = requests.get(f"{base_url}/tickets/{ticket_id}", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return {}


def main():
    parser = argparse.ArgumentParser(description="Pull production tickets for Phase 1.3")
    parser.add_argument("--token", type=str, help="Use existing access token (skip OAuth)")
    parser.add_argument("--limit", type=int, default=500, help="Number of tickets to pull")
    parser.add_argument("--details", action="store_true", help="Fetch full ticket details (slower)")
    parser.add_argument("--output", type=str, default="production_tickets.json", help="Output file")
    args = parser.parse_args()

    # Get access token
    if args.token:
        access_token = args.token
    else:
        # Try saved production refresh token first
        access_token = refresh_production_token()
        if access_token:
            print("Using saved production refresh token")
        else:
            access_token = get_production_token()

    # Pull tickets
    tickets = pull_tickets(access_token, args.limit)
    print(f"\nPulled {len(tickets)} tickets total")

    if not tickets:
        print("No tickets found. Exiting.")
        sys.exit(1)

    # Optionally fetch full details (includes description/body)
    if args.details:
        print(f"\nFetching full details for {len(tickets)} tickets (this may take a while)...")
        detailed_tickets = []
        for i, t in enumerate(tickets):
            tid = t.get("id")
            detail = fetch_ticket_details(access_token, tid)
            if detail:
                detailed_tickets.append(detail)
            else:
                detailed_tickets.append(t)
            if (i + 1) % 25 == 0:
                print(f"  Fetched {i + 1}/{len(tickets)} details...")
        tickets = detailed_tickets

    # Save to file
    output = {
        "pulled_at": datetime.now().isoformat(),
        "org_id": PRODUCTION_ORG_ID,
        "count": len(tickets),
        "tickets": tickets,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(tickets)} tickets to {args.output}")
    print(f"\nNext: Run classification against these tickets:")
    print(f"  python batch_test.py --production-file {args.output}")

    # Print summary
    subjects = [t.get("subject", "N/A") for t in tickets[:10]]
    print(f"\nFirst 10 tickets:")
    for i, s in enumerate(subjects):
        print(f"  {i+1}. {s[:70]}")


if __name__ == "__main__":
    main()
