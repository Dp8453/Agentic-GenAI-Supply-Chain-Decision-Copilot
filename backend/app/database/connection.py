from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

db_url = settings.get_database_url()

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"connect_timeout": 1},
    echo=False
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


_db_active = None

def get_db():
    """
    Dependency generator for FastAPI routes to yield database sessions with instant offline fallback.
    """
    global _db_active
    if _db_active is False:
        yield None
        return

    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        _db_active = True
        yield db
    except Exception as e:
        _db_active = False
        logger.warning(f"Database connection unavailable, falling back to offline mode: {e}")
        yield None
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass




def check_db_connection() -> bool:
    """
    Helper function to check database connectivity. Returns True if DB is reachable.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False
