from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import MetaData, Text
from sqlalchemy.dialects.postgresql import JSON

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

ROLE_CHOICES = ("admin", "order_manager", "customer")
ORDER_STATUS_CHOICES = ("Pending", "Processing", "Shipped", "Delivered")

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(10), nullable=False, default='customer')
    blocked= db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cart_items    = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders        = db.relationship("Order",     back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "blocked": self.blocked,
            "created_at": self.created_at.isoformat()
        }

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(20))

    # Relationship
    products = db.relationship("Product", back_populates="category", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "label": self.label,
            "icon": self.icon,
            "products": [product.to_dict() for product in self.products]
        }

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    in_stock = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=0.0)
    reviews = db.Column(db.Integer, default=0)

    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)    # Relationship to access category info from product
    category = db.relationship("Category", back_populates="products")
    
    cart_items = db.relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.name if self.category else None,
            "price": self.price,
            "image": self.image,
            "description": self.description,
            "inStock": self.in_stock,
            "rating": self.rating,
            "reviews": self.reviews,
        }


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id          = db.Column(db.Integer, primary_key=True)
    quantity    = db.Column(db.Integer, nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    product_id  = db.Column(db.Integer, db.ForeignKey("products.id"))

    # Relationships
    user        = db.relationship("User", back_populates="cart_items")
    product     = db.relationship("Product", back_populates="cart_items")

    def to_dict(self):
        return {
            "id": self.id,
            "quantity": self.quantity,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "product": self.product.to_dict() if self.product else None
        }

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="pending")
    shipping_info = db.Column(JSON, nullable=True)
    total_price = db.Column(db.Float, nullable=False)

    user = db.relationship("User", back_populates="orders")
    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice = db.relationship("Invoice", back_populates="order", uselist=False)

    def to_dict(self):
        shipping_info = self.shipping_info or {}
        shipping_cost = shipping_info.get("shipping", 0)

        return {
            "id": self.id,
            "userId": self.user_id,
            "user": self.user.username if self.user else None,
            "createdAt": self.created_at.isoformat(),
            "status": self.status.lower(),
            "subtotal": float(sum(item.price_at_order * item.quantity for item in self.order_items)),
            "shipping": float(shipping_cost),
            "total": float(self.total_price),
            "shippingInfo": {
                "firstName": shipping_info.get("firstName", ""),
                "lastName": shipping_info.get("lastName", ""),
                "email": shipping_info.get("email", ""),
                "city": shipping_info.get("city", ""),
                "county": shipping_info.get("county", ""),
            },
            "items": [
                {
                    "id": item.product_id,
                    "name": item.product.name if item.product else "Unknown Product",
                    "image": item.product.image if item.product else None,
                    "quantity": item.quantity,
                    "price": float(item.price_at_order),
                }
                for item in self.order_items
            ]
        }



class OrderItem(db.Model):
    __tablename__ = "order_items"

    id             = db.Column(db.Integer, primary_key=True)
    quantity       = db.Column(db.Integer, nullable=False)
    price_at_order = db.Column(db.Float,   nullable=False)
    order_id       = db.Column(db.Integer, db.ForeignKey("orders.id"))
    product_id     = db.Column(db.Integer, db.ForeignKey("products.id"))

    # Relationships
    order          = db.relationship("Order", back_populates="order_items")
    product        = db.relationship("Product", back_populates="order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "quantity": self.quantity,
            "price_at_order": self.price_at_order,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product": self.product.to_dict() if self.product else None
        }

class Invoice(db.Model):
    __tablename__ = "invoices"

    id             = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    issued_at      = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_url        = db.Column(db.String(255))
    order_id       = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True)

    # Relationships
    order          = db.relationship("Order", back_populates="invoice", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "issued_at": self.issued_at.isoformat(),
            "pdf_url": self.pdf_url,
            "order_id": self.order_id,
            
        }


class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)