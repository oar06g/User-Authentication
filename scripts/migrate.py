import os
from configparser import ConfigParser
from src.models import Base
from src.config import Database

def migrate():
    """Run alembic migration"""
    os.system('alembic revision --autogenerate -m "done changes"')
    os.system('alembic upgrade head')


def setup(anyway: bool = False):
    """Setup database and migrations"""
    path = os.path.join(os.path.dirname(__file__), '..', 'config.ini') 
    config = ConfigParser()
    config.read(path)

    first_time = config.getboolean('initialize', 'first_time', fallback=True)

    engine = Database.get_engine()

    if anyway or first_time:
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Initialize migrations if folder not exists
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
        if not os.path.exists(migrations_dir):
            os.system('alembic init migrations')

        # Update config
        if not config.has_section('initialize'):
            config.add_section('initialize')
        config.set('initialize', 'first_time', 'False')
        with open(path, 'w', encoding='utf-8') as f:
            config.write(f)
    else:
        migrate()
