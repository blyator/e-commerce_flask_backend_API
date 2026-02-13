from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Product, Category, CartItem, Order, OrderItem, Invoice
from datetime import datetime
import uuid
import logging
from sqlalchemy.exc import SQLAlchemyError
from views.mailserver import send_email, send_order_confirmation_email


order_bp = Blueprint('order', __name__, url_prefix='/orders')
logger = logging.getLogger(__name__)


def get_current_user_id():
    try:
        identity = get_jwt_identity()
        if identity is None:
            return None
        
  
        if isinstance(identity, dict):
            return identity.get('id')
        else:
            return identity
    except Exception as e:
        logger.error(f"Error getting current user ID: {str(e)}")
        return None


@order_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_orders():
    try:
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token or user not authenticated'}), 401
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        status_filter = request.args.get('status')

        if user.role in ['admin', 'manager']:
            orders_query = Order.query
        else:
            orders_query = Order.query.filter_by(user_id=user_id)

        if status_filter and status_filter.lower() != "all":
            orders_query = orders_query.filter(Order.status.ilike(f'%{status_filter}%'))

        orders_query = orders_query.order_by(Order.created_at.desc())
        orders = orders_query.all()

        orders_data = [order.to_dict() for order in orders]
        return jsonify({"orders": orders_data}), 200

    except Exception as e:
        logger.error(f"Error fetching all orders: {str(e)}")
        return jsonify({'error': 'Failed to fetch orders', 'details': str(e)}), 500


@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_orders():
    try:
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token or user not authenticated'}), 401

        status_filter = request.args.get('status')

        orders_query = Order.query.filter_by(user_id=user_id)

        if status_filter and status_filter.lower() != "all":
            orders_query = orders_query.filter(Order.status.ilike(f'%{status_filter}%'))

        orders_query = orders_query.order_by(Order.created_at.desc())
        orders = orders_query.all()

 
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            
            order_dict.update({
                'id': order.id,
                'userId': order.user_id,
                'status': order.status.lower() if order.status else 'pending',
                'createdAt': order.created_at.isoformat() if order.created_at else datetime.now().isoformat(),
                'total_price': float(order.total_price) if order.total_price else 0.0,
                'total': float(order.total_price) if order.total_price else 0.0,
                'shippingInfo': order.shipping_info if order.shipping_info else {},
                'shipping_info': order.shipping_info if order.shipping_info else {},
                'items': [
                    {
                        'id': item.product.id,
                        'name': item.product.name,
                        'price': float(item.price_at_order),
                        'quantity': item.quantity,
                        'image': item.product.image if hasattr(item.product, 'image') else None
                    }
                    for item in order.order_items
                ] if hasattr(order, 'order_items') else []
            })
            
            orders_data.append(order_dict)

        return jsonify({"orders": orders_data}), 200

    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return jsonify({'error': 'Failed to fetch orders', 'details': str(e)}), 500


@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    try:
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token or user not authenticated'}), 401
        

        user = User.query.get(user_id)
        if user.role == 'admin':
            order = Order.query.get(order_id)
        else:
            order = Order.query.filter_by(id=order_id, user_id=user_id).first()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        order_data = order.to_dict()
        

        order_data.update({
            'id': order.id,
            'userId': order.user_id,
            'status': order.status.lower() if order.status else 'pending',
            'createdAt': order.created_at.isoformat() if order.created_at else datetime.now().isoformat(),
            'total_price': float(order.total_price) if order.total_price else 0.0,
            'total': float(order.total_price) if order.total_price else 0.0,
            'shippingInfo': order.shipping_info if order.shipping_info else {},
            'shipping_info': order.shipping_info if order.shipping_info else {},
        })

        if order.invoice:
            order_data['invoice_number'] = order.invoice.invoice_number
            order_data['invoice_id'] = order.invoice.id
            order_data['invoice_issued_at'] = order.invoice.issued_at.isoformat()
            order_data['invoice_pdf_url'] = order.invoice.pdf_url

        return jsonify(order_data), 200

    except Exception as e:
        logger.error(f"Error fetching order details: {str(e)}")
        return jsonify({'error': 'Failed to fetch order details'}), 500


@order_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    try:
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token or user not authenticated'}), 401
            
        data = request.get_json()

        if not data or 'shipping_info' not in data:
            return jsonify({'error': 'Shipping information is required'}), 400

        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400

        total_price = sum(item.product.price * item.quantity for item in cart_items)
        
        shipping_cost = float(data.get('shipping_info', {}).get('shipping', 0))
        total_price += shipping_cost

        order = Order(
            user_id=user_id,
            shipping_info=data['shipping_info'],
            total_price=total_price,
            status='pending'  
        )
        db.session.add(order)
        db.session.flush()  

        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price_at_order=cart_item.product.price
            )
            db.session.add(order_item)

        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        invoice = Invoice(
            invoice_number=invoice_number,
            order_id=order.id,
            pdf_url=f"/invoices/{order.id}.pdf"
        )
        db.session.add(invoice)

        CartItem.query.filter_by(user_id=user_id).delete()

        db.session.commit()
        
 
        try:
            send_order_confirmation_email(
                name=f"{order.shipping_info.get('firstName', '')} {order.shipping_info.get('lastName', '')}".strip(),
                email=order.shipping_info.get('email', ''),
                order={
                    "id": order.id,
                    "invoice_number": invoice.invoice_number,
                    "total": order.total_price,
                    "shippingInfo": {
                        "firstName": order.shipping_info.get('firstName', ''),
                        "lastName": order.shipping_info.get('lastName', ''),
                        "city": order.shipping_info.get('city', ''),
                    },
                    "items": [
                        {
                            "name": item.product.name,
                            "quantity": item.quantity,
                            "price": item.price_at_order
                        }
                        for item in order.order_items
                    ]
                }
            )
        except Exception as email_error:
            logger.warning(f"Failed to send confirmation email: {str(email_error)}")
        
        order_dict = order.to_dict()
        order_dict.update({
            'id': order.id,
            'userId': order.user_id,
            'status': order.status.lower(),
            'createdAt': order.created_at.isoformat(),
            'total_price': float(order.total_price),
            'total': float(order.total_price),
            'shippingInfo': order.shipping_info,
            'shipping_info': order.shipping_info,
        })
        
        return jsonify({
            'message': 'Order placed successfully',
            'order': order_dict,
            'invoice_number': invoice_number
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during checkout: {str(e)}")
        return jsonify({'error': 'Failed to process order'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during checkout: {str(e)}")
        return jsonify({'error': 'Checkout failed'}), 500


@order_bp.route('/<int:order_id>/invoice', methods=['GET'])
@jwt_required()
def get_order_invoice(order_id):
    try:
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token or user not authenticated'}), 401

        user = User.query.get(user_id)
        if user.role == 'admin':
            order = Order.query.get(order_id)
        else:
            order = Order.query.filter_by(id=order_id, user_id=user_id).first()
            
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        invoice = Invoice.query.filter_by(order_id=order_id).first()
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        invoice_data = {
            'invoice_number': invoice.invoice_number,
            'order_id': order.id,
            'date': order.created_at.isoformat(),
            'customer': {
                'name': f"{order.shipping_info.get('firstName', '')} {order.shipping_info.get('lastName', '')}",
                'email': order.shipping_info.get('email', '')
            },
            'shipping_address': {
                'city': order.shipping_info.get('city', ''),
                'county': order.shipping_info.get('county', '')
            },
            'items': [
                {
                    'name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price_at_order),
                    'total': float(item.price_at_order * item.quantity)
                }
                for item in order.order_items
            ],
            'subtotal': float(sum(item.price_at_order * item.quantity for item in order.order_items)),
            'shipping': float(order.shipping_info.get('shipping', 0)),
            'total': float(order.total_price),
            'status': order.status.lower()
        }

        return jsonify(invoice_data), 200

    except Exception as e:
        logger.error(f"Error generating invoice: {str(e)}")
        return jsonify({'error': 'Failed to generate invoice'}), 500


@order_bp.route('/<int:order_id>/status', methods=['PUT', 'PATCH'])
@jwt_required()
def update_order_status(order_id):
    try:
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token or user not authenticated'}), 401
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400


        new_status = data['status'].lower()
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        
        if new_status not in valid_statuses:
            return jsonify({'error': 'Invalid status', 'valid_statuses': valid_statuses}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        order.status = new_status
        db.session.commit()


        order_dict = order.to_dict()
        order_dict.update({
            'id': order.id,
            'userId': order.user_id,
            'status': order.status.lower(),
            'createdAt': order.created_at.isoformat(),
            'total_price': float(order.total_price),
            'total': float(order.total_price),
            'shippingInfo': order.shipping_info,
            'shipping_info': order.shipping_info,
        })

        return jsonify({
            'message': 'Order status updated',
            'order': order_dict
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating order status: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500