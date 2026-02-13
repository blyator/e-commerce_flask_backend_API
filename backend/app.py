from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger
from models import db, TokenBlocklist, jwt
from views import auth_bp, user_bp, product_bp, order_bp, category_bp, cart_bp
from views.mailserver import email
from dotenv import load_dotenv
import os
from datetime import timedelta


migrate = Migrate()

def create_app():

    load_dotenv()

    app = Flask(__name__)

    # Config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    app.config['SWAGGER'] = {
        'title': 'The Shop API',
        'uiversion': 3
    }

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, credentials=True)
    Swagger(app)

    # Initialize Mail
    email(app)


    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return jsonify({"error": "Token has been revoked, please login again."}), 401

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(cart_bp)

    @app.route('/')
    def index():
        return {'message': 'Welcome to The Shop API'}, 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
