"""FastAPI application factory for immutable QAP research evidence."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from qap.api.errors import ApiBoundaryError
from qap.api.operations import OperationManager
from qap.api.paper_operation_views import PaperOperationReader
from qap.api.readers import RunArtifactReader
from qap.api.routes import (
    experiments_router,
    health_router,
    operations_router,
    pairs_router,
    paper_operations,
    portfolios_router,
    product_market_data_router,
    research_universe_router,
    workspace_router,
)
from qap.api.routes.lab_studies import router as lab_studies_router
from qap.api.routes.live_paper import router as live_paper_router
from qap.api.routes.pair_rotation import router as pair_rotation_router
from qap.api.schemas import ErrorDetailDto, ErrorEnvelopeDto
from qap.api.settings import ApiSettings
from qap.product_current_evidence import ProductCurrentEvidenceStore
from qap.product_market_data import ProductMarketData
from qap.product_market_data_prepare import ProductMarketDataPreparation
from qap.product_universe import ProductUniverse


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
    app.state.paper_book_provider = None
    run_reader = RunArtifactReader(
        settings.run_root,
        market_data_root=settings.market_data_root,
    )
    paper_operation_reader = PaperOperationReader(
        settings.run_root / "paper-operations"
    )
    app.state.run_reader = run_reader
    app.state.paper_operation_reader = paper_operation_reader
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
    app.state.product_current_evidence = ProductCurrentEvidenceStore(settings.run_root)
    app.state.operation_manager = OperationManager(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-QAP-Actor-Id"],
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
    app.include_router(pair_rotation_router)
    app.include_router(lab_studies_router)
    app.include_router(live_paper_router)
    app.include_router(experiments_router)
    app.include_router(portfolios_router)
    app.include_router(pairs_router)
    app.include_router(paper_operations.router)
    app.include_router(operations_router)
    return app


def create_default_app() -> FastAPI:
    """Create the launch app from operational-only environment settings."""

    return create_app(ApiSettings.from_environment())


__all__ = ["create_app", "create_default_app"]
