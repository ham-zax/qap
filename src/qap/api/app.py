"""FastAPI application factory for immutable QAP research evidence."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from qap.api.basket_views import BasketArtifactReader
from qap.api.errors import ApiBoundaryError
from qap.api.history_views import HistoryReader
from qap.api.operations import OperationManager
from qap.api.paper_operation_views import PaperOperationReader
from qap.api.readers import RunArtifactReader
from qap.api.routes import (
    baskets_router,
    experiments_router,
    health_router,
    history_router,
    operations_router,
    pairs_router,
    paper_operations,
    portfolios_router,
    product_current_evidence_router,
    product_market_data_router,
    product_pair_study_router,
    product_research_router,
    research_recipes_router,
    research_universe_router,
    scanner_router,
    workspace_router,
)
from qap.api.scanner_views import ScannerArtifactReader
from qap.api.schemas import ErrorDetailDto, ErrorEnvelopeDto
from qap.api.settings import ApiSettings
from qap.product_current_approved import CurrentApprovedResearch
from qap.product_current_evidence import ProductCurrentEvidenceStore
from qap.product_market_data import ProductMarketData
from qap.product_market_data_prepare import ProductMarketDataPreparation
from qap.product_pair_study import ProductPairStudy
from qap.product_universe import ProductUniverse
from qap.research_recipe_entry import ResearchRecipeService


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    context: dict[str, str],
) -> JSONResponse:
    payload = ErrorEnvelopeDto(
        error=ErrorDetailDto(code=code, message=message, context=context)
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


def create_app(settings: ApiSettings) -> FastAPI:
    """Create the local single-operator QAP application boundary."""

    app = FastAPI(
        title="QAP Research Application API",
        version="1.0.0",
        description=(
            "Local command/query access to QAP research operations and validated "
            "immutable evidence."
        ),
    )
    app.state.settings = settings
    run_reader = RunArtifactReader(
        settings.run_root,
        market_data_root=settings.market_data_root,
    )
    paper_operation_reader = PaperOperationReader(
        settings.run_root / "paper-operations"
    )
    scanner_reader = ScannerArtifactReader(settings.run_root)
    basket_reader = BasketArtifactReader(settings.run_root)
    app.state.run_reader = run_reader
    app.state.paper_operation_reader = paper_operation_reader
    app.state.scanner_reader = scanner_reader
    app.state.basket_reader = basket_reader
    app.state.history_reader = HistoryReader(
        scanner=scanner_reader,
        baskets=basket_reader,
        runs=run_reader,
        paper=paper_operation_reader,
    )
    product_universe = ProductUniverse(settings.run_root)
    product_market_data = ProductMarketData(
        settings.run_root,
        settings.market_data_root,
    )
    app.state.product_universe = product_universe
    app.state.product_market_data = product_market_data
    app.state.product_market_data_preparation = ProductMarketDataPreparation(
        product_universe,
        product_market_data,
    )
    app.state.product_pair_study = ProductPairStudy(
        product_universe, product_market_data
    )
    current_approved_research = CurrentApprovedResearch(
        product_universe,
        product_market_data,
    )
    app.state.current_approved_research = current_approved_research
    app.state.research_recipe_service = ResearchRecipeService(
        run_root=settings.run_root,
        data_root=settings.market_data_root,
        repository_root=settings.repository_root,
        current_approved=current_approved_research,
    )
    app.state.product_current_evidence = ProductCurrentEvidenceStore(settings.run_root)
    app.state.operation_manager = OperationManager(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type"],
    )

    @app.exception_handler(ApiBoundaryError)
    async def api_boundary_error(
        request: Request,
        error: ApiBoundaryError,
    ) -> JSONResponse:
        del request
        return _error_response(
            status_code=error.status_code,
            code=error.code,
            message=error.message,
            context=error.context,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        del request, error
        return _error_response(
            status_code=422,
            code="request_validation_error",
            message="Request parameters are invalid.",
            context={},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(
        request: Request,
        error: StarletteHTTPException,
    ) -> JSONResponse:
        del request
        if error.status_code == 404:
            return _error_response(
                status_code=404,
                code="route_not_found",
                message="API route was not found.",
                context={},
            )
        return _error_response(
            status_code=error.status_code,
            code="http_error",
            message="HTTP request failed.",
            context={},
        )

    @app.exception_handler(Exception)
    async def unexpected_error(
        request: Request,
        error: Exception,
    ) -> JSONResponse:
        del request, error
        return _error_response(
            status_code=500,
            code="internal_server_error",
            message="The request could not be completed.",
            context={},
        )

    _ = (
        api_boundary_error,
        request_validation_error,
        http_error,
        unexpected_error,
    )

    app.include_router(health_router)
    app.include_router(workspace_router)
    app.include_router(research_universe_router)
    app.include_router(product_market_data_router)
    app.include_router(product_pair_study_router)
    app.include_router(product_research_router)
    app.include_router(research_recipes_router)
    app.include_router(product_current_evidence_router)
    app.include_router(experiments_router)
    app.include_router(history_router)
    app.include_router(portfolios_router)
    app.include_router(pairs_router)
    app.include_router(paper_operations.router)
    app.include_router(scanner_router)
    app.include_router(baskets_router)
    app.include_router(operations_router)
    return app


def create_default_app() -> FastAPI:
    """Create the launch app from operational-only environment settings."""

    return create_app(ApiSettings.from_environment())


__all__ = ["create_app", "create_default_app"]
