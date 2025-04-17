import httpx
import json

for _ in range(20):
    url = "https://api.osv.dev/v1/querybatch"
    versions = ["","==2.0.40"]
    name = "sqlalchemy"

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
        response = httpx.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))
    except httpx.RequestError as e:
        print(f"Request failed: {e}")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Unexpected error: {e}")
