from functools import lru_cache
import io
from langchain.tools import tool
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np


class PythonCodeInput(BaseModel):
    code: str = Field(
        description=(
            "Valid Python code/expression to execute on the pandas DataFrame `df`. "
            "Examples: `df['Net Sales'].mean()`, `df.groupby('Gender')['Net Sales'].sum()`, "
            "or `df['Type of Customer'].value_counts()`. Always reference the DataFrame as `df`."
        )
    )


@lru_cache(maxsize=1)
def _load_dataframe(file_path: str) -> pd.DataFrame:
    from app.core.storage.s3_client import S3Client

    print(f"[InsightAI] Downloading {file_path} from S3 and caching in memory...")

    s3_client = S3Client()
    file_stream = s3_client.get_file_stream(file_path)
    file_buffer = io.BytesIO(file_stream.read())

    if file_path.endswith(".csv"):
        return pd.read_csv(file_buffer)
    elif file_path.endswith(".xlsx"):
        return pd.read_excel(file_buffer)
    else:
        raise ValueError("Unsupported file format")


def get_dataframe_schema(file_path: str) -> str:
    """Generates a text summary of the DataFrame schema for the LLM system prompt."""
    df = _load_dataframe(file_path)
    cols_info = [f"  - '{col}' ({dtype})" for col, dtype in df.dtypes.items()]
    head_sample = df.head(2).to_string(index=False)

    schema_summary = (
        f"Dataset Overview:\n"
        f"- Total Rows: {len(df)}, Total Columns: {len(df.columns)}\n"
        f"- Column Names & Types:\n" + "\n".join(cols_info) + "\n\n"
        f"- Sample Rows:\n{head_sample}"
    )
    return schema_summary


def get_math_tool(file_path: str):
    df = _load_dataframe(file_path)

    @tool("execute_pandas_code", args_schema=PythonCodeInput)
    def execute_pandas_code(code: str) -> str:
        """
        Executes Python code/expressions directly on the loaded dataset pandas DataFrame `df`.
        Use this tool for math calculations, aggregations, counts, sums, averages, grouping,
        filtering, sorting, and statistical analysis.
        Input must be valid Python code operating on `df`.
        """
        if not code or not code.strip():
            return "Error: No python code provided."

        clean_code = code.strip()
        # Clean up markdown code blocks if the LLM wrapped it in ```python
        if clean_code.startswith("```"):
            lines = clean_code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_code = "\n".join(lines).strip()

        try:
            local_vars = {"df": df, "pd": pd, "np": np}

            # Try evaluating as a single expression first (e.g. df['Net Sales'].mean())
            try:
                result = eval(clean_code, {"__builtins__": __builtins__}, local_vars)
            except SyntaxError:
                # If it's a multiline statement, exec it
                exec(clean_code, {"__builtins__": __builtins__}, local_vars)
                result = local_vars.get("result", "Code executed successfully.")

            if isinstance(result, (pd.DataFrame, pd.Series)):
                return result.to_string()
            return str(result)

        except Exception as e:
            return f"Python Execution Error: {type(e).__name__}: {str(e)}"

    return execute_pandas_code
