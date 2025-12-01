"""
Integration tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from starlette import status

from tests.constants import Urls


@pytest.mark.anyio
async def test_register_success(unauthenticated_client: AsyncClient) -> None:
    """Test successful user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User"
    }

    response = await unauthenticated_client.post(url=Urls.AUTH_REGISTER, json=user_data)

    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.anyio
async def test_register_duplicate_email(unauthenticated_client: AsyncClient, test_user) -> None:
    """Test registration with duplicate email returns 409."""
    user_data = {
        "email": test_user.email,
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User"
    }

    response = await unauthenticated_client.post(url=Urls.AUTH_REGISTER, json=user_data)

    assert response.status_code == status.HTTP_409_CONFLICT, response.text
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_register_invalid_email(unauthenticated_client: AsyncClient) -> None:
    """Test registration with invalid email returns 422."""
    user_data = {
        "email": "invalid-email",
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User"
    }

    response = await unauthenticated_client.post(url=Urls.AUTH_REGISTER, json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


@pytest.mark.anyio
async def test_login_success(unauthenticated_client: AsyncClient, test_user) -> None:
    """Test successful user login."""
    login_data = {
        "username": test_user.email,
        "password": "testpassword123"  # Must match the password in test_user fixture
    }

    response = await unauthenticated_client.post(url=Urls.AUTH_LOGIN, data=login_data)

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_invalid_credentials(unauthenticated_client: AsyncClient) -> None:
    """Test login with invalid credentials returns 401."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    }

    response = await unauthenticated_client.post(url=Urls.AUTH_LOGIN, data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


@pytest.mark.anyio
async def test_get_current_user(authenticated_client: AsyncClient, test_user) -> None:
    """Test retrieving current user information."""
    response = await authenticated_client.get(url=Urls.AUTH_ME)

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["email"] == test_user.email
    assert data["first_name"] == test_user.first_name
    assert "id" in data


@pytest.mark.anyio
async def test_get_current_user_unauthorized(unauthenticated_client: AsyncClient) -> None:
    """Test getting current user without authentication returns 401."""
    response = await unauthenticated_client.get(url=Urls.AUTH_ME)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


@pytest.mark.anyio
async def test_logout_success(authenticated_client: AsyncClient) -> None:
    """Test successful logout."""
    response = await authenticated_client.post(url=Urls.AUTH_LOGOUT)
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text


@pytest.mark.anyio
async def test_logout_unauthorized(unauthenticated_client: AsyncClient) -> None:
    """Test logout without authentication returns 401."""
    response = await unauthenticated_client.post(url=Urls.AUTH_LOGOUT)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text

