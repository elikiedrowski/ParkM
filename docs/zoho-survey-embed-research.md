# Zoho Survey Embed — Feasibility Research (Apr 19, 2026)

**Timebox:** 15 min, per Apr 16 call.
**Outcome:** Technically feasible, but not worth the complexity right now. **Deferred.**

## What Sadie asked for

CSRs currently close a ticket using two marketplace apps in Zoho Desk's right panel:
1. Our CSR Wizard (custom-built)
2. Zoho Survey's "ParkM Support Survey" app

The Survey app generates a UNIQUE trackable link per click that ties the response back to a specific ticket + CSR. Sadie wanted to know if we could embed that link-generation step into our wizard so CSRs don't switch apps.

## Findings

| Question | Answer |
|---|---|
| Does Zoho Survey have a public API for generating unique links? | **Yes.** REST API with OAuth, supports custom variables (ticket ID, CSR). Rate limit 60 req/min. |
| Can our existing Desk OAuth tokens hit that API? | **No.** Zoho Survey uses its own OAuth scope (`ZohoSurvey.invitation.CREATE`). We'd need a separate OAuth app + separate token lifecycle. |
| Can our widget invoke the Survey marketplace app directly via the Desk SDK? | **No.** `ZOHODESK.invoke()` only routes within our own extension. No cross-extension invocation API. |
| Any existing examples of extensions embedding Survey? | **None found** in Zoho developer docs or community forums. |

## Implementation cost if we did it

1. Register a new Zoho OAuth app for Survey API access (client_id, client_secret, refresh token)
2. Store credentials on Railway (env vars) + handle token refresh
3. Build FastAPI endpoint `/survey/generate-link` that:
   - Accepts ticket_id + CSR email
   - Calls Zoho Survey API with custom variables
   - Returns the unique trackable URL
4. Wire a widget button "Send Survey" that calls the endpoint and inserts link into the reply
5. Test OAuth token refresh edge cases

Rough estimate: 4–6 hours of work, plus ongoing maintenance of a second OAuth token.

## Recommendation: Defer

From the Apr 16 call:
> Eli: "Boom, boom, boom. I'm doing a whole bunch over here. I'm done. Boom. I don't think that's worth even looking into."
> Sadie: "No, no. My only thought was just if we could get everything in the wizard."
> Katie: "Let's 15 minutes tops."

The current workflow (click Survey app in marketplace right panel → send) is one extra click and the panel is already right there. The integration would save perhaps 5 seconds per closed ticket but introduce a second OAuth token to maintain. Not a worthwhile trade right now.

**Revisit if:** survey completion rates drop, CSRs complain about the context switch, or we're doing a broader Desk-integrations overhaul anyway.
