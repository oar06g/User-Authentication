import os
from configparser import ConfigParser
from src.models import Base
from src.config import Database

path = os.path.join(os.path.dirname(__file__), 'config.ini')
config = ConfigParser()

# Create config.ini with default section if missing
if not os.path.exists(path):
    config['initialize'] = {'first_time': 'true'}
    with open(path, 'w') as f:
        config.write(f)

# Read config and ensure 'initialize' section exists
config.read(path)
if 'initialize' not in config:
    config['initialize'] = {'first_time': 'true'}

first_time = config.getboolean('initialize', 'first_time', fallback=True)

engine = Database.get_engine()

if first_time:
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Mark as initialized so we don't rebuild on next run
    config['initialize']['first_time'] = 'false'
    with open(path, 'w') as f:
        config.write(f)