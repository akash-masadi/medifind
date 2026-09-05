import asyncio
import json
import logging
import httpx
from .config import get_settings
log = logging.getLogger("sidecar.groq")


class GroqUnavailable(Exception):
    """Raised when Groq cannot give us a usable answer right now."""


class GroqClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._settings = get_settings()

    async def complete_json(self, system: str, user: str) -> dict:
        s = self._settings
        payload = {
            "model": s.groq_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # JSON mode. The word "JSON" must appear in the prompt or
            # the API rejects the request.
            "response_format": {"type": "json_object"},
            # 0 = as reproducible as this gets. Creativity is not wanted here.
            "temperature": 0,
            "max_tokens": s.groq_max_tokens,
        }
        headers = {"Authorization": f"Bearer {s.groq_api_key}"}

        # Two attempts. Retrying more on a 4-second budget just makes the
        # caller wait for a failure it could have had sooner.
        for attempt in (1, 2):
            try:
                r = await self._client.post(
                    f"{s.groq_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=httpx.Timeout(s.groq_timeout_seconds, connect=2.0),
                )
            except httpx.TimeoutException:
                log.warning("groq timeout attempt=%s", attempt)
                if attempt == 2:
                    raise GroqUnavailable("timeout") from None
                continue
            except httpx.HTTPError as exc:
                raise GroqUnavailable(f"transport: {exc}") from exc

            # 429 = rate limited. Groq tells you how long to wait; believe it.
            if r.status_code == 429:
                wait = float(r.headers.get("retry-after", "1"))
                log.warning("groq rate limited, retry-after=%s", wait)
                if attempt == 2 or wait > 2.0:
                    raise GroqUnavailable("rate_limited")
                await asyncio.sleep(wait)
                continue

            # 5xx is worth one retry; 4xx is our bug and never will be.
            if r.status_code >= 500:
                if attempt == 2:
                    raise GroqUnavailable(f"upstream_{r.status_code}")
                continue
            if r.status_code >= 400:
                log.error("groq rejected request: %s %s", r.status_code, r.text[:300])
                raise GroqUnavailable(f"client_error_{r.status_code}")

            body = r.json()
            content = body["choices"][0]["message"]["content"]
            usage = body.get("usage", {})
            log.info(
                "groq ok model=%s prompt_tokens=%s completion_tokens=%s",
                s.groq_model, usage.get("prompt_tokens"), usage.get("completion_tokens"),
            )
            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                # Rare with JSON mode, but truncation by max_tokens does it.
                raise GroqUnavailable("unparseable_json") from exc

        raise GroqUnavailable("exhausted")