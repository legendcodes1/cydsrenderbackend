from app.__init__ import create_app, db
from flask_migrate import Migrate
from flask.cli import AppGroup
import click  # Importing click

# Initialize the app and migrate instance
app = create_app()
migrate = Migrate(app, db)

# Create a custom CLI group for migrations
@app.cli.group('migrate')  # You can use a built-in Flask CLI decorator for simplicity
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
