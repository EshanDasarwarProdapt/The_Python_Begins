"""
Database setup for the Smart Task Manager.

Single responsibility of this file: create the SQLAlchemy "engine"
(the thing that actually talks to the SQLite file), the "SessionLocal"
factory (used to create a new database session per request), and the
declarative `Base` class that our models inherit from.

It also defines `get_db()`, a small generator function used as a
FastAPI dependency. This is the standard "Dependency Injection"
pattern in FastAPI:
    - Each request gets its OWN database session.
    - The session is guaranteed to be closed afterwards (even if the
      request raises an error), because of the `finally` block.
    - Routes never create sessions themselves - they just declare
      `db: Session = Depends(get_db)` and FastAPI wires it up for them.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file, stored next to the `app` folder as `tasks.db`.
# The three slashes + relative path means "relative to where the app
# is run from" -- for this teaching project that's simple and enough.
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

# `connect_args` is only needed for SQLite: by default SQLite only
# allows one thread to talk to a connection, but FastAPI can use
# multiple threads to serve requests, so we relax that restriction.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal is a *factory* for database sessions. Every time we call
# SessionLocal() we get a brand new session/transaction to work with.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class that all our ORM models (see models.py)
# inherit from. SQLAlchemy uses it to keep track of every table we
# define.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session for a single
    request, and always closes it afterwards.

    Usage in a route:
        @router.get("/tasks")
        def list_tasks(db: Session = Depends(get_db)):
            ...

    Why a generator with `yield` instead of just `return`ing a session?
    FastAPI treats this special "yield dependency" as having two parts:
    everything BEFORE the `yield` runs before the request is handled,
    and everything AFTER the `yield` (here, closing the session) runs
    after the response has been sent - even if the route raised an
    exception. This guarantees we never leak open database connections.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
