# ParkM Sales Productivity — Detailed Hour Breakdown

This is the component-level breakdown behind the phase estimates in [sales-productivity-initiative.md](sales-productivity-initiative.md).

*Updated March 8, 2026 — Priorities reordered per customer, Event Venue scope expanded, PM/meeting hours added.*

---

## Phase 1 — Google Reviews POC

| Priority | Component | Hours |
|---|---|---|
| **#1. Google Reviews as Leads** | | **25–27** |
| | Outscraper integration (keyword-filtered review scraping + property discovery) | 4–6 |
| | GPT-4o parking classifier (prompt engineering, tuning, testing) | 8–10 |
| | Scoring algorithm (parking pain score 0–100) | 3–4 |
| | Output formatting (ranked lead list, CSV/JSON export) | 2–3 |
| | Real-data testing & iteration | 5–6 |
| **Cross-cutting** | Infra setup, config, API key management, initial testing | 3–5 |
| **Phase 1 Dev Subtotal** | | **28–32** |
| **PM / Meetings / Demos** | Project management, status meetings, demo sessions | 2–3 |
| **Phase 1 Total** | | **30–35** |

---

## Phase 2 — Account Briefs + Event Venue + Smart Target Lists

*Priorities #2, #3, #4 are interdependent and should be developed concurrently.*

| Priority | Component | Hours |
|---|---|---|
| **#2. AI-Generated Account Briefs** | | **38–40** |
| | Data aggregation layer (pull from all sources) | 10–12 |
| | GPT-4o talking points prompt (engineering + testing) | 4–6 |
| | Brief template (HTML to polished PDF rendering) | 8–10 |
| | Email delivery pipeline (scheduling, formatting, recipients) | 9–12 |
| | Integration testing across data sources | 4–6 |
| | | |
| **#3. Event Venue Proximity Intelligence** | | **22–26** |
| | Google Maps Distance Matrix integration | 4–4 |
| | Curated venue list per metro (stadiums, amphitheaters, convention centers) | 2–3 |
| | Ticketmaster / SeatGeek event calendar integration | 5–6 |
| | Wire venue + event data into account brief output | 2–3 |
| | Reverse venue lookup — find all apartment complexes near a venue | 5–6 |
| | Cross-reference reverse results with ALN property data + scoring | 3–4 |
| | | |
| **#4. Smart Target List Generation** | | **13–16** |
| | Enrichment pipeline (layer priorities #1, #3, #5 onto ALN property universe) | 7–10 |
| | Filtering / prioritization logic (rank by pain score, turnover, proximity) | 4–6 |
| | | |
| **Cross-cutting** | End-to-end QA, integration testing | 5–7 |
| **Phase 2 Dev Subtotal** | | **78–89** |
| **PM / Meetings / Demos** | Project management, weekly status meetings, demo sessions | 4–6 |
| **Phase 2 Total** | | **82–95** |

---

## Phase 3 — PM Turnover Alerts

*Can be built standalone and integrated into briefs/target lists after the fact.*

| Priority | Component | Hours |
|---|---|---|
| **#5. Automated PM Turnover Alerts** | | **18–21** |
| | ALN API integration (change detection client) | 9–10 |
| | Change detection / diff logic | 5–6 |
| | Alert system (email or CRM push) | 4–5 |
| | Integration into account briefs and target lists | 2–3 |
| **Phase 3 Dev Subtotal** | | **20–24** |
| **PM / Meetings / Demos** | Project management, status meetings, demo sessions | 1–2 |
| **Phase 3 Total** | | **21–26** |

---

## Grand Total

| Phase | Priorities | Dev Hours | PM/Meetings | Total Hours |
|---|---|---|---|---|
| Phase 1 — Google Reviews POC | #1 Google Reviews | 28–32 | 2–3 | 30–35 |
| Phase 2 — Briefs + Venue + Target Lists | #2 Briefs + #3 Venue + #4 Target Lists | 78–89 | 4–6 | 82–95 |
| Phase 3 — PM Turnover Alerts | #5 PM Turnover | 20–24 | 1–2 | 21–26 |
| **Total (all 5 priorities)** | | **126–145** | **7–11** | **133–156** |
