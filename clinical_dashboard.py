import json
import os
import sqlite3
import time

import pandas as pd
import streamlit as st
from openai import OpenAI

from support.prompts import DASHBOARD_INSTRUCTIONS, DATA_DICTIONARY_HTML, WORKFLOW_INSTRUCTIONS

# Server URL configuration:
# - In production: Use SERVER_URL environment variable
# - In development: Read from config.json (created by ngrok tunnel in Makefile)
server_url = os.getenv("SERVER_URL")
if server_url is None:
    try:
        with open("config.json") as f:
            config = json.load(f)
        server_url = config["server_url"]
    except FileNotFoundError:
        server_url = "/mcp"

instructions = WORKFLOW_INSTRUCTIONS

client = OpenAI()
tools = [
    {
        "type": "mcp",
        "server_label": "clinical-mcp",
        "server_url": server_url,
        "require_approval": "never",
        "headers": {"ngrok-skip-browser-warning": "true"},
    }
]

if "history" not in st.session_state:
    st.session_state.history = []
if "last_resp_id" not in st.session_state:
    st.session_state.last_resp_id = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

st.set_page_config(page_title="CLIN 9000", page_icon="🩺", layout="centered")


def inject_css():
    """Inject custom CSS for clinical themed UI."""
    with open("support/styles.css", "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


inject_css()

st.image("icon/banner.png", use_container_width=True)

st.markdown(DASHBOARD_INSTRUCTIONS, unsafe_allow_html=True)


tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Data Dictionary", "Study Protocol", "Audit Log"])
with tab1:
    for user_msg, assistant_msg in st.session_state.history:
        st.markdown(
            f'<div class="clinical-bubble-user"><b>You:</b> {user_msg}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="clinical-bubble-assistant"><b>Assistant:</b> {assistant_msg}</div>',
            unsafe_allow_html=True,
        )

    col_space, col2 = st.columns([1, 4])

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your question", key=f"user_input_{st.session_state.input_key}")
        submitted = st.form_submit_button("Send")



    if submitted and user_input:
        with col2:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Preparing request...")
            progress_bar.progress(20)
            req = dict(model="gpt-4o", tools=tools, instructions=instructions, input=user_input)
            if st.session_state.last_resp_id:
                req["previous_response_id"] = st.session_state.last_resp_id

            status_text.text("Sending to LLM...")
            progress_bar.progress(50)
            resp = client.responses.create(**req)

            st.session_state.last_resp_id = resp.id
            st.session_state.history.append([user_input, resp.output_text])
            status_text.text("Complete!")
            progress_bar.progress(100)

            st.session_state.input_key += 1
            time.sleep(0.5)

            st.rerun()

    if st.button("Clear Chat"):
        st.session_state.history = []
        st.session_state.last_resp_id = None
        st.session_state.input_key += 1
        st.rerun()

with tab2:
    st.markdown(DATA_DICTIONARY_HTML, unsafe_allow_html=True)

with tab3:
    # Read and display the markdown file as-is
    with open("support/study_protocol.md", "r") as f:
        protocol_content = f.read()
    st.markdown(protocol_content)

with tab4:
    st.header("MCP Tool Usage Audit Log")

    def load_audit_log() -> pd.DataFrame:
        """Return last 100 audit rows ordered by most recent first."""
        query = (
            "SELECT id, timestamp, tool_name, arguments, approved "
            "FROM audit_log "
            "ORDER BY timestamp DESC "
            "LIMIT 100"
        )

        try:
            conn = sqlite3.connect("clinical.db")
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error loading audit log from SQLite: {e}")
            return pd.DataFrame(
                columns=[
                    "id",
                    "timestamp",
                    "tool_name",
                    "arguments",
                    "approved",
                ]
            )

    audit_df = load_audit_log()

    if not audit_df.empty:
        st.dataframe(
            audit_df,
            use_container_width=True,
            column_config={
                "timestamp": "Timestamp",
                "tool_name": "Tool Name",
                "arguments": "Arguments",
                "approved": "Approved",
            },
        )

        if st.button("Refresh Audit Log"):
            st.rerun()
    else:
        st.info("No audit log entries found. Start using the chat to generate log entries.")
