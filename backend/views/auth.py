from datetime import datetime, timezone
from functools import wraps

from extensions import limiter
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (JWTManager, create_access_token, get_jwt,
                                get_jwt_identity, jwt_required,
                                verify_jwt_in_request)
from models import TokenBlocklist, User, db, jwt
from views.mailserver import send_email
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')

            if user_role not in roles:
                return jsonify({"error": "You are not authorized to access this resource"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None

@jwt.revoked_token_loader
def revoked_token_response(jwt_header, jwt_payload):
    return jsonify({"error": "Token has been revoked, please login again."}), 401


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: UserRegistration
          required:
            - email
            - password
            - username
          properties:
            username:
              type: string
            email:
              type: string
            password:
              type: string
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid input
      409:
        description: Email already exists
    """
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    username = data.get('username') or data.get('name')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(
        username=username,
        email=data['email'],
        role='customer',
        password_hash=generate_password_hash(data['password'])
    )

    db.session.add(user)
    db.session.commit()
    send_email(user.username, user.email)

    access_token = create_access_token(identity={"id": user.id, "role": user.role})
    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at
    }

    return jsonify({
        "user": user_info,
        "access_token": access_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("1000 per minute")
def login():
    """
    Login user
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: UserLogin
          required:
            - email
            - password
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Email or password wrong
      403:
        description: Account suspended
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email or password is missing"}), 400
        
        user = User.query.filter_by(email=email).first()
        

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Email or password wrong"}), 401
        

        if user.blocked:
            return jsonify({"error": "Account is suspended"}), 403
        

        access_token = create_access_token(identity={"id": user.id, "role": user.role})
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at
        }
        
        return jsonify({
            "access_token": access_token,
            "user": user_info
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    """
    Logout user (Revoke token)
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Successfully logged out
      500:
        description: Internal server error
    """
    try:
        jti = get_jwt()['jti']
        now = datetime.now(timezone.utc)
        token = TokenBlocklist(jti=jti, created_at=now)
        db.session.add(token)
        db.session.commit()
        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        print(f"Logout error: {e}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500