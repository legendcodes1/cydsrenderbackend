from my_app import create_app, db
from flask_migrate import Migrate
from flask.cli import AppGroup
import click  # Importing click

app = create_app()
migrate = Migrate(app, db)

# Create a custom CLI group for migrations
migrate_cli = AppGroup('migrate')

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

app.cli.add_command(migrate_cli)

if __name__ == '__main__':
    app.run(debug=True)
