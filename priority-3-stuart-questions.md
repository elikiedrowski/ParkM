# ParkM.app API — Questions for Stuart

## Access & Credentials
1. Can you share the API documentation? (URL, PDF, or Swagger/OpenAPI spec)
2. What authentication does the API use? (API key, OAuth, Bearer token?)
3. Can we get credentials for a service account with read + write access?
4. Is there a sandbox/test environment, or do we develop against production?
5. What's the base URL for the API?

## Endpoints We Need
We need access to these — can you confirm they exist and share the endpoint paths?

| What we need | Example |
|---|---|
| Customer lookup by email | `GET /customers?email=...` |
| List permits for a customer | `GET /customers/{id}/permits` |
| Payment/transaction history | `GET /customers/{id}/payments` |
| Last charge date + amount | (part of payments?) |
| Permit status (active/canceled) | (part of permits?) |
| Cancel a permit | `POST /permits/{id}/cancel` |
| Update vehicle/license plate | `PUT /permits/{id}/vehicle` |

## Technical Details
6. Are there rate limits?
7. Any IP whitelisting required? (Our server is on Railway.app — IP may change)
8. What format are responses in? (JSON assumed)
9. How is a customer identified — by email, customer ID, or both?
