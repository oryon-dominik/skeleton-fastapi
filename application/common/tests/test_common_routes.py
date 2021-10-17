import pytest
from httpx import AsyncClient

from fastapi.testclient import TestClient
from fastapi import HTTPException

from ...config import Settings, get_settings
from ...main import app

from ..dependencies import block_request_when_in_production

client = TestClient(app)


# -- overwrite settings for production and develop ----------------------------
async def override_get_settings_for_production():
    return Settings(PRODUCTION=True, DEBUG=False)

async def override_get_settings_for_develop():
    return Settings(PRODUCTION=False, DEBUG=True)

async def override_block_request_when_in_production_for_production():
    settings = await override_get_settings_for_production()
    return await block_request_when_in_production(_settings=settings)

async def override_block_request_when_in_production_for_develop():
    settings = await override_get_settings_for_develop()
    return await block_request_when_in_production(_settings=settings)
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_settings_are_not_exposed_in_production():
    app.dependency_overrides[get_settings] = override_get_settings_for_production
    app.dependency_overrides[block_request_when_in_production] = override_block_request_when_in_production_for_production
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/settings")
    assert response.status_code == 400
    assert response.json() == {"detail":"This endpoint is not available in production"}

@pytest.mark.asyncio
async def test_settings_reachable_in_develop():
    app.dependency_overrides[get_settings] = override_get_settings_for_develop
    app.dependency_overrides[block_request_when_in_production] = override_block_request_when_in_production_for_develop
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/settings")
    assert response.status_code == 200
    assert "settings" in response.json()
