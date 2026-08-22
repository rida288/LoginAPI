from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from app.util.groq_model import get_best_groq_model
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

        # Initialize LLM
        self.llm = ChatGroq(model_name=get_best_groq_model(), temperature=0)

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
        try:
            response = self.agent.invoke({"messages": [("human", question)]})
            # Last message in the response is the final AI answer
            return response["messages"][-1].content
        except Exception as e:
            return f"An error occurred while processing your request: {str(e)}"
