from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from app.tools.search_tool import get_search_tool
from app.tools.math_tool import get_math_tool
from sqlalchemy.orm import Session

class ChatService:
    def __init__(self, db: Session, project_id: int, file_path: str):
        self.db = db
        self.project_id = project_id
        self.file_path = file_path
        
        # Initialize LLM for orchestrator
        self.llm = ChatGroq(model_name="llama3-70b-8192", temperature=0)
        
        # Initialize tools
        self.search_tool = get_search_tool(db=self.db, project_id=self.project_id)
        self.math_tool = get_math_tool(file_path=self.file_path)
        
        self.tools = [self.search_tool, self.math_tool]
        
        # Define prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent data assistant. "
                       "You have access to a spreadsheet dataset. "
                       "Use the 'math_and_data_engine' tool for questions requiring math, filtering, counting, or statistics. "
                       "Use the 'semantic_search' tool for questions requiring contextual meaning or fuzzy text matching. "
                       "If a question requires both, you can use both tools. "
                       "Provide clear, concise, and helpful answers."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        # Create agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def ask_question(self, question: str) -> str:
        try:
            response = self.agent_executor.invoke({"input": question})
            return response["output"]
        except Exception as e:
            return f"An error occurred while processing your request: {str(e)}"
