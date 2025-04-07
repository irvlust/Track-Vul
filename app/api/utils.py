import httpx
from aiocache import cached
from app.config import settings
from httpx import RequestError, HTTPStatusError
from app.log_utils import logger


async def check_vulnerabilities(name: str, version: str) -> bool:
    vulns = await get_vulnerabilities(name, version)
    # for now, this assumes that if a valid list is returned, then there's a vulnerability
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
            return data.get("vulns", [])

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