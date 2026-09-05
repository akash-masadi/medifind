import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from .analyzer import analyze
from .config import get_settings
from .groq_client import GroqClient
from .schemas import AnalyzeRequest, AnalyzeResponse


def require_token(x_api_token: str = Header(default="")) -> None:
    # compare_digest, not ==, so timing doesn't leak the token.
    if not secrets.compare_digest(x_api_token, get_settings().api_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid X-API-Token")


def get_groq(request: Request) -> GroqClient:
    # The shared AsyncClient created at startup — see main.py.
    return GroqClient(request.app.state.http)


router = APIRouter(prefix="/v1", dependencies=[Depends(require_token)])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_symptoms(
    payload: AnalyzeRequest,
    groq: GroqClient = Depends(get_groq),
) -> AnalyzeResponse:
    return await analyze(payload, groq)
