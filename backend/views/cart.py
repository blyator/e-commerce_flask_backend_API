# routes/cart.py
from extensions import cache
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import CartItem, Product, db

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")
from sqlalchemy.orm import joinedload


def make_cart_cache_key(*args, **kwargs):
    user_identity = get_jwt_identity()
    if isinstance(user_identity, dict):
        user_id = user_identity.get("id")
    else:
        user_id = user_identity
    return f"view//cart/{user_id}"


@cart_bp.route("", methods=["GET"])
@jwt_required()
@cache.cached(timeout=120, make_cache_key=make_cart_cache_key)
def view_cart():
    """
    View current user cart
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    responses:
      200:
        description: List of cart items
    """
    try:

        user_identity = get_jwt_identity()
        if isinstance(user_identity, dict):
            user_id = user_identity.get("id")
        else:
            user_id = user_identity

        if not user_id:
            return jsonify({"error": "Invalid token format"}), 401

        cart_items = (
            CartItem.query.options(joinedload(CartItem.product))
            .filter_by(user_id=user_id)
            .all()
        )

        return jsonify([item.to_dict() for item in cart_items])

    except Exception as e:
        print(f"Error in view_cart: {str(e)}")
        return jsonify({"error": "Failed to fetch cart", "details": str(e)}), 500


@cart_bp.route("", methods=["POST"])
@jwt_required()
def add_to_cart():
    """
    Add product to cart
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - product_id
            - quantity
          properties:
            product_id:
              type: integer
            quantity:
              type: integer
    responses:
      201:
        description: Item added to cart
      200:
        description: Item quantity updated
      400:
        description: Invalid input
    """
    try:

        user_identity = get_jwt_identity()
        if isinstance(user_identity, dict):
            user_id = user_identity.get("id")
        else:
            user_id = user_identity

        if not user_id:
            return jsonify({"error": "Invalid token format"}), 401

        data = request.get_json()

        if not data or "product_id" not in data or "quantity" not in data:
            return jsonify({"error": "product_id and quantity are required"}), 400

        product_id = data["product_id"]
        quantity = data["quantity"]

        if not isinstance(quantity, int) or quantity < 1:
            return jsonify({"error": "quantity must be a positive integer"}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        existing_item = CartItem.query.filter_by(
            user_id=user_id, product_id=product_id
        ).first()

        if existing_item:

            existing_item.quantity += quantity
            db.session.commit()
            # Invalidate cart cache
            cache.delete(f"view//cart/{user_id}")
            return jsonify(existing_item.to_dict()), 200
        else:

            new_item = CartItem(
                user_id=user_id, product_id=product_id, quantity=quantity
            )
            db.session.add(new_item)
            db.session.commit()
            # Invalidate cart cache
            cache.delete(f"view//cart/{user_id}")
            return jsonify(new_item.to_dict()), 201

    except Exception as e:
        print(f"Error in add_to_cart: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to add to cart", "details": str(e)}), 500


@cart_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def remove_from_cart(item_id):
    """
    Remove item from cart
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Item removed
      404:
        description: Item not found
    """
    try:
        user_identity = get_jwt_identity()
        if isinstance(user_identity, dict):
            user_id = user_identity.get("id")
        else:
            user_id = user_identity

        if not user_id:
            return jsonify({"error": "Invalid token format"}), 401

        item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()

        if not item:
            return jsonify({"error": "Cart item not found"}), 404

        db.session.delete(item)
        db.session.commit()
        # Invalidate cart cache
        cache.delete(f"view//cart/{user_id}")
        return jsonify({"message": "Item removed successfully"}), 200

    except Exception as e:
        print(f"Error in remove_from_cart: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to remove item", "details": str(e)}), 500


@cart_bp.route("/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_cart_item(item_id):
    """
    Update cart item quantity
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        required: true
        type: integer
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - quantity
          properties:
            quantity:
              type: integer
    responses:
      200:
        description: Item updated
      400:
        description: Invalid quantity
      404:
        description: Item not found
    """
    try:
        user_identity = get_jwt_identity()
        if isinstance(user_identity, dict):
            user_id = user_identity.get("id")
        else:
            user_id = user_identity

        if not user_id:
            return jsonify({"error": "Invalid token format"}), 401

        data = request.get_json()

        if not data or "quantity" not in data:
            return jsonify({"error": "quantity is required"}), 400

        quantity = data["quantity"]

        if not isinstance(quantity, int) or quantity < 1:
            return jsonify({"error": "quantity must be a positive integer"}), 400

        item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()

        if not item:
            return jsonify({"error": "Cart item not found"}), 404

        item.quantity = quantity
        db.session.commit()
        # Invalidate cart cache
        cache.delete(f"view//cart/{user_id}")
        return jsonify(item.to_dict()), 200

    except Exception as e:
        print(f"Error in update_cart_item: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to update item", "details": str(e)}), 500


@cart_bp.route("/clear", methods=["DELETE"])
@jwt_required()
def clear_cart():
    """
    Clear all items from cart
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    responses:
      200:
        description: Cart cleared
    """
    try:
        user_identity = get_jwt_identity()
        if isinstance(user_identity, dict):
            user_id = user_identity.get("id")
        else:
            user_id = user_identity

        if not user_id:
            return jsonify({"error": "Invalid token format"}), 401

        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        # Invalidate cart cache
        cache.delete(f"view//cart/{user_id}")
        return jsonify({"message": "Cart cleared successfully"}), 200

    except Exception as e:
        print(f"Error in clear_cart: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to clear cart", "details": str(e)}), 500
