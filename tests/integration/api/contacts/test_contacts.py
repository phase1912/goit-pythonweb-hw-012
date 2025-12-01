"""
Integration tests for contacts endpoints.
"""
import pytest
from httpx import AsyncClient
from starlette import status

from tests.constants import Urls


@pytest.mark.anyio
async def test_create_contact_success(authenticated_client: AsyncClient) -> None:
    """Test successful contact creation."""
    contact_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone_number": "+9876543210",
        "date_of_birth": "1995-05-20",
        "additional_data": "New contact"
    }

    response = await authenticated_client.post(url=Urls.CONTACTS, json=contact_data)

    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["first_name"] == contact_data["first_name"]
    assert data["last_name"] == contact_data["last_name"]
    assert data["email"] == contact_data["email"]
    assert "id" in data


@pytest.mark.anyio
async def test_create_contact_unauthorized(unauthenticated_client: AsyncClient) -> None:
    """Test creating contact without authentication returns 401."""
    contact_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone_number": "+9876543210",
        "date_of_birth": "1995-05-20"
    }

    response = await unauthenticated_client.post(url=Urls.CONTACTS, json=contact_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


@pytest.mark.anyio
async def test_get_contacts_list(authenticated_client: AsyncClient, test_contact) -> None:
    """Test retrieving contacts list."""
    response = await authenticated_client.get(url=Urls.CONTACTS)

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert "contacts" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert len(data["contacts"]) >= 1


@pytest.mark.anyio
async def test_get_contacts_unauthorized(unauthenticated_client: AsyncClient) -> None:
    """Test retrieving contacts without authentication returns 401."""
    response = await unauthenticated_client.get(url=Urls.CONTACTS)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


@pytest.mark.anyio
async def test_get_contact_by_id(authenticated_client: AsyncClient, test_contact) -> None:
    """Test retrieving a specific contact by ID."""
    url = Urls.CONTACT_DETAIL.format(id=test_contact.id)
    response = await authenticated_client.get(url=url)

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["id"] == test_contact.id
    assert data["first_name"] == test_contact.first_name
    assert data["email"] == test_contact.email


@pytest.mark.anyio
async def test_get_contact_not_found(authenticated_client: AsyncClient) -> None:
    """Test retrieving non-existent contact returns 404."""
    url = Urls.CONTACT_DETAIL.format(id=99999)
    response = await authenticated_client.get(url=url)

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


@pytest.mark.anyio
async def test_update_contact_success(authenticated_client: AsyncClient, test_contact) -> None:
    """Test successful contact update."""
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "email": "updated.email@example.com"
    }

    url = Urls.CONTACT_DETAIL.format(id=test_contact.id)
    response = await authenticated_client.put(url=url, json=update_data)

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]
    assert data["email"] == update_data["email"]


@pytest.mark.anyio
async def test_delete_contact_success(authenticated_client: AsyncClient, test_contact) -> None:
    """Test successful contact deletion."""
    url = Urls.CONTACT_DETAIL.format(id=test_contact.id)
    response = await authenticated_client.delete(url=url)

    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text

    # Verify deletion
    get_response = await authenticated_client.get(url=url)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_search_contacts(authenticated_client: AsyncClient, test_contact) -> None:
    """Test searching contacts."""
    response = await authenticated_client.get(
        url=Urls.CONTACTS_SEARCH,
        params={"q": test_contact.first_name}
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert "contacts" in data
    assert len(data["contacts"]) >= 1


@pytest.mark.anyio
async def test_get_upcoming_birthdays(authenticated_client: AsyncClient) -> None:
    """Test retrieving contacts with upcoming birthdays."""
    response = await authenticated_client.get(
        url=Urls.CONTACTS_BIRTHDAYS,
        params={"days": 7}
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert isinstance(data, list)

