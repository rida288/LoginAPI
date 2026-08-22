from langchain.tools import tool
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.db.models.project_embedding import ProjectEmbedding
from app.service.ingestion import embedding_model

class SearchInput(BaseModel):
    question: str = Field(description="The natural language query to search for")

def get_search_tool(db: Session, project_id: int):
    @tool("semantic_search", args_schema=SearchInput)
    def semantic_search(question: str) -> str:
        """
        Use this tool to search for semantic meaning, context, or fuzzy matching in the spreadsheet's text data.
        Input should be a search query.
        """
        # Embed the query
        query_embedding = embedding_model.embed_query(question)
        
        # Query pgvector for the top 5 closest matches, filtered by project_id
        stmt = select(ProjectEmbedding).where(
            ProjectEmbedding.project_id == project_id
        ).order_by(
            ProjectEmbedding.embedding.cosine_distance(query_embedding)
        ).limit(5)
        
        results = db.execute(stmt).scalars().all()
        
        if not results:
            return "No relevant text data found for this query."
            
        # Combine the results into a string
        result_texts = []
        for res in results:
            result_texts.append(f"Row {res.row_index}: {res.content}")
            
        return "\n".join(result_texts)
        
    return semantic_search
