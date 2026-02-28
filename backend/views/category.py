from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.orm import joinedload

from extensions import cache
from models import Category, db

category_bp = Blueprint("category", __name__, url_prefix="/categories")


@category_bp.route("/", methods=["GET"])
@cache.cached(timeout=3600)
def list_categories():
    """
    List all categories with products
    ---
    tags:
      - Categories
    responses:
      200:
        description: List of categories
    """
    categories = Category.query.options(joinedload(Category.products)).all()
    return jsonify([category.to_dict() for category in categories]), 200


@category_bp.route("/", methods=["POST"])
@jwt_required()
def add_category():
    """
    Add a new category (Admin only)
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
    responses:
      201:
        description: Category created
      403:
        description: Admin only
      409:
        description: Category exists
    """
    if get_jwt_identity()["role"] != "admin":
        return jsonify({"error": "Permission denied"}), 403

    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Name is required"}), 400

    existing = Category.query.filter_by(name=data["name"]).first()
    if existing:
        return jsonify({"error": "Category with this name already exists."}), 409

    category = Category(name=data["name"])
    db.session.add(category)
    db.session.commit()

    # Invalidate categories cache
    cache.delete("view//categories/")

    return jsonify(category.to_dict()), 201
