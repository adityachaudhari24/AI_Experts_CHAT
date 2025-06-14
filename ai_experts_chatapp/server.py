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

# System prompt configuration
DEFAULT_SYSTEM_PROMPT = """You are an AI expert assistant. You are knowledgeable, helpful, and professional. 
Provide clear, accurate, and detailed responses. If you're unsure about something, say so rather than guessing.
Always strive to be helpful while being honest about your limitations."""

CUSTOM_SYSTEM_PROMPT = """You are an AI expert assistant. You are knowledgeable, helpful, and professional. 
Provide clear, accurate, and detailed responses. If you're unsure about something, say so rather than guessing.
Always strive to be helpful while being honest about your limitations. 

You greet people on their input and encourage them to ask questions related to AI and machine learning.

You provide answers if the question asked is related to the topic of AI and machine learning.

You provide the reference to the source of your information always.
You are not allowed to answer questions that are not related to AI and machine learning.

"""



def get_system_message(custom_prompt: str = None) -> SystemMessage:
    """Get system message with custom or default prompt"""
    prompt = custom_prompt if custom_prompt else DEFAULT_SYSTEM_PROMPT
    return SystemMessage(content=prompt)


# Define the function that calls the model
def call_model(state: MessagesState):
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    
    # Add system prompt if not already present
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        system_message = get_system_message(CUSTOM_SYSTEM_PROMPT)
        messages = [system_message] + messages
    
    
    response = model.invoke(messages)
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
    system_prompt: Optional[str] = None

@app.post('/chat')
async def chat(request: ChatRequest):
    try:
        # Create dynamic config with sessionID as thread_id
        dynamic_config = {"configurable": {"thread_id": request.sessionID}}
        
        # Prepare input messages with optional system prompt
        input_messages = []
        if request.system_prompt:
            input_messages.append(get_system_message(request.system_prompt))
        input_messages.append(HumanMessage(request.query))
        
        output = workflowApp.invoke({"messages": input_messages}, dynamic_config)
        # Get the last message which is the AI response
        ai_message = output["messages"][-1]
        return {"response": ai_message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


