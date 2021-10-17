import time
import logging
import multiprocessing
from datetime import timedelta

import humanize
from devtools import debug

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import settings, Settings, get_settings
from .config import logging as logging_config  # noqa, keep this unsued import to load the config once

from .common.exceptions import UnknownTeapotException
from .common.dependencies import block_request_when_in_production

from .api import api_router

# -- APPLICATION --------------------------------------------------------------
disable_auto_docs = dict(docs_url=None, redoc_url=None) if settings.PRODUCTION else {}
app = FastAPI(
    root_path=settings.ROOT_PATH,
    **disable_auto_docs
)
app.include_router(api_router, prefix=settings.API_URL_PREFIX)

# -- LOGGING ------------------------------------------------------------------
log = logging.getLogger('application')

# -- MIDDLEWARES --------------------------------------------------------------
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)
# ALLOWED_HOSTS
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS,
)

# Time taken
@app.middleware("http")
async def request_time_taken(request: Request, call_next):
    """Adds a middleware to EVERY request response cycle."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    readable = humanize.precisedelta(timedelta(seconds=process_time), format="%0.4f")
    response.headers["time-taken"] = f"{readable}"
    return response

# -- STARTUP EVENTS -----------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    Executes events on startup.
    """
    # work the queue (every 15 seconds)
    # from .event.sheduler import work_the_queue
    # await work_the_queue()
    pass

# -- EXCEPTION-HANDLERS -------------------------------------------------------
@app.exception_handler(UnknownTeapotException)
async def teapot_exception_handler(request: Request, exc: UnknownTeapotException):
    """
    To raise this Exception:
    
    `raise UnknownTeapotException`
    somewhere in your code
    """
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. Liquid spilled..."},
    )

# -- DEBUG INFORMATION - not shown in PRODUCTION ------------------------------
if settings.DEBUG:
    debug(app)

@app.get("/settings", include_in_schema=False)
async def show_settings_info(
    settings: Settings = Depends(get_settings),
    allowed: bool = Depends(block_request_when_in_production)
):
    """debug-settings-info"""
    return {"settings": settings.dict()} if allowed else {"message": "You are not allowed to see this."}


# -----------------------------------------------------------------------------
log.info(
    "[red on yellow] A FastAPI-application skeleton composed by oryon-dominik with :heart:. ",
    extra={"markup": True}
)
