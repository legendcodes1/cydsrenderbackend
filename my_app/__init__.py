from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Import CORS
from .config import Config
import os
from dotenv import load_dotenv  # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Set the secret key from environment variables or fallback for development
    app.secret_key = os.getenv('SECRET_KEY', 'fallback-dev-secret-key')  # Use a secure key in production

    # Use DATABASE_URL from environment variables for SQLAlchemy connection
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'sslmode': 'require'  # Include SSL mode if necessary
        }
    }

    db.init_app(app)

    # Enable CORS for your frontend origin
    CORS(app, resources={r"/*": {
    "origins": "http://localhost:5173",  # Update this with your frontend's URL if different
    "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Add PATCH method here
    "allow_headers": ["Content-Type"]
}})

    with app.app_context():
        from . import routes  # Import routes module
        from .routes import main  # Import the main blueprint
        app.register_blueprint(main)  # Register the main blueprint
        db.create_all()  # Create database tables if necessary
    
    return app
