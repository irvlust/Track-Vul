import requests
import time
from requirements import parse
from app.schemas import DependencyCreate, ApplicationCreate, AllDependenciesCreate
from fastapi import HTTPException, status
from app.database import get_db
from app.models import Dependency as DBDep, Application as DBApp, AllDependencies
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_context():
    async for session in get_db():
        try:
            yield session
        finally:
            await session.close()


async def add_app(
    app_number: int,
    db: AsyncSession
):
    application_name = f"App number {str(app_number)}"

    raw_data = {
        "id": app_number,
        "name": application_name,
        # "name": "dummy",
        "description": f"Name of app {str(app_number)}",
    }

    try:
        app_data = ApplicationCreate.model_validate(raw_data)

    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dependency parse error: {ve.errors()}"
        )

    app_obj = DBApp(**app_data.model_dump())
    db.add(app_obj)

    # await db.commit()
    await db.flush()
    return app_obj

async def create_dependency(
    name: str,
    specs: str,
    extras: str,
    application_id: int,
    db: AsyncSession
):

    raw_data = {
        "name": name,
        "version_specs": specs,
        "extras": extras
    }

    try:
        dep_data = DependencyCreate.model_validate(raw_data)

    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dependency parse error: {ve.errors()}"
        )

    dep_obj = DBDep(**dep_data.model_dump(), application_id=application_id)
    db.add(dep_obj)

    await db.commit()

async def parse_content(content, app_number: int, db: AsyncSession):

    app_obj = await add_app(app_number, db)

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue  # skip empty or comment lines
        try:
            req = next(parse(line))
            specs = ",".join(f"{typ}{val}" for typ, val in sorted(req.specs, key=lambda x: f"{x[0]}{x[1]}")) if req.specs else None
            extras = ",".join(req.extras) if req.extras else None
            print("DDDDD", req.name, specs, extras)
            await create_dependency(req.name, specs, extras, app_obj.id, db=db)
        except Exception as e:
            # print(f"Skipping line: {line[:60]}... → {e}")
            pass


async def main():
    async with get_db_context() as db:

        # await add_dummy_app(db=db)
        app_number = 1
        GITHUB_TOKEN = ""
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        # GitHub's rate limits (30–60 per minute for authenticated users) apply.

        # Monthly chunks for 2024 (repository creation date)
        month_chunks = [
            "2024-01-01..2024-01-31",
            "2024-02-01..2024-02-29",
            "2024-03-01..2024-03-31",
            "2024-04-01..2024-04-30",
            "2024-05-01..2024-05-31",
            "2024-06-01..2024-06-30",
            "2024-07-01..2024-07-31",
            "2024-08-01..2024-08-31",
            "2024-09-01..2024-09-30",
            "2024-10-01..2024-10-31",
            "2024-11-01..2024-11-30",
            "2024-12-01..2024-12-31"
        ]

        for date_range in month_chunks:
            repo_query = f"created:{date_range}"
            print(f"\n==================== REPO QUERY [{repo_query}] ====================")

            for page in range(1, 11):
                repo_search_url = f"https://api.github.com/search/repositories?q={repo_query}&per_page=100&page={page}"
                repo_resp = requests.get(repo_search_url, headers=headers)

                if repo_resp.status_code == 403:
                    print("Rate limit hit. Sleeping for 60 seconds...")
                    time.sleep(60)
                    continue

                if repo_resp.status_code != 200:
                    print(f"Error fetching repos: {repo_resp.status_code}")
                    print(repo_resp.text)
                    break

                repo_items = repo_resp.json().get("items", [])
                print(f"IIIIIIIIII Found {len(repo_items)} repos")

                if not repo_items:
                    break

                for repo in repo_items:
                    full_name = repo["full_name"]  # e.g. "owner/repo"
                    print(f"Searching in repo: {full_name}")
                    file_search_url = f"https://api.github.com/search/code?q=filename:requirements.txt+repo:{full_name}&per_page=10"
                    file_resp = requests.get(file_search_url, headers=headers)

                    if file_resp.status_code == 403:
                        print(f"Rate limit hit during file search in repo: {full_name}. Sleeping for 60 seconds...")
                        time.sleep(60)
                        continue

                    if file_resp.status_code != 200:
                        print(f"Error searching in repo: {full_name} | Status: {file_resp.status_code}")
                        print(file_resp.text)
                        continue

                    files = file_resp.json().get("items", [])
                    for file in files:
                        file_url = file["url"]
                        content_resp = requests.get(file_url, headers=headers)

                        if content_resp.status_code != 200:
                            print(f"Error fetching file metadata: {file_url}")
                            continue

                        content_json = content_resp.json()
                        download_url = content_json.get("download_url")

                        if download_url:
                            raw_content = requests.get(download_url).text
                            await parse_content(raw_content, app_number, db=db)
                            app_number += 1

                        time.sleep(1.5)  # Sleep between file fetches

                    time.sleep(1)  # Sleep between repo file searches

                time.sleep(2)  # Sleep between repo pages


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())