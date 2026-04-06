"""Database connection and session management."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator, Optional
from app.config import config


class DatabaseManager:
    """Manages database connections."""
    
    def __init__(self):
        """Initialize database connection."""
        if not config.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL must be set in environment variables or .env file. "
                "Please create a .env file with DATABASE_URL=postgresql://user:password@host:port/dbname"
            )
        
        self.engine = create_engine(
            config.DATABASE_URL,
            poolclass=NullPool,
            echo=False
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session context manager."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(self, sql: str) -> list[dict]:
        """Execute a SQL query and return results as list of dicts."""
        with self.get_session() as session:
            result = session.execute(text(sql))
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]


# Lazy initialization - only create when first accessed
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create the database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# For backward compatibility, but will raise error if DATABASE_URL not set
try:
    db_manager = get_db_manager()
except ValueError:
    # Don't fail at import time, fail when actually used
    db_manager = None

