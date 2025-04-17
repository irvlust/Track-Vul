import asyncio
from collections import defaultdict
from sqlalchemy import select
from contextlib import asynccontextmanager

from app.database import get_db
from app.models import AllDependencies


@asynccontextmanager
async def get_db_context():
    async for session in get_db():
        try:
            yield session
        finally:
            await session.close()


async def main():
    async with get_db_context() as db:
        result = await db.execute(
            select(AllDependencies.application_name, AllDependencies.dependency_name, AllDependencies.version_specs)
        )
        rows = result.all()

        app_deps = [(app, name, version) for app, name, version in rows]

        # 1. Total dependency rows
        total_rows = len(app_deps)

        # 2. Unique (name, version_specs) pairs
        unique_name_version = set((name, version) for _, name, version in app_deps)

        # 3. Unique package names
        unique_names = set(name for _, name, _ in app_deps)

        # 4. Unique version specifications
        unique_versions = set(version for _, _, version in app_deps if version)

        # 5. Packages with multiple version_specs
        name_to_versions = defaultdict(set)
        for _, name, version in app_deps:
            name_to_versions[name].add(version)
        packages_with_multiple_versions = [name for name, versions in name_to_versions.items() if len(versions) > 1]

        # 6. Version specs used by multiple packages
        version_to_names = defaultdict(set)
        for _, name, version in app_deps:
            if version:
                version_to_names[version].add(name)
        versions_used_by_multiple_packages = [ver for ver, names in version_to_names.items() if len(names) > 1]

        # 7. Unique applications
        unique_apps = set(app for app, _, _ in app_deps)

        # 8. Unique Application–Dependency links
        unique_app_dep_links = set((app, name) for app, name, _ in app_deps)

        # Output
        print("\n==================== ANALYSIS RESULTS ====================")
        print(f"1. Total dependency rows: {total_rows}")
        print(f"2. Unique (package name, version_specs) pairs: {len(unique_name_version)}")
        print(f"3. Unique package names: {len(unique_names)}")
        print(f"4. Unique version specifications: {len(unique_versions)}")
        print(f"5. Packages with multiple version_specs: {len(packages_with_multiple_versions)}")
        print(f"6. Version_specs used by multiple packages: {len(versions_used_by_multiple_packages)}")
        print(f"7. Unique applications: {len(unique_apps)}")
        print(f"8. Application–Dependency relationships: {len(unique_app_dep_links)}")
        print("==========================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
