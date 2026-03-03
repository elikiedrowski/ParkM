# ParkM Sales Productivity Initiative — Meeting Prep

**Meeting:** Tuesday, March 3, 2026 ~11:00 AM
**Attendees:** Patrick Cameron, Lauren Kiedrowski, Eli Kiedrowski
**Purpose:** Review "art of the possible" for Patrick's 5 sales productivity ideas

---

## Background

Patrick shared 5 ideas to improve sales rep productivity. The core thesis: use AI-driven pre-sales intelligence to turn average reps from 3x to 6x ROI. All ideas are low-risk (internal rep tooling, not customer-facing AI), and they extend the same AI pattern ParkM already has running in Zoho Desk.

---

## The 5 Initiatives — Our Assessment

### 1. Google Reviews as Leads — "Blue Ocean" Opportunity

**Patrick's idea:** Flag bad Google reviews that mention parking as high-value leads (~$500/lead).

**Our take: This is real and buildable.**

- Google Places API lets us search for apartment complexes by metro and pull reviews
- We run each review through GPT-4o to detect parking complaints, classify severity, and score the property
- Output: a ranked lead list with a "Parking Pain Score" per property
- Nobody else is doing this for the parking vertical — Patrick's "blue ocean" assessment checks out

**The catch:** Google's official API only returns 5 reviews per property. But 5 is likely enough for lead qualification — if even 1 of the top 5 reviews mentions parking, that's a signal. Third-party services (Outscraper, Lobstr.io) can pull all reviews if we need deeper coverage later.

**Estimate:**

| | Time | API Cost |
|---|---|---|
| POC — 1 metro, ~500 properties | 1-2 weeks | ~$5 |
| Scale — 10 metros, ~5K properties | +1 week | ~$150 |
| National — 50 metros, ~25K properties | +2 weeks | ~$750 |

### 2. Property Manager Turnover Alerts

**Patrick's idea:** New PMs are brought in to "clean this place up" — they're open to new vendors. Detect turnover and prioritize those accounts.

**Our take: ALN already does this.** The question is what tier ParkM has access to.

- ALN contacts every property on a 25-business-day cycle and tracks PM name, regional manager, and management company
- They logged 11,000+ PM changes in Q1 2022 alone
- **Vendor Edge Pro** has Watch Lists with email alerts on PM changes
- **Compass tier** has API access for direct CRM integration

**Estimate:**

| | Time | Cost |
|---|---|---|
| If ALN Compass (API access) | 1-2 weeks to integrate | Included in ALN sub |
| If Vendor Edge Pro (alerts/exports) | 1 week to build import pipeline | Included in ALN sub |
| If no ALN sub or basic tier | Needs subscription discussion | ~$31K-$60K/year |

**Key question for Patrick:** What ALN tier does ParkM have? He mentioned reps "currently use this tool."

### 3. AI-Generated Account Briefs ("Sell 90")

**Patrick's idea:** Auto-generate a one-pager per target account so reps walk in prepared. He called this "Sell 90."

**Our take: This is the platform that ties everything together.** The brief aggregates signals from all the other initiatives into one deliverable per property.

Data sources per brief:

| Data | Source | Ready? |
|---|---|---|
| Property details (units, location, rent, occupancy) | ALN | Depends on access |
| Property manager name + tenure | ALN | Depends on access |
| Parking complaints + pain score | Google Reviews + GPT-4o | Build in Phase 1 |
| Nearby event venues + distances | Google Maps API | Easy add |
| Upcoming events at nearby venues | Ticketmaster API (free) | Easy add |
| Nearby ParkM customers | Internal CRM | Needs CRM access |
| Suggested talking points | GPT-4o generated | Build in Phase 2 |

**Estimate:**

| | Time | Cost |
|---|---|---|
| MVP brief (reviews + venues + GPT talking points) | 2-3 weeks | ~$50/month API costs |
| Full brief (+ ALN data + CRM + events) | 4-6 weeks | ALN sub + ~$100/month |

Delivery options: PDF email digest, web dashboard, or Zoho CRM card. Simplest first = email/PDF.

### 4. Event Venue Proximity Intelligence

**Patrick's idea:** Properties near venues like Red Rocks can charge premium event-night parking. Arm reps with this knowledge.

**Our take: Easy win, great "wow factor" in the brief.**

- Google Maps API calculates distance from any property to a curated venue list (stadiums, amphitheaters, convention centers)
- Ticketmaster/SeatGeek APIs provide upcoming events (free tier)
- Example output: "This property is 0.3 mi from American Airlines Center. 48 events/year. Next: Mavs vs. Lakers, March 15."

**Estimate:**

| | Time | Cost |
|---|---|---|
| Build + integrate into brief | 3-5 days | ~$5/month (Google Maps free tier covers most of it) |

### 5. ALN Target List Generation

**Patrick's idea:** Use ALN to generate target lists of properties near existing ParkM customers, then enrich with intelligence from initiatives 1-4.

**Our take: ALN is the foundation — everything else layers on top.**

```
ALN Property Universe
 ├── Google Reviews → Parking Pain Score
 ├── PM Turnover → Timing Signal
 ├── Venue Proximity → Revenue Opportunity
 └── Account Brief → Synthesized Output for Rep
```

This is less a standalone initiative and more the "glue." Once we know what ALN access looks like, building the enrichment pipeline is straightforward.

**Estimate:** Included in the account brief work (Initiative 3).

---

## Risk Framework

Patrick categorized AI use cases as high-risk vs. low-risk. Everything we're proposing is low-risk:

| | Low Risk (All 5 initiatives) | High Risk (Not proposing) |
|---|---|---|
| **What** | Pre-sales intelligence, lead scoring, account briefs | Bots talking to customers/prospects |
| **Who sees it** | Internal reps only | Prospects and customers |
| **If it's wrong** | Rep wastes 5 min reading a brief | Brand damage, lost deal |
| **Proof point** | AI classifier already live in Zoho Desk | — |

---

## Proposed Phased Roadmap

### Phase 1 — Google Reviews POC (1-2 weeks)

Pick one metro. Scan apartment complexes. Score them for parking pain. Deliver a ranked lead list to Chad.

| Initiative | What Gets Built | Hours |
|---|---|---|
| **1. Google Reviews as Leads** | Google Places API integration, GPT-4o parking classifier, pain scoring, ranked lead list output | 22–30 |
| Cross-cutting | Infra setup, config, initial testing | 3–5 |
| **Phase 1 Total** | | **25–35** |

### Phase 2 — PM Turnover + Account Briefs (3-4 weeks after Phase 1)

Integrate ALN data for PM turnover detection. Build the account brief generator that combines reviews data from Phase 1 with turnover signals into a one-page brief per property with AI-generated talking points.

| Initiative | What Gets Built | Hours |
|---|---|---|
| **2. PM Turnover Monitoring** | ALN integration, change detection logic, alert system (email or CRM push) | 15–25 |
| **3. Account Brief Generator** | Data aggregation layer, brief template, GPT-4o talking points, delivery mechanism | 25–40 |

**Phase 2 hours depend on two open questions:**

| Scenario | #2 PM Turnover | #3 Account Brief | Phase 2 Total |
|---|---|---|---|
| ALN API access + basic HTML/CSV output | 15–18 | 25–30 | **40–48** |
| ALN API access + polished PDF + email delivery | 15–18 | 35–40 | **50–58** |
| ALN CSV export only + basic HTML/CSV output | 22–25 | 25–30 | **47–55** |
| ALN CSV export only + polished PDF + email delivery | 22–25 | 35–40 | **57–65** |

### Phase 3 — Full Intelligence Platform (3-5 weeks after Phase 2)

Add venue/event enrichment and ALN target list generation. Automate refresh cadence. Connect to CRM if applicable.

| Initiative | What Gets Built | Hours |
|---|---|---|
| **4. Venue Proximity** | Google Maps distance calculations, curated venue list, Ticketmaster/SeatGeek event calendar integration | 10–16 |
| **5. ALN Target List Enrichment** | Enrichment pipeline (layer initiatives 1-4 onto ALN property universe), filtering and prioritization | 10–16 |
| Cross-cutting | End-to-end QA, project management | 5–7 |
| **Phase 3 Total** | | **25–39** |

### Summary

| Phase | Initiatives Included | Hours |
|---|---|---|
| Phase 1 — Google Reviews POC | #1 Google Reviews as Leads | 25–35 |
| Phase 2 — PM Turnover + Account Briefs | #2 PM Turnover + #3 Account Briefs | 40–65 |
| Phase 3 — Full Intelligence | #4 Venue Proximity + #5 ALN Enrichment | 25–39 |
| **Total (all 5 initiatives)** | | **90–139** |

## Estimated Costs

| Item | Monthly Ongoing |
|---|---|
| Google APIs (Places, Maps) | ~$50-150 depending on scale |
| OpenAI (GPT-4o classification) | ~$20-50 depending on volume |
| ALN subscription (if not existing) | ~$2,500-$5,000/month |
| Third-party review service (if needed) | ~$25-150 depending on provider |
| **Total monthly run cost (excl. ALN)** | **~$100-350/month** |

At $500/lead, ParkM would break even generating **1 lead per month** (excluding ALN). The ROI math is strongly in favor.

---

## Questions to Discuss with Patrick

1. **ALN Access** — What tier does ParkM have? Is API access available, or export only? Can we get a data sample?
2. **Target Market** — Which metro for the Phase 1 POC? (Dallas, Denver, another?)
3. **Rep Workflow** — How do reps consume intelligence today? Email, CRM, spreadsheet?
4. **Lead Delivery** — How should parking pain leads reach Chad's team?
5. **Budget** — Appetite for API costs (~$100-350/month) beyond existing ALN?

---

## Example Output: Account Brief

Below is what a completed account brief would look like for a sales rep. This is the end-state deliverable from Phase 2.

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

## What We're Asking Patrick For

1. **Go/no-go on Phase 1** — green light to build the Google Reviews POC for one metro
2. **ALN access details** — so we can scope Phase 2 accurately
3. **A target metro** — so we can deliver real results, not hypotheticals
4. **Intro to Chad** (or Chad's input) on how reps want to receive this intelligence
