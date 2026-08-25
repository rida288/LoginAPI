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
    # Explicitly ensure the HNSW vector index exists even on pre-existing tables.
    # Base.metadata.create_all skips tables that already exist, so the index
    # defined in the SQLAlchemy model may never have been created in production.
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_project_embeddings_embedding_hnsw
            ON project_embeddings
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))
        conn.commit()
    print("[InsightAI] Database tables and HNSW index verified.")