import os

# MUST run before app.config is imported — get_settings() is lru_cached,
# so the first call freezes these values for the whole test session.
os.environ["SIDECAR_API_TOKEN"] = "test-token"
os.environ["SIDECAR_GROQ_API_KEY"] = "test-key"
os.environ["SIDECAR_ENVIRONMENT"] = "test"

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

AUTH = {"X-API-Token": "test-token"}


@pytest.fixture
def client():
    # The `with` block runs lifespan, so app.state.http exists.
    with TestClient(app) as c:
        yield c


def groq_reply(**fields) -> dict:
    """Build a fake Groq chat-completion envelope around a JSON answer."""
    answer = {
        "specialization": "DERMATOLOGIST",
        "confidence": 0.8,
        "severityScore": 20,
        "matchedSymptoms": ["itchy rash"],
        "explanation": "A skin specialist is the right first stop.",
    }
    answer.update(fields)
    return {
        "choices": [{"message": {"content": json.dumps(answer)}}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 60},
    }
