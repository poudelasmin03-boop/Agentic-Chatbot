 ####   Note + code

#Load all the required library
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_tavily import TavilySearch
from langchain.messages import HumanMessage,AIMessage,SystemMessage
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from typing import TypedDict,Annotated
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.tools import tool

### Datahase sqllite

import sqlite3

load_dotenv()




search_tool = TavilySearch(
  max_results = 4
)

## Chat groq  model
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.3
)


class State(TypedDict):
  messages: Annotated[list,add_messages]



### give memory in  fro chat bot
## check point 3 start middle end
conn = sqlite3.connect(database="Chatbot.db",check_same_thread=False)

memory  = SqliteSaver(conn)

print("Successfully databases is created...")


tools = [search_tool]

llm_with_tools = llm.bind_tools(tools)




def tool_calling_llm(state:State):
  """Provide  the current information  to user"""
  result = llm_with_tools.invoke(state["messages"])
  return{
    "messages":[result]
  }



## custom tool
@tool
def add(a:int,b:int)->int:
  """Add 2 number and return an answer of it.."""
  return a+b






graph = StateGraph(State)

graph.add_node("tool_calling_llm",tool_calling_llm)
graph.add_node("tools",ToolNode(tools))


graph.add_edge(START,"tool_calling_llm")
graph.add_conditional_edges(
  "tool_calling_llm",
  tools_condition
)
graph.add_edge("tools","tool_calling_llm")



#### Here we used memory->
graph_app = graph.compile(checkpointer=memory)

print("<--Enter 1 for exists--->")





#####  Chat  Threading->Like a previous chat history like other chatgpt 



import uuid

def generate_threat_id():
   print(uuid.uuid4())
   return str(uuid.uuid4())



def  ask_question_to_bot(question:str,thread_id:str):
      # question = input("You: ")
      # if question == "1":
      #       print("Exists....")
      #       break

     
      
      config={
      "configurable":{
            "thread_id":thread_id
      }
       }
         
      
      ### Streaming
      
      ### Streaming means models start the sending token words as soon as they generated instead of waiting for the entire response .
      
      ##   Mimics human like conversation (builds trust feels alive)

      ##  Here stream 

      for event in graph_app.stream(
          {
              "messages":[
                  ("user",question)
              ]
          },
          config=config,
          stream_mode="messages"
      ):
        message,metadata = event

        if isinstance(message,AIMessage) and message.content:
            yield message.content



