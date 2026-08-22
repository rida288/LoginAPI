from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from app.tools.search_tool import get_search_tool
from app.tools.math_tool import get_math_tool
from sqlalchemy.orm import Session

SYSTEM_PROMPT = (
    "You are an intelligent data assistant. "
    "You have access to a spreadsheet dataset. "
    "Use the 'math_and_data_engine' tool for questions requiring math, filtering, counting, or statistics. "
    "Use the 'semantic_search' tool for questions requiring contextual meaning or fuzzy text matching. "
    "If a question requires both, you can use both tools. "
    "Provide clear, concise, and helpful answers."
)

class ChatService:
    def __init__(self, db: Session, project_id: int, file_path: str):
        self.db = db
        self.project_id = project_id
        self.file_path = file_path

        # Initialize LLM - Swapped to openai/gpt-oss-20b for flawless tool calling (fixes JSON parsing errors)
        self.llm = ChatGroq(model_name="openai/gpt-oss-20b", temperature=0)

        # Initialize tools
        self.search_tool = get_search_tool(db=self.db, project_id=self.project_id)
        self.math_tool = get_math_tool(file_path=self.file_path)

        self.tools = [self.search_tool, self.math_tool]

        # create_react_agent is the stable API in LangChain/LangGraph 1.x
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
        )

    def ask_question(self, question: str) -> str:
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.agent.invoke({"messages": [("human", question)]})
                return response["messages"][-1].content
            except Exception as e:
                error_msg = str(e)
                # Handle rate limits
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt
                        print(f"[InsightAI] Rate limit hit for chat_service, retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                        continue
                
                # Handle malformed JSON from the LLM
                if "Failed to parse tool call" in error_msg or "JSON" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"[InsightAI] LLM hallucinated invalid JSON, retrying...")
                        time.sleep(1)
                        continue
                    return "The AI agent made a syntax error while trying to answer your question. Please try asking in a slightly different way."
                
                return f"An error occurred while processing your request: {error_msg}"
