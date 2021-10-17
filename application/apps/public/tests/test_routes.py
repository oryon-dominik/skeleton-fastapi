import pytest
from httpx import AsyncClient

from fastapi.testclient import TestClient

from ....main import app


client = TestClient(app)


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/api/public/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to a Skeleton-FastAPI-Application. Composed by oryon-dominik with 💖"}
