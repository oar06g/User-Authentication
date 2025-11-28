from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from typing import Generator

from src.settings import DB_URL

class Database:
    _engine = None
    _session_factory = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls._engine = create_engine(
                DB_URL,
                pool_pre_ping=True,
                pool_recycle=280,
                echo=True
            )
        return cls._engine
    @classmethod
    def get_session_factory(cls):
        if cls._session_factory is None:
            engine = cls.get_engine()
            cls._session_factory = scoped_session(
                sessionmaker(
                    bind=engine,
                    autoflush=False,
                    autocommit=False,
                    expire_on_commit=False
                )
            )
        return cls._session_factory

def get_db() -> Generator[Session, None, None]:
    session = Database.get_session_factory()()
    try:
        yield session
    finally:
        session.close()