import asyncio
from collections import Counter
from sqlalchemy import select
from contextlib import asynccontextmanager

from app.database import get_db
from app.models import Dependency as DBDep

@asynccontextmanager
async def get_db_context():
    async for session in get_db():
        try:
            yield session
        finally:
            await session.close()


async def main():
    async with get_db_context() as db: 
        result = await db.execute(select(DBDep.name, DBDep.version_specs))
        rows = result.all()

        # 1. Total rows
        total_rows = len(rows)

        # 2. Unique (name, version_specs) pairs
        unique_name_version = set(rows)

        # 3. Unique package names
        package_names = [name for name, _ in rows]
        unique_names = set(package_names)

        # 4. Packages with multiple entries
        name_counts = Counter(package_names)
        duplicates = [name for name, count in name_counts.items() if count > 1]

        # 5. Version specs with multiple uses across different names
        version_counts = Counter(version for _, version in rows if version)
        versions_with_multiple_packages = [
            version for version, count in version_counts.items() if count > 1
        ]

        # Display results
        print("\n==================== RESULTS ====================")
        print(f"Total rows: {total_rows}")
        print(f"Unique (name, version_specs) pairs: {len(unique_name_version)}")
        print(f"Unique package names: {len(unique_names)}")
        print(f"Packages with multiple entries: {len(duplicates)}") # specific package entries that have more than one version_spec 
        # or - Package names that appear multiple times with different version specifications
        # if duplicates:
        #     print("   ", duplicates)
        print(f"Version specs used by multiple packages: {len(versions_with_multiple_packages)}")  # specific version_spec entries that have more than one package name
        # or - Version specifications that are shared across multiple different package names
        # if versions_with_multiple_packages:
        #     print("   ", versions_with_multiple_packages)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
