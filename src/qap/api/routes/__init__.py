"""Thin FastAPI routers over immutable QAP artifact readers."""

from qap.api.routes.experiments import router as experiments_router
from qap.api.routes.health import router as health_router
from qap.api.routes.pairs import router as pairs_router
from qap.api.routes.portfolios import router as portfolios_router

__all__ = [
    "experiments_router",
    "health_router",
    "pairs_router",
    "portfolios_router",
]
