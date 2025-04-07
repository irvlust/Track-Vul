from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from app.schemas import Application, ApplicationCreate, ApplicationDependenciesListResponse, UniqueDependency, DependencyInfo, DependencyCreate
from app.models import Application as DBApp, Dependency as DBDep
from app.database import get_db
from requirements import parse
from typing import List, Dict, Optional
from pydantic import ValidationError
from app.api.utils import get_vulnerabilities, check_vulnerabilities
from app.log_utils import logger

router = APIRouter()


@router.post("/application", response_model=ApplicationCreate)
async def create_application(
    name: str = Form(...),
    description: str = Form(...),
    requirements: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        content = await requirements.read()
        text = content.decode()
        parsed_deps = list(parse(text))
    except Exception as e:
        logger.error(f"Failed to parse requirements.txt for app '{name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid requirements file: {str(e)}"
        )

    # Check if app with same name exists
    result = await db.execute(select(DBApp).where(DBApp.name == name))
    app_obj = result.scalar_one_or_none()

    if app_obj:
        # get rid of old one
        await db.execute(delete(DBDep).where(DBDep.application_id == app_obj.id))
        app_obj.description = description
    else:
        app_obj = DBApp(name=name, description=description)
        db.add(app_obj)
        await db.flush()

    for req in parsed_deps:
        raw_data = {
            "name": req.name,
            # add sort to get unique sort values
            "version_specs": ",".join(f"{typ}{val}" for typ, val in sorted(req.specs, key=lambda x: x[1])) if req.specs else None,
            "extras": ",".join(req.extras) if req.extras else None,
        }

        try:
            dep_data = DependencyCreate.model_validate(raw_data)

        except ValidationError as ve:
            logger.error(f"Validation error for dependency '{req.name}' in app '{name}': {ve.errors()}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Dependency parse error: {ve.errors()}"
            )

        dep_obj = DBDep(**dep_data.model_dump(), application_id=app_obj.id)
        db.add(dep_obj)

    await db.commit()

    return ApplicationCreate.model_validate(app_obj)



@router.get("/applications", response_model=list[Application])
async def get_applications(db: AsyncSession = Depends(get_db)):
    # catch a connection error
    try:
        result = await db.execute(
            select(DBApp).options(joinedload(DBApp.dependencies))
        )
        apps = result.unique().scalars().all()
    except Exception as e:
        logger.error(f"[get_applications] Failed to fetch applications from database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch applications: {str(e)}"
        )

    app_list = []
    for app in apps:
        try:
            is_vulnerable = False
            for dep in app.dependencies:
                version = dep.version_specs or ""
                if await check_vulnerabilities(dep.name, version):
                    is_vulnerable = True
                    break

            app_data = Application.model_validate({
                "name": app.name,
                "vulnerable": is_vulnerable
            })

            app_list.append(app_data)

        except ValidationError as ve:
            logger.error(f"[get_applications] Validation error for application '{app.name}': {ve.errors()}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Application validation failed: {ve.errors()}"
            )
        except Exception as e:
            logger.error(f"[get_applications] Unexpected error processing application '{app.name}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing application '{app.name}': {str(e)}"
            )
        
    return app_list


@router.get("/application/{name}/dependencies", response_model=list[ApplicationDependenciesListResponse])
async def get_application_dependencies(name: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DBApp).where(DBApp.name == name))
        app_obj = result.scalar_one_or_none()

        if not app_obj:
            logger.warning(f"[get_application_dependencies] Application '{name}' not found in database.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        result = await db.execute(
            select(DBDep.name, DBDep.version_specs).where(DBDep.application_id == app_obj.id)
        )
        dependencies = result.all()
    except Exception as e:
        logger.error(f"[get_application_dependencies] Database error while fetching dependencies for '{name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching application '{name}' dependencies: {str(e)}"
        )

    response = []
    for dep in dependencies:
        try:
            is_vuln = await check_vulnerabilities(dep.name, dep.version_specs or "")

            dep_data = {
                "name": dep.name,
                "version_specs": dep.version_specs,
                "vulnerable": is_vuln
            }
            validated = ApplicationDependenciesListResponse.model_validate(dep_data)
            response.append(validated)

        except ValidationError as ve:
            logger.error(f"[get_application_dependencies] Validation error for dependency '{dep.name}': {ve.errors()}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Dependency validation failed for '{dep.name}': {ve.errors()}"
            )
        except Exception as e:
            logger.error(f"[get_application_dependencies] Failed to check vulnerabilities for '{dep.name}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check vulnerabilities for '{dep.name}': {str(e)}"
            )

    return response


@router.get("/dependencies", response_model=List[UniqueDependency])
async def list_unique_dependencies(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DBDep.name, DBDep.version_specs))
        raw_dependencies = result.all()
    except Exception as e:
        logger.error(f"[list_unique_dependencies] Database error while fetching dependencies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching dependencies: {str(e)}"
        )

    seen = set()
    unique_deps: List[UniqueDependency] = []

    for name, version_specs in raw_dependencies:
        key = (name, version_specs)
        if key in seen:
            continue
        seen.add(key)

        try:
            is_vuln = await check_vulnerabilities(name, version_specs or "")

            dep_data = {
                "name": name,
                "version_specs": version_specs,
                "vulnerable": is_vuln
            }
            dep = UniqueDependency.model_validate(dep_data)
            unique_deps.append(dep)

        except ValidationError as ve:
            logger.error(f"[list_unique_dependencies] Validation failed for '{name}': {ve.errors()}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed for dependency '{name}': {ve.errors()}"
            )

        except Exception as e:
            logger.error(f"[list_unique_dependencies] Failed to check vulnerabilities for '{name}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check vulnerabilities for dependency '{name}': {str(e)}"
            )

    return unique_deps


@router.get("/dependency/{name}", response_model=List[DependencyInfo])
async def get_dependency_info(name: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(DBDep.version_specs, DBDep.application_id)
            .where(DBDep.name == name)
            .distinct()
        )
        entries = result.all()
    except Exception as e:
        logger.error(f"[get_dependency_info] DB error fetching dependencies for '{name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching dependency '{name}': {str(e)}"
        )

    if not entries:
        logger.warning(f"[get_dependency_info] No dependencies found for '{name}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No entries found for dependency '{name}'"
        )

    try:
        app_ids = list({row.application_id for row in entries})
        apps = {}

        if app_ids:
            app_result = await db.execute(
                select(DBApp.id, DBApp.name).where(DBApp.id.in_(app_ids))
            )
            apps = {id_: app_name for id_, app_name in app_result.all()}
    except Exception as e:
        logger.error(f"[get_dependency_info] Failed to fetch related app names for '{name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching associated applications for '{name}': {str(e)}"
        )

    response_dict: Dict[Optional[str], DependencyInfo] = {}

    for version_specs, app_id in entries:
        app_name = apps.get(app_id, "unknown")
        try:
            vulns = await get_vulnerabilities(name, version_specs or "")
        
        except Exception as e:
            logger.error(f"[get_dependency_info] Failed to fetch vulns for '{name}' ({version_specs}): {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch vulnerabilities for '{name}': {str(e)}"
            )

        if version_specs not in response_dict:
            try:
                validated = DependencyInfo.model_validate({
                    "version_specs": version_specs,
                    "application_usage": [app_name],
                    "vulns": vulns,
                    "usage_count": 1
                })
                response_dict[version_specs] = validated
            except ValidationError as ve:
                logger.error(f"[get_dependency_info] Validation failed for '{name}' ({version_specs}): {ve.errors()}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to validate DependencyInfo for '{name}': {ve.errors()}"
                )

        else:
            response_dict[version_specs].application_usage.append(app_name)
            response_dict[version_specs].usage_count = len(response_dict[version_specs].application_usage)

    return list(response_dict.values())
