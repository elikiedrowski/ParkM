"""
Creates the Agent Corrected Intent custom field in Zoho Desk.
This is the 11th custom field — used by CSRs to flag AI misclassifications
and feed corrections back into LLM training.
"""
import asyncio
import httpx
from src.config import get_settings

settings = get_settings()

NEW_FIELD = {
    "displayLabel": "Agent Corrected Intent",
    "apiName": "cf_agent_corrected_intent",
    "type": "PICK_LIST",
    "isRequired": False,
    "description": "CSR sets this when AI classification is wrong. Used to improve LLM accuracy over time.",
    "pickListValues": [
        {"actualValue": "correct", "displayValue": "✓ Correct (No Change)"},
        {"actualValue": "refund_request", "displayValue": "Refund Request"},
        {"actualValue": "permit_cancellation", "displayValue": "Permit Cancellation"},
        {"actualValue": "account_update", "displayValue": "Account Update"},
        {"actualValue": "payment_issue", "displayValue": "Payment Issue"},
        {"actualValue": "permit_inquiry", "displayValue": "Permit Inquiry"},
        {"actualValue": "move_out", "displayValue": "Move Out"},
        {"actualValue": "technical_issue", "displayValue": "Technical Issue"},
        {"actualValue": "general_question", "displayValue": "General Question"},
        {"actualValue": "unclear", "displayValue": "Unclear"}
    ]
}


async def get_access_token(client: httpx.AsyncClient) -> str:
    """Get fresh access token via OAuth refresh flow"""
    response = await client.post(
        f"https://accounts.zoho.{settings.zoho_data_center}/oauth/v2/token",
        data={
            "refresh_token": settings.zoho_refresh_token,
            "client_id": settings.zoho_client_id,
            "client_secret": settings.zoho_client_secret,
            "grant_type": "refresh_token"
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    raise Exception(f"Token refresh failed: {response.text}")


async def main():
    print(f"Creating field: {NEW_FIELD['displayLabel']}")
    print(f"Org ID: {settings.zoho_org_id}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get fresh access token
        access_token = await get_access_token(client)
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "orgId": settings.zoho_org_id,
            "Content-Type": "application/json"
        }

        # Check if it already exists
        existing_resp = await client.get(
            f"{settings.zoho_base_url}/fields?module=tickets",
            headers=headers
        )
        if existing_resp.status_code == 200:
            existing = [f.get("apiName") for f in existing_resp.json().get("data", [])]
            if NEW_FIELD["apiName"] in existing:
                print(f"⚠  Field '{NEW_FIELD['apiName']}' already exists — skipping.")
                return

        # Create the field
        response = await client.post(
            f"{settings.zoho_base_url}/fields?module=tickets",
            headers=headers,
            json=NEW_FIELD
        )

        if response.status_code in [200, 201]:
            print(f"✓ Created: {NEW_FIELD['displayLabel']} ({NEW_FIELD['apiName']})")
            print()
            print("Next step: Verify in Zoho Desk UI")
            print("  Settings → Customization → Layouts and Fields → Tickets → Fields")
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  {response.text}")


if __name__ == "__main__":
    asyncio.run(main())
