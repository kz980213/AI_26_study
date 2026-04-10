from fastapi.testclient import TestClient
from app.main import app
from app.db import fake_users_db

client = TestClient(app)
def setup_function():
    fake_users_db.clear()

def create_user_and_login(username="kk", password="123456"):
    client.post("/auth/register", json={
        "username": username,
        "password": password
    })
    res = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_change_password_success():
    headers = create_user_and_login()

    res = client.put("/users/me/password", json={
        "old_password": "123456",
        "new_password": "654321"
    }, headers=headers)

    assert res.status_code == 200
    assert res.json()["message"] == "Password updated successfully"

def test_change_password_old_password_wrong():
    headers = create_user_and_login()

    res = client.put("/users/me/password", json={
        "old_password": "wrong123",
        "new_password": "654321"
    }, headers=headers)

    assert res.status_code == 400

def test_change_password_same_password():
    headers = create_user_and_login()

    res = client.put("/users/me/password", json={
        "old_password": "123456",
        "new_password": "123456"
    }, headers=headers)

    assert res.status_code == 400

def test_change_password_without_token():
    res = client.put("/users/me/password", json={
        "old_password": "123456",
        "new_password": "654321"
    })

    assert res.status_code in [401, 403]