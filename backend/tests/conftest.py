import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import limiter
from models import CartItem, Category, Product, User
from models import db as _db


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        _db.session.expire_on_commit = False
        yield _db
        _db.session.rollback()
        _db.session.remove()


@pytest.fixture
def admin_user(db):
    user = User.query.filter_by(email="admin@test.com").first()
    if not user:
        user = User(
            username="admin",
            email="admin@test.com",
            role="admin",
            password_hash=generate_password_hash("admin123"),
        )
        db.session.add(user)
        db.session.commit()
    return user


@pytest.fixture
def customer_user(db):
    user = User.query.filter_by(email="customer@test.com").first()
    if not user:
        user = User(
            username="customer",
            email="customer@test.com",
            role="customer",
            password_hash=generate_password_hash("customer123"),
        )
        db.session.add(user)
        db.session.commit()
    return user


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post(
        "/login", json={"email": "admin@test.com", "password": "admin123"}
    )
    return response.get_json()["access_token"]


@pytest.fixture
def customer_token(client, customer_user):
    response = client.post(
        "/login", json={"email": "customer@test.com", "password": "customer123"}
    )
    return response.get_json()["access_token"]


@pytest.fixture
def category(db):
    cat = Category.query.filter_by(name="Electronics").first()
    if not cat:
        cat = Category(name="Electronics", label="electronics")
        db.session.add(cat)
        db.session.commit()
    return cat


@pytest.fixture
def product(db, category):
    prod = Product.query.filter_by(name="Test Product").first()
    if not prod:
        prod = Product(
            name="Test Product", price=99.99, category_id=category.id, in_stock=True
        )
        db.session.add(prod)
        db.session.commit()
    return prod
