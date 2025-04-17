from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class DependencyCreate(BaseModel):
    name: str
    version_specs: Optional[str] = None
    extras: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationCreate(BaseModel):
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class Application(BaseModel):
    name: str
    vulnerable: bool

    model_config = ConfigDict(from_attributes=True)

class ApplicationDependenciesListResponse(BaseModel):
    name: str
    vulnerable: bool
    version_specs: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UniqueDependency(BaseModel):
    name: str
    version_specs: Optional[str] = None
    vulnerable: bool

    model_config = ConfigDict(from_attributes=True)

class DependencyInfo(BaseModel):
    version_specs: Optional[str] = None
    application_usage: List[str]
    osv_vulns: Dict[str, Any]
    usage_count: int

    model_config = ConfigDict(from_attributes=True)

class DependencyNoVersionInfo(BaseModel):
    application_usage: List[str]
    osv_vulns: Dict[str, Any]
    usage_count: int

    model_config = ConfigDict(from_attributes=True)

class DependencyVersion(BaseModel):
    version_spec: Optional[str] = None
    osv_vulns: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class DependencyVersionRequest(BaseModel):
    name: str
    version_spec: Optional[str] = None

# fol test purposes
class AllDependenciesCreate(BaseModel):
    application_name: str
    dependency_name: str
    version_specs: str
    # extras: str
