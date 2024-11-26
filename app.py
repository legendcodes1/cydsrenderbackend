import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Import CORS
from flask_migrate import Migrate
import click  # Importing click
from dotenv import load_dotenv  # Import load_dotenv
from waitress import serve  # Importing waitress

# Load environment variables from .env file (for local development only)
load_dotenv()

# Initialize the database and migration
db = SQLAlchemy()
migrate = Migrate()

# Create the Flask app and configure it
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

    # Initialize the app with the database and migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Enable CORS for your frontend origin
    CORS(app, resources={r"/*": {"origins": [
        "http://localhost:5173",  # Local development
        "https://cydswebsite-epw5cljul-faruqs-projects-89c90b8f.vercel.app"  # Your Vercel frontend URL
    ], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type"]}})

    # Register routes and blueprints
    with app.app_context():
        from app.routes import main  # Assuming routes.py is inside app folder
        app.register_blueprint(main)  # Register the main blueprint

    # CLI commands for migrations
    @app.cli.group('migrate')
    def migrate_cli():
        """Migrate commands group.""" 
        pass

    @migrate_cli.command('init')
    def init_command():
        """Initialize migration repository.""" 
        from flask_migrate import init
        init()

    @migrate_cli.command('migrate')
    @click.option('-m', '--message', help='Message for the migration')
    def migrate_command(message):
        """Create a new migration.""" 
        from flask_migrate import migrate
        migrate(message=message)

    @migrate_cli.command('upgrade')
    def upgrade_command():
        """Apply the latest migration.""" 
        from flask_migrate import upgrade
        upgrade()

    return app

# Create the app instance
app = create_app()

# Start the app using Waitress if this script is executed directly
if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=5000)
