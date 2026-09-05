from langchain.tools import tool
from typing import Callable
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.db.models.project_embedding import ProjectEmbedding
from app.service.ingestion import embedding_model

class SearchInput(BaseModel):
    query: str = Field(default=None, description="The natural language query to search for")
    question: str = Field(default=None, description="The natural language query to search for (alias for query)")

def get_search_tool(db_getter: Callable, project_id: int):
    @tool("semantic_search", args_schema=SearchInput)
    def semantic_search(query: str = None, question: str = None) -> str:
        """
        Use this tool to search for semantic meaning, context, or fuzzy matching in the spreadsheet's text data.
        Input should be a search query.
        """
        actual_query = query or question
        if not actual_query:
            return "Error: Please provide a query or question."
            
        # Embed the query with a robust retry loop (network API may be flaky)
        import time
        import concurrent.futures
        query_embedding = None
        for attempt in range(5):
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(embedding_model.embed_query, actual_query)
                    query_embedding = future.result(timeout=15.0)
                break
            except concurrent.futures.TimeoutError:
                print(f"[InsightAI] HuggingFace API timeout on search attempt {attempt+1}, retrying...")
                time.sleep(2)
            except Exception as e:
                if attempt == 4:
                    return f"Error: Failed to generate query embedding after 5 attempts: {e}"
                print(f"[InsightAI] HuggingFace API network error on search, retrying... ({e})")
                time.sleep(2)
                
        if query_embedding is None:
            return "Error: Failed to generate query embedding due to persistent timeouts."
        
        # Retrieve the thread-local DB session at invocation time
        db = db_getter()
        
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
