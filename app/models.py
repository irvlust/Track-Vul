from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    dependencies = relationship("Dependency", back_populates="application", cascade="all, delete-orphan")


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version_specs = Column(String, nullable=True)
    extras = Column(String, nullable=True)

    application_id = Column(Integer, ForeignKey("applications.id"))
    application = relationship("Application", back_populates="dependencies")

# for test purposes
class AllDependencies(Base):
    __tablename__ = "alldependencies"
    id = Column(Integer, primary_key=True, index=True)
    application_name = Column(String, nullable=False)
    dependency_name = Column(String, nullable=False)
    version_specs = Column(String, nullable=True)
    # extras = Column(String, nullable=True)
