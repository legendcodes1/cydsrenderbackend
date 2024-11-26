from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Import CORS
from app.config import Config
import os
from dotenv import load_dotenv  # Import load_dotenv


# Load environment variables from .env file (for local development only)
load_dotenv()

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

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
    CORS(app, resources={r"/*": {"origins": [
        "http://localhost:5173",  # Local development
        "https://cydswebsite-epw5cljul-faruqs-projects-89c90b8f.vercel.app"  # Your Vercel frontend URL
    ], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type"]}})

    # Register routes and blueprints
    with app.app_context():
        from .routes import main  # Corrected import to routes.py
        app.register_blueprint(main)  # Register the main blueprint
    
    return app