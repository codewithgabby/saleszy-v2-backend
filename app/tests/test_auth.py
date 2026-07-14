from fastapi.testclient import TestClient

def test_register_and_login(client: TestClient):
    # 1. Register
    response = client.post("/api/v1/auth/register", json={
        "legal_name": "Test Shop",
        "owner_name": "Tester",
        "email": "test@shop.com",
        "phone": "08000000000",
        "password": "password123"
    })
    assert response.status_code == 201

    # 2. Login
    response = client.post("/api/v1/auth/login", json={
        "email": "test@shop.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()