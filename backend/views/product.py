from extensions import cache, limiter
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import Category, Product, db
from sqlalchemy.orm import joinedload

product_bp = Blueprint("product", __name__, url_prefix="/products")


@product_bp.route("/", methods=["GET"])
@cache.cached(timeout=300, query_string=True)
@limiter.limit("2000 per minute")
def get_products():
    """
    Get all products (Paginated)
    ---
    tags:
      - Products
    parameters:
      - name: search
        in: query
        type: string
        description: Search term for products
      - name: category
        in: query
        type: string
        enum: [all, skincare, makeup, haircare]
        description: Filter by category name
      - name: sort
        in: query
        type: string
        enum: [price-low, price-high, rating, newest, name]
        description: Sort criteria
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: per_page
        in: query
        type: integer
        default: 10
        description: Items per page
    responses:
      200:
        description: Paginated list of products
    """
    search = request.args.get("search", "", type=str).lower()
    category_name = request.args.get("category", "all", type=str).lower()
    sort = request.args.get("sort", "newest", type=str).lower()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    query = Product.query.options(joinedload(Product.category)).join(Category)

    if category_name != "all":
        query = query.filter(Category.name.ilike(category_name))

    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%"))
            | (Product.description.ilike(f"%{search}%"))
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

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "products": [p.to_dict() for p in pagination.items],
            "page/per_page": f"{pagination.page}/{pagination.pages}",
            "current_page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }
    )


@product_bp.route("/", methods=["POST"])
@jwt_required()
def add_product():
    """
    Add a new product (Admin/Manager only)
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: ProductAdd
          required:
            - name
            - price
            - category_id
          properties:
            name:
              type: string
            price:
              type: number
            category_id:
              type: integer
            image:
              type: string
            description:
              type: string
            in_stock:
              type: boolean
    responses:
      201:
        description: Product created successfully
      400:
        description: Missing required fields
      403:
        description: Permission denied
    """
    user = get_jwt_identity()
    if user["role"] != "admin" and user["role"] != "manager":
        return jsonify({"error": "Permission denied"}), 403

    data = request.get_json()

    required_fields = ["name", "price", "category_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    new_product = Product(
        name=data["name"],
        price=data["price"],
        category_id=data["category_id"],
        image=data.get("image"),
        description=data.get("description"),
        in_stock=data.get("in_stock", True),
        rating=data.get("rating", 0.0),
        reviews=data.get("reviews", 0),
    )

    db.session.add(new_product)
    db.session.commit()

    # Invalidate products cache
    cache.delete("view//products/")

    return jsonify(new_product.to_dict()), 201


@product_bp.route("/categories", methods=["GET"])
def get_categories():
    """
    Get all categories
    ---
    tags:
      - Products
    responses:
      200:
        description: List of categories
    """
    categories = Category.query.all()
    return jsonify(
        [
            {"id": c.id, "name": c.name, "label": c.label, "icon": c.icon}
            for c in categories
        ]
    )


@product_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_product(id):
    """
    Update a product (Admin/Manager only)
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
      - name: body
        in: body
        required: true
        schema:
          id: ProductUpdate
          properties:
            name:
              type: string
            price:
              type: number
            category_id:
              type: integer
            image:
              type: string
            description:
              type: string
            in_stock:
              type: boolean
    responses:
      200:
        description: Product updated successfully
      403:
        description: Permission denied
      404:
        description: Product not found
    """
    identity = get_jwt_identity()

    if identity["role"] not in ["admin", "manager"]:
        return jsonify({"error": "Permission denied"}), 403

    product = Product.query.get_or_404(id)
    data = request.get_json()
    for field in ["name", "description", "price", "in_stock", "image", "category_id"]:
        if field in data:
            setattr(product, field, data[field])
    db.session.commit()

    # Invalidate products cache
    cache.delete("view//products/")

    return jsonify(product.to_dict())


@product_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_product(id):
    """
    Delete a product (Admin/Manager only)
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Product deleted successfully
      403:
        description: Permission denied
      404:
        description: Product not found
    """
    try:
        identity = get_jwt_identity()
        print("JWT Identity:", identity, "| Type:", type(identity))

        if not isinstance(identity, dict):
            return (
                jsonify({"error": "Invalid token format - identity must be a dict"}),
                401,
            )

        if identity.get("role") not in ["admin", "manager"]:
            return jsonify({"error": "Permission denied"}), 403

        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()

        # Invalidate products cache
        cache.delete("view//products/")

        return jsonify({"message": "Product deleted"}), 200

    except Exception as e:
        db.session.rollback()
        print("Delete error:", str(e))
        return jsonify({"error": str(e)}), 500
