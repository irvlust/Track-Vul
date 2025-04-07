import pytest
from httpx import RequestError, Request
from fastapi import status
from unittest.mock import AsyncMock, patch
from tests.helpers.test_app_factory import create_app

# use this as a base for other tests if required
@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "side_effect,expected_msg",
    [
        (RuntimeError("Invalid JSON response from vulnerability API"), "Error processing application"),
        (RuntimeError("HTTP error from vulnerability API: 500"), "Error processing application"),
        (RuntimeError("Unexpected error: boom"), "Error processing application"),
    ],
)
@patch("app.api.routes_applications.check_vulnerabilities", new_callable=AsyncMock)
async def test_get_applications_uncached_errors(mock_check_vulns, side_effect, expected_msg, client):
    mock_check_vulns.side_effect = side_effect
    await create_app(client)

    response = await client.get("/applications")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert expected_msg in response.text

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.check_vulnerabilities", new_callable=AsyncMock)
async def test_get_applications_vuln_check_error(mock_check_vulns, client):
    mock_check_vulns.side_effect = RequestError("check_vulnerabilities failed", request=Request("GET", "http://testserver"))

    await create_app(client)

    response = await client.get("/applications")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error processing application" in response.text



@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.check_vulnerabilities", new_callable=AsyncMock)
async def test_get_application_dependencies_vuln_check_error(mock_check_vulns, client):
    mock_check_vulns.side_effect = RequestError("check_vulnerabilities failed", request=None)

    await create_app(client)

    response = await client.get("/application/TestApp/dependencies")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to check vulnerabilities" in response.text

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.check_vulnerabilities", new_callable=AsyncMock)
async def test_list_unique_dependencies_vuln_check_error(mock_check_vulns, client):
    mock_check_vulns.side_effect = RequestError("check_vulnerabilities failed", request=None)
    await create_app(client)

    response = await client.get("/dependencies")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to check vulnerabilities" in response.text

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.routes_applications.get_vulnerabilities", new_callable=AsyncMock)
async def test_get_dependency_info_vuln_fetch_error(mock_get_vulns, client):
    mock_get_vulns.side_effect = RequestError("get_vulnerabilities failed", request=None)
    await create_app(client)

    response = await client.get("/dependency/fastapi")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to fetch vulnerabilities" in response.text
