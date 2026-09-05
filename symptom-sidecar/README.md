# MediFind Symptom Sidecar

A small FastAPI service that turns free-text symptoms into a routing decision:
which specialist, how urgent, and why. Backed by Groq for the language
understanding, with a deterministic safety screen in front of it.

Deployment runbook: see `NOTES.md` for the operational log.

## Why it exists

`SymptomAnalysisServiceImpl` in the Java backend matches symptom text against a
curated keyword dictionary. It is fast, free and deterministic, but it cannot
read a sentence — "my chest feels heavy and my left arm has been tingling"
contains no dictionary key, so it falls through to `GENERAL_PHYSICIAN`.
This service fills that gap.

The response deliberately matches the `SymptomAnalysisService.SymptomAnalysis`
record field-for-field, so the Java side can adopt it by writing one HTTP
client — no controller or DTO changes.

## Two rules the code enforces

1. **Deterministic safety logic never sits behind the model.** `redflags.py`
   runs before any network call. If it fires, the service returns EMERGENCY
   immediately and never contacts Groq. The model may *escalate* urgency
   (`severityScore >= 70`), never de-escalate it.
2. **The output is a closed set.** `specialization` is passed straight to
   `doctorRankingService.rankDoctors(...)`, so a value outside the 17 known
   specializations returns zero doctors. The prompt is built from the same
   tuple the validator checks against, so the two cannot drift apart.

Any failure — timeout, 429, invented specialization, truncated JSON — degrades
to a safe `GENERAL_PHYSICIAN` response with `source: "fallback"` rather than
returning a 5xx. Every response carries `source` so you can tell the three
paths apart in production.

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest respx          # test-only

cp .env.example .env               # paste your real Groq key into it
uvicorn app.main:app --reload
```

```bash
curl -s -X POST localhost:8000/v1/analyze \
  -H "X-API-Token: dev-token-change-me" -H "Content-Type: application/json" \
  -d '{"symptoms":["itchy red patches on my elbows"]}' | python3 -m json.tool
```

Watch the `source` field: `red_flag` short-circuits, `model` is the happy path,
`fallback` means something upstream failed — the log line says what.

## Tests

```bash
python -m pytest                   # 35 tests, no network, no tokens spent
```

`respx` mocks the Groq HTTP boundary, so the suite covers rate limits,
timeouts, truncated JSON and invented specializations without spending money.

The quality suite is separate and **not** run by pytest, because it costs real
tokens:

```bash
.venv/bin/python -m tests.run_eval
```

It scores the live model against `tests/eval_cases.py`. Run it whenever you
change the prompt, the model ID or the temperature, and record the score in
`NOTES.md`. Prompt changes that feel better routinely score worse.

## Layout

| File | Responsibility |
|---|---|
| `app/config.py` | Settings from `SIDECAR_*` env vars |
| `app/taxonomy.py` | The 17 specializations, fallback, disclaimer |
| `app/redflags.py` | Deterministic emergency screen |
| `app/prompt.py` | Instructions sent to the model |
| `app/schemas.py` | Request/response shapes and the closed-set validator |
| `app/groq_client.py` | The only code that talks to Groq |
| `app/analyzer.py` | Orchestrates screen → model → merge → degrade |
| `app/routes.py` | Auth and the endpoint |
| `app/main.py` | App assembly, shared HTTP client, `/healthz` |

## Deploying

`deploy/` holds the systemd unit, the Nginx site and the redeploy script.
The service listens on a Unix socket at `/run/sidecar/gunicorn.sock` — nothing
binds a network port except Nginx.

## Caveats

- The red-flag patterns are **illustrative, not clinical**. A real deployment
  wants them reviewed by a clinician and traced to a published triage protocol.
- A symptom checker that reports urgency can fall under medical-device rules
  depending on the claims made and the market. Worth a qualified answer before
  this is public.
- Nothing is logged except model name, token counts, which branch fired and
  error counts. **Never add the symptom text to a log line** — journald keeps
  logs for weeks and anyone with sudo can read them.
