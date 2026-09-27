from app.core.database import Base, engine 
from app.db.models.user import User 
from app.db.models.token import TokenBlacklist
from app.db.models.project import Project 
from app.db.models.project_embedding import ProjectEmbedding 
from sqlalchemy import text

import time

def create_tables():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            Base.metadata.create_all(bind=engine)
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_project_embeddings_embedding_hnsw
                    ON project_embeddings
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """))
                conn.commit()
            print("[InsightAI] Database tables and HNSW index verified.")
            return
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[InsightAI] Database initialization failed after {max_retries} attempts: {e}")
                raise e
            print(f"[InsightAI] Database connection attempt {attempt + 1} failed ({e}), retrying in 2s...")
            time.sleep(2)