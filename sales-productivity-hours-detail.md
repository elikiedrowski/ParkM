# ParkM Sales Productivity — Detailed Hour Breakdown

This is the component-level breakdown behind the phase estimates in [sales-productivity-initiative.md](sales-productivity-initiative.md).

*Updated March 8, 2026 — Priorities reordered per customer, Event Venue scope expanded, PM/meeting hours added.*

---

## Phase 1 — Google Reviews POC

| Priority | Component | Hours |
|---|---|---|
| **#1. Google Reviews as Leads** | | **24–30** |
| | Outscraper integration (keyword-filtered review scraping + property discovery) | 4–6 |
| | GPT-4o parking classifier (prompt engineering, tuning, testing) | 6–10 |
| | Scoring algorithm (parking pain score 0–100) | 3–4 |
| | Output formatting (ranked lead list, CSV/JSON export) | 2–3 |
| | Real-data testing & iteration | 4–6 |
| | Demo prep & walkthrough with stakeholders | 2–3 |
| **Cross-cutting** | Infra setup, config, API key management, initial testing | 3–5 |
| **Phase 1 Dev Subtotal** | | **27–35** |
| **PM / Meetings / Demos** | Project management, status meetings, demo sessions | 4–6 |
| **Phase 1 Total** | | **31–41** |

---

## Phase 2 — Account Briefs + Event Venue + Smart Target Lists

*Priorities #2, #3, #4 are interdependent and should be developed concurrently.*

| Priority | Component | Hours |
|---|---|---|
| **#2. AI-Generated Account Briefs** | | **35–40** |
| | Data aggregation layer (pull from all sources) | 8–12 |
| | GPT-4o talking points prompt (engineering + testing) | 4–6 |
| | Brief template (HTML to polished PDF rendering) | 6–10 |
| | Email delivery pipeline (scheduling, formatting, recipients) | 8–12 |
| | Integration testing across data sources | 4–6 |
| | | |
| **#3. Event Venue Proximity Intelligence** | | **18–26** |
| | Google Maps Distance Matrix integration | 3–4 |
| | Curated venue list per metro (stadiums, amphitheaters, convention centers) | 2–3 |
| | Ticketmaster / SeatGeek event calendar integration | 4–6 |
| | Wire venue + event data into account brief output | 2–3 |
| | Reverse venue lookup — find all apartment complexes near a venue (NEW) | 4–6 |
| | Cross-reference reverse results with ALN property data + scoring (NEW) | 2–4 |
| | | |
| **#4. Smart Target List Generation** | | **12–16** |
| | Enrichment pipeline (layer priorities #1, #3, #5 onto ALN property universe) | 6–10 |
| | Filtering / prioritization logic (rank by pain score, turnover, proximity) | 4–6 |
| | | |
| **Cross-cutting** | End-to-end QA, integration testing | 5–7 |
| **Phase 2 Dev Subtotal** | | **70–89** |
| **PM / Meetings / Demos** | Project management, weekly status meetings, demo sessions | 10–14 |
| **Phase 2 Total** | | **80–103** |

---

## Phase 3 — PM Turnover Alerts

*Can be built standalone and integrated into briefs/target lists after the fact.*

| Priority | Component | Hours |
|---|---|---|
| **#5. Automated PM Turnover Alerts** | | **15–18** |
| | ALN API integration (change detection client) | 8–10 |
| | Change detection / diff logic | 4–6 |
| | Alert system (email or CRM push) | 3–5 |
| | Integration into account briefs and target lists | 2–3 |
| **Phase 3 Dev Subtotal** | | **17–24** |
| **PM / Meetings / Demos** | Project management, status meetings, demo sessions | 3–4 |
| **Phase 3 Total** | | **20–28** |

---

## Grand Total

| Phase | Priorities | Dev Hours | PM/Meetings | Total Hours |
|---|---|---|---|---|
| Phase 1 — Google Reviews POC | #1 Google Reviews | 27–35 | 4–6 | 31–41 |
| Phase 2 — Briefs + Venue + Target Lists | #2 Briefs + #3 Venue + #4 Target Lists | 70–89 | 10–14 | 80–103 |
| Phase 3 — PM Turnover Alerts | #5 PM Turnover | 17–24 | 3–4 | 20–28 |
| **Total (all 5 priorities)** | | **114–148** | **17–24** | **131–172** |

---

## Change Log

| Date | Change |
|---|---|
| March 3, 2026 | Initial estimates. ALN API access confirmed. Google Places API ruled out. |
| March 8, 2026 | Priorities reordered per customer. Event Venue scope expanded (reverse lookup). PM/meeting/demo hours added. Interdependency analysis added. SOW cost structure added. |
