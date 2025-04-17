import httpx
from aiocache import cached
from app.config import settings
from httpx import RequestError, HTTPStatusError
from app.log_utils import logger


async def check_vulnerabilities(name: str, version: str) -> bool:
    osv_vulns = await get_vulnerabilities(name, version)

    if not isinstance(osv_vulns, dict):
        return False

    vulns = osv_vulns.get("vulns")

    if not vulns or not isinstance(vulns, list):
        return False

    return bool(vulns)

async def _get_vulnerabilities_uncached(name: str, version: str) -> list[dict]:
    url = settings.OSV_API_URL
    payload = {
        "version": version,
        "package": {
            "name": name,
            "ecosystem": "PyPI"
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                logger.error(f"Invalid JSON response from OSV API for '{name} {version}'")
                raise RuntimeError("Invalid JSON response from vulnerability API")
            # TODO: check for the next_page_token and deal with it (call a routine)
            return data

    except HTTPStatusError as e:
        logger.error(f"HTTP error from OSV API for '{name} {version}': {e}")
        raise RuntimeError(f"HTTP error from vulnerability API: {str(e)}")
    except RequestError as e:
        logger.error(f"Network error while calling OSV API for '{name} {version}': {e}")
        raise RuntimeError(f"Network error while calling vulnerability API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while calling OSV API for '{name} {version}': {e}")
        raise RuntimeError(f"Unexpected error: {str(e)}")

# Need the following as go between for testing
@cached(ttl=3600)
async def get_vulnerabilities(name: str, version: str) -> list[dict]:
    return await _get_vulnerabilities_uncached(name, version)

async def _get_batch_vulnerabilities_uncached(name: str, versions: list[str]) -> dict[str, list[dict]]:
    url = settings.OSV_API_BATCH_URL
    payload = {
        "queries": [
            {
                "version": version,
                "package": {
                    "name": name,
                    "ecosystem": "PyPI"
                }
            }
            for version in versions
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                logger.error(f"Invalid JSON response from OSV batch API for '{name}'")
                raise RuntimeError("Invalid JSON response from OSV batch API")
            return data

    except HTTPStatusError as e:
        logger.error(f"HTTP error from OSV batch API for '{name}': {e}")
        raise RuntimeError(f"HTTP error from OSV batch API: {str(e)}")
    except RequestError as e:
        logger.error(f"Network error while calling OSV batch API for '{name}': {e}")
        raise RuntimeError(f"Network error while calling OSV batch API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while calling OSV batch API for '{name}': {e}")
        raise RuntimeError(f"Unexpected error from OSV batch API: {str(e)}")

# Need the following as go between for testing
@cached(ttl=3600)
async def get_batch_vulnerabilities(name: str, versions: list[str]) -> dict[str, list[dict]]:
    return await _get_batch_vulnerabilities_uncached(name, versions)
