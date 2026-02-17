"""
Script to create custom fields in Zoho Desk
Automates the setup process described in zoho-custom-fields-setup.md
"""
import asyncio
import httpx
import json
from src.config import get_settings

settings = get_settings()

# Custom field definitions
CUSTOM_FIELDS = [
    {
        "displayLabel": "AI Intent",
        "apiName": "cf_ai_intent",
        "type": "PICK_LIST",
        "isRequired": False,
        "description": "AI-detected customer intent",
        "pickListValues": [
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
    },
    {
        "displayLabel": "AI Complexity",
        "apiName": "cf_ai_complexity",
        "type": "PICK_LIST",
        "isRequired": False,
        "description": "Complexity level of the request",
        "pickListValues": [
            {"actualValue": "simple", "displayValue": "Simple"},
            {"actualValue": "moderate", "displayValue": "Moderate"},
            {"actualValue": "complex", "displayValue": "Complex"}
        ]
    },
    {
        "displayLabel": "AI Language",
        "apiName": "cf_ai_language",
        "type": "PICK_LIST",
        "isRequired": False,
        "description": "Detected language of the email",
        "pickListValues": [
            {"actualValue": "english", "displayValue": "English"},
            {"actualValue": "spanish", "displayValue": "Spanish"},
            {"actualValue": "mixed", "displayValue": "Mixed"},
            {"actualValue": "other", "displayValue": "Other"}
        ]
    },
    {
        "displayLabel": "AI Urgency",
        "apiName": "cf_ai_urgency",
        "type": "PICK_LIST",
        "isRequired": False,
        "description": "Urgency level based on tone and content",
        "pickListValues": [
            {"actualValue": "high", "displayValue": "High"},
            {"actualValue": "medium", "displayValue": "Medium"},
            {"actualValue": "low", "displayValue": "Low"}
        ]
    },
    {
        "displayLabel": "AI Confidence",
        "apiName": "cf_ai_confidence",
        "type": "NUMBER",
        "isRequired": False,
        "description": "Classification confidence percentage (0-100)",
        "defaultValue": 0,
        "maxLength": 3
    },
    {
        "displayLabel": "Requires Refund",
        "apiName": "cf_requires_refund",
        "type": "CHECKBOX",
        "isRequired": False,
        "description": "AI detected refund request",
        "defaultValue": False
    },
    {
        "displayLabel": "Requires Human Review",
        "apiName": "cf_requires_human_review",
        "type": "CHECKBOX",
        "isRequired": False,
        "description": "Flagged for human review (low confidence or complex)",
        "defaultValue": False
    },
    {
        "displayLabel": "License Plate",
        "apiName": "cf_license_plate",
        "type": "SINGLE_LINE",
        "isRequired": False,
        "description": "Extracted vehicle license plate number",
        "maxLength": 20
    },
    {
        "displayLabel": "Move Out Date",
        "apiName": "cf_move_out_date",
        "type": "DATE",
        "isRequired": False,
        "description": "Extracted customer move-out date (for refund eligibility)"
    },
    {
        "displayLabel": "Routing Queue",
        "apiName": "cf_routing_queue",
        "type": "SINGLE_LINE",
        "isRequired": False,
        "description": "AI-recommended queue for routing",
        "maxLength": 50
    }
]


async def create_custom_field(client: httpx.AsyncClient, field_def: dict) -> dict:
    """
    Create a single custom field in Zoho Desk
    
    Args:
        client: HTTP client
        field_def: Field definition
        
    Returns:
        API response
    """
    headers = {
        "Authorization": f"Zoho-oauthtoken {settings.zoho_api_token or settings.zoho_refresh_token}",
        "orgId": settings.zoho_org_id,
        "Content-Type": "application/json"
    }
    
    # Zoho Desk custom fields API endpoint
    url = f"{settings.zoho_base_url}/customFields"
    
    try:
        response = await client.post(
            url,
            headers=headers,
            json=field_def
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✓ Created field: {field_def['displayLabel']} ({field_def['apiName']})")
            return {"success": True, "field": field_def['displayLabel'], "response": result}
        else:
            error_msg = response.text
            print(f"✗ Failed to create {field_def['displayLabel']}: {response.status_code}")
            print(f"  Error: {error_msg}")
            return {"success": False, "field": field_def['displayLabel'], "error": error_msg, "status": response.status_code}
            
    except Exception as e:
        print(f"✗ Exception creating {field_def['displayLabel']}: {str(e)}")
        return {"success": False, "field": field_def['displayLabel'], "error": str(e)}


async def list_existing_fields(client: httpx.AsyncClient) -> list:
    """List existing custom fields to avoid duplicates"""
    headers = {
        "Authorization": f"Zoho-oauthtoken {settings.zoho_api_token or settings.zoho_refresh_token}",
        "orgId": settings.zoho_org_id
    }
    
    try:
        response = await client.get(
            f"{settings.zoho_base_url}/customFields",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(f"Warning: Could not fetch existing fields: {response.status_code}")
            return []
    except Exception as e:
        print(f"Warning: Error fetching existing fields: {e}")
        return []


async def main():
    """Main function to create all custom fields"""
    print("=" * 70)
    print("Zoho Desk Custom Fields Creation")
    print("=" * 70)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, check existing fields
        print("Checking existing custom fields...")
        existing_fields = await list_existing_fields(client)
        existing_api_names = [f.get("apiName") for f in existing_fields if f.get("apiName")]
        
        if existing_api_names:
            print(f"Found {len(existing_api_names)} existing custom fields")
            print()
        
        # Create each field
        results = []
        for i, field_def in enumerate(CUSTOM_FIELDS, 1):
            print(f"[{i}/{len(CUSTOM_FIELDS)}] Creating: {field_def['displayLabel']}...")
            
            # Check if field already exists
            if field_def['apiName'] in existing_api_names:
                print(f"  ⚠ Field already exists, skipping")
                results.append({"success": True, "field": field_def['displayLabel'], "skipped": True})
                continue
            
            result = await create_custom_field(client, field_def)
            results.append(result)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        # Summary
        print()
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        skipped = [r for r in results if r.get("skipped")]
        
        print(f"✓ Successful: {len(successful)}")
        if skipped:
            print(f"⚠ Skipped (already exist): {len(skipped)}")
        if failed:
            print(f"✗ Failed: {len(failed)}")
            print()
            print("Failed fields:")
            for r in failed:
                print(f"  - {r['field']}: {r.get('error', 'Unknown error')}")
        
        print()
        
        if len(successful) == len(CUSTOM_FIELDS) or (len(successful) + len(skipped)) == len(CUSTOM_FIELDS):
            print("✓ All custom fields are ready!")
            print()
            print("Next steps:")
            print("1. Verify fields in Zoho Desk UI (Settings → Customization → Fields)")
            print("2. Check field API names match expectations")
            print("3. Proceed to webhook configuration")
        else:
            print("⚠ Some fields failed to create")
            print()
            print("Manual creation required:")
            print("1. Log in to Zoho Desk")
            print("2. Go to Settings → Customization → Layouts and Fields → Tickets")
            print("3. Create missing fields manually (see zoho-custom-fields-setup.md)")
            print()
            print("Failed fields that need manual creation:")
            for r in failed:
                print(f"  - {r['field']}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
