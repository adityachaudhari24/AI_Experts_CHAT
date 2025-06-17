import streamlit as st
import requests
import uuid
from typing import Dict

st.set_page_config(
    page_title="AI Experts Chat",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

API_BASE_URL = "http://fastapi:8000"

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid1())

def initialize_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = generate_session_id()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'is_loading' not in st.session_state:
        st.session_state.is_loading = False

def call_chat_api(query: str, session_id: str) -> str:
    """Call the /chat API endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "query": query,
                "sessionID": session_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response received")
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"Connection error: {str(e)}"

def display_message(message: Dict[str, str]):
    """Display a single message in the chat"""
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def main():
    initialize_session_state()
    st.title("🤖 AI Experts Chat")
    st.text("your session ID: " + st.session_state.session_id)
    
    # Sidebar with session info and controls
    with st.sidebar:
        st.header("Session Info")
        st.code(f"ID: {st.session_state.session_id[:8]}...")
        
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = generate_session_id()
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        server_status = "🟢 Online" if check_server_status() else "🔴 Offline"
        st.write(f"**Server:** {server_status}")
        st.write(f"**Messages:** {len(st.session_state.messages)}")
    
    # Display chat messages
    for message in st.session_state.messages:
        display_message(message)
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = call_chat_api(prompt, st.session_state.session_id)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def check_server_status() -> bool:
    """Check if the backend server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    main()