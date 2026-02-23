from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger
from models import db, TokenBlocklist, jwt
from extensions import cache, limiter
from celery_app import celery_init_app
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
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 20,
        'max_overflow': 40,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
    }
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Celery config
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
            result_backend=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
            task_ignore_result=True,
            include=['tasks'],
        ),
    )
    celery_init_app(app)

    # Cache config
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300

    # Rate Limiter config
    app.config['RATELIMIT_STORAGE_URI'] = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    app.config['RATELIMIT_STRATEGY'] = 'fixed-window'
    app.config['RATELIMIT_HEADERS_ENABLED'] = True
    
    # Swagger config
    app.config['SWAGGER'] = {
    'title': 'The Shop API',
    'uiversion': 3,
    'specs_route': '/apidocs/',
    'ui_params': {
        'apisSorter': 'alpha',
        'operationsSorter': 'alpha',
        'tagsSorter': 'alpha',
        'docExpansion': 'list',
        'defaultModelsExpandDepth': -1,
        'onComplete': '''function() {
            fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: "user@demo.com", password: "demo1234" })
            })
            .then(res => res.json())
            .then(data => {
                if (data.access_token) {
                    ui.preauthorizeApiKey("Bearer", "Bearer " + data.access_token);
                }
            });
        }'''
    },
    'tags': [
        {'name': 'Authentication', 'description': 'Login, Logout, and Registration'},
        {'name': 'Products', 'description': 'Product catalog management'},
        {'name': 'Categories', 'description': 'Product categories'},
        {'name': 'Cart', 'description': 'User shopping cart'},
        {'name': 'Orders', 'description': 'Order processing and history'},
        {'name': 'Users', 'description': 'User account and management'}
    ],
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Login then Paste token with format: Bearer {token}'
        }
    },
    'security': [
        {
            'Bearer': []
        }
    ]
}

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    limiter.init_app(app)
    jwt.init_app(app)
    CORS(app, credentials=True)
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "The Shop API",
            "version": "0.0.1"
        },
        "host": os.getenv("API_HOST", "localhost:5001"),
        "basePath": "/api",
        "schemes": [os.getenv("API_SCHEME", "http")]
    }

    Swagger(app, template=swagger_template)

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

app = create_app()
celery_app = app.extensions["celery"]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
