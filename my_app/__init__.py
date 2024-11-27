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
  # Corrected CORS configuration
    CORS(app, resources={r"/*": {
        "origins": ["http://localhost:5173", "https://cydsfinalfrontend.vercel.app"],  # List of allowed origins
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }})

    with app.app_context():
        from . import routes  # Import routes module
        from .routes import main  # Import the main blueprint
        app.register_blueprint(main)  # Register the main blueprint
        db.create_all()  # Create database tables if necessary
    
    return app
