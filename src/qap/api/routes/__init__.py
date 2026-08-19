"""Thin FastAPI routers over immutable QAP artifact readers."""

from qap.api.routes.baskets import router as baskets_router
from qap.api.routes.experiments import router as experiments_router
from qap.api.routes.health import router as health_router
from qap.api.routes.operations import router as operations_router
from qap.api.routes.pairs import router as pairs_router
from qap.api.routes.portfolios import router as portfolios_router
from qap.api.routes.product_market_data import router as product_market_data_router
from qap.api.routes.product_research import router as product_research_router
from qap.api.routes.research_universe import router as research_universe_router
from qap.api.routes.scanner import router as scanner_router
from qap.api.routes.workspace import router as workspace_router

__all__ = [
    "baskets_router",
    "experiments_router",
    "health_router",
    "operations_router",
    "pairs_router",
    "portfolios_router",
    "product_market_data_router",
    "product_research_router",
    "research_universe_router",
    "scanner_router",
    "workspace_router",
]
