import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Separate test database URL - never use production database for testing
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:"
)

engine_kwargs: dict[str, object] = {}
if TEST_DATABASE_URL.startswith("sqlite"):
    # Keep the same in-memory DB across connections/threads for TestClient.
    engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

test_engine = create_engine(TEST_DATABASE_URL, **engine_kwargs)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    # Create the database tables
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the database tables after each test to ensure isolation
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    # Override the get_db dependency to use the test database session
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()  # Clear overrides after the test
