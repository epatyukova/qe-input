from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition

def define_model(model_name, tools: None):
    if tools:
        llm = ChatOpenAI(model=OPENAI_MODEL,temperature=0)
        return llm.bind_tools(tools)
    else:
        return ChatOpenAI(model=model_name,temperature=0)
    
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage

class State(MessagesState):
    summary: str
    generator_input: Dict

# System message
sys_msg = SystemMessage(content="You are a helpful assistant helping to generate input files for Quantum Espresso \
                                 for single point energy calculations. You need to call tools in appropriate order \
                                 to get all nessecary information for input file generation.")

# Node
def assistant(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}