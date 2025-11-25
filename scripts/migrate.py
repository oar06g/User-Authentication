import os
from configparser import ConfigParser

def migrate():
    path = os.path.join(os.path.dirname(__file__), '..', 'config.ini') 
    config = ConfigParser()
    config.read(path)
    first_time = config.getboolean('initialize', 'first_time')
    if first_time:
        init = 'alembic init migrations'
        os.system(init)
        config.set('initialize', 'first_time', 'false')
        with open(path, 'w') as configfile: config.write(configfile)
        upgrade = 'alembic upgrade head'
        os.system(upgrade)
    else:
        init = 'alembic revision --autogenerate -m "done changes"'
        os.system(init)
        upgrade = 'alembic upgrade head'
        os.system(upgrade)