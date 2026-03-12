#!/usr/bin/env python3
"""
Create 49 single-intent + 12 multi-intent test tickets in the Zoho sandbox.

Each ticket is created with a synthetic subject + description. The sandbox
webhook fires on creation → classifier + tagger run automatically → Sadie
can open each ticket in Zoho and see the wizard live.

Usage:
    cd /home/elikiedrowski12/ParmM_Zoho
    python scripts/create_sandbox_test_tickets.py

Outputs: review/sandbox_test_tickets.json  (ticket ID mapping)
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx

# ── Load .env ────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Config ───────────────────────────────────────────────────────────────────
SANDBOX_ORG_ID = "856336669"
ZOHO_BASE = "https://desk.zoho.com/api/v1"
OAUTH_URL = "https://accounts.zoho.com/oauth/v2/token"
RATE_DELAY = 1.0  # seconds between ticket creates (safe for Zoho)
TARGET_DEPT = "Testing"

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
SANDBOX_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")


# ── Synthetic emails (same as generate_review_doc.py) ────────────────────────
SINGLE_INTENT_EMAILS = [
    {"target_tag": "Customer Canceling a Permit and Refunding", "subject": "[Test 1/49] Cancel my parking permit - need refund", "body": "Hi, I moved out of Riverside Apartments on March 1st 2026. My license plate is ABC1234. I need to cancel my parking permit and get a refund for the remaining balance. I was charged $75 on February 15th but I already moved out. Please help.", "from": "jane.doe@test.parkm.local"},
    {"target_tag": "Customer Inquiring for Grandfathered Permit", "subject": "[Test 2/49] Grandfathered permit question", "body": "Hello, I've been living at Oak Hill Community for over 3 years now. I was told my permit was grandfathered in under the old pricing. Can you confirm that my permit is still valid under the grandfathered rate? My plate is XYZ5678.", "from": "mike.smith@test.parkm.local"},
    {"target_tag": "Customer Inquiring for Locked Down Permit", "subject": "[Test 3/49] Why is my permit locked?", "body": "I tried to renew my parking permit online but it says my permit is locked down. I live at Maple Grove unit 204. Can someone explain why it's locked and what I need to do? My plate is LMN9012.", "from": "sarah.jones@test.parkm.local"},
    {"target_tag": "Customer Inquiring for Additional Permit", "subject": "[Test 4/49] Need a second parking permit", "body": "Hi there, I already have one permit for my Toyota but I just got a second car, a Honda Civic plate DEF3456. I live at Sunset Ridge apartment 112. Can I get an additional permit? What's the process and cost?", "from": "tom.williams@test.parkm.local"},
    {"target_tag": "Customer Rental Car", "subject": "[Test 5/49] Rental car temporary permit needed", "body": "My car is in the shop and I have a rental car for the next two weeks. The rental plate is RENT789. I live at Creekside Village unit 305. How do I get a temporary permit so I don't get towed? My regular plate is GHI7890.", "from": "lisa.brown@test.parkm.local"},
    {"target_tag": "Customer Double Charged or Extra Charges", "subject": "[Test 6/49] Charged twice for my permit this month!", "body": "I was charged $50 on March 1st and then another $50 on March 3rd for my parking permit at Willow Park. I should only have been charged once. My plate is JKL2345. Can you please look into this and refund the extra charge?", "from": "david.garcia@test.parkm.local"},
    {"target_tag": "Customer Guest Permit and Pricing Questions", "subject": "[Test 7/49] Guest parking permit info", "body": "Hi, I'm having family visit me at Pine Valley Apartments next weekend. How do I get a guest parking permit? How much does it cost and how long is it valid? I'm in unit 401.", "from": "emily.wilson@test.parkm.local"},
    {"target_tag": "Customer Miscellaneous Questions", "subject": "[Test 8/49] General question about parking", "body": "Hello, I just moved into Lakeside Terrace and I have a few questions about the parking situation. Is there assigned parking? Are there any visitor spots? What are the quiet hours for the parking garage? Thanks!", "from": "chris.martinez@test.parkm.local"},
    {"target_tag": "Customer Sending Money Order", "subject": "[Test 9/49] Sending money order for parking permit", "body": "Hi, I don't have a credit card so I'd like to pay for my parking permit with a money order. I live at Brookfield Commons unit 210. Where do I mail the money order and who do I make it out to? The amount should be $45.", "from": "nancy.taylor@test.parkm.local"},
    {"target_tag": "Customer Need help buying a permit", "subject": "[Test 10/49] How do I buy a parking permit?", "body": "I just signed my lease at Harbor Point Apartments and the leasing office said I need to buy a parking permit online. I went to the website but I'm confused about which permit to select. I'm in building C, unit 108. Can you walk me through the process?", "from": "kevin.anderson@test.parkm.local"},
    {"target_tag": "Customer Need Help Renewing Permit", "subject": "[Test 11/49] Permit renewal issue", "body": "My parking permit expired yesterday and I'm trying to renew it online but the system keeps giving me an error. I live at Elmwood Estates unit 502 and my plate is MNO4567. Can you help me renew my permit before I get towed?", "from": "amanda.thomas@test.parkm.local"},
    {"target_tag": "Customer Need Help Creating an Account", "subject": "[Test 12/49] Can't create my ParkM account", "body": "Hi, I'm a new resident at Stonegate Apartments unit 301. The leasing office told me to create an account on ParkM but when I try to register it says my email is already in use. I've never used ParkM before. My email is jessica.lee@test.parkm.local. Please help.", "from": "jessica.lee@test.parkm.local"},
    {"target_tag": "Customer New Towing Legislation No Parking", "subject": "[Test 13/49] New towing law question", "body": "I heard there's new legislation about towing in our area. I park at Ridgewood Community and I'm worried about how the new no-parking rules affect my vehicle. Can you explain what the new towing laws mean for residents? My plate is PQR6789.", "from": "ryan.clark@test.parkm.local"},
    {"target_tag": "Customer No Plate or Expired Tags", "subject": "[Test 14/49] My car has expired tags - will I get towed?", "body": "Hi, I'm waiting for my new registration to come in the mail. My current tags on my car are expired. I live at Cedar Springs unit 115 and my plate is STU8901. Will I get towed or ticketed while I wait for my new tags? What should I do?", "from": "michelle.lewis@test.parkm.local"},
    {"target_tag": "Customer Someone is Parking in my Spot", "subject": "[Test 15/49] Someone keeps parking in my assigned spot!", "body": "There is a black SUV with plate VWX2345 that keeps parking in my assigned spot #42 at Fairview Apartments. This has happened three times this week. I've left notes but they keep doing it. What can be done about this? I'm in unit 208.", "from": "brian.walker@test.parkm.local"},
    {"target_tag": "Customer Parking Space Not in Dropdown", "subject": "[Test 16/49] My parking space isn't listed", "body": "I'm trying to register my vehicle for space #167 at Highland Park Apartments but the space number isn't showing up in the dropdown menu on the website. I'm in unit 403. Can you add my space to the system?", "from": "jennifer.hall@test.parkm.local"},
    {"target_tag": "Customer Password Reset", "subject": "[Test 17/49] Forgot my password", "body": "I can't remember my password for my ParkM account. I've tried the reset link but I'm not getting the email. My account email is daniel.young@test.parkm.local. Can you send me a password reset or reset it for me?", "from": "daniel.young@test.parkm.local"},
    {"target_tag": "Customer Towed Booted Ticketed", "subject": "[Test 18/49] MY CAR WAS TOWED!! HELP!!", "body": "I came outside this morning and my car is GONE. It was towed from the parking lot at Westwood Apartments. I have a valid permit! My plate is YZA3456 and I'm in unit 510. This is an emergency, I need my car for work. Who towed it and how do I get it back??", "from": "mark.king@test.parkm.local"},
    {"target_tag": "Customer Warned or Tagged", "subject": "[Test 19/49] Warning sticker on my car", "body": "I found a warning tag on my windshield at Valley View Apartments. It says my vehicle will be towed if not resolved in 48 hours. I have a valid permit for space #23. My plate is BCD4567, unit 102. Why did I get warned?", "from": "stephanie.wright@test.parkm.local"},
    {"target_tag": "Customer Payment Help", "subject": "[Test 20/49] Payment not going through", "body": "I'm trying to pay for my parking permit at Autumn Ridge but my credit card keeps getting declined. I've tried two different cards. I'm in unit 205. Is there something wrong with the payment system? Can I pay another way?", "from": "jason.green@test.parkm.local"},
    {"target_tag": "Customer Update Vehicle Info", "subject": "[Test 21/49] Need to update my license plate", "body": "Hi, I just got a new car and need to update my license plate on my parking permit. Old plate: EFG5678, new plate: HIJ6789. I live at Magnolia Gardens unit 304. Can you update this for me?", "from": "laura.adams@test.parkm.local"},
    {"target_tag": "Customer Update Contact Info", "subject": "[Test 22/49] Update my phone number and email", "body": "Hi, I need to update my contact information on my ParkM account. My new phone number is 555-123-4567 and my new email is rachel.new@test.parkm.local. I live at Cypress Point unit 201. Thanks!", "from": "rachel.nelson@test.parkm.local"},
    {"target_tag": "Property Changing Resident Type for Approved Permit", "subject": "[Test 23/49] Change resident type for unit 305", "body": "Hi, this is the leasing office at Birchwood Estates. We need to change the resident type for the tenant in unit 305 from 'Standard' to 'Premium' for their approved permit. The resident is John Smith, plate KLM7890. Please update accordingly.", "from": "leasing@test.parkm.local"},
    {"target_tag": "Property Approving Grandfathered Permit", "subject": "[Test 24/49] Approve grandfathered permit - unit 412", "body": "Hello ParkM team, this is the property manager at Oakridge Manor. We'd like to approve a grandfathered permit for our long-term resident in unit 412, Maria Gonzalez. Her plate is NOP8901. She's been here since 2020 and qualifies for the old rate.", "from": "manager@test.parkm.local"},
    {"target_tag": "Property Approving Override Additional Permit", "subject": "[Test 25/49] Override approval for additional permit", "body": "Hi, this is Ashley from the front desk at Pinecrest Village. We're approving an override for an additional parking permit for unit 215, resident James Brown. His second vehicle plate is QRS9012. Please process this override.", "from": "frontdesk@test.parkm.local"},
    {"target_tag": "Property Extending Expiration Date on a Permit", "subject": "[Test 26/49] Extend permit expiration for resident", "body": "Hello, this is the management office at Lakeshore Commons. We need to extend the permit expiration for resident in unit 608, Sarah Miller. Her current permit expires March 15th but her lease was extended through June 30th. Plate TUV1234.", "from": "office@test.parkm.local"},
    {"target_tag": "Property Audits or Reports", "subject": "[Test 27/49] Monthly parking audit report needed", "body": "Hi ParkM, this is the property manager at Summit Hills. We need the monthly parking audit report for February 2026. Specifically, we need the number of active permits, expired permits, and any violations issued. Please send it as a spreadsheet if possible.", "from": "pm@test.parkm.local"},
    {"target_tag": "Property Checking if a Vehicle is Permitted", "subject": "[Test 28/49] Is this vehicle permitted?", "body": "Hi, this is maintenance at Greenfield Apartments. There's a red Ford F-150 with plate WXY2345 parked in lot B. Can you check if this vehicle has a valid permit? We want to verify before we call for a tow.", "from": "maintenance@test.parkm.local"},
    {"target_tag": "Property Checking Who Has a Space Number", "subject": "[Test 29/49] Who is assigned to space #55?", "body": "Hello, this is the leasing office at Riverdale Townhomes. We have a dispute about parking space #55. Can you tell us who is currently assigned to that space? We need to resolve this with our residents.", "from": "leasing2@test.parkm.local"},
    {"target_tag": "Property Checking Who is in a Unit", "subject": "[Test 30/49] Who is registered in unit 407?", "body": "Hi ParkM, this is the property manager at Courtyard Place. We need to know which residents are registered and have parking permits in unit 407. We're doing a lease audit and need to verify the information matches our records.", "from": "manager2@test.parkm.local"},
    {"target_tag": "Property Inquiring about a Tow Boot Ticket", "subject": "[Test 31/49] Tow inquiry for our property", "body": "Hello, this is management at Westgate Apartments. One of our residents is complaining that their car was towed from our lot last night. The vehicle is a blue Honda Civic plate ZAB3456. Can you provide details on why it was towed and which company performed the tow?", "from": "management@test.parkm.local"},
    {"target_tag": "Property Inquiring About a Warning Tag", "subject": "[Test 32/49] Warning tag placed on resident vehicle", "body": "Hi, this is the office at Meadowbrook Village. A resident in unit 103 received a warning tag on their vehicle, plate CDE4567. They're upset and came to us. Can you explain why the warning was issued and what steps the resident needs to take?", "from": "office2@test.parkm.local"},
    {"target_tag": "Property Monitor Request", "subject": "[Test 33/49] Request parking lot monitoring", "body": "Hello ParkM, this is the HOA president at Eagle Ridge. We've been having issues with unauthorized vehicles parking overnight in our guest lot. Can we set up monitoring for lot C, especially between 10 PM and 6 AM? We'd like to start enforcement next week.", "from": "hoa@test.parkm.local"},
    {"target_tag": "Property Leasing Staff Login", "subject": "[Test 34/49] New leasing agent needs access", "body": "Hi, this is the property manager at Silver Creek Apartments. We have a new leasing agent, Brittany Cooper, who needs login access to the ParkM system. Her email is brittany.cooper@silvercreek.com. Can you set up her account?", "from": "pm2@test.parkm.local"},
    {"target_tag": "Property Miscellaneous Questions", "subject": "[Test 35/49] General parking questions for our property", "body": "Hi ParkM, I'm the new property manager at Woodland Hills. I have a few general questions: How often do you patrol our lot? What's the process if we need to add more spaces? Do you provide signage? Can we get a copy of our current contract? Thanks.", "from": "newmanager@test.parkm.local"},
    {"target_tag": "Property Sending Money Order", "subject": "[Test 36/49] Sending money order for resident permit", "body": "Hello, this is the office at Heritage Park. One of our residents in unit 502 doesn't have a bank account and would like to pay for their permit via money order. The amount is $60. Where should we send the money order and who do we make it payable to?", "from": "office3@test.parkm.local"},
    {"target_tag": "Property Update or Register Employee Vehicles", "subject": "[Test 37/49] Register employee vehicles", "body": "Hi ParkM, this is HR at Cornerstone Communities. We need to register vehicles for three new maintenance employees: 1) John, plate FGH5678, 2) Maria, plate IJK6789, 3) Sam, plate LMN7890. They all need permits for lot A starting immediately.", "from": "hr@test.parkm.local"},
    {"target_tag": "Property Update Resident Vehicle", "subject": "[Test 38/49] Update resident vehicle info", "body": "Hi, leasing office at Springdale Apartments here. Our resident in unit 210, Michael Johnson, got a new car. Old plate: OPQ8901, new plate: RST9012. Can you update his parking permit with the new vehicle information?", "from": "leasing3@test.parkm.local"},
    {"target_tag": "Property Update Resident Contact Information", "subject": "[Test 39/49] Update resident contact info", "body": "Hello, this is the office at Foxwood Apartments. The resident in unit 318, Karen Davis, has a new phone number: 555-987-6543 and new email: karen.davis.new@gmail.com. Please update her ParkM account. Thanks!", "from": "office4@test.parkm.local"},
    {"target_tag": "Property Update Resident Password", "subject": "[Test 40/49] Reset password for resident", "body": "Hi ParkM, this is the leasing office at Walnut Creek Apartments. Our resident in unit 105, Robert Wilson, has been locked out of his ParkM account. He says he's tried the forgot password link multiple times with no luck. Can you manually reset his password? His email is robert.wilson@email.com.", "from": "leasing4@test.parkm.local"},
    {"target_tag": "Property Register Resident Account for Them", "subject": "[Test 41/49] Create account for elderly resident", "body": "Hello, this is the office at Sunflower Senior Living. We have an elderly resident, Dorothy Thompson in unit 101, who is not tech-savvy and needs help creating her ParkM account. Her email is dorothy.t@gmail.com, phone 555-111-2222. Her vehicle is a silver Buick, plate UVW1234. Can you create her account for her?", "from": "office5@test.parkm.local"},
    {"target_tag": "Property Cancel Resident Account", "subject": "[Test 42/49] Cancel resident account - moved out", "body": "Hi ParkM, this is the leasing office at Riverwalk Apartments. Resident in unit 404, Thomas Lee, moved out on March 5th. Please cancel his parking permit and account. His plate was XYZ2345. Thanks.", "from": "leasing5@test.parkm.local"},
    {"target_tag": "Property Permitting PAID Resident Vehicle for Them", "subject": "[Test 43/49] Process paid permit for resident", "body": "Hi, the office at Crestview Condos here. We collected payment from our resident in unit 509, Angela Martinez, for a parking permit. Amount: $55. Her vehicle is a white Toyota Camry, plate ABC3456. Can you issue the permit on her behalf? She's already paid us directly.", "from": "office6@test.parkm.local"},
    {"target_tag": "Property Resident Payment Help", "subject": "[Test 44/49] Resident having payment issues", "body": "Hello, this is the property manager at Bayview Apartments. Our resident in unit 602, Steven Chen, is having trouble making a payment for his parking permit through the website. He says his card keeps getting declined but it works everywhere else. His email is steven.chen@email.com. Can you assist?", "from": "manager3@test.parkm.local"},
    {"target_tag": "Property Guest Permits", "subject": "[Test 45/49] Guest permit policy for our community", "body": "Hi ParkM, this is the office at Palm Gardens. We're getting a lot of questions from residents about guest permits. Can you clarify: How many guest permits can each unit have? What's the cost? Is there a time limit? How do residents request them?", "from": "office7@test.parkm.local"},
    {"target_tag": "Property Potential Leads", "subject": "[Test 46/49] Interested in ParkM for our community", "body": "Hello, I'm the HOA board president at Magnolia Square, a 200-unit apartment community. We're currently not using any parking management system and are interested in learning about ParkM's services. Can someone reach out to discuss pricing and setup? My direct number is 555-444-3333.", "from": "president@test.parkm.local"},
    {"target_tag": "Sales Rep Asking for a Vehicle to be Released", "subject": "[Test 47/49] Release vehicle from tow hold", "body": "Hey team, this is Jake from the towing division. We need to release the vehicle with plate DEF4567 that was flagged at Woodland Estates. The property manager confirmed it's a registered resident. Please release the hold so we can let it go.", "from": "jake@test.parkm.local"},
    {"target_tag": "Sales Rep Asking for a Vehicle to be Grandfathered", "subject": "[Test 48/49] Grandfather this vehicle in", "body": "Hi ParkM, this is Marcus from sales. The property at Hilltop Villas wants to grandfather in a vehicle for their long-term resident. Plate GHI5678, unit 201. The property confirmed they qualify under the old pricing. Can you process this?", "from": "marcus@test.parkm.local"},
    {"target_tag": "Towing or Monitoring Leads", "subject": "[Test 49/49] Parking enforcement services inquiry", "body": "Hi, I manage a commercial property complex in downtown. We're looking for a parking monitoring and towing enforcement partner. We have 3 buildings with about 500 parking spaces total. Would ParkM be able to provide monitoring and enforcement services? What's the process to get started?", "from": "info@test.parkm.local"},
    {"target_tag": "The Law Asking for Information", "subject": "[Test 50/49] Law enforcement request for vehicle information", "body": "This is Officer Johnson, badge #4521, with the Metro Police Department. We are investigating a case (Case #2026-1234) and need information about a vehicle registered in your system. The plate is JKL6789. We need the registered owner's name and address associated with this permit. Please respond as soon as possible.", "from": "officer@test.parkm.local"},
]

MULTI_INTENT_EMAILS = [
    {"label": "Cancel Permit + Refund + Password Reset", "subject": "[Multi 1/12] Cancel permit, get refund, and can't log in", "body": "Hi, I moved out of Riverside Apartments on Feb 28th 2026. I need to cancel my parking permit and get a refund. Also, I can't log into my account to see my charges - I forgot my password. My plate is MNO1234 and I was charged $65 last month. Please help with all of this.", "from": "multi1@test.parkm.local"},
    {"label": "Double Charged + Cancel Permit", "subject": "[Multi 2/12] Charged twice AND I'm moving out", "body": "I was charged $50 twice on March 1st for my permit at Willow Creek. That needs to be fixed. Also, I'm moving out on March 15th so I need to cancel my permit entirely. Plate: PQR2345, unit 303. This is really frustrating.", "from": "multi2@test.parkm.local"},
    {"label": "Update Vehicle + Renew Permit", "subject": "[Multi 3/12] New car - need to update plate and renew", "body": "Hey, I just got a new car and my permit is about to expire. I need to update my plate from STU3456 to VWX4567 AND renew my parking permit at Summit Apartments unit 210. Can we do both at once?", "from": "multi3@test.parkm.local"},
    {"label": "Towed + Refund Request", "subject": "[Multi 4/12] Car towed but I had a permit! I want a refund!", "body": "MY CAR WAS TOWED from Oakdale Apartments even though I have a valid permit!! Plate YZA5678, space #15, unit 404. I had to pay $250 to get my car back. I want a refund for the tow AND I want a refund on my parking permit because clearly it doesn't work. This is unacceptable!", "from": "multi4@test.parkm.local"},
    {"label": "Property: Check Vehicle + Check Unit", "subject": "[Multi 5/12] Vehicle check and unit verification", "body": "Hi ParkM, this is the leasing office at Brookside Manor. Can you check two things: 1) Is the vehicle with plate BCD6789 permitted in our lot? And 2) Who is currently registered in unit 512? We're doing an end-of-month audit. Thanks!", "from": "multi5@test.parkm.local"},
    {"label": "Guest Permit + Someone in My Spot", "subject": "[Multi 6/12] Guest permit and someone in my spot", "body": "Two issues: First, my parents are visiting this weekend and I need a guest permit for them at Meadow Lakes unit 207. Second, there's been a silver Honda with plate EFG7890 parking in my assigned spot #31 every day this week. Can you handle both?", "from": "multi6@test.parkm.local"},
    {"label": "Property: Register Account + Permit Payment", "subject": "[Multi 7/12] New resident needs account and permit", "body": "Hello, this is the office at Cedar Point. We have a new move-in, Patricia Holmes, unit 603. She needs a ParkM account created (email: patricia.h@email.com, phone: 555-222-3333) AND we collected her permit payment of $45. Her vehicle is a blue Honda Accord plate HIJ8901. Please set up her account and issue the permit.", "from": "multi7@test.parkm.local"},
    {"label": "Warning Tag + No Plate/Expired Tags", "subject": "[Multi 8/12] Got a warning but my tags are being renewed", "body": "I got a warning tag on my car at Sunridge Apartments. The warning says my tags are expired, which they are, but I've already submitted my renewal to the DMV and I'm waiting for the new stickers. My plate is KLM9012, unit 108, space #22. What do I do so I don't get towed while I wait?", "from": "multi8@test.parkm.local"},
    {"label": "Property: Employee Vehicles + Leasing Staff Login", "subject": "[Multi 9/12] New staff setup - vehicles and system access", "body": "Hi ParkM, this is HR at Grandview Properties. We have two new employees starting Monday. They both need: 1) Their vehicles registered for staff parking (John - plate NOP0123, Sarah - plate QRS1234), and 2) Login access to the ParkM management system. John's email: john@grandview.com, Sarah's email: sarah@grandview.com.", "from": "multi9@test.parkm.local"},
    {"label": "Create Account + Buy Permit + Payment Help", "subject": "[Multi 10/12] New here - can't figure anything out", "body": "Hi, I just moved into Lakeview Terrace unit 401 and I'm completely lost. I need to create a ParkM account, buy a parking permit, and I'm not sure what payment methods you accept. I tried to go to the website but I don't even know where to start. My car is a red Nissan plate TUV2345. Help!!", "from": "multi10@test.parkm.local"},
    {"label": "Property: Extend Permit + Change Resident Type", "subject": "[Multi 11/12] Lease renewal - extend permit and change type", "body": "Hello ParkM, this is management at Ivy Court. Resident in unit 208, James White, renewed his lease and is upgrading from Standard to Premium parking. We need to: 1) Extend his permit expiration from March 31st to September 30th, and 2) Change his resident type to Premium. Plate WXY3456. Thanks!", "from": "multi11@test.parkm.local"},
    {"label": "Refund + Update Contact Info + Miscellaneous", "subject": "[Multi 12/12] Moving out - refund, update info, and questions", "body": "Hi, I'm moving out of Parkside Heights on March 20th. A few things: 1) I need a refund on my remaining permit balance - I was charged $70 on March 1st. 2) My new email will be jane.newemail@gmail.com and phone 555-999-8888, please update that. 3) Also, do I need to return any parking stickers or key fobs? Plate ZAB4567, unit 506.", "from": "multi12@test.parkm.local"},
]


# ── Zoho helpers ─────────────────────────────────────────────────────────────

async def get_access_token(refresh_token: str) -> str:
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(OAUTH_URL, data={
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
        })
        data = r.json()
        if "access_token" not in data:
            raise RuntimeError(f"Token error: {data}")
        return data["access_token"]


async def get_departments(token: str) -> list:
    hdrs = {"orgId": SANDBOX_ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{ZOHO_BASE}/departments", headers=hdrs)
        r.raise_for_status()
    return r.json().get("data", [])


async def get_default_contact_id(token: str) -> str:
    """Reuse an existing sandbox contact (we don't have Desk.contacts scope)."""
    hdrs = {"orgId": SANDBOX_ORG_ID, "Authorization": f"Zoho-oauthtoken {token}"}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{ZOHO_BASE}/tickets", headers=hdrs,
                        params={"limit": 10, "sortBy": "createdTime"})
        r.raise_for_status()
    for ticket in r.json().get("data", []):
        cid = ticket.get("contactId")
        if cid:
            return cid
    raise RuntimeError("No existing sandbox tickets with contacts found.")


async def create_ticket(token: str, dept_id: str, contact_id: str,
                        subject: str, description: str) -> dict:
    hdrs = {
        "orgId": SANDBOX_ORG_ID,
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "subject": subject,
        "departmentId": dept_id,
        "description": description,
        "status": "Open",
        "channel": "Email",
    }
    if contact_id:
        payload["contactId"] = contact_id

    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{ZOHO_BASE}/tickets", headers=hdrs, json=payload)
        return r.json()


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    if not CLIENT_ID or not CLIENT_SECRET or not SANDBOX_TOKEN:
        print("ERROR: ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, and ZOHO_REFRESH_TOKEN must be set.")
        sys.exit(1)

    print("=" * 60)
    print("ParkM — Create Test Tickets in Zoho Sandbox")
    print("=" * 60)

    # Auth
    print("\nGetting sandbox access token...")
    token = await get_access_token(SANDBOX_TOKEN)
    print("  OK")

    # Department
    depts = await get_departments(token)
    target_dept = next((d for d in depts if TARGET_DEPT.lower() in d["name"].lower()), depts[0])
    dept_id = target_dept["id"]
    print(f"  Department: {target_dept['name']} ({dept_id})")

    # Contact
    print("  Getting default contact...")
    contact_id = await get_default_contact_id(token)
    print(f"  Contact: {contact_id}")

    all_emails = (
        [{"type": "single", "idx": i + 1, **e} for i, e in enumerate(SINGLE_INTENT_EMAILS)]
        + [{"type": "multi", "idx": i + 1, **e} for i, e in enumerate(MULTI_INTENT_EMAILS)]
    )

    total = len(all_emails)
    print(f"\nCreating {total} test tickets...\n")

    results = []
    success = 0
    failed = 0
    t_start = time.time()

    for i, email in enumerate(all_emails):
        label = email.get("target_tag") or email.get("label")
        subject = email["subject"]
        body = email["body"]

        try:
            result = await create_ticket(token, dept_id, contact_id, subject, body)
            ticket_id = result.get("id")
            ticket_num = result.get("ticketNumber")

            if ticket_id:
                success += 1
                results.append({
                    "type": email["type"],
                    "index": email["idx"],
                    "label": label,
                    "ticket_id": ticket_id,
                    "ticket_number": ticket_num,
                    "subject": subject,
                })
                print(f"  [{i+1}/{total}] #{ticket_num} - {label}")
            else:
                failed += 1
                print(f"  [{i+1}/{total}] FAIL - {label}: {result}")
        except Exception as e:
            failed += 1
            print(f"  [{i+1}/{total}] ERROR - {label}: {e}")

        await asyncio.sleep(RATE_DELAY)

    elapsed = time.time() - t_start

    # Save results
    out_path = Path(__file__).parent.parent / "review" / "sandbox_test_tickets.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "sandbox_org": SANDBOX_ORG_ID,
            "department": target_dept["name"],
            "total": total,
            "success": success,
            "failed": failed,
            "tickets": results,
        }, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Done in {elapsed:.0f}s")
    print(f"  Created: {success}")
    print(f"  Failed:  {failed}")
    print(f"\nSaved: {out_path}")
    print("\nThe sandbox webhook will auto-classify each ticket.")
    print("Sadie can now open these tickets in Zoho and see the wizard live!")


if __name__ == "__main__":
    asyncio.run(main())
