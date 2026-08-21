import streamlit as st
import uuid
import os
import tempfile
from database import create_session, get_all_sessions, get_messages, add_message, update_session_title
from rag_engine import process_and_index_pdf, answer_query

st.set_page_config(page_title="RAG Chatbot", layout="wide")

st.title("AI RAG Chatbot")

# --- Sidebar: Config & Session Management ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.warning("Please enter your OpenAI API Key to continue.")
        st.stop()
        
    st.header("Document Upload")
    uploaded_file = st.file_uploader("Upload a PDF document for RAG", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Process & Index PDF"):
            with st.spinner("Processing PDF..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                process_and_index_pdf(tmp_path, api_key)
                os.remove(tmp_path)
            st.success("PDF processed and indexed successfully!")

# --- Main Layout ---
chat_col, history_col = st.columns([3, 1])

with history_col:
    st.header("Chat History")
    if st.button("➕ New Chat"):
        new_id = str(uuid.uuid4())
        create_session(new_id, "New Chat")
        st.session_state["current_session_id"] = new_id
        st.rerun()

    sessions = get_all_sessions()
    if not sessions:
        # Create a default session
        default_id = str(uuid.uuid4())
        create_session(default_id, "New Chat")
        st.session_state["current_session_id"] = default_id
        st.rerun()

    # Session selector
    session_options = {s["id"]: s["title"] for s in sessions}
    
    # Check if current_session_id is in state, else pick first
    if "current_session_id" not in st.session_state or st.session_state["current_session_id"] not in session_options:
        st.session_state["current_session_id"] = sessions[0]["id"]
        
    for session_id_opt, title in session_options.items():
        # Highlight the current session
        is_current = session_id_opt == st.session_state["current_session_id"]
        button_type = "primary" if is_current else "secondary"
        if st.button(title, key=f"btn_{session_id_opt}", use_container_width=True, type=button_type):
            st.session_state["current_session_id"] = session_id_opt
            st.rerun()

with chat_col:
    # --- Main Chat Interface ---
    session_id = st.session_state["current_session_id"]
    messages = get_messages(session_id)
    
    # Display chat messages from history on app rerun
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # React to user input
    if prompt := st.chat_input("Ask a question..."):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Save user message
        add_message(session_id, "user", prompt)
        
        # If this is the first message in the session, update the session title
        if len(messages) == 0:
            new_title = prompt[:30] + "..." if len(prompt) > 30 else prompt
            update_session_title(session_id, new_title)
        
        # Get bot response
        with st.chat_message("ai"):
            with st.spinner("Thinking..."):
                try:
                    response = answer_query(prompt, api_key, messages)
                    st.markdown(response)
                    add_message(session_id, "ai", response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

