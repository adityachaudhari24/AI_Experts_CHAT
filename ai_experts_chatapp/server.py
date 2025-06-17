from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver
import traceback
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Validate OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")


# DB URL if you move all to DevContainers then change below to "mongodb://admin:admin@mongodb:27017"
DB_URI = "mongodb://admin:admin@localhost:27017"

# function to create a workflow
def createWorkflow():
    # Define a new graph
    workflow = StateGraph(state_schema=MessagesState)
    
    # Define the (single) node in the graph
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    #workflow compilation will be done later with a checkpointer in async context manager
    return workflow


# FastAPI initialization with lifespan for mongoDB connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    with MongoDBSaver.from_conn_string(DB_URI) as mongo_checkpointer:
        # Store the workflow in app state
        workflow = createWorkflow()
        app.state.workflow = workflow.compile(checkpointer=mongo_checkpointer)
        yield

app = FastAPI(lifespan=lifespan)

# Add memory to the graph
#memory = MemorySaver()


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
        
        output = app.state.workflow.invoke({"messages": input_messages}, dynamic_config)
        
        # for event in app.state.workflow.stream({"messages": input_messages}, dynamic_config, stream_mode="values"):
        #     if "messages" in event:
        #         event["messages"][-1].pretty_print()
        
        # Get the last message which is the AI response
        ai_message = output["messages"][-1]
        print(f"AI Response: {ai_message.content} and request id is {request.sessionID}")  # Debugging output
        return {"response": ai_message.content}

    except Exception as e:
        error_stack = traceback.format_exc()  # Capture the full stack trace
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\nStack Trace:\n{error_stack}")


