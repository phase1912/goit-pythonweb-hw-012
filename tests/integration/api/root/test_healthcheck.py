"""
Integration tests for root endpoints.
"""
import pytest
from httpx import AsyncClient
from starlette import status

from tests.constants import Urls


@pytest.mark.anyio
async def test_health_check(unauthenticated_client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await unauthenticated_client.get(url=Urls.HEALTHCHECK)
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_root_endpoint(unauthenticated_client: AsyncClient) -> None:
    """Test root endpoint returns API information."""
    response = await unauthenticated_client.get(url=Urls.ROOT)
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert "message" in data
    assert "Contacts API" in data["message"]
    assert "docs" in data

