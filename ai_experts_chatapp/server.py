from fastapi import FastAPI, Query, HTTPException
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

# Load environment variables
load_dotenv()

# Validate OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

app = FastAPI()

# function to create a workflow for a specific request 
def createWorkflow(query: str):
    # Define a new graph
    workflow = StateGraph(state_schema=MessagesState)
    
    # Define the (single) node in the graph
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    _systemMessage = SystemMessage(content="You are a helpful AI assistant. You provide clear, concise, and accurate responses. Always maintain a professional and friendly tone. You only provide answers if asked about the AI and AI technology for rest of the things you pass that with polite tone saynig you are not trainied to provide other answers then the AI")
    response =model.invoke([_systemMessage, HumanMessage(content=query)])
    return response


@app.get('/')
def root():
    return {"status": 'Server is up and running'}

@app.post('/chat')
async def chat(query: str = Query(..., description="Chat Message")):
    try:
        
        model = init_chat_model("gpt-4o-mini", model_provider="openai")
        _systemMessage = SystemMessage(content="You are a helpful AI assistant. You provide clear, concise, and accurate responses. Always maintain a professional and friendly tone. You only provide answers if asked about the AI and AI technology for rest of the things you pass that with polite tone saynig you are not trainied to provide other answers then the AI")
        
        response =model.invoke([_systemMessage, HumanMessage(content=query)])
        return response
        

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


