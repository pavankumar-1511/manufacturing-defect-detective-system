import os
import io
import pytest
import numpy as np
import cv2
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app

# Create in-memory SQLite database for isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_clean_image_bytes():
    """Generates bytes of a valid, pristine industrial part image."""
    img = np.full((300, 300, 3), 190, dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (280, 280), (120, 120, 120), 2)
    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()

@pytest.fixture
def sample_defective_image_bytes():
    """Generates bytes of a valid part image with a severe scratch defect."""
    img = np.full((300, 300, 3), 180, dtype=np.uint8)
    # Scratch defect
    cv2.line(img, (50, 60), (240, 250), (10, 10, 10), 3)
    cv2.line(img, (52, 62), (238, 248), (250, 250, 250), 1)
    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()
