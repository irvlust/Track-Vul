import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.api.utils import _get_vulnerabilities_uncached

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.utils.httpx.AsyncClient")
async def test_get_vulnerabilities_uncached_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "vulns": [{"id": "OSV-2021-1234", "summary": "Sample vuln"}]
    }

    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client

    vulns = await _get_vulnerabilities_uncached("sample-package", "1.2.3")
    assert isinstance(vulns, list)
    assert len(vulns) == 1
    assert vulns[0]["id"] == "OSV-2021-1234"

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.utils.httpx.AsyncClient")
async def test_get_vulnerabilities_uncached_http_error(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Internal Server Error",
        request=MagicMock(),
        response=MagicMock(status_code=500)
    )

    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client

    with pytest.raises(RuntimeError, match="HTTP error from vulnerability API"):
        await _get_vulnerabilities_uncached("sample-package", "1.2.3")

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.utils.httpx.AsyncClient")
async def test_get_vulnerabilities_uncached_invalid_json(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")

    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client

    with pytest.raises(RuntimeError, match="Invalid JSON response from vulnerability API"):
        await _get_vulnerabilities_uncached("sample-package", "1.2.3")

@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.utils.httpx.AsyncClient")
async def test_get_vulnerabilities_uncached_network_error(mock_client_class):
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("Network down", request=MagicMock()))
    mock_client_class.return_value.__aenter__.return_value = mock_client

    with pytest.raises(RuntimeError, match="Network error while calling vulnerability API"):
        await _get_vulnerabilities_uncached("sample-package", "1.2.3")