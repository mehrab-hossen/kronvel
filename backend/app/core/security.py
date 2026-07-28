"""
Security context stub.
Today: placeholder for API key validation.
Day 5+: extended with agent execution context (which identity/policy scope
an agent action runs under), referenced in SECURITY.md as a reviewed surface.
"""
from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if settings.environment == "development":
        return  # auth disabled in local dev for MVP velocity
    if x_api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    # Real key validation is added when this MVP moves toward a non-demo deployment.

    