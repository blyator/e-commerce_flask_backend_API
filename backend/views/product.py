from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Product, Category

product_bp = Blueprint('product', __name__, url_prefix='/products')

@product_bp.route('/', methods=['GET'])
def get_products():
    search = request.args.get("search", "", type=str).lower()
    category_name = request.args.get("category", "all", type=str).lower()
    sort = request.args.get("sort", "newest", type=str).lower() 

    query = Product.query.join(Category)

    if category_name != "all":
        query = query.filter(Category.name.ilike(category_name))

    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%"))
        )

    sort_map = {
        "price-low": Product.price.asc(),
        "price-high": Product.price.desc(),
        "rating": Product.rating.desc(),
        "newest": Product.id.desc(),
        "name": Product.name.asc(),
    }
    sort_criteria = sort_map.get(sort, Product.id.desc())
    query = query.order_by(sort_criteria)

    products = query.all()
    return jsonify([p.to_dict() for p in products])



@product_bp.route('/', methods=['POST'])
@jwt_required()
def add_product():
    user = get_jwt_identity()
    if user['role'] != 'admin' and user['role'] != 'manager':
        return jsonify({"error": "Permission denied"}), 403

    data = request.get_json()

    required_fields = ['name', 'price', 'category_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    new_product = Product(
        name=data['name'],
        price=data['price'],
        category_id=data['category_id'],
        image=data.get('image'),
        description=data.get('description'),
        in_stock=data.get('in_stock', True),
        rating=data.get('rating', 0.0),
        reviews=data.get('reviews', 0),
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify(new_product.to_dict()), 201


@product_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "label": c.label,
            "icon": c.icon
        }
        for c in categories
    ])


@product_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):
    identity = get_jwt_identity()

    if identity['role'] not in ['admin', 'manager']:
        return jsonify({"error": "Permission denied"}), 403

    product = Product.query.get_or_404(id)
    data = request.get_json()
    for field in ['name', 'description', 'price', 'in_stock', 'image', 'category_id']:
        if field in data:
            setattr(product, field, data[field])
    db.session.commit()
    return jsonify(product.to_dict())




@product_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    try:
        identity = get_jwt_identity()
        print("JWT Identity:", identity, "| Type:", type(identity))

        if not isinstance(identity, dict):
            return jsonify({"error": "Invalid token format - identity must be a dict"}), 401

        if identity.get('role') not in ['admin', 'manager']:
            return jsonify({"error": "Permission denied"}), 403

        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted"}), 200

    except Exception as e:
        db.session.rollback()
        print("Delete error:", str(e))
        return jsonify({"error": str(e)}), 500

        return jsonify({"error": str(e)}), 500