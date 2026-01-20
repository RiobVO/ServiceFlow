from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

connect_args = {}
if settings.db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.db_url, echo=False, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
