from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.math_tool import get_math_tool
from app.tools.search_tool import get_search_tool

SYSTEM_PROMPT = (
    "You are an expert data analytics assistant capable of complex data analysis and statistical reasoning. "
    "You have access to a spreadsheet dataset. "
    "Use the 'math_and_data_engine' tool for complex data analytics tasks. This includes analyzing large datasets, "
    "computing statistics, grouping, filtering, cross-referencing columns, and running multi-step aggregations. "
    "Use the 'semantic_search' tool for questions requiring contextual meaning or fuzzy text matching. "
    "If a question requires both semantic understanding and data crunching, you can use both tools. "
    "Think step-by-step to break down complex queries. Provide clear, comprehensive, and accurate answers based on the data."
)


class ChatService:
    """
    Constructed once per project and cached at the application level
    (see app.core.service_cache). The DB session is NOT stored here —
    a fresh session is created inside ask_question() which runs in a
    thread pool, keeping session usage fully thread-safe.
    """

    def __init__(self, project_id: int, file_path: str):
        self.project_id = project_id
        self.file_path = file_path

        # LLM client — reused across all requests for this project
        self.llm = ChatGroq(model_name="openai/gpt-oss-120b", temperature=0)

        # math_tool contains an lru_cached dataframe download from S3 — only
        # happens on the very first request; subsequent calls hit memory.
        self.math_tool = get_math_tool(file_path=self.file_path)

    def ask_question(self, question: str) -> str:
        """
        Answers a question using the ReAct agent.

        This method runs inside asyncio.to_thread (a worker thread).
        It creates its OWN database session rather than accepting one as a
        parameter — SQLAlchemy sessions are not thread-safe and must not be
        shared across threads.
        """
        import time
        from app.core.database import SessionLocal

        # Create a fresh, thread-local DB session for this request
        db = SessionLocal()
        try:
            # Build a fresh search tool bound to this thread's session
            search_tool = get_search_tool(db=db, project_id=self.project_id)

            # Assemble the agent with both tools for this request
            agent = create_react_agent(
                model=self.llm,
                tools=[search_tool, self.math_tool],
                prompt=SYSTEM_PROMPT,
            )

            max_retries = 3

            for attempt in range(max_retries):
                try:
                    response = agent.invoke({"messages": [("human", question)]})
                    return response["messages"][-1].content
                except Exception as e:
                    error_msg = str(e)

                    # Handle rate limits with exponential backoff
                    if "429" in error_msg or "rate limit" in error_msg.lower():
                        if attempt < max_retries - 1:
                            sleep_time = 2 ** attempt
                            print(f"[InsightAI] Rate limit hit, retrying in {sleep_time}s...")
                            time.sleep(sleep_time)
                            continue

                    # Handle malformed JSON tool calls from the LLM
                    if "Failed to parse tool call" in error_msg or "JSON" in error_msg:
                        if attempt < max_retries - 1:
                            print(f"[InsightAI] LLM produced invalid JSON, retrying...")
                            time.sleep(1)
                            continue
                        return (
                            "The AI agent made a syntax error while trying to answer your question. "
                            "Please try asking in a slightly different way."
                        )

                    return f"An error occurred while processing your request: {error_msg}"

        finally:
            # Always close the thread-local session, even if an exception occurs
            db.close()
