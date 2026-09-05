import logging

from pydantic import ValidationError

from . import redflags
from .groq_client import GroqClient, GroqUnavailable
from .prompt import SYSTEM_PROMPT, build_user_message
from .schemas import AnalyzeRequest, AnalyzeResponse, ModelAnswer
from .taxonomy import DISCLAIMER, FALLBACK

log = logging.getLogger("sidecar.analyze")

EMERGENCY_THRESHOLD = 70


async def analyze(req: AnalyzeRequest, groq: GroqClient) -> AnalyzeResponse:
    # ---- Rule 1: deterministic screen first, and it short-circuits. ----
    flagged = redflags.screen(req.symptoms)
    if flagged is not None:
        spec, severity, matched = flagged
        log.info("red flag fired spec=%s severity=%s", spec, severity)
        return AnalyzeResponse(
            specialization=spec,
            emergency=True,
            conditionType="EMERGENCY",
            confidence=0.99,
            severityScore=severity,
            # A pattern can match across the " | " join boundary without
            # matching any single phrase; fall back to echoing the input.
            matchedSymptoms=matched or req.symptoms,
            explanation=(
                "These symptoms can indicate a medical emergency. "
                "Please seek immediate medical attention."
            ),
            source="red_flag",
            disclaimer=DISCLAIMER,
        )

    # ---- Ask the model. Any failure degrades; nothing propagates. ----
    try:
        raw = await groq.complete_json(
            SYSTEM_PROMPT, build_user_message(req.symptoms, req.age, req.sex)
        )
        answer = ModelAnswer.model_validate(raw)
    except GroqUnavailable as exc:
        log.warning("degraded: groq unavailable (%s)", exc)
        return _fallback(req)
    except ValidationError as exc:
        # Model returned JSON, but not JSON we accept — e.g. an invented
        # specialization. Log the reason, not the patient's symptoms.
        log.warning("degraded: model answer rejected (%s errors)", exc.error_count())
        return _fallback(req)

    # ---- Rule 1 again: the model may escalate, never de-escalate. ----
    emergency = answer.severityScore >= EMERGENCY_THRESHOLD

    return AnalyzeResponse(
        specialization=answer.specialization,
        emergency=emergency,
        conditionType="EMERGENCY" if emergency else "NORMAL",
        confidence=round(answer.confidence, 2),
        severityScore=answer.severityScore,
        matchedSymptoms=answer.matchedSymptoms or req.symptoms,
        explanation=answer.explanation,
        source="model",
        disclaimer=DISCLAIMER,   # server-supplied, never from the model
    )


def _fallback(req: AnalyzeRequest) -> AnalyzeResponse:
    """Always available, always safe, deliberately unhelpful."""
    return AnalyzeResponse(
        specialization=FALLBACK,
        emergency=False,
        conditionType="NORMAL",
        confidence=0.2,
        severityScore=20,
        matchedSymptoms=req.symptoms,
        explanation=(
            "We could not analyse these symptoms automatically. "
            "A general physician can assess you and refer you onward."
        ),
        source="fallback",
        disclaimer=DISCLAIMER,
    )
