#!/bin/bash

# Zoho Desk API Connection Setup Script
# This script helps you set up authentication with Zoho Desk

echo "=== Zoho Desk Connection Setup ==="
echo ""

# Prompt for necessary information
read -p "Enter your Zoho Desk Organization ID: " ORG_ID
read -p "Enter your Zoho data center (com/eu/in/com.au): " DATA_CENTER
read -p "Choose authentication method (1=OAuth, 2=API Token): " AUTH_METHOD

# Create .env file
cat > .env << EOF
# Zoho Desk Configuration
ZOHO_ORG_ID=$ORG_ID
ZOHO_DATA_CENTER=$DATA_CENTER
ZOHO_BASE_URL=https://desk.zoho.$DATA_CENTER/api/v1
EOF

if [ "$AUTH_METHOD" == "1" ]; then
    echo ""
    echo "OAuth Setup Required:"
    echo "1. Go to https://api-console.zoho.$DATA_CENTER/"
    echo "2. Create a 'Server-based Application'"
    echo "3. Add authorized redirect URI: http://localhost:8080/callback"
    echo "4. Note your Client ID and Client Secret"
    echo ""
    read -p "Enter Client ID: " CLIENT_ID
    read -p "Enter Client Secret: " CLIENT_SECRET
    
    cat >> .env << EOF

# OAuth Configuration
ZOHO_CLIENT_ID=$CLIENT_ID
ZOHO_CLIENT_SECRET=$CLIENT_SECRET
ZOHO_REDIRECT_URI=http://localhost:8080/callback
EOF
    
    echo ""
    echo "OAuth credentials saved!"
    echo "Next step: Run the OAuth authorization flow"
    
elif [ "$AUTH_METHOD" == "2" ]; then
    echo ""
    echo "API Token Setup:"
    echo "1. Go to Zoho Desk → Settings → Developer Space → API"
    echo "2. Generate a new API token"
    echo ""
    read -p "Enter your API Token: " API_TOKEN
    
    cat >> .env << EOF

# API Token Configuration
ZOHO_API_TOKEN=$API_TOKEN
EOF
    
    echo ""
    echo "API Token saved!"
fi

echo ""
echo "Configuration saved to .env file"
echo ""
echo "Testing connection..."

# Test the connection
if [ "$AUTH_METHOD" == "2" ]; then
    curl -X GET \
        "https://desk.zoho.$DATA_CENTER/api/v1/organizationId" \
        -H "orgId: $ORG_ID" \
        -H "Authorization: Zoho-oauthtoken $API_TOKEN"
fi

echo ""
echo "Setup complete!"
