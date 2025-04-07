import pytest
from unittest.mock import AsyncMock, patch
from tests.helpers.test_app_factory import create_app


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.check_vulnerabilities", new_callable=AsyncMock)
async def test_get_dependencies_for_app(mock_check_vulnerabilities, client):
    mock_check_vulnerabilities.return_value = True

    await create_app(client)


    response = await client.get("/application/TestApp/dependencies")
    apps = response.json()

    assert response.status_code == 200
    assert isinstance(apps, list)
    assert len(apps) == 2
    assert apps[0]["name"] == "fastapi"
    assert apps[0]["vulnerable"] is True

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.check_vulnerabilities", new_callable=AsyncMock)
async def test_list_all_unique_dependencies(mock_check_vulnerabilities, client):
    mock_check_vulnerabilities.return_value = True

    await create_app(client)

    response = await client.get("/dependencies")

    assert response.status_code == 200
    apps = response.json()
    assert isinstance(apps, list)
    assert len(apps) == 2
    assert apps[0]["name"] == "fastapi"
    assert apps[0]["vulnerable"] is True

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.get_vulnerabilities", new_callable=AsyncMock)
async def test_dependency_detail(mock_get_vulnerabilities, client):
    mock_get_vulnerabilities.return_value = [{"blah": "blah"}]

    await create_app(client)


    response = await client.get("/dependency/fastapi")

    assert response.status_code == 200
    apps = response.json()
    assert isinstance(apps, list)
    assert len(apps) == 1
    assert apps[0]["application_usage"] == ["TestApp"]
    assert apps[0]["version_specs"] == '==0.103.0'
    assert apps[0]["vulns"] == [{'blah':'blah'}]

