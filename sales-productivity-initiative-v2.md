# ParkM Sales Productivity Technology Project

**Prepared by:** The CRM Wizards (Lauren Kiedrowski, Eli Kiedrowski)
**Prepared for:** ParkM (Chad, Patrick Cameron)
**Last updated:** May 26, 2026
**Document version:** v2 — Revised scope per Lauren / Chad sign-off (supersedes [v1 initiative](sales-productivity-initiative.md) and [v1 SOW](sales-productivity-sow.md))

---

## Outline & Timeline

| Phase | Focus Area | Proposed Timeline |
|---|---|---|
| 1 | Google Reviews as Valuable Lead Source | Week 1–6 |
| 2 | AI-Generated Account Briefs + Smart Target List Generation | Week 4–9 |

**Total Timeline:** 9 weeks with parallel execution.

---

## Phase 1: Google Reviews as Valuable Lead Source

**Timeline:** Week 1–6

### Problem it solves

Reps have no systematic way to identify properties with parking problems. Target lists are built manually today — reps query ALN for properties with 250+ units, 80%+ occupancy, built before 2025. There is no signal-based prospecting for properties actively struggling with parking. Competitors aren't mining Google reviews for lead intelligence — "blue ocean" opportunity.

### Solution

- Use **Lobstr.io** (cloud-based browser automation) to scrape Google Reviews for apartment complexes by metro area
- Lobstr.io provides keyword filtering, language/date filters, and scheduled recurring scrapes ("Squids") that run automatically with export to CSV, JSON, Google Sheets, or S3
- Run scraped reviews through **GPT-4o** (or preferred latest model) AI classifier to detect parking complaints, classify severity, and extract key themes (not enough spots, visitor towing, reserved spot violations, garage safety, etc.)
- Generate a **"Parking Pain Score"** per property based on complaint volume, severity, and recency
- **Output:** ranked lead list with pain scores, complaint summaries, and selected review quotes — exportable as CSV/JSON for import into CRM or outbound tools

### Deliverables

Establishing an automated pipeline to identify, extract, and classify public sentiment regarding property-specific parking challenges to discover high-intent sales opportunities before competitors mine them.

- Deployment of **cloud-based browser automation architectures** to systematically scrape public Google Reviews for multi-family apartment complexes across designated metropolitan areas.
- Configuration of **scheduled recurring data extraction schedules** running automatically with custom parametric filtering for language, date range boundaries, and target keywords.
- Engineering of **data pipelines** exportable to structured formats.
- Integration of an advanced **AI classification model** engineered to parse raw review text, accurately distinguish parking complaints from non-parking remarks, classify the underlying problem severity, and auto-extract core operational themes (e.g., parking spot shortages, unauthorized visitor towing, reserved space violations, etc.).
- Development of an **algorithm to calculate a standardized, weighted "Parking Pain Score"** per property based on total complaint volume, thematic severity, and historical recency.
- Delivery of a **ranked lead intelligence interface** exportable for immediate ingestion into the Client CRM platform (Zoho CRM) or outbound email tooling.

### Why this first

- Fully independent — no dependencies on other priorities
- Immediate, tangible value — delivers a ranked lead list reps can use right away
- Proves the AI pattern — same GPT-4o (or preferred latest model) classification already live in ParkM's Zoho Desk
- Low risk — internal rep tooling, not customer-facing
- Foundation for enrichment — pain scores feed into Account Briefs and Smart Target Lists

### Estimated impact

New lead source that competitors aren't using; signal-based prospecting replaces manual queries. High-value convertible leads deliver hard ROI that pays for this project.

---

## Phase 2: Account Briefs + Smart Target Lists

**Timeline:** Week 4–9

### Problem it solves

Outside reps are "old school pavement pounding sellers" who drive routes by state. They walk into properties with light preparation — lacking detailed context on parking complaints, awareness of nearby venue opportunities, or knowledge of PM tenure/recent management changes. Building a dossier on a target account is a manual, time-consuming process.

ParkM also builds target lists manually — querying ALN for basic criteria (250+ units, 80%+ occupancy, built before 2025). These lists have no intelligence layer, no prioritization beyond basic property attributes, and no signals about which properties are most likely to convert.

### Solution Part I — AI-Powered Account Brief Platform

Build an AI-powered account brief platform that auto-generates a one-pager per target property. A data aggregation layer pulls from all available sources into a unified property profile:

- Property details from **ALN** (units, location, rent, occupancy, year built)
- Property manager name, tenure, and management company from **ALN**
- Parking complaints and pain score from **Lobstr.io reviews + GPT-4o** (or preferred latest model)
- Nearby ParkM customers from **internal CRM**
- Nearby event venues and distances from **Google Maps API**

#### A) Property → Nearby Venues

- Google Maps Distance Matrix API calculates distance from any property to a curated venue list per metro (stadiums, amphitheaters, convention centers, entertainment districts)
- Example output: *"This property is 0.3 mi from American Airlines Center"*
- Venue proximity data wires directly into Account Briefs

#### B) Venue → Nearby Apartment Complexes

- Given a major venue in a rep's metro, find all apartment complexes within a configurable radius (e.g., 1 mile, 3 miles)
- Cross-reference results with ALN property universe for unit counts, occupancy, and management details
- Score and rank results by unit count, occupancy, and parking pain score
- Example output: *"American Airlines Center — 23 apartment communities within 2 miles, 8,400 total units. Here are the top 10 targets ranked by unit count and parking pain score."*
- Enables reps to prospect venue-adjacent properties as a category, not just enrich existing leads

#### Brief generation and delivery

- **GPT-4o** (or preferred latest model) generates contextual talking points based on the aggregated data — e.g., "Lead with the new PM role," "Reference resident parking complaints," "Highlight event-night revenue opportunity"
- Brief template renders aggregated data into a polished, branded **PDF**
- **Delivery options:** PDF email digest (simplest first), web dashboard, or CRM card. Email delivery can send briefs on a configurable schedule (daily/weekly digest, or on-demand per property).

### Solution Part II — Smart Target List Enrichment Pipeline

Build an enrichment pipeline that layers all the above intelligence onto the ALN property universe:

```
ALN Property Universe
 ├── Google Reviews → Parking Pain Score
 ├── PM Turnover → Timing Signal
 ├── Venue Proximity → Revenue Opportunity
 └── Account Brief → Synthesized Output for Rep
```

- Filtering and prioritization logic ranks properties by pain score, PM turnover recency, venue proximity, and standard ALN attributes
- **Output:** "Smart" target lists that surface the highest-opportunity properties first
- This is less a standalone initiative and more the "glue" — with ALN API access, building the enrichment pipeline is straightforward once the data sources exist

### Deliverables

Creating a centralized intelligence hub and automated delivery mechanism that equips field sales reps with synthesized property profiles, maps data, and contextual AI talking points to elevate pitch win rates and data-driven route planning.

- **Architecture of an automated AI-powered account brief platform** that aggregates multi-source signals into a highly professional, cohesive one-page property profile.
- **Establishment of a real-time data aggregation layer** connecting via API to the Apartment List Network (ALN) database to dynamically fetch core multi-family metrics (total units, physical location, average rent, current occupancy, and year built) alongside property manager names, current tenure, and parent management company details.
- **Integration with the Google Maps Distance Matrix API** to calculate precise localized driving distances from prospective multi-family properties to regional high-traffic event hubs (stadiums, convention centers, amphitheaters, and entertainment districts).
- **Implementation of reverse lookup architectures** enabling representatives to query by major entertainment venue and automatically reveal all surrounding apartment communities within configurable geographical radii (e.g., 1-mile or 3-mile boundaries), ranked by unit size and parking pain scores.
- **Data connectivity with internal CRM records** to surface nearby active ParkM clients for proximity-based social proof references.
- **Deployment of generative AI prompts** to auto-synthesize context-aware sales talking points (e.g., instructing field sellers to lead conversations focusing on recent property manager turnover, specific resident review quotes, or high-yield event-night parking revenue opportunities).
- **Design of a branded, executive-ready PDF briefing template** automated for delivery across multiple pipelines (e.g., email digests, on-demand generation, Zoho CRM cards).
- **Development of an enrichment pipeline and prioritization engine** that overlays the extracted data points (parking pain scores, PM turnover timing signals, and venue proximity parameters) onto the core ALN property universe to produce prioritized **"Smart Target Lists"** unearthing premium leads.

### Why second

- This is the platform that ties everything together — the delivery vehicle for all intelligence
- Directly addresses the outside rep workflow — account briefs are especially valuable for route planning
- Aggregates signals into one actionable deliverable

### Estimated impact

Reps walk into every meeting prepared; eliminates manual research time; standardizes pre-sales intelligence across the team; enables data-driven route planning. Identifies revenue opportunities reps didn't know existed; creates a new prospecting category (venue-adjacent properties). Replaces manual ALN queries with AI-enriched, prioritized target lists; surfaces highest-opportunity properties first; differentiates ParkM's prospecting from competitors with basic ALN access.

---

## Proposed Investment

| Development Phase | Focus Area | Estimated Hours |
|---|---|---|
| 1 | Google Reviews as Valuable Lead Source | 60 – 65 |
| 2 | AI-Generated Account Briefs + Smart Target List Generation | 90 – 95 |
| | **Development Subtotal** | **150 – 160** |
| Cross-Cutting | Project Mgmt, Meetings, & Demos | 14 – 18 |
| | **Total Anticipated Hours** | **164 – 178** |

---

## Estimated Third-Party Tool Costs (Ongoing, Paid by Customer)

| Item | Monthly Cost | Notes |
|---|---|---|
| Automated review scraping | ~$10–30/month | Starts at $10/mo (~10K credits). Scales with property count. |
| Google Maps API | ~$5–20 | Distance calculations for venue proximity. Free tier covers most usage. |
| LLM | ~$20–50 | Classification, scoring, talking point generation. |
| **Subtotal — Third-Party Tools** | **~$35–120/month** | |

---

## Estimated Hosting & Infrastructure Costs (Ongoing, Paid by Customer)

| Item | Monthly Cost | Notes |
|---|---|---|
| Application hosting (Railway or similar PaaS) | ~$5–20 | Depends on traffic volume and compute needs. |
| Database (PostgreSQL on Railway/Supabase) | ~$0–20 | Free tier likely sufficient initially; scales with data volume. |
| File storage (S3 or equivalent for generated PDFs) | ~$1–5 | Minimal — PDF briefs are small files. |
| **Subtotal — Hosting & Infrastructure** | **~$6–45/month** | |

---

## Estimated Total Ongoing Customer Costs (Excluding ALN)

| Category | Monthly Cost |
|---|---|
| Third-party tools | ~$35–120 |
| Hosting & infrastructure | ~$6–45 |
| **Total ongoing (excl. ALN)** | **~$41–165/month** |

*Note: ALN subscription is an existing ParkM cost.*
