from flask import Blueprint, jsonify, request
from models import db, Category
from flask_jwt_extended import jwt_required, get_jwt_identity

category_bp = Blueprint('category', __name__, url_prefix='/categories')

@category_bp.route('/', methods=['GET'])
def list_categories():

    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories]), 200

@category_bp.route('/', methods=['POST'])
@jwt_required()
def add_category():
    if get_jwt_identity()['role'] != 'admin':
        return jsonify({"error": "Permission denied"}), 403

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400

    existing = Category.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({"error": "Category with this name already exists."}), 409

    category = Category(name=data['name'])
    db.session.add(category)
    db.session.commit()

    return jsonify(category.to_dict()), 201
