# Recommended Solution Strategy for ParkM — Sales Productivity Initiative

Proposed Project Timeline

| Priority | Focus Area | Timeline | Dependencies |
|---|---|---|---|
| 1 | Google Reviews as Valuable Lead Source | Week 1-3 | None |
| 2 | AI-Generated Account Briefs | Week 3-7 | Priority 1 data |
| 3 | Event Venue Proximity Intelligence | Week 3-7 | Google Maps API |
| 4 | Smart Target List Generation | Week 5-7 | Priorities 1, 3, 5 |
| 5 | Automated PM Turnover Alerts | Week 7-9 | ALN API |

Total Timeline: 9 weeks with parallel execution
Parallel Execution: Priorities 2, 3, and 4 are interdependent and developed concurrently in Phase 2
Critical Path: Account Brief platform (Priority 2) is the delivery vehicle for all intelligence
Quick Wins: Priority 1 delivers immediate value as a standalone POC

## Priority 1: Google Reviews as Valuable Lead Source

Timeline: Week 1-3

Problem it solves: Reps have no systematic way to identify properties with parking problems. Target lists are built manually today — reps query ALN for properties with 250+ units, 80%+ occupancy, built before 2025. There is no signal-based prospecting, and no way to identify properties actively struggling with parking. Nobody else in the parking vertical is mining Google Reviews for lead intelligence — this is a "blue ocean" opportunity.

Solution:

- Use Lobstr.io (cloud-based browser automation) to scrape Google Reviews for apartment complexes by metro area
- Lobstr.io provides keyword filtering, language/date filters, and scheduled recurring scrapes ("Squids") that run automatically (daily, weekly, etc.) with export to CSV, JSON, Google Sheets, or S3
- Run scraped reviews through GPT-4o AI classifier to detect parking complaints, classify severity, and extract key themes (not enough spots, visitor towing, reserved spot violations, garage safety, etc.)
- Generate a "Parking Pain Score" (0–100) per property based on complaint volume, severity, and recency
- Output: ranked lead list with pain scores, complaint summaries, and selected review quotes — exportable as CSV/JSON for import into CRM or outbound tools

Google Places API — ruled out: The official Google Places API is hard-coded to return only 5 "most relevant" reviews per property. No pagination, no keyword filtering, no customization. Google treats the Places API as a discovery tool, not a review analysis tool. Third-party scraping bypasses this limitation entirely.

Legal note: Public data scraping operates in a legal grey area, but US courts (hiQ v. LinkedIn) have ruled that scraping publicly available data is not a CFAA violation. Data is used for internal lead qualification only — no impersonation or GDPR violations.

Why this first:

- Fully independent — no dependencies on other priorities
- Immediate, tangible value — delivers a ranked lead list reps can use right away
- Proves the AI pattern — same GPT-4o classification already live in ParkM's Zoho Desk
- Low risk — internal rep tooling, not customer-facing
- Foundation for enrichment — pain scores feed into Account Briefs (Priority 2) and Smart Target Lists (Priority 4)

Estimated impact: New lead source that no competitor is using; signal-based prospecting replaces manual ALN queries; at $500/lead, ParkM breaks even generating 1 lead per month

## Priority 2: AI-Generated Account Briefs

Timeline: Week 3-7

Problem it solves: Outside reps are "old school pavement pounding sellers" who drive routes by state. They walk into properties with no preparation — no context on parking complaints, no awareness of nearby venues, no knowledge of PM tenure or recent management changes. Building a dossier on a target account is a manual, time-consuming process that most reps skip entirely.

Solution:

- Build an AI-powered account brief platform that auto-generates a one-pager per target property
- Data aggregation layer pulls from all available sources into a unified property profile:
  - Property details from ALN (units, location, rent, occupancy, year built)
  - Property manager name, tenure, and management company from ALN
  - Parking complaints and pain score from Lobstr.io reviews + GPT-4o (Priority 1)
  - Nearby event venues and distances from Google Maps API (Priority 3)
  - Upcoming events at nearby venues from Ticketmaster API (Priority 3)
  - Nearby ParkM customers from internal CRM
- GPT-4o generates contextual talking points based on the aggregated data — e.g., "Lead with the new PM role," "Reference resident parking complaints," "Highlight event-night revenue opportunity"
- Brief template renders aggregated data into a polished, branded PDF
- Email delivery pipeline sends briefs on a configurable schedule (daily/weekly digest, or on-demand per property)
- Delivery options: PDF email digest (simplest first), web dashboard, or CRM card

Data sources and readiness:

| Data | Source | Ready? |
|---|---|---|
| Property details (units, location, rent, occupancy) | ALN | Yes — full API access confirmed |
| Property manager name + tenure | ALN | Yes — full API access confirmed |
| Parking complaints + pain score | Lobstr.io reviews + GPT-4o | Built in Priority 1 |
| Nearby event venues + distances | Google Maps API | Built in Priority 3 |
| Upcoming events at nearby venues | Ticketmaster API (free) | Built in Priority 3 |
| Nearby ParkM customers | Internal CRM | Needs CRM access |
| Suggested talking points | GPT-4o generated | Built here |

Technical Dependencies:

- Priority 1 classification data (parking pain scores, complaint summaries)
- Priority 3 venue proximity data (distances, event calendars)
- ALN API access (confirmed — full access with ~150 licenses)
- CRM access for nearby ParkM customer data

Why second:

- This is the platform that ties everything together — the delivery vehicle for all intelligence
- Directly addresses the outside rep workflow — account briefs are especially valuable for route planning
- Aggregates signals from all other priorities into one actionable deliverable
- Needs Priority 1 data to be meaningful; ideally also Priority 3 venue data
- Must be developed concurrently with Priorities 3 and 4 due to interdependencies

Estimated impact: Reps walk into every meeting prepared; eliminates manual research time; standardizes pre-sales intelligence across the team; enables data-driven route planning

## Priority 3: Event Venue Proximity Intelligence

Timeline: Week 3-7

Problem it solves: Properties near major venues like Red Rocks can charge premium event-night parking, but reps don't know which properties are near venues or what events are coming up. There is no systematic way to identify venue-adjacent properties as a prospecting category. Reps currently rely on local knowledge and manual research.

Solution:

**A) Property → Nearby Venues (original scope)**
- Google Maps Distance Matrix API calculates distance from any property to a curated venue list per metro (stadiums, amphitheaters, convention centers, entertainment districts)
- Ticketmaster / SeatGeek APIs provide upcoming event calendars (free tier)
- Example output: "This property is 0.3 mi from American Airlines Center. 48 events/year. Next: Mavs vs. Lakers, March 15."
- Venue proximity data wires directly into Account Briefs (Priority 2)

**B) Venue → Nearby Apartment Complexes (new scope, March 8)**
- Given a major venue in a rep's metro, find all apartment complexes within a configurable radius (e.g., 1 mile, 3 miles)
- Cross-reference results with ALN property universe for unit counts, occupancy, and management details
- Score and rank results by unit count, occupancy, and parking pain score
- Output: "American Airlines Center — 23 apartment communities within 2 miles, 8,400 total units. Here are the top 10 targets ranked by unit count and parking pain score."
- Enables reps to prospect venue-adjacent properties as a category, not just enrich existing leads

Technical Dependencies:

- Google Maps Distance Matrix API
- Curated venue list per metro (stadiums, amphitheaters, convention centers)
- Ticketmaster / SeatGeek API for event calendar data
- ALN API for reverse venue lookup (property universe query by location)
- Priority 1 pain scores for ranking (optional but valuable)

Why third:

- Feeds directly into Account Briefs (Priority 2) — venue proximity is a key talking point
- Reverse venue lookup adds a new prospecting dimension (venue → properties)
- Revenue opportunity signal — event-night parking is a concrete dollar value reps can pitch
- Should be developed concurrently with Priority 2 due to data integration
- Google Maps API costs are minimal (free tier covers most usage)

Estimated impact: Identifies revenue opportunities reps didn't know existed; creates a new prospecting category (venue-adjacent properties); arms reps with event-specific talking points

## Priority 4: Smart Target List Generation

Timeline: Week 5-7

Problem it solves: Reps build target lists manually — querying ALN for basic criteria (250+ units, 80%+ occupancy, built before 2025). These lists have no intelligence layer, no prioritization beyond basic property attributes, and no signals about which properties are most likely to convert. The same list could be generated by any competitor with ALN access.

Solution:

- Build an enrichment pipeline that layers intelligence from all other priorities onto the ALN property universe:

```
ALN Property Universe
 ├── Google Reviews → Parking Pain Score (Priority 1)
 ├── PM Turnover → Timing Signal (Priority 5)
 ├── Venue Proximity → Revenue Opportunity (Priority 3)
 └── Account Brief → Synthesized Output for Rep (Priority 2)
```

- Filtering and prioritization logic ranks properties by pain score, PM turnover recency, venue proximity, and standard ALN attributes
- Output: "Smart" target lists that surface the highest-opportunity properties first
- This is less a standalone initiative and more the "glue" — with ALN API access confirmed, building the enrichment pipeline is straightforward once the data sources exist

Technical Dependencies:

- Priority 1 data (parking pain scores)
- Priority 3 data (venue proximity scores)
- Priority 5 data (PM turnover signals) — can integrate later if Priority 5 is deferred
- ALN API access (confirmed)

Why fourth:

- Depends on other priorities to provide the enrichment data that makes lists "smart"
- Without Priorities 1, 3, and 5, this is just another basic ALN query
- Relatively lightweight once the data sources exist — the value is in the integration, not the build
- Developed concurrently with Priorities 2 and 3 in Phase 2

Estimated impact: Replaces manual ALN queries with AI-enriched, prioritized target lists; surfaces highest-opportunity properties first; differentiates ParkM's prospecting from any competitor with basic ALN access

## Priority 5: Automated Property Manager Turnover Alerts

Timeline: Week 7-9

Problem it solves: New property managers are often brought in to "clean the place up" and are open to new vendors and solutions. But reps have no systematic way to detect PM changes — they find out through word of mouth or by accident. By the time they learn about a change, the 90-day "new regime" window may have closed. ALN tracks 11,000+ PM changes per quarter, but ParkM isn't using this data proactively.

Solution:

- Build ALN API integration specifically for PM change detection
- ALN contacts every property on a 25-business-day cycle and tracks PM name, regional manager, and management company
- Change detection / diff logic compares current ALN data against previous snapshots to identify PM changes
- Alert system notifies reps when a PM change is detected on a target or priority account — via email alert or CRM push
- Integration into Account Briefs (Priority 2): PM turnover data enriches the brief with talking points like "Congratulations on your new role — new managers typically re-evaluate vendor relationships in the first 90 days"
- Integration into Smart Target Lists (Priority 4): PM turnover becomes a prioritization signal — properties with recent PM changes rank higher

Technical Dependencies:

- ALN API access (confirmed — full access with ~150 licenses)
- Can be built standalone and integrated into Priorities 2 and 4 after the fact

Why fifth:

- Can be built independently — no dependency on other priorities
- Integration into briefs and target lists is straightforward after the fact
- Could be deferred if client sees it as lower priority relative to the other sales intelligence
- High value signal — "new regime in town" is one of the strongest prospecting triggers

Estimated impact: Captures the 90-day "new regime" prospecting window; proactive outreach instead of reactive; leverages ALN data ParkM is already paying for but not using for change detection

---

## Implementation Phasing Recommendation

### Phase 1: Google Reviews POC
Priorities: 1 (Google Reviews as Leads)
Fully independent — build and deliver as a standalone POC
Proves the AI pattern and delivers immediate value
Pick one metro, scrape reviews, score for parking pain, deliver ranked lead list
Foundation for all subsequent enrichment

### Phase 2: Account Briefs + Event Venue + Smart Target Lists
Priorities: 2 (Account Briefs) + 3 (Event Venue) + 4 (Smart Target Lists)
These are interdependent and should be developed concurrently
The Account Brief is the delivery vehicle; venue proximity and target lists are the intelligence that feeds it
Client should commit to all three — building one without the others reduces value significantly

### Phase 3: PM Turnover Alerts
Priorities: 5 (PM Turnover Alerts)
Can be built standalone and integrated into briefs/target lists after the fact
Could be deferred if client prefers to evaluate Phase 1 and 2 results first
High value but lowest urgency — ALN data will still be there

---

## Why This Phasing Makes Sense

1. **Independence:** Priority 1 has zero dependencies — it can be built, tested, and delivering value before anything else starts
2. **Interdependency:** Priorities 2, 3, and 4 feed each other — the account brief consumes venue proximity and target list data, while target lists consume pain scores and venue data. Building one without the others leaves value on the table.
3. **Risk reduction:** Phase 1 proves the AI pattern (GPT-4o classification) on a contained problem before scaling to the full intelligence platform
4. **Deferability:** Priority 5 is high-value but can be added at any time without reworking earlier phases
5. **Quick wins:** Phase 1 delivers a usable lead list in 2-3 weeks, giving reps something new immediately

---

## Risk Framework

All 5 initiatives are low-risk internal rep tooling:

| | Low Risk (All 5 Priorities) | High Risk (Not Proposing) |
|---|---|---|
| **What** | Pre-sales intelligence, lead scoring, account briefs | Bots talking to customers/prospects |
| **Who sees it** | Internal reps only | Prospects and customers |
| **If it's wrong** | Rep wastes 5 min reading a brief | Brand damage, lost deal |
| **Proof point** | AI classifier already live in Zoho Desk | — |

---

## Key Success Metrics to Track

- Number of new leads generated from Google Review mining (Phase 1)
- Parking Pain Score accuracy — validated against rep feedback and deal outcomes
- Account brief utilization rate — are reps actually using the briefs?
- Meeting preparation time reduction — before vs. after briefs
- Venue-adjacent property conversion rate — do venue-proximity leads close at higher rates?
- Smart target list quality — are enriched lists producing better leads than manual ALN queries?
- PM turnover alert response time — how quickly do reps act on turnover signals?
- Revenue attributed to AI-generated leads and intelligence

---

## Proposed Investment

| Priority | Focus Area | Anticipated Hours |
|---|---|---|
| 1 | Google Reviews as Valuable Lead Source | 28-32 |
| 2 | AI-Generated Account Briefs | 38-40 |
| 3 | Event Venue Proximity Intelligence | 22-26 |
| 4 | Smart Target List Generation | 13-16 |
| 5 | Automated PM Turnover Alerts | 20-24 |
| | **Development Subtotal** | **126-145** |
| | Project Management, Meetings, & Demos | 7-11 |
| | **Total Anticipated Hours** | **133-156** |

### Third-Party Tool Costs (Ongoing, Paid by Customer)

| Item | Monthly Cost | Notes |
|---|---|---|
| Lobstr.io (automated review scraping) | ~$10-30/month | Starts at $10/mo (~10K credits). Scales with property count. |
| Google Maps API | ~$5-20 | Distance calculations for venue proximity. Free tier covers most usage. |
| Ticketmaster / SeatGeek API | $0 | Free tier sufficient for event data |
| OpenAI GPT-4o | ~$20-50 | Classification, scoring, talking point generation |
| **Subtotal — Third-Party Tools** | **~$35-120/month** | |

### Hosting & Infrastructure Costs (Ongoing, Paid by Customer)

| Item | Monthly Cost | Notes |
|---|---|---|
| Application hosting (Railway or similar PaaS) | ~$5-20 | Depends on traffic volume and compute needs |
| Database (PostgreSQL on Railway/Supabase) | ~$0-20 | Free tier likely sufficient initially; scales with data volume |
| File storage (S3 or equivalent for generated PDFs) | ~$1-5 | Minimal — PDF briefs are small files |
| **Subtotal — Hosting & Infrastructure** | **~$6-45/month** | |

### Total Ongoing Customer Costs (Excluding ALN)

| Category | Monthly Cost |
|---|---|
| Third-party tools | ~$35-120 |
| Hosting & infrastructure | ~$6-45 |
| **Total ongoing (excl. ALN)** | **~$41-165/month** |

*Note: ALN subscription is an existing ParkM cost. ParkM currently has full API access with ~150 licenses.*
