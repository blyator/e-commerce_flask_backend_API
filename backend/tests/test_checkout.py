import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


from models import CartItem


def test_checkout_with_items(client, customer_token, customer_user, product, db):
    cart_item = CartItem(user_id=customer_user.id, product_id=product.id, quantity=2)
    db.session.add(cart_item)
    db.session.commit()

    response = client.post(
        "/orders/checkout",
        json={
            "shipping_info": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@test.com",
                "city": "NYC",
                "shipping": 10.0,
            }
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "order" in data
    assert "id" in data["order"]


def test_checkout_empty_cart(client, customer_token):
    response = client.post(
        "/orders/checkout",
        json={
            "shipping_info": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@test.com",
                "city": "NYC",
                "shipping": 10.0,
            }
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 400
    assert "Cart is empty" in response.get_json()["error"]


def test_checkout_unauthenticated(client, product):
    response = client.post(
        "/orders/checkout",
        json={
            "shipping_info": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@test.com",
                "city": "NYC",
                "shipping": 10.0,
            }
        },
    )
    assert response.status_code == 401


def test_checkout_missing_shipping(client, customer_token):
    response = client.post(
        "/orders/checkout",
        json={},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 400
