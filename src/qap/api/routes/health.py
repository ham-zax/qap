"""Health route for the local read-only API."""

from fastapi import APIRouter

from qap.api.schemas import HealthDto

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthDto, operation_id="getHealth")
def health() -> HealthDto:
    return HealthDto()


__all__ = ["router"]
