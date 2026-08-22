import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.project_embedding import ProjectEmbedding
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
import os

# Initialize the embedding model via API to save server memory
embedding_model = HuggingFaceInferenceAPIEmbeddings(
    api_key=os.environ.get("HUGGINGFACEHUB_API_TOKEN", ""),
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def extract_text_content(self, row: pd.Series) -> str:
        """
        Combine all textual information in a row into a single searchable string.
        """
        parts = []
        for col, val in row.items():
            if pd.notna(val) and isinstance(val, (str, int, float)):
                parts.append(f"{col}: {val}")
        return " | ".join(parts)

    def process_and_embed_project_data(self, project_id: int, file_path: str, batch_size: int = 100):
        """
        Reads a spreadsheet, extracts text, generates embeddings in batches,
        and saves them to the pgvector database.
        """
        from app.core.storage.s3_client import S3Client
        import io
        
        # Get file stream from B2
        s3_client = S3Client()
        file_stream = s3_client.get_file_stream(file_path)
        file_buffer = io.BytesIO(file_stream.read())
        
        # Determine file type and read
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_buffer)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_buffer)
        else:
            raise ValueError("Unsupported file format for ingestion")
        
        # Clean dataframe
        df = df.dropna(how='all')
        
        texts_to_embed = []
        row_indices = []
        
        # Iterate over dataframe
        for idx, row in df.iterrows():
            content = self.extract_text_content(row)
            if content.strip():
                texts_to_embed.append(content)
                row_indices.append(idx)
        
        # Process in batches for optimized performance
        total_rows = len(texts_to_embed)
        for i in range(0, total_rows, batch_size):
            batch_texts = texts_to_embed[i:i + batch_size]
            batch_indices = row_indices[i:i + batch_size]
            
            # Generate embeddings for the batch
            embeddings = embedding_model.embed_documents(batch_texts)
            
            # Create ProjectEmbedding objects
            db_embeddings = []
            for j in range(len(batch_texts)):
                db_emb = ProjectEmbedding(
                    project_id=project_id,
                    row_index=batch_indices[j],
                    content=batch_texts[j],
                    embedding=embeddings[j]
                )
                db_embeddings.append(db_emb)
            
            # Bulk save to DB for efficiency
            self.db.bulk_save_objects(db_embeddings)
            self.db.commit()
            
        return total_rows
