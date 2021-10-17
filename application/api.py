from fastapi import APIRouter, Depends, status

from .apps.authentication.dependencies import valid_authentication_header
from .apps.authentication.dependencies import oauth2_scheme

from .apps.authentication.routes import protected_router as protected_auth_router
from .apps.authentication.routes import public_router as public_auth_router
from .apps.public.routes import router as public_router


"""-- API ROUTES --------------------------------------------------------------
Combines all application endpoints.

Dependencies set here have precedence over the module dependencies.
They will be executed in order of their appearance.
"""

# Dependencies used in ALL routers
DEPENDENCIES: list = []

# Dependencies used for ALL protected routes
auth_dependencies: list = [Depends(valid_authentication_header), Depends(oauth2_scheme)]

# Default responses used by ALL routes
default_responses: dict = {
    status.HTTP_404_NOT_FOUND: {"description": "Route not found"},
}
defaults = dict(responses=default_responses)

# * protected routes
protected = APIRouter(
    dependencies=DEPENDENCIES + auth_dependencies,
    **defaults
)

protected.include_router(protected_auth_router)

# ! public routing - be aware: these routes are OPENLY AVAILABLE to the Internet
public = APIRouter(
    dependencies=DEPENDENCIES,
    **defaults
)

public.include_router(public_router)
public.include_router(public_auth_router)

# merge all routes together
api_router = APIRouter()
api_router.include_router(protected)
api_router.include_router(public)
