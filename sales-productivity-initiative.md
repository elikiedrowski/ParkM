# ParkM Sales Productivity Initiative — Project Outline & SOW

**Prepared by:** The CRM Wizards (Lauren Kiedrowski, Eli Kiedrowski)
**Prepared for:** ParkM (Patrick Cameron, Chad)
**Last updated:** March 8, 2026
**Document version:** 3.0 — Priorities reordered per customer feedback, SOW cost structure added

---

## Background

ParkM has identified 5 sales productivity initiatives to improve rep effectiveness using AI-driven pre-sales intelligence. The priorities below are listed in the order specified by the customer as of March 8, 2026. All 5 initiatives are low-risk (internal rep tooling, not customer-facing AI) and extend the same AI pattern already running in ParkM's Zoho Desk environment.

**Current sales operations (confirmed March 3):**
- Reps organized by state (outbound by state, inside by state). Currently covering **33 states** with goal of every state
- Outside team described as "old school pavement pounding sellers" — account briefs especially valuable for route planning
- Target lists built manually today: reps query ALN for properties with 250+ units, 80%+ occupancy, built before 2025
- Recently stood up an outbound engine using **Klenty** (K-L-E-N-T-Y) — quarterly contract, just started
- ALN access confirmed: full access including API, ~150 licenses, ~10 in use

---

## Customer Priorities (Updated March 8, 2026)

### Priority #1: Google Reviews as Valuable Lead Source

**Customer goal:** Flag negative Google reviews that mention parking as high-potential leads.

- Use web scraping to search for apartment complexes by metro and pull reviews
- Run reviews through AI to detect parking complaints, classify severity, and score the property
- Output: a ranked lead list with a "Parking Pain Score" per property
- Nobody else is doing this for the parking vertical — a "blue ocean" opportunity

**Google Places API — ruled out (March 3 investigation):**
The official Google Places API is hard-coded to return only 5 "most relevant" reviews per property. There is no pagination, no keyword filtering, and no way to customize which reviews are returned. Google treats the Places API as a discovery tool, not a review management or lead tool. The Google Business Profile API offers unlimited reviews with filtering, but only for businesses you own/manage — not applicable here.

**Recommended approach: Outscraper (POC) + Lobstr.io (ongoing monitoring)**

Third-party scraping services bypass the API limits using cloud-based browser automation. They support keyword filtering (e.g., "parking"), unlimited review counts, and export to CSV/JSON.

| | Outscraper | Lobstr.io |
|---|---|---|
| **Best for** | Discovery — find businesses + scrape reviews in one go | Automation — scheduled recurring scrapes |
| **Keyword filtering** | Yes — keyword queries + rating filters | Yes — keyword, language, date filters |
| **Export formats** | CSV, XLSX, JSON, Parquet | CSV, JSON, Google Sheets, S3 |
| **Free tier** | First 500 reviews free | 100–1,000 credits (varies) |
| **Paid pricing** | $3 per 1,000 reviews | Starts at $10/mo (~10K credits) |

**Legal note:** Public data scraping operates in a legal grey area, but US courts (hiQ v. LinkedIn) have ruled that scraping publicly available data is not a CFAA violation. Data is used for internal lead qualification only — no impersonation or GDPR violations.

**Development estimate: 24–30 hours**

### Priority #2: AI-Generated Account Briefs

**Customer goal:** Auto-generate a one-pager per target account so reps walk in prepared.

This is the platform that ties everything together. The brief aggregates signals from the other initiatives into one deliverable per property.

**Data sources per brief:**

| Data | Source | Ready? |
|---|---|---|
| Property details (units, location, rent, occupancy) | ALN | Yes — full API access confirmed |
| Property manager name + tenure | ALN | Yes — full API access confirmed |
| Parking complaints + pain score | Outscraper reviews + GPT-4o | Built in Priority #1 |
| Nearby event venues + distances | Google Maps API | Built in Priority #3 |
| Upcoming events at nearby venues | Ticketmaster API (free) | Built in Priority #3 |
| Nearby ParkM customers | Internal CRM | Needs CRM access |
| Suggested talking points | GPT-4o generated | Built here |

**Delivery options:** PDF email digest, web dashboard, or CRM card. Simplest first = email/PDF.

**Development estimate: 35–40 hours**

### Priority #3: Event Venue Proximity Intelligence

**Customer goal:** Properties near venues like Red Rocks can charge premium event-night parking. Arm reps with this knowledge. Additionally, "flip it on its head" — given a major venue, show all surrounding apartment complexes as potential target accounts.

**Two directions:**

**A) Property → Nearby Venues (original scope)**
- Google Maps API calculates distance from any property to a curated venue list (stadiums, amphitheaters, convention centers)
- Ticketmaster/SeatGeek APIs provide upcoming events (free tier)
- Example output: "This property is 0.3 mi from American Airlines Center. 48 events/year. Next: Mavs vs. Lakers, March 15."

**B) Venue → Nearby Apartment Complexes (new scope, March 8)**
- Given a major venue in a rep's metro, find all apartment complexes within a configurable radius (e.g., 1 mile, 3 miles)
- Cross-reference with ALN property universe for unit counts, occupancy, and management details
- Output: "American Airlines Center — 23 apartment communities within 2 miles, 8,400 total units. Here are the top 10 targets ranked by unit count and parking pain score."
- Enables reps to prospect venue-adjacent properties as a category, not just enrich existing leads

**Development estimate: 18–26 hours** (expanded from original 12–16 to include reverse venue lookup)

### Priority #4: "Smart" Target List Generation

**Customer goal:** Use ALN to generate target lists of properties near existing ParkM customers, then enrich with intelligence from the other priorities.

ALN is the foundation — everything else layers on top to generate "smart" target lists:

```
ALN Property Universe
 ├── Google Reviews → Parking Pain Score
 ├── PM Turnover → Timing Signal
 ├── Venue Proximity → Revenue Opportunity
 └── Account Brief → Synthesized Output for Rep
```

This is less a standalone initiative and more the "glue." With ALN API access confirmed, building the enrichment pipeline is straightforward.

**Development estimate: 12–16 hours**

### Priority #5: Automated Property Manager Turnover Alerts

**Customer goal:** New PMs are often brought in to "clean the place up" and are open to new vendors/solutions. Detect turnover and prioritize those accounts.

- Build ALN API integration to provide automated seller alerts when PM changes are detected
- ALN contacts every property on a 25-business-day cycle and tracks PM name, regional manager, and management company (11,000+ PM changes in Q1 2022 alone)
- Integrate key target account info into AI account briefs (Priority #2)
- High turnover = prospecting signal — "new regime in town" is open to re-pitching

**ALN Access (confirmed March 3):** ParkM has full access to ALN including API. ~150 licenses, ~10 in use. Direct API integration — no spreadsheet uploads.

**Development estimate: 15–18 hours**

---

## Interdependency Analysis

**Key observation (March 8):** These priorities are not fully independent. Several are interdependent and may need concurrent development rather than strict sequential phases.

| Priority | Dependencies | Can be built standalone? |
|---|---|---|
| **#1 Google Reviews** | None | Yes — good candidate for initial phase |
| **#2 Account Briefs** | Consumes output from #1, #3, #4, #5 | No — needs at least #1 complete, ideally #3 and #4 |
| **#3 Event Venue** | Feeds into #2 (briefs) and #4 (target lists) | Partially — venue data is standalone, but full value comes from integration |
| **#4 Smart Target Lists** | Layers #1, #3, #5 onto ALN property universe | No — needs other priorities to provide enrichment data |
| **#5 PM Turnover** | Feeds into #2 (briefs) and #4 (target lists) | Yes — can be built independently, integrated later |

**Recommended phasing:**

- **Phase 1 — Priority #1 (Google Reviews):** Fully independent. Build and deliver as a standalone POC to demonstrate value.
- **Phase 2 — Priorities #2, #3, #4 (Account Briefs + Event Venue + Smart Target Lists):** These are interdependent and should be developed concurrently. The account brief is the delivery vehicle; venue proximity and target lists are the intelligence that feeds it. Client should commit to all three.
- **Phase 3 — Priority #5 (PM Turnover Alerts):** Can be built standalone and integrated into briefs/target lists after the fact. Could be deferred if client sees it as lower priority relative to the other sales intelligence.

---

## Proposed Phased Roadmap

### Phase 1 — Google Reviews POC (2–3 weeks)

Pick one metro. Scrape apartment complex reviews. Score them for parking pain. Deliver a ranked lead list.

| Component | Hours |
|---|---|
| **Priority #1: Google Reviews as Leads** | **24–30** |
| Outscraper integration (keyword-filtered review scraping + property discovery) | 4–6 |
| GPT-4o parking classifier (prompt engineering, tuning, testing) | 6–10 |
| Scoring algorithm (parking pain score 0–100) | 3–4 |
| Output formatting (ranked lead list, CSV/JSON export) | 2–3 |
| Real-data testing & iteration | 4–6 |
| Demo prep & walkthrough with stakeholders | 2–3 |
| Cross-cutting (infra setup, config, API key management) | 3–5 |
| **Phase 1 Development Subtotal** | **27–35** |
| Project management, meetings, & demos | 4–6 |
| **Phase 1 Total** | **31–41** |

### Phase 2 — Account Briefs + Event Venue + Smart Target Lists (5–7 weeks)

Build the core intelligence platform: venue proximity data (both directions), enriched target lists, and the account brief that synthesizes everything into a one-pager per property.

| Component | Hours |
|---|---|
| **Priority #2: AI-Generated Account Briefs** | **35–40** |
| Data aggregation layer (pull from all sources) | 8–12 |
| GPT-4o talking points prompt (engineering + testing) | 4–6 |
| Brief template (HTML to polished PDF rendering) | 6–10 |
| Email delivery pipeline (scheduling, formatting, recipients) | 8–12 |
| Integration testing across data sources | 4–6 |
| | |
| **Priority #3: Event Venue Proximity Intelligence** | **18–26** |
| Google Maps Distance Matrix integration | 3–4 |
| Curated venue list per metro (stadiums, amphitheaters, convention centers) | 2–3 |
| Ticketmaster / SeatGeek event calendar integration | 4–6 |
| Wire venue + event data into account brief output | 2–3 |
| Reverse venue lookup — find all apartment complexes near a venue | 4–6 |
| Cross-reference reverse results with ALN property data + scoring | 2–4 |
| | |
| **Priority #4: Smart Target List Generation** | **12–16** |
| Enrichment pipeline (layer priorities #1, #3, #5 onto ALN property universe) | 6–10 |
| Filtering / prioritization logic (rank by pain score, turnover, proximity) | 4–6 |
| | |
| Cross-cutting (end-to-end QA, integration testing) | 5–7 |
| **Phase 2 Development Subtotal** | **70–89** |
| Project management, meetings, & demos | 10–14 |
| **Phase 2 Total** | **80–103** |

### Phase 3 — PM Turnover Alerts (2–3 weeks)

Build ALN API integration for automated PM change detection. Wire turnover signals into account briefs and target lists.

| Component | Hours |
|---|---|
| **Priority #5: Automated PM Turnover Alerts** | **15–18** |
| ALN API integration (change detection client) | 8–10 |
| Change detection / diff logic | 4–6 |
| Alert system (email or CRM push) | 3–5 |
| Integration into account briefs and target lists | 2–3 |
| **Phase 3 Development Subtotal** | **17–24** |
| Project management, meetings, & demos | 3–4 |
| **Phase 3 Total** | **20–28** |

### Summary

| Phase | Priorities Included | Dev Hours | PM/Meetings | Total Hours |
|---|---|---|---|---|
| Phase 1 — Google Reviews POC | #1 Google Reviews | 27–35 | 4–6 | 31–41 |
| Phase 2 — Briefs + Venue + Target Lists | #2 Briefs + #3 Venue + #4 Target Lists | 70–89 | 10–14 | 80–103 |
| Phase 3 — PM Turnover Alerts | #5 PM Turnover | 17–24 | 3–4 | 20–28 |
| **Total (all 5 priorities)** | | **114–148** | **17–24** | **131–172** |

---

## Estimated Costs

### The CRM Wizards — Software Consulting & Development

| Phase | Hours |
|---|---|
| Phase 1 — Google Reviews POC | 31–41 |
| Phase 2 — Briefs + Venue + Target Lists | 80–103 |
| Phase 3 — PM Turnover Alerts | 20–28 |
| **Total** | **131–172** |

*Note: Includes development, project management, status meetings, and demo/review sessions.*

### Third-Party Tool Costs (Ongoing, Paid by Customer)

| Item | Monthly Cost | Notes |
|---|---|---|
| Outscraper (review scraping) | ~$15–75 | Pay-as-you-go, $3/1K reviews. Free tier covers POC. |
| Lobstr.io (automated recurring scans) | ~$10 | Optional — add when scaling to automated weekly scans |
| Google Maps API | ~$5–20 | Distance calculations for venue proximity. Free tier covers most usage. |
| Ticketmaster / SeatGeek API | $0 | Free tier sufficient for event data |
| OpenAI GPT-4o | ~$20–50 | Classification, scoring, talking point generation |
| **Subtotal — Third-Party Tools** | **~$50–155/month** | |

### Hosting & Infrastructure Costs (Ongoing, Paid by Customer)

| Item | Monthly Cost | Notes |
|---|---|---|
| Application hosting (Railway or similar PaaS) | ~$5–20 | Depends on traffic volume and compute needs |
| Database (PostgreSQL on Railway/Supabase) | ~$0–20 | Free tier likely sufficient initially; scales with data volume |
| File storage (S3 or equivalent for generated PDFs) | ~$1–5 | Minimal — PDF briefs are small files |
| **Subtotal — Hosting & Infrastructure** | **~$6–45/month** | |

### Total Ongoing Customer Costs (Excluding ALN)

| Category | Monthly Cost |
|---|---|
| Third-party tools | ~$50–155 |
| Hosting & infrastructure | ~$6–45 |
| **Total ongoing (excl. ALN)** | **~$56–200/month** |

*Note: ALN subscription is an existing ParkM cost. ParkM currently has full API access with ~150 licenses.*

At $500/lead, ParkM would break even generating **1 lead per month**. The ROI math is strongly in favor.

---

## Risk Framework

All 5 initiatives are low-risk (internal rep tooling):

| | Low Risk (All 5 priorities) | High Risk (Not proposing) |
|---|---|---|
| **What** | Pre-sales intelligence, lead scoring, account briefs | Bots talking to customers/prospects |
| **Who sees it** | Internal reps only | Prospects and customers |
| **If it's wrong** | Rep wastes 5 min reading a brief | Brand damage, lost deal |
| **Proof point** | AI classifier already live in Zoho Desk | — |

---

## Meeting History

### March 3, 2026 — Lauren/Eli/Patrick

**Decisions / Alignment:**
- All 5 initiatives reviewed and aligned. Patrick presented to Chad on March 4.
- ALN access confirmed — full access including API. Patrick shared credentials.
- Phase 1 & 2 (Zoho Desk AI — separate project) complete for initial development — waiting on team feedback from Katie and Sadie
- Notification templates added to Zoho Desk Phase 2 wizard (not in original scope)

**Questions Answered:**

| Question | Answer |
|---|---|
| ALN Access tier? | Full access including API. ~150 licenses, using ~10. |
| Rep workflow? | Outside reps = pavement pounders on routes. Inside reps organized by state. |
| How are target lists built today? | Manually — reps query ALN: 250+ units, 80%+ occupancy, built before 2025 |
| How many states? | 33 currently, goal is all states |
| Outbound tooling? | Klenty (quarterly contract, just stood up) |
| Google Places API 5-review limit? | Hard-coded top 5, no filtering/pagination. Pivoting to Outscraper + Lobstr.io. |

### March 8, 2026 — Priority Reordering & SOW Scoping

**Key decisions:**
- Customer reordered priorities: Account Briefs moved to #2, Event Venue to #3, Smart Target Lists to #4, PM Turnover to #5
- Event Venue scope expanded: added reverse lookup (venue → nearby apartment complexes as targets)
- Interdependency identified: Priorities #2, #3, #4 should be developed concurrently in Phase 2
- Priority #5 (PM Turnover) can be deferred as a standalone final phase if client prefers
- Need to prepare formal proposal and SOW with full cost breakdown

---

## Open Questions

1. **Target metro for Phase 1 POC** — Which metro to start with? (Dallas, Denver, another?)
2. **Lead delivery format** — How should parking pain leads reach the sales team?
3. **Phase 2 commitment** — Client needs to commit to #2, #3, #4 together given interdependencies (or agree to a modified approach)
4. **Priority #5 timing** — Does client want PM Turnover in the initial engagement or deferred?

---

## Example Output: Account Brief

Below is what a completed account brief would look like for a sales rep. This is the end-state deliverable from Priority #2.

---

> ## ParkM Account Brief
>
> **Prepared:** March 3, 2026 | **For:** Chad's Sales Team
>
> ---
>
> ### Sunset Ridge Apartments
> **1420 W Mockingbird Ln, Dallas, TX 75235** | [View on Google Maps](#)
>
> ---
>
> | | |
> |---|---|
> | **Units** | 312 |
> | **Year Built** | 2003 |
> | **Average Rent** | $1,485/mo |
> | **Occupancy** | 91% |
> | **Google Rating** | 3.2 / 5.0 (147 reviews) |
> | **Management Company** | Greystone Property Mgmt |
> | **Property Manager** | Jennifer Walsh |
> | **PM Start Date** | January 2026 (8 weeks ago) |
> | **Previous PM** | Marcus Rivera (2.5 years) |
>
> ---
>
> ### PRIORITY SIGNALS
>
> **PM Turnover Detected**
> New PM started 8 weeks ago. New managers typically re-evaluate vendor relationships in the first 90 days. Window is closing — act within the next 4 weeks.
>
> **Parking Pain Score: 78 / 100 (HIGH)**
> Based on analysis of 47 Google reviews mentioning parking:
>
> | Complaint | Mentions | Recency |
> |---|---|---|
> | Not enough spots / overflow | 19 | Most recent: 2 weeks ago |
> | Visitor parking / towing issues | 14 | Most recent: 1 month ago |
> | Reserved spot violations | 9 | Most recent: 3 months ago |
> | Garage lighting / safety | 5 | Most recent: 1 month ago |
>
> **Selected Reviews:**
> - *"There are NEVER enough parking spots. I've had to park on the street multiple times this week."* — Sarah M., 2 weeks ago (2 stars)
> - *"Visitor parking is a joke. My guests got towed twice."* — James R., 1 month ago (1 star)
> - *"Management does nothing about people parking in reserved spots."* — Michelle K., 3 months ago (2 stars)
>
> ---
>
> ### NEARBY VENUES
>
> | Venue | Distance | Events/Year | Next Event |
> |---|---|---|---|
> | American Airlines Center | 2.1 mi | 48 | Mavs vs. Lakers — Mar 15 |
> | Dallas Convention Center | 3.4 mi | 35 | Home & Garden Expo — Mar 22 |
> | Deep Ellum (entertainment district) | 1.8 mi | Nightly | — |
>
> Proximity to American Airlines Center = opportunity for premium event-night parking revenue.
>
> ---
>
> ### SUGGESTED TALKING POINTS
>
> 1. **Lead with the new role:** "Congratulations on your new role at Sunset Ridge. I work with a lot of property managers in the Dallas market who are looking to get parking under control early in their tenure."
>
> 2. **Reference the resident feedback:** "I've seen some resident feedback online about parking availability and visitor towing issues. We help properties like yours manage parking more efficiently — would that be worth a quick conversation?"
>
> 3. **Lead with revenue opportunity:** "With your proximity to American Airlines Center, there's an opportunity to generate revenue from event-night parking that most properties are leaving on the table. We can help you set that up."
>
> ---
>
> ### NEARBY PARKM CUSTOMERS
>
> | Property | Distance | Customer Since |
> |---|---|---|
> | The Village at Lake Highlands | 4.2 mi | 2024 |
> | Preston Hollow Apartments | 3.1 mi | 2025 |
>
> *"We already work with Preston Hollow just down the road — happy to connect you with their PM if you'd like a reference."*
>
> ---
>
> *Sources: ALN Data, Google Reviews, Google Maps, Ticketmaster, ParkM CRM*
> *Generated by ParkM Sales Intelligence*

---

## Action Items

### The CRM Wizards (Lauren / Eli)
- [ ] Prepare formal proposal document for client review (Lauren updating pricing in Google Docs)
- [ ] Confirm Phase 1 target metro with Patrick
- [ ] Determine if Phase 2 commitment model works for client (concurrent #2, #3, #4)

### ParkM (Patrick)
- [ ] Share ALN API credentials with Eli
- [ ] Confirm target metro for Phase 1 POC
- [ ] Confirm commitment to Phase 2 priorities (#2, #3, #4) as a concurrent block
- [ ] Decide on Priority #5 (PM Turnover) timing — include in initial engagement or defer?
- [ ] Resolve Zoho login / authenticator issue (talk to Stuart)
