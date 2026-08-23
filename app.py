"""
app.py
-------
Main Streamlit entrypoint for EchoCart.
"""

import streamlit as st
from services import db_service, command_handler
from components import ui_helpers

# ===== Page config (must be first Streamlit call) =====
st.set_page_config(
    page_title="EchoCart",
    page_icon="🛒",
    layout="wide",
)

# ===== Init =====
db_service.init_db()
ui_helpers.load_css()

# ===== Session state (holds last command result across reruns) =====
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ===== Header =====
ui_helpers.render_header()

# ===== Command input =====
st.markdown("### Type a command")
st.caption('Try: "Add milk", "I need 2 bottles of water", "Remove milk", "Find toothpaste under 200 rupees"')

command_text = st.text_input("Command", label_visibility="collapsed", placeholder="Type your command here...")

if st.button("Execute", type="primary"):
    if command_text.strip():
        result = command_handler.execute(command_text)
        st.session_state.last_result = result
        st.rerun()

# ===== Feedback banner =====
if st.session_state.last_result:
    ui_helpers.render_feedback(
        st.session_state.last_result["success"],
        st.session_state.last_result["message"]
    )

# ===== Search results (if last command was a SEARCH) =====
if st.session_state.last_result and st.session_state.last_result["intent"] == "SEARCH":
    st.markdown("### Search Results")
    ui_helpers.render_search_results(st.session_state.last_result["data"])

# ===== Shopping list (always shown) =====
st.markdown("### Your Shopping List")
shopping_list = db_service.get_shopping_list()
ui_helpers.render_shopping_list(shopping_list)