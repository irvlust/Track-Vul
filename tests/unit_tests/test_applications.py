import pytest
from unittest.mock import AsyncMock, patch
from tests.helpers.test_app_factory import create_app

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_application(client):
    files = {
        "requirements": ("requirements.txt", b"fastapi==0.103.0\nuvicorn>=0.23.0,<0.24.0")
    }
    data = {
        "name": "TestApp",
        "description": "Test app with deps"
    }

    response = await client.post("/application", data=data, files=files)
    assert response.status_code == 200
    assert response.json()["name"] == "TestApp"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_application_parser(client):
    files = {
        "requirements": ("requirements.txt", b"fastapi==0.103.0\nfastapi==0.103.0\nuvicorn>=0.23.0,<0.24.0")
    }
    data = {
        "name": "TestApp",
        "description": "Test app with deps"
    }

    response = await client.post("/application", data=data, files=files)
    assert response.status_code == 400

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.check_vulnerabilities", new_callable=AsyncMock)
async def test_list_applications(mock_check_vulnerabilities, client):
    mock_check_vulnerabilities.return_value = True

    await create_app(client)

    response = await client.get("/applications")
    assert response.status_code == 200

    apps = response.json()
    assert isinstance(apps, list)
    assert len(apps) == 1
    assert apps[0]["name"] == "TestApp"
    assert apps[0]["vulnerable"] is True

