# ParkM Sales Productivity — Detailed Hour Breakdown

This is the component-level breakdown behind the phase estimates in [sales-productivity-initiative.md](sales-productivity-initiative.md).

---

## Phase 1 — Google Reviews POC

| Initiative | Component | Hours |
|---|---|---|
| **1. Google Reviews as Leads** | | **24–30** |
| | Google Places API integration (search + review retrieval) | 4–6 |
| | GPT-4o parking classifier (prompt engineering, tuning, testing) | 6–10 |
| | Scoring algorithm (parking pain score 0–100) | 3–4 |
| | Output formatting (ranked lead list, CSV/JSON export) | 2–3 |
| | Real-data testing & iteration | 4–6 |
| | Demo prep & walkthrough with stakeholders | 2–3 |
| **Cross-cutting** | Infra setup, config, API key management, initial testing | 3–5 |
| **Phase 1 Total** | | **27–35** |

---

## Phase 2 — PM Turnover + Account Briefs

| Initiative | Component | Hours |
|---|---|---|
| **2. PM Turnover Monitoring** | | **15–25** |
| | ALN integration (API client or CSV import pipeline) | 8–12 |
| | Change detection / diff logic | 4–6 |
| | Alert system (email or CRM push) | 3–5 |
| | | |
| **3. Account Brief Generator** | | **35–40** |
| | Data aggregation layer (pull from all sources) | 8–12 |
| | GPT-4o talking points prompt (engineering + testing) | 4–6 |
| | Brief template (HTML to polished PDF rendering) | 6–10 |
| | Email delivery pipeline (scheduling, formatting, recipients) | 8–12 |
| | Integration testing across data sources | 4–6 |

**Phase 2 total (ALN API access confirmed March 3):**

| Initiative | Hours |
|---|---|
| #2 PM Turnover (ALN API integration) | 15–18 |
| #3 Account Brief (polished PDF + email) | 35–40 |
| **Phase 2 Total** | **50–58** |

---

## Phase 3 — Full Intelligence Platform

| Initiative | Component | Hours |
|---|---|---|
| **4. Venue Proximity** | | **12–16** |
| | Google Maps Distance Matrix integration | 3–4 |
| | Curated venue list per metro (stadiums, amphitheaters, convention centers) | 2–3 |
| | Ticketmaster / SeatGeek event calendar integration | 4–6 |
| | Wire venue + event data into account brief output | 2–3 |
| | | |
| **5. ALN Target List Enrichment** | | **12–16** |
| | Enrichment pipeline (layer initiatives 1–4 onto ALN property universe) | 6–10 |
| | Filtering / prioritization logic (rank by pain score, turnover, proximity) | 4–6 |
| | | |
| **Cross-cutting** | End-to-end QA, project management | 5–7 |
| **Phase 3 Total** | | **29–39** |

---

## Grand Total

| Phase | Initiatives | Hours |
|---|---|---|
| Phase 1 — Google Reviews POC | #1 Google Reviews as Leads | 27–35 |
| Phase 2 — PM Turnover + Account Briefs | #2 PM Turnover + #3 Account Briefs | 50–58 |
| Phase 3 — Full Intelligence | #4 Venue Proximity + #5 ALN Enrichment | 29–39 |
| **Total (all 5 initiatives)** | | **106–132** |
