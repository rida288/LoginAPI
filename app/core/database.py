import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:pwd@127.0.0.1:5432/postgres"  # local fallback for dev
)

if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://") and not SQLALCHEMY_DATABASE_URL.startswith("postgresql+"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {"connect_timeout": 10}
if "127.0.0.1" not in SQLALCHEMY_DATABASE_URL and "localhost" not in SQLALCHEMY_DATABASE_URL:
    connect_args["sslmode"] = os.getenv("DB_SSL_MODE", "require")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,           # number of persistent connections
    max_overflow=10,       # extra connections allowed under burst load
    pool_pre_ping=True,    # test connection health before each use
    pool_recycle=300,      # recycle connections every 5 min (avoids stale conn errors)
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()