"""Application factory and a single validated data snapshot per process."""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from .config import Settings
from .routes import router
from .service import DomainError, WindService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, service: WindService | None = None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        if service is not None:
            app.state.service = service
        else:
            try:
                app.state.service = WindService.load(settings)
            except (ValueError, OSError, KeyError, TypeError):
                logger.exception('Cannot load validated Elexon data')
                app.state.service = None
        app.state.frontend_ready = settings.static_dir is None or ((settings.static_dir / 'index.html').is_file() and (settings.static_dir / 'assets').is_dir())
        if not app.state.frontend_ready:
            logger.error('Configured frontend build is missing')
        logger.info('Startup complete: data_ready=%s frontend_ready=%s',
                    app.state.service is not None, app.state.frontend_ready)
        yield
        logger.info('Application shutdown')

    app = FastAPI(title='Wind forecast accuracy API', version='0.2.0', lifespan=lifespan,
                  description='Retrospective January 2026 decision-time wind forecasts and accuracy. No interpolation.')
    app.state.settings = settings
    app.state.service = None
    app.state.frontend_ready = False

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status, content={
            'error': {'code': exc.code, 'message': exc.message}})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.exception('Unhandled request failure', exc_info=exc)
        return JSONResponse(status_code=500, content={'error': {
            'code': 'internal_error', 'message': 'The data service encountered an unexpected error.'}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = '; '.join(f"{'.'.join(map(str, item['loc']))}: {item['msg']}" for item in exc.errors())
        return JSONResponse(status_code=422, content={
            'error': {'code': 'invalid_request', 'message': details}})

    @app.get('/health/live', include_in_schema=False)
    def live():
        return {'status': 'live'}

    @app.get('/health/ready', include_in_schema=False)
    def ready():
        if app.state.service is None or not app.state.frontend_ready:
            return JSONResponse(status_code=503, content={'status': 'not_ready'})
        return {'status': 'ready'}

    app.include_router(router)
    if settings.static_dir is not None:
        # Only explicit static routes; unknown API paths must never become HTML.
        @app.get('/', include_in_schema=False)
        def dashboard():
            if not app.state.frontend_ready:
                raise DomainError(503, 'frontend_unavailable', 'The dashboard build is unavailable.')
            return FileResponse(settings.static_dir / 'index.html', headers={
                'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff'})

        if (settings.static_dir / 'assets').is_dir():
            app.mount('/assets', StaticFiles(directory=settings.static_dir / 'assets'), name='assets')
    return app


app = create_app()
