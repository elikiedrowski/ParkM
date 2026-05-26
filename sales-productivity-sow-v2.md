# ParkM Sales Productivity Technology Project — Deliverables

**Prepared by:** The CRM Wizards (Lauren Kiedrowski, Eli Kiedrowski)
**Prepared for:** ParkM (Chad, Patrick Cameron)
**Last updated:** May 26, 2026
**Document version:** v2 — Revised scope per Lauren / Chad sign-off (supersedes [v1 SOW](sales-productivity-sow.md))

---

## Project Deliverables

The project will be executed in two overlapping development phases.

---

## Phase 1: Google Reviews as Valuable Lead Source

**Timeline Estimate:** Week 1–6

### Description

Establishing an automated pipeline to identify, extract, and classify public sentiment regarding property-specific parking challenges to discover high-intent sales opportunities before competitors mine them.

### Deliverables

- Deployment of **cloud-based browser automation architectures** to systematically scrape public Google Reviews for multi-family apartment complexes across designated metropolitan areas.
- Configuration of **scheduled recurring data extraction schedules** running automatically with custom parametric filtering for language, date range boundaries, and target keywords.
- Engineering of **data pipelines** exportable to structured formats.
- Integration of an advanced **AI classification model** engineered to parse raw review text, accurately distinguish parking complaints from non-parking remarks, classify the underlying problem severity, and auto-extract core operational themes (e.g., parking spot shortages, unauthorized visitor towing, reserved space violations, etc.).
- Development of an **algorithm to calculate a standardized, weighted "Parking Pain Score"** per property based on total complaint volume, thematic severity, and historical recency.
- Delivery of a **ranked lead intelligence interface** exportable for immediate ingestion into the Client CRM platform (Zoho CRM) or outbound email tooling.

---

## Phase 2: Account Briefs & Smart Target Lists

**Timeline Estimate:** Week 4–9

### Description

Creating a centralized intelligence hub and automated delivery mechanism that equips field sales reps with synthesized property profiles, maps data, and contextual AI talking points to elevate pitch win rates and data-driven route planning.

### Deliverables

- **Architecture of an automated AI-powered account brief platform** that aggregates multi-source signals into a highly professional, cohesive one-page property profile.
- **Establishment of a real-time data aggregation layer** connecting via API to the Apartment List Network (ALN) database to dynamically fetch core multi-family metrics (total units, physical location, average rent, current occupancy, and year built) alongside property manager names, current tenure, and parent management company details.
- **Integration with the Google Maps Distance Matrix API** to calculate precise localized driving distances from prospective multi-family properties to regional high-traffic event hubs (stadiums, convention centers, amphitheaters, and entertainment districts).
- **Implementation of reverse lookup architectures** enabling representatives to query by major entertainment venue and automatically reveal all surrounding apartment communities within configurable geographical radii (e.g., 1-mile or 3-mile boundaries), ranked by unit size and parking pain scores.
- **Data connectivity with internal CRM records** to surface nearby active ParkM clients for proximity-based social proof references.
- **Deployment of generative AI prompts** to auto-synthesize context-aware sales talking points (e.g., instructing field sellers to lead conversations focusing on recent property manager turnover, specific resident review quotes, or high-yield event-night parking revenue opportunities).
- **Design of a branded, executive-ready PDF briefing template** automated for delivery across multiple pipelines (e.g., email digests, on-demand generation, Zoho CRM cards).
- **Development of an enrichment pipeline and prioritization engine** that overlays the extracted data points (parking pain scores, PM turnover timing signals, and venue proximity parameters) onto the core ALN property universe to produce prioritized **"Smart Target Lists"** unearthing premium leads.
