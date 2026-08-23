from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from ..main import app
from ..database import get_db, Base
from ..auth import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_user():
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data

def test_create_user_duplicate_email():
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser1", "password": "testpassword123"},
    )
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser2", "password": "testpassword123"},
    )
    assert response.status_code == 400

def test_login():
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword123"},
    )
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_short_url():
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword123"},
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/urls/",
        headers={"Authorization": f"Bearer {token}"},
        json={"original_url": "https://www.example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://www.example.com/"
    assert data["click_count"] == 0

def test_create_custom_short_url():
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword123"},
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/urls/",
        headers={"Authorization": f"Bearer {token}"},
        json={"original_url": "https://www.example.com", "custom_code": "mysite"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "mysite"

def test_redirect():
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword123"},
    )
    token = login_response.json()["access_token"]
    
    create_response = client.post(
        "/urls/",
        headers={"Authorization": f"Bearer {token}"},
        json={"original_url": "https://www.example.com"},
    )
    short_code = create_response.json()["short_code"]
    
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.example.com/"

def test_get_url_stats():
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "testuser", "password": "testpassword123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword123"},
    )
    token = login_response.json()["access_token"]
    
    create_response = client.post(
        "/urls/",
        headers={"Authorization": f"Bearer {token}"},
        json={"original_url": "https://www.example.com"},
    )
    url_id = create_response.json()["id"]
    
    response = client.get(
        f"/urls/{url_id}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_clicks" in data
    assert "unique_visitors" in data
    assert "clicks_by_date" in data
