from app.core.database import Base, engine 
from app.db.models.user import User 
from app.db.models.token import TokenBlacklist
from app.db.models.project import Project 
from app.db.models.project_embedding import ProjectEmbedding 
from sqlalchemy import text

def create_tables():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)