import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db
from app.models import Base

# Hardcoded to match your actual PostgreSQL connection
# User: johnfem007, Password: postgres, Database: saleszy_v2
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:johnfem007@localhost:5432/saleszy_v2"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Drop tables after each test so your real data stays safe
    Base.metadata.drop_all(bind=engine)