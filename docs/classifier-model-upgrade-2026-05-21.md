# Classifier Model Upgrade — 2026-05-21

## Summary
Switched the production ticket classifier from **`gpt-4o`** to **`gpt-4.1-mini`**.

## Motivation
- Production Railway had `AI_MODEL=gpt-4o` set, overriding the `gpt-4o-mini` default in `src/config.py`. The repo's stated intent did not match what was actually running.
- GPT-4.1-mini is a newer-generation model with better instruction-following than GPT-4o at a fraction of the cost.
- Net result of this change: quality upgrade **and** ~6× cost reduction per classified ticket.

## Cost comparison (per 1M tokens)

| Model | Input | Output | Relative cost vs. gpt-4o-mini |
|---|---|---|---|
| gpt-4o-mini | $0.15 | $0.60 | 1× |
| gpt-4.1-nano | $0.10 | $0.40 | ~0.7× |
| **gpt-4.1-mini (new)** | **$0.40** | **$1.60** | **~2.7×** |
| gpt-4.1 | $2.00 | $8.00 | ~13× |
| gpt-4o (previous prod) | $2.50 | $10.00 | ~17× |

Going from `gpt-4o` → `gpt-4.1-mini` cuts per-token cost by ~84%.

## Changes made

### 1. Code
- `src/config.py` — default `ai_model` updated from `gpt-4o-mini` to `gpt-4.1-mini`. Stale Claude-3.5-Sonnet comment removed.
- `src/services/analytics_logger.py` — added pricing entries for `gpt-4.1-nano`, `gpt-4.1-mini`, and `gpt-4.1` so `estimate_openai_cost()` reports accurate spend in analytics logs.

### 2. Production Railway (ParkM_Production / ParkM service)
- `AI_MODEL` env var updated: `gpt-4o` → `gpt-4.1-mini`. Setting a variable on Railway auto-triggers a redeploy; the next webhook-classified ticket runs on the new model.

## What to watch for
- **Calibrated confidence ranges**: the classifier prompt in `src/services/classifier.py` includes calibration guidance originally tuned for GPT-4o-mini. GPT-4.1-mini follows instructions differently and may produce a different confidence distribution. Check the next batch of `cf_ai_confidence` values vs. agent correction rates and re-tune if needed.
- **Classification accuracy**: spot-check the first ~50 tickets classified under the new model to confirm tag quality holds (or improves) vs. the previous GPT-4o baseline.
- **Sandbox parity**: this change was made directly in the production repo/Railway project per explicit request. The sandbox repo (`ParkM_Sandbox` remote) should be brought to parity before its next deploy.
