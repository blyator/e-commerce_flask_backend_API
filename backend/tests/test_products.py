import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_add_product_as_admin(client, admin_token, category):
    response = client.post(
        "/products/",
        json={"name": "New Product", "price": 49.99, "category_id": category.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "New Product"


def test_add_product_as_customer(client, customer_token, category):
    response = client.post(
        "/products/",
        json={"name": "New Product", "price": 49.99, "category_id": category.id},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403


def test_add_product_unauthenticated(client, category):
    response = client.post(
        "/products/",
        json={"name": "New Product", "price": 49.99, "category_id": category.id},
    )
    assert response.status_code == 401


def test_add_product_missing_fields(client, admin_token):
    response = client.post(
        "/products/",
        json={"name": "Product"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
