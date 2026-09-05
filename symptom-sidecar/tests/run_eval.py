"""Score the live model against tests/eval_cases.CASES.

Costs real Groq tokens. Needs SIDECAR_GROQ_API_KEY in the environment
or in .env. Run from the project root:

    .venv/bin/python -m tests.run_eval
"""
import asyncio
import time

import httpx

from app.analyzer import analyze
from app.groq_client import GroqClient
from app.schemas import AnalyzeRequest
from tests.eval_cases import CASES


async def main() -> None:
    hits = 0
    started = time.perf_counter()

    async with httpx.AsyncClient() as http:
        groq = GroqClient(http)
        for symptoms, expected in CASES:
            t0 = time.perf_counter()
            got = await analyze(AnalyzeRequest(symptoms=symptoms), groq)
            ms = (time.perf_counter() - t0) * 1000

            ok = got.specialization == expected
            hits += ok
            mark = "PASS" if ok else "FAIL"
            print(
                f"{mark}  {ms:6.0f}ms  {got.source:9s} "
                f"expected={expected:<19s} got={got.specialization:<19s} "
                f"conf={got.confidence}"
            )
            if not ok:
                print(f"        {symptoms[0]!r}")

    total = len(CASES)
    elapsed = time.perf_counter() - started
    print(f"\nscore: {hits}/{total} = {hits / total:.0%}   ({elapsed:.1f}s total)")


if __name__ == "__main__":
    asyncio.run(main())
