import streamlit as st

with st.chat_message("user"):
    st.write("Hello 👋")
    
    prompt = st.chat_input("What is your name?")
if prompt:
    with st.chat_message("assistant"):
        st.write(f"Hello {prompt}, how can I help you today?")
    st.write("This is a simple chat app using Streamlit.")