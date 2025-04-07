import pytest
from tests.helpers.test_app_factory import create_app


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_list_applications(client):

    await create_app(client)

    response = await client.get("/applications")
    assert response.status_code == 200

    apps = response.json()
    assert isinstance(apps, list)
    assert len(apps) == 1
    assert apps[0]["name"] == "TestApp"
    assert apps[0]["vulnerable"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_get_dependencies_for_app(client):
    await create_app(client)

    response = await client.get("/application/TestApp/dependencies")

    assert response.status_code == 200
    apps = response.json()
    assert isinstance(apps, list)
    assert len(apps) == 2
    assert apps[0]["name"] == "fastapi"
    assert apps[0]["vulnerable"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_list_all_unique_dependencies(client):
    await create_app(client)

    response = await client.get("/dependencies")

    assert response.status_code == 200
    apps = response.json()
    assert isinstance(apps, list)
    assert len(apps) == 2
    assert apps[0]["name"] == "fastapi"
    assert apps[0]["vulnerable"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_dependency_detail(client):
    await create_app(client)

    response = await client.get("/dependency/fastapi")

    assert response.status_code == 200
    apps = response.json()
    assert isinstance(apps, list)
    assert len(apps) == 1
    assert apps[0]["application_usage"] == ["TestApp"]
    assert apps[0]["version_specs"] == '==0.103.0'
    assert "vulns" in apps[0]




