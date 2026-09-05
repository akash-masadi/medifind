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

- [ ] Paste a real Groq key into `.env` and run `python -m tests.run_eval`;
      record the score below.
- [ ] Confirm the model ID `llama-3.3-70b-versatile` is still current at
      console.groq.com/docs/models — retired IDs return 404 `model_not_found`.
- [ ] Get the red-flag list reviewed by a clinician.
- [ ] `SymptomSearchController.java` logs `request.getSymptoms()` at INFO —
      change to a count before this goes anywhere near production data.

## Eval scores

| Date | Model | Prompt change | Score |
|---|---|---|---|
| | | | _(not yet run — needs a real API key)_ |
