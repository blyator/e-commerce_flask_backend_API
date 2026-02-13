from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from views.mailserver import send_manager_invite_email
from models import db, User, Order




user_bp = Blueprint('user', __name__, url_prefix='/users')


@user_bp.route('', methods=['GET'])
@jwt_required()
def get_all_users():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({"error": "Admin only"}), 403
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]})


@user_bp.route('/<int:id>/block', methods=['PATCH'])
@jwt_required()
def toggle_block_user(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({"error": "Admin only"}), 403

    user = User.query.get_or_404(id)
    user.blocked = not user.blocked
    db.session.commit()

    status = "blocked" if user.blocked else "unblocked"
    return jsonify({
        "message": f"User {status} successfully",
        "user": user.to_dict()
    }), 200


@user_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({"error": "Admin only"}), 403

    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"User with ID {id} deleted successfully."}), 200


@user_bp.route('/create-manager', methods=['POST'])
@jwt_required()
def create_manager():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({"error": "Admin only"}), 403

    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if user:
        user.role = 'manager'
        db.session.commit()

        send_manager_invite_email(name=user.username, email=email, is_existing_user=True)

        return jsonify({
            "message": f"User '{email}' role updated to manager.",
            "user": user.to_dict()
        }), 200

    default_password = "manager@thebeauty"
    hashed_password = generate_password_hash(default_password)

    username = email.split('@')[0]

    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        role='manager'
    )
    db.session.add(new_user)
    db.session.commit()

    send_manager_invite_email(name=username, email=email, is_existing_user=False, password=default_password)

    return jsonify({
        "message": f"Manager account created for {email}",
        "default_password": default_password,
        "user": new_user.to_dict()
    }), 201





@user_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_account():
    identity = get_jwt_identity()
    user_id = identity.get("id")

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        Order.query.filter_by(user_id=user_id).update({"user_id": None})
        db.session.commit()


        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "Account deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete account: {str(e)}"}), 500
    



@user_bp.route("/change-password", methods=["PATCH"])
@jwt_required()
def change_password():
    identity = get_jwt_identity()
    user_id = identity.get("id")

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return jsonify({"error": "Both current and new passwords are required"}), 400


    if not check_password_hash(user.password_hash, current_password):
        return jsonify({"error": "Current password is incorrect"}), 400

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200


