from langchain.tools import tool
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_groq import ChatGroq
import pandas as pd

def get_math_tool(file_path: str):
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
        raise ValueError("Unsupported file format")

    # Initialize a specific LLM for the Pandas agent (Llama 3 is excellent for code generation)
    llm = ChatGroq(model_name="llama3-70b-8192", temperature=0)
    
    # Create the pandas agent
    pandas_agent = create_pandas_dataframe_agent(
        llm, 
        df, 
        verbose=True, 
        allow_dangerous_code=True,
        agent_type="tool-calling"
    )

    @tool("math_and_data_engine")
    def math_and_data_engine(query: str) -> str:
        """
        Use this tool when the question requires math, aggregations, counting, sorting, or exact column filtering on the dataset.
        Input should be a detailed natural language question about the data.
        """
        try:
            response = pandas_agent.invoke({"input": query})
            return response["output"]
        except Exception as e:
            return f"Error executing data analysis: {str(e)}"

    return math_and_data_engine
