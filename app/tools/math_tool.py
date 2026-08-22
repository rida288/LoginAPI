from langchain.tools import tool
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
import pandas as pd

class ToolInput(BaseModel):
    query: str = Field(default=None, description="The natural language question or search query")
    question: str = Field(default=None, description="The natural language question or search query (alias for query)")

from functools import lru_cache
import time

@lru_cache(maxsize=1)
def _load_dataframe(file_path: str) -> pd.DataFrame:
    from app.core.storage.s3_client import S3Client
    import io
    print(f"[InsightAI] Downloading {file_path} from S3 and caching in memory...")
    
    # Get file stream from B2
    s3_client = S3Client()
    file_stream = s3_client.get_file_stream(file_path)
    file_buffer = io.BytesIO(file_stream.read())
    
    # Determine file type and read
    if file_path.endswith('.csv'):
        return pd.read_csv(file_buffer)
    elif file_path.endswith('.xlsx'):
        return pd.read_excel(file_buffer)
    else:
        raise ValueError("Unsupported file format")

def get_math_tool(file_path: str):
    df = _load_dataframe(file_path)

    # Initialize a specific LLM for the Pandas agent
    llm = ChatGroq(model_name="openai/gpt-oss-120b", temperature=0)
    
    # Create the pandas agent
    pandas_agent = create_pandas_dataframe_agent(
        llm, 
        df, 
        verbose=True, 
        allow_dangerous_code=True,
        agent_type="tool-calling",
        number_of_head_rows=1,
        max_iterations=3,
        max_execution_time=10
    )

    @tool("math_and_data_engine", args_schema=ToolInput)
    def math_and_data_engine(query: str = None, question: str = None) -> str:
        """
        Use this tool when the question requires math, aggregations, counting, sorting, or exact column filtering on the dataset.
        Input should be a detailed natural language question about the data.
        """
        actual_query = query or question
        if not actual_query:
            return "Error: Please provide a query or question."
            
        # Implement exponential backoff for the agent invocation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = pandas_agent.invoke({"input": actual_query})
                return response["output"]
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt
                        print(f"[InsightAI] Rate limit hit for math_tool, retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                        continue
                return f"Error executing data analysis: {error_msg}"

    return math_and_data_engine
