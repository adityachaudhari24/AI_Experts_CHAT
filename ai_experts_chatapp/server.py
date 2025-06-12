from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()

# Add memory to the graph
memory = MemorySaver()

# Validate OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = {"configurable": {"thread_id": "abc123"}}


# Define the function that calls the model
def call_model(state: MessagesState):
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    response = model.invoke(state["messages"])
    return {"messages": response}
    
# function to create a workflow for a specific request 
def createWorkflow():
    # Define a new graph
    workflow = StateGraph(state_schema=MessagesState)
    
    # Define the (single) node in the graph
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    workflowApp = workflow.compile(checkpointer=memory)
    
    return workflowApp
    

# Initialize the workflow
workflowApp = createWorkflow()

@app.get('/')
def root():
    return {"status": 'Server is up and running'}

# Define request body model
class ChatRequest(BaseModel):
    query: str
    sessionID: str

@app.post('/chat')
async def chat(request: ChatRequest):
    try:
        # Create dynamic config with sessionID as thread_id
        dynamic_config = {"configurable": {"thread_id": request.sessionID}}
        input_messages = [HumanMessage(request.query)]
        output = workflowApp.invoke({"messages": input_messages}, dynamic_config)
        # Get the last message which is the AI response
        ai_message = output["messages"][-1]
        #print(ai_message)
        return {"response": ai_message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


