import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Set test environment before importing app modules
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/goaltracking_test",
)

from app.db import get_db
from app.main import app
from app.models import Base


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    database_url = os.environ["DATABASE_URL"]

    # Create the test database if it doesn't exist
    base_url = database_url.rsplit("/", 1)[0]
    db_name = database_url.rsplit("/", 1)[1]

    temp_engine = create_engine(f"{base_url}/postgres", isolation_level="AUTOCOMMIT")
    with temp_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        )
        if not result.fetchone():
            conn.execute(text(f"CREATE DATABASE {db_name}"))
    temp_engine.dispose()

    # Create engine for test database
    test_engine = create_engine(database_url)

    # Create extensions and types
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        conn.execute(
            text("""
            DO $$ BEGIN
                CREATE TYPE activity_type AS ENUM ('run', 'hangout', 'work');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$
        """)
        )
        conn.execute(
            text("""
            DO $$ BEGIN
                CREATE TYPE run_workout_type AS ENUM ('easy','tempo','intervals','long','race','recovery');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$
        """)
        )
        conn.execute(
            text("""
            DO $$ BEGIN
                CREATE TYPE work_status AS ENUM ('idea','todo','in_progress','blocked','done');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$
        """)
        )
        conn.commit()

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Cleanup
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
