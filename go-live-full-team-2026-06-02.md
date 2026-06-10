# Full-Team Go-Live — Session Handoff (June 2, 2026, ~9:50pm MT)

Phases 1–3 of the ParkM AI Wizard opened to the **entire CSR team** (was a
3→8 person pilot). Executed Tuesday night June 2 rather than Wednesday AM, at
Eli's call. This doc is the portable record of what was done, how it was
verified, and how to roll back.

## What changed in production

### 1. Access opened to everyone
- **Mechanism:** deleted the `WIDGET_ALLOWED_AGENTS` env var on prod Railway.
  Code default `os.getenv("WIDGET_ALLOWED_AGENTS", "")` → empty string →
  `main.py:1088` returns `allowed: true` for every agent.
- **Command used:** `railway variable delete WIDGET_ALLOWED_AGENTS`
  (the CLI rejects setting an empty value via `--set`, so *delete* is the way).
- Deleting auto-triggers a deploy, but the live container kept serving the
  **old baked-in env** until the new deploy reached `SUCCESS`. Had to wait for
  deploy completion before `/widget/access` actually flipped. A manual
  `railway redeploy --yes` was also run.

### 2. Page layout cleaned up (done manually by Eli in Zoho UI)
- Removed the standalone **Tagging** field from the layout.
- Moved **AI Tags** + **Agent Corrected Tags** into **Additional Information**.
- Hid the standalone **AI Classification** section (data still shows in the
  wizard panel on the right).
- Note: removing a field from a *page layout* hides it from the UI but does
  **not** delete the field org-wide — `Tagging` still appears in API responses.

## Verification (all green)

| Check | Result |
|---|---|
| `/health` | healthy — Zoho connected, classifier ready |
| Deploy | new build `SUCCESS`, live |
| `/widget/access?email=<anyone>` | `{"allowed": true}` (pilot, brand-new, manager, blank) |
| `WIDGET_ALLOWED_AGENTS` | confirmed removed from prod service |
| Custom fields read post-layout | `cf_ai_tags` + `cf_agent_corrected_tags` both read via prod API |
| Classifier active on live tickets | newest tickets tagged (#100598–#100603 all have `cf_ai_tags`) |

## Rollback (back to pilot-only in ~1 min)

Re-add the var with the last pilot list and redeploy:

```
WIDGET_ALLOWED_AGENTS=eli@thecrmwizards.com,sadie@parkm.com,delainey@parkm.com,mekenzie@parkm.com,brody@parkm.com,tricia@parkm.com,sophie@parkm.com,emma@parkm.com
```

```
railway variable set "WIDGET_ALLOWED_AGENTS=<value above>"
railway redeploy --yes
```

## Infra reference

- **Prod URL:** https://parkm-production-7e56.up.railway.app
- **Railway project:** `ParkM_Production` — id `43c381fd-7043-4625-bd32-2ba43abc5b2b`
  (ParkM-owned, shared into Eli's personal workspace where sandbox also lives;
  shows under "My Projects" but is ParkM-owned). CLI logged in as
  eli@thecrmwizards.com.
- **Prod Zoho org:** 854251057 | **Sandbox org:** 856336669
- Local `.env` points at **sandbox**. To hit prod from local, override
  `ZOHO_ORG_ID=854251057` + `ZOHO_REFRESH_TOKEN=$(cat .production_refresh_token)`.
- `AI_MODEL=gpt-4.1-mini` (prod).

## Open / remaining items

- **Eli:** visual eyeball of the wizard rendering in Zoho Desk on a live
  ticket (API side already confirmed).
- **Sadie:** give the trained CSR team the go-ahead this morning (Wed Jun 3).
- **Non-blocking cleanup:** orphaned prod fields `cf_ai_intent` + `cf_tag_testing`
  still exist — confirm with Sadie before deleting.
- **Open longer-term:** Phase 4/5 scope docs owed to Katie.

## Go-live update email (final version, to Sadie / cc Katie)

> Hi Sadie,
>
> We're live — Phases 1–3 are now open to the entire CSR team. Everything's
> done and verified on our end:
>
> - Access opened to all CSRs — the pilot allowlist is removed; every agent now
>   sees the wizard on their tickets automatically, no per-user setup.
> - Ticket layout updated: the standalone Tagging field is gone. AI Tags and
>   Agent Corrected Tags now sit in Additional Information, and the duplicate AI
>   Classification section is hidden (that data still lives in the wizard panel).
>
> Since the team's already trained, they're clear to start whenever you give
> the word this morning. I'll be watching production through the first wave and
> will jump on anything that comes up.
>
> Best,
> Eli
