import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.institution import Institution
from app.models.major import Major


@pytest.fixture()
def db_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        yield testing_session
    finally:
        engine.dispose()


@pytest.fixture()
def client(db_factory):
    testing_session = db_factory

    with testing_session() as db:
        santa_monica = Institution(name="Santa Monica College", institution_type="community_college")
        ucla = Institution(name="University of California, Los Angeles", institution_type="university")
        csulb = Institution(name="California State University, Long Beach", institution_type="university")
        db.add_all([santa_monica, ucla, csulb])
        db.flush()
        db.add(Major(name="Computer Science", institution_id=ucla.id))
        db.add(Major(name="Psychology", institution_id=csulb.id))
        db.commit()

    def override_get_db():
        with testing_session() as db:
            yield db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
