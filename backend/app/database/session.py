from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
from app.database.mongodb import is_mongo_enabled, init_mongo_db

Base = declarative_base()

if not is_mongo_enabled():
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

def get_db():
    if is_mongo_enabled():
        yield None
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

def init_db():
    if is_mongo_enabled():
        init_mongo_db()
    else:
        from app.models.inspection import Inspection  # noqa: F401
        Base.metadata.create_all(bind=engine)
