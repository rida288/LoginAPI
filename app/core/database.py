from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:pwd@127.0.0.1:5433/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL) 

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() #create table w/class 

#allow to get an instance of a session to interact w/db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
 