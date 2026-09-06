# Operational notes

Running log of what worked, what didn't, and the eval scores. Dated entries,
newest last. In six months you will be a stranger to this service and this
file is the only thing that remembers.

## 2026-09-05 — first build

Local: Python 3.14.6 in `.venv`. `pytest` → 35 passed.

**Three red-flag misses found by the tests, all the same bug class.** The
original patterns required adjacent keywords, but people do not write that way:

| Phrase | Old pattern | Result |
|---|---|---|
| `chest feels heavy` | `chest (pain\|pressure\|tight\|heav)` | missed |
| `my face is drooping` | `face droop` | missed |
| `ending my life` | `end my life` | missed |
| `his speech is slurred` | `slurred speech` | missed (word order) |

Fixed with `[\w\s]{0,N}` gaps and both word orders. `[\w\s]` rather than `.`
so a match can never span the `" | "` separator between two symptom phrases.
All four phrasings are now permanent regression cases in `test_redflags.py`.

Lesson: the screen that exists to catch emergencies is exactly the code where
adjacency assumptions do the most damage. Test it with prose, not keywords.

Verified end to end against a running server:

- `/healthz` → 200, no auth
- no token → 401
- `["chest feels heavy", "left arm tingling since morning"]` → `source: red_flag`,
  `CARDIOLOGIST`, severity 90, **no Groq call**
- placeholder API key → `source: fallback`, logged
  `degraded: groq unavailable (client_error_401)`, HTTP 200 not 500
- `{"symptoms": []}` → 422
- confirmed zero symptom text in the logs

## TODO before this is real

- [x] Real key + eval run. See below.
- [x] Model ID corrected — see "model availability" below.
- [ ] Get the red-flag list reviewed by a clinician.
- [ ] `SymptomSearchController.java` logs `request.getSymptoms()` at INFO —
      change to a count before this goes anywhere near production data.

## Eval scores

| Date | Model | Prompt change | Score |
|---|---|---|---|
| 2026-09-05 | `openai/gpt-oss-120b` | baseline | **14/15 = 93%** |

Latency 530–1035 ms per call, ~800 ms typical. 12.2 s for the 15-case suite.

### The one failure

`"sharp pain in lower right belly since last night"` → `GENERAL_PHYSICIAN`
(conf 0.78), expected `GASTROENTEROLOGIST`.

Arguably the eval is wrong, not the model: acute right-lower-quadrant pain is a
classic appendicitis presentation, which needs urgent *surgical* assessment —
neither answer is really right, and `GASTROENTEROLOGIST` was a sloppy label.

**Action for clinical review:** this may belong in `redflags.py` rather than in
the model path at all. Add to the list of patterns for a clinician to rule on.

## 2026-09-05 — model availability

The first eval run scored 1/15, every case `source: fallback`. Two stacked
causes, found by bisecting with plain `curl` rather than reading code:

1. **401** — the real key was in the repo-root `.env`; the sidecar reads
   `symptom-sidecar/.env`, which still held the `gsk_replace_me` placeholder.
   The key now lives in `symptom-sidecar/.env`. The root `.env` still has a
   duplicate `SIDECAR_*` block (lines ~83-90) — **delete it**, two sources of
   truth for a secret is a hazard. Both files are gitignored; verified the key
   is not in git history.
2. **404 `model_not_found`** — `llama-3.3-70b-versatile` is not available to
   this account. `GET /openai/v1/models` with the key is the definitive check;
   it returned 14 models, no Llama chat models among them. Switched to
   `openai/gpt-oss-120b`.

Also tested `openai/gpt-oss-20b`: faster (665 ms vs 915 ms) but it returned
`"confidence": "HIGH"` — a string where the schema wants a float, which the
validator rejects into a fallback. A concrete demonstration of why the closed
schema is validated rather than trusted. Staying on 120b.

`groq_max_tokens` raised 400 → 700: gpt-oss spends completion tokens on
reasoning before the JSON appears (202 used on a trivial case), and truncation
shows up as `unparseable_json`, not as an obvious error.
