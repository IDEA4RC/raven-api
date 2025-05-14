"""
Script to initialize the database
"""

from app.db.session import engine
from app.models.base import Base


def init_db() -> None:
    """
    Initializes the database by creating all tables defined in the models.
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database successfully initialized!")
