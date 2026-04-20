# Live Learning Loop — Classifier Design

**Status:** Design — implementation pending (target: Apr 20, 2026)
**Owner:** Eli Kiedrowski
**Decided in:** ParkM:CRM Wizards weekly status call, Apr 16, 2026

## Problem

The classifier (GPT-4o-mini, 51 tags) currently runs against a fixed system prompt
containing tag definitions. CSR corrections — when an agent overrides
`cf_ai_tags` by setting `cf_agent_corrected_tags` — are written to Postgres but
never fed back to the model. So the same misclassification repeats indefinitely.

Sadie's first 200-ticket review found 31 mistagged tickets (~82% accuracy). Many
errors followed clear patterns (over-tagging "Customer double charged", missing
"Customer cancelling a permit and refunding" when secondary topics are mentioned,
etc.) — exactly the kind of feedback that should propagate automatically.

## Goal

When a CSR corrects a tag, future classifications should benefit from that
correction within minutes — without fine-tuning, redeployment, or manual prompt
edits.

## Approach: in-context few-shot injection

On each `/webhook/ticket` call:

1. Look up the most recent N corrections from the `corrections` Postgres table,
   filtered by `department_id`.
2. Format them into a "Recent human corrections" block.
3. Inject the block into the classifier's system prompt before calling OpenAI.

```
Recent human corrections (learn from these — same pattern, same tag):

  - Subject: "cancel my permit and refund me"
    Correct tag: Customer cancelling a permit and refunding
    AI had picked: Customer update vehicle info

  - Subject: "my permit stopped working last week"
    Correct tag: Customer inquiring for locked down permit
    AI had picked: Customer additional permit

  ... (up to N entries)
```

GPT then has those examples in-context when classifying the new ticket.

## Parameters

| Parameter | Value | Why |
|---|---|---|
| `N` (corrections to inject) | 20 | Enough variety, fits comfortably under context limit |
| Cache TTL | 600 s (10 min) | Balances freshness vs. DB load |
| Cache key | `corrections:{department_id}` | Per-department isolation |
| Subject truncation | 120 chars | Keeps prompt tight |
| Order | Most recent first | Recency bias is desirable |

## Per-department isolation

The cache and DB query both filter by `department_id`. Production CSR corrections
will only influence production classifications. Sandbox corrections will only
influence sandbox. This prevents test data from polluting prod and vice versa.

## What gets cached vs. what's fresh

- **Cached for 10 min:** the formatted few-shot block (one block per dept)
- **Fresh on every call:** nothing extra — the cached block is dropped straight
  into the prompt

When the cache expires, the next classification triggers a single DB query
(`SELECT * FROM corrections WHERE department_id = ? ORDER BY timestamp DESC LIMIT 20`)
and rebuilds the block.

## Cost impact

Approx +600 tokens per classification (20 corrections × ~30 tokens each). With
GPT-4o-mini input pricing at $0.15/MTok, that's **+$0.0001 per ticket**.
OpenAI prompt caching halves this further on repeated calls within 5 min.

For ~200 tickets/day (current volume), incremental cost is well under
$0.10/month. Trivial.

## Why not fine-tuning?

| | Few-shot injection | Fine-tuning |
|---|---|---|
| Time for new correction to take effect | ≤10 min | Days (re-training cycle) |
| Cost | $0.0001/ticket | $5–20/training run |
| Rollback | Disable injection flag | Retrain previous checkpoint |
| Debuggability | Read prompt directly | Opaque |
| Data quality risk | Low (only N most recent) | High (every correction enters weights) |

Fine-tuning is the right answer at much higher correction volume (1000s/month).
At current scale, in-context learning is strictly better.

## Failure modes & mitigations

| Failure | Mitigation |
|---|---|
| Bad correction enters cache (CSR mistake) | Cache rolls over in 10 min once a better correction is made; can manually delete the row |
| DB query fails | Catch exception, fall back to base prompt (no corrections injected); log warning |
| Prompt too long with future tag growth | N is configurable; can drop to 10 if needed |
| Sandbox corrections leak to prod | `department_id` filter prevents this |

## Disable switch

A single env var `LIVE_LEARNING_ENABLED=false` skips the injection step entirely
and reverts to the base prompt. Useful for A/B comparison or emergency rollback.

## Validation plan

1. Backfill: take Sadie's 31 mistagged tickets, re-classify them with the
   live-learning loop active using the corrections she identified. Measure
   accuracy lift.
2. Sandbox round 2: ~100 tickets across uncommon tags. Compare base prompt vs.
   live-learning accuracy.
3. Production rollout: enable for production once sandbox accuracy meets bar
   (target ≥90%).

## Implementation files

- `src/services/classifier.py` — add `_get_recent_corrections_block()` and inject
  into system prompt
- `src/db/database.py` — add helper `read_recent_corrections(engine, department_id, limit)`
- `src/services/analytics_aggregator.py` — no change (cache is separate)
- `main.py` — no change (transparent to webhook handler)
