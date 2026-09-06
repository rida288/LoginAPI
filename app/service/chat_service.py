import threading
from langchain_google_genai import ChatGoogleGenerativeAI
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
    (see app.core.service_cache).

    The LangGraph ReAct agent is compiled ONCE in __init__ and reused for
    every subsequent request. Per-request DB session safety is achieved via
    threading.local(): ask_question() sets self._local.db before invoking
    the agent, and the semantic_search tool reads self._local.db at call
    time rather than closing over a specific session object.
    """

    def __init__(self, project_id: int, file_path: str):
        self.project_id = project_id
        self.file_path = file_path

        # Thread-local storage for the per-request DB session.
        # Each worker thread that calls ask_question() writes its own session
        # here, so concurrent requests never share a session.
        self._local = threading.local()

        # Returns the DB session bound to the current worker thread.
        # Called by the search tool at invocation time, not at build time.
        def _get_db():
            return self._local.db

        # LLM client — reused across all requests for this project
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

        # math_tool contains an lru_cached dataframe download from S3 — only
        # happens on the very first request; subsequent calls hit memory.
        self.math_tool = get_math_tool(file_path=self.file_path)

        # search_tool is built with a db_getter callable, not a concrete session,
        # so it remains safe to reuse across threads.
        self.search_tool = get_search_tool(db_getter=_get_db, project_id=self.project_id)

        # Compile the ReAct agent graph ONCE. This is the expensive step that
        # was previously being re-run on every single request.
        print(f"[InsightAI] Compiling ReAct agent for project {project_id}...")
        self.agent = create_react_agent(
            model=self.llm,
            tools=[self.search_tool, self.math_tool],
            prompt=SYSTEM_PROMPT,
        )
        print(f"[InsightAI] Agent for project {project_id} ready.")

    def ask_question(self, question: str) -> str:
        """
        Answers a question using the pre-compiled ReAct agent.

        This method runs inside asyncio.to_thread (a worker thread).
        It creates its OWN database session and stores it in thread-local
        storage so the semantic_search tool can safely access it.
        """
        import time
        from app.core.database import SessionLocal

        # Create a fresh, thread-local DB session for this request and
        # expose it to the search tool via self._local.
        db = SessionLocal()
        self._local.db = db

        try:
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    response = self.agent.invoke({"messages": [("human", question)]})
                    raw = response["messages"][-1].content
                    # Gemini can return content as a list of parts (e.g. [{"type": "text", "text": "..."}])
                    # rather than a plain string. Flatten it so the frontend always gets a string.
                    if isinstance(raw, list):
                        return " ".join(
                            part.get("text", "") for part in raw
                            if isinstance(part, dict)
                        )
                    return raw
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
            self._local.db = None

