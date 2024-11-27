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

    # Connection pooling settings through SQLAlchemy engine options
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,    # Number of connections to keep in the pool
        'max_overflow': 20,  # Allow extra connections beyond pool_size
        'pool_timeout': 30,  # Timeout in seconds to wait for a connection from the pool
        'pool_recycle': 3600,  # Recycle connections after 3600 seconds (1 hour)
        # SSL mode disabled by removing 'connect_args'
    }

    db.init_app(app)

    # Enable CORS for your frontend origin
    CORS(app, resources={r"/*": {
        "origins": ["http://localhost:5173", "https://cydsfinalfrontend.vercel.app"],  # List of allowed origins
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }})

    with app.app_context():
        from . import routes  # Import routes module
        from .routes import main  # Import the main blueprint
        app.register_blueprint(main)  # Register the main blueprint
        db.create_all()  # Create database tables if necessary
    
    return app
