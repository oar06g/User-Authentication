import os
from configparser import ConfigParser
from sqlalchemy import inspect
from src.models import Base
from src.config import Database


def run_alembic(cmd: str):
    os.system(f"alembic {cmd}")


def is_database_empty(engine) -> bool:
    inspector = inspect(engine)
    return len(inspector.get_table_names()) == 0


def migrate():
    """Run autogenerate + upgrade safely."""
    print("🔄 Running Alembic migration...")
    run_alembic('revision --autogenerate -m "auto changes"')
    run_alembic('upgrade head')


def setup(anyway: bool = False):
    """Full setup with smart DB checks."""
    path = os.path.join(os.path.dirname(__file__), '..', 'config.ini') 
    config = ConfigParser()
    config.read(path)

    first_time = config.getboolean('initialize', 'first_time', fallback=True)

    engine = Database.get_engine()
    db_empty = is_database_empty(engine)

    migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
    migrations_exist = os.path.exists(migrations_dir) and \
                       os.path.exists(os.path.join(migrations_dir, 'versions'))

    # First-time DB init
    if anyway or first_time or db_empty:
        print("📦 Initializing database...")
        Base.metadata.create_all(bind=engine)

        if not migrations_exist:
            print("📁 Initializing migrations folder...")
            run_alembic("init migrations")

        config.set('initialize', 'first_time', 'False')
        with open(path, 'w', encoding='utf-8') as f:
            config.write(f)

    else:
        if not migrations_exist:
            print("⚠️ No migrations folder found! Creating it...")
            run_alembic("init migrations")

        migrate()
