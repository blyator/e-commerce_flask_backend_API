import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from models import User


def test_login_success(client, customer_user):
    response = client.post(
        "/login", json={"email": "customer@test.com", "password": "customer123"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "customer@test.com"


def test_login_invalid_email(client):
    response = client.post(
        "/login", json={"email": "wrong@test.com", "password": "password"}
    )
    assert response.status_code == 401
    assert "error" in response.get_json()


def test_login_invalid_password(client, customer_user):
    response = client.post(
        "/login", json={"email": "customer@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_missing_fields(client):
    response = client.post("/login", json={"email": "test@test.com"})
    assert response.status_code == 400


def test_login_blocked_user(client, db):
    from werkzeug.security import generate_password_hash

    user = User(
        username="blocked",
        email="blocked@test.com",
        role="customer",
        blocked=True,
        password_hash=generate_password_hash("password123"),
    )
    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/login", json={"email": "blocked@test.com", "password": "password123"}
    )
    assert response.status_code == 403
