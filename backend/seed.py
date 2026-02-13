from models import db, Category, Product, User, Order, OrderItem
from app import app
from werkzeug.security import generate_password_hash
from random import randint, sample
from datetime import datetime, timedelta


# Sample categories
categories = [
    {"name": "skincare", "label": "Skincare", "icon": "✨"},
    {"name": "makeup", "label": "Makeup", "icon": "💄"},
    {"name": "haircare", "label": "Haircare", "icon": "💇‍♀️"},
]

# Sample products
products = [
    {"name": "Hydrating Vitamin C Serum", "category": "skincare", "price": 600, "image": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop", "description": "A powerful vitamin C serum that brightens and hydrates your skin for a radiant glow.", "in_stock": True, "rating": 4.8, "reviews": 324},
    {"name": "Gentle Cleansing Foam", "category": "skincare", "price": 499, "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400&h=400&fit=crop", "description": "A gentle, sulfate-free cleanser that removes makeup and impurities without stripping your skin.", "in_stock": True, "rating": 4.6, "reviews": 189},
    {"name": "Retinol Night Cream", "category": "skincare", "price": 1280, "image": "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=400&h=400&fit=crop", "description": "Anti-aging night cream with retinol to reduce fine lines and improve skin texture.", "in_stock": True, "rating": 4.9, "reviews": 456},
    {"name": "Hydrating Face Mask", "category": "skincare", "price": 455, "image": "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=400&h=400&fit=crop", "description": "Intensive hydrating mask with hyaluronic acid for plump, moisturized skin.", "in_stock": True, "rating": 4.7, "reviews": 267},
    {"name": "Full Coverage Foundation", "category": "makeup", "price": 1520, "image": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=400&h=400&fit=crop", "description": "Long-lasting, full coverage foundation available in 40 shades.", "in_stock": True, "rating": 4.5, "reviews": 892},
    {"name": "Matte Liquid Lipstick", "category": "makeup", "price": 289, "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&h=400&fit=crop", "description": "Long-wearing matte liquid lipstick that doesn't dry out your lips.", "in_stock": True, "rating": 4.4, "reviews": 634},
    {"name": "Eyeshadow Palette", "category": "makeup", "price": 650, "image": "https://images.unsplash.com/photo-1650664370914-f026578ec2a4?q=80&w=769&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D=crop", "description": "18-shade eyeshadow palette with matte and shimmer finishes.", "in_stock": True, "rating": 4.8, "reviews": 445},
    {"name": "Volumizing Mascara", "category": "makeup", "price": 350, "image": "https://images.unsplash.com/photo-1619168213439-8af6b0fd5956?q=80&w=707&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D=crop", "description": "Waterproof volumizing mascara for dramatic, long-lasting lashes.", "in_stock": False, "rating": 4.6, "reviews": 523},
    {"name": "Nourishing Hair Oil", "category": "haircare", "price": 1750, "image": "https://images.unsplash.com/photo-1669281393011-c335050cf0e9?q=80&w=1025&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D=crop", "description": "Lightweight hair oil that nourishes and adds shine without weighing hair down.", "in_stock": True, "rating": 4.7, "reviews": 298},
    {"name": "Repair Shampoo", "category": "haircare", "price": 2085, "image": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=400&fit=crop", "description": "Sulfate-free shampoo that repairs and strengthens damaged hair.", "in_stock": True, "rating": 4.5, "reviews": 412},
    {"name": "Deep Conditioning Mask", "category": "haircare", "price": 550, "image": "https://images.unsplash.com/photo-1526045478516-99145907023c?w=400&h=400&fit=crop", "description": "Weekly deep conditioning treatment for dry and damaged hair.", "in_stock": True, "rating": 4.9, "reviews": 356},
    {"name": "Heat Protection Spray", "category": "haircare", "price": 2999, "image": "https://images.unsplash.com/photo-1651763473748-f3674427ade3?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D=crop", "description": "Protects hair from heat damage up to 450°F while adding shine.", "in_stock": True, "rating": 4.4, "reviews": 278},
    {"name": "Brightening Eye Cream", "category": "skincare", "price": 999, "image": "https://images.unsplash.com/photo-1570554886111-e80fcca6a029?w=400&h=400&fit=crop", "description": "Reduces dark circles and puffiness while firming the delicate eye area.", "in_stock": True, "rating": 4.6, "reviews": 203},
    {"name": "Contouring Kit", "category": "makeup", "price": 580, "image": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400&h=400&fit=crop", "description": "Professional contouring kit with 6 shades for sculpting and highlighting.", "in_stock": True, "rating": 4.3, "reviews": 167},
    {"name": "Dry Shampoo", "category": "haircare", "price": 1490, "image": "https://images.unsplash.com/photo-1630398917451-1a409990fbc5?q=80&w=735&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D=crop", "description": "Refreshes hair between washes and adds volume at the roots.", "in_stock": True, "rating": 4.2, "reviews": 389},
    {"name": "Exfoliating Scrub", "category": "skincare", "price": 1200, "image": "https://images.unsplash.com/photo-1589504695518-a9a9ac06c2e9?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D=crop", "description": "Gentle exfoliating scrub that removes dead skin cells for smoother skin.", "in_stock": True, "rating": 4.5, "reviews": 445},
]
def seed():
    with app.app_context():
        print("🌱 Seeding data...")
        
        try:
            # Clear existing data
            print("Dropping existing tables...")
            db.drop_all()
            print("Creating new tables...")
            db.create_all()

            # Add categories
            print("Adding categories...")
            category_map = {}
            for cat in categories:
                c = Category(name=cat["name"], label=cat["label"], icon=cat["icon"])
                db.session.add(c)
                category_map[cat["name"]] = c
            db.session.commit()
            print(f"Added {len(categories)} categories")

            # Add admin user
            print("Adding admin user...")
            admin_user = User(
                username="admin",
                email="admin@admin",
                password_hash=generate_password_hash("admin@thebeauty"),
                role="admin"
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created")

            # Add products
            print("Adding products...")
            for prod in products:
                product = Product(
                    name=prod["name"],
                    price=prod["price"],
                    image=prod["image"],
                    description=prod["description"],
                    in_stock=prod["in_stock"],
                    rating=prod["rating"],
                    reviews=prod["reviews"],
                    category=category_map[prod["category"]],
                )
                db.session.add(product)
            db.session.commit()
            print(f"Added {len(products)} products")

            # Add test users and orders
            print("Creating test users and orders...")
            for i in range(1, 11):
                print(f"Creating user {i}...")
                user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash=generate_password_hash("password123"),
                role="customer"  # Updated role
)
                db.session.add(user)
                db.session.commit()

                order_count = randint(1, 2)
                for order_num in range(1, order_count + 1):
                    print(f"  Creating order {order_num} for user {i}...")
                    order = Order(
                        user_id=user.id,
                        created_at=datetime.utcnow() - timedelta(days=randint(1, 90)),
                        status="pending",
                        total_price=0
                    )
                    db.session.add(order)
                    db.session.commit()

                    selected_products = sample(products, k=randint(1, 3))
                    total_price = 0
                    
                    for prod_data in selected_products:
                        product = Product.query.filter_by(name=prod_data["name"]).first()
                        if product:
                            quantity = randint(1, 3)
                            item = OrderItem(
                                order_id=order.id,
                                product_id=product.id,
                                quantity=quantity,
                                price_at_order=product.price
                            )
                            db.session.add(item)
                            total_price += product.price * quantity
                            print(f"    Added {quantity}x {product.name} @ KES {product.price}")
                    
                    order.total_price = total_price
                    db.session.commit()
                    print(f"  Order total: KES {total_price}")

            print("Done seeding successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f" Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    seed()