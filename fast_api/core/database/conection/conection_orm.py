from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fast_api.core.config.configapi import settings

DATABASE_URI = f'{settings.POSTGRES_PREFIX}://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}'

engine = create_engine(DATABASE_URI)

Session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = Session_local()

    try:
        yield db
    finally:
        db.close()