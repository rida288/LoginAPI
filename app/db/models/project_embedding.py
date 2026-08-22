from sqlalchemy import Column, Integer, Text, ForeignKey, Index 
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class ProjectEmbedding(Base):
    __tablename__ = "project_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # Using 384 dimensions for all-MiniLM-L6-v2 embeddings
    embedding = Column(Vector(384))

    project = relationship("Project")

Index(
    'ix_project_embeddings_embedding_hnsw',
    ProjectEmbedding.embedding,
    postgresql_using='hnsw', #Hierarchical Navigable Small World index 
    postgresql_with={'m': 16, 'ef_construction': 64},
    postgresql_ops={'embedding': 'vector_cosine_ops'}
)
