import httpx
import respx

from .conftest import AUTH, groq_reply

URL = "https://api.groq.com/openai/v1/chat/completions"


def test_healthz_needs_no_token(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_requires_token(client):
    r = client.post("/v1/analyze", json={"symptoms": ["headache"]})
    assert r.status_code == 401


def test_rejects_empty_symptoms(client):
    r = client.post("/v1/analyze", headers=AUTH, json={"symptoms": []})
    assert r.status_code == 422


@respx.mock
def test_red_flag_never_calls_groq(client):
    route = respx.post(URL).mock(return_value=httpx.Response(200, json=groq_reply()))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["crushing chest pain"]}
    ).json()

    assert body["source"] == "red_flag"
    assert body["emergency"] is True
    assert body["conditionType"] == "EMERGENCY"
    assert body["specialization"] == "CARDIOLOGIST"
    assert not route.called      # the whole point of rule one


@respx.mock
def test_happy_path_uses_model(client):
    respx.post(URL).mock(return_value=httpx.Response(200, json=groq_reply()))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["itchy rash on elbows"]}
    ).json()

    assert body["source"] == "model"
    assert body["specialization"] == "DERMATOLOGIST"
    assert body["emergency"] is False
    assert body["disclaimer"]


@respx.mock
def test_model_may_escalate_to_emergency(client):
    respx.post(URL).mock(return_value=httpx.Response(
        200, json=groq_reply(specialization="NEUROLOGIST", severityScore=85)))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["worst headache of my life"]}
    ).json()

    assert body["source"] == "model"
    assert body["emergency"] is True
    assert body["conditionType"] == "EMERGENCY"


@respx.mock
def test_invented_specialization_is_rejected(client):
    respx.post(URL).mock(return_value=httpx.Response(
        200, json=groq_reply(specialization="Heart Specialist")))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["palpitations at night"]}
    ).json()

    # Degrades to the safe default instead of returning an unusable value.
    assert body["source"] == "fallback"
    assert body["specialization"] == "GENERAL_PHYSICIAN"


@respx.mock
def test_lowercase_specialization_is_normalised(client):
    respx.post(URL).mock(return_value=httpx.Response(
        200, json=groq_reply(specialization="ent specialist")))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["ringing in my ears"]}
    ).json()

    assert body["source"] == "model"
    assert body["specialization"] == "ENT_SPECIALIST"


@respx.mock
def test_groq_down_degrades_not_500(client):
    respx.post(URL).mock(return_value=httpx.Response(503))

    r = client.post("/v1/analyze", headers=AUTH, json={"symptoms": ["sore throat"]})

    assert r.status_code == 200
    assert r.json()["source"] == "fallback"


@respx.mock
def test_rate_limited_degrades(client):
    respx.post(URL).mock(
        return_value=httpx.Response(429, headers={"retry-after": "9"}))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["back pain"]}
    ).json()
    assert body["source"] == "fallback"


@respx.mock
def test_timeout_degrades(client):
    respx.post(URL).mock(side_effect=httpx.ReadTimeout("too slow"))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["knee pain"]}
    ).json()
    assert body["source"] == "fallback"


@respx.mock
def test_truncated_json_degrades(client):
    respx.post(URL).mock(return_value=httpx.Response(200, json={
        "choices": [{"message": {"content": '{"specialization": "DERMATO'}}]}))

    body = client.post(
        "/v1/analyze", headers=AUTH, json={"symptoms": ["dry skin"]}
    ).json()
    assert body["source"] == "fallback"
