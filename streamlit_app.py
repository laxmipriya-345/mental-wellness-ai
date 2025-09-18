# streamlit_app.py
import os
import json
import time
import uuid
import re
from datetime import datetime

import streamlit as st
import openai

# -------------------------
# Config / Defaults
# -------------------------
DEFAULT_MODEL = "gpt-3.5-turbo"   # or gpt-4o-mini if available
SYSTEM_PROMPT = (
    "You are CalmFriend, an empathetic, non-judgmental, youth-friendly mental wellness companion. "
    "Always validate feelings first, use short kind sentences, suggest one simple coping step, and "
    "ask a gentle follow-up question. Never give medical advice. If the user indicates immediate self-harm or danger, "
    "do not try to handle it — trigger the crisis escalation response."
)

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "hurt myself",
    "i can't go on", "no reason to live", "i will kill myself"
]


# -------------------------
# Helper functions
# -------------------------
def simple_crisis_check(text: str) -> bool:
    t = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in t:
            return True
    if re.search(r"\bi want to (die|kill|hurt)\b", t):
        return True
    return False


def call_chat_model(messages, model=DEFAULT_MODEL, temperature=0.7, max_tokens=350):
    """Call OpenAI ChatCompletion endpoint with messages list."""
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return resp["choices"][0]["message"]["content"].strip()


# -------------------------
# Streamlit UI + logic
# -------------------------
st.set_page_config(page_title="CalmFriend - Youth Mental Wellness", page_icon="💙", layout="centered")

st.header("💙 CalmFriend — AI wellness companion (Demo)")
st.write(
    "A confidential, empathetic space to share feelings. "
    "*Not a replacement for a therapist.* If you are in danger, contact local emergency services immediately."
)

# API key input
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if not st.session_state.api_key:
    st.warning("🔑 Please enter your OpenAI API key to continue")
    key_input = st.text_input("OpenAI API Key", type="password")
    if key_input:
        st.session_state.api_key = key_input
        openai.api_key = key_input
else:
    openai.api_key = st.session_state.api_key

if not openai.api_key:
    st.stop()

# Sidebar controls
with st.sidebar:
    st.subheader("Settings")
    model_name = st.selectbox("Model", options=[DEFAULT_MODEL, "gpt-4o-mini", "gpt-4"], index=0)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    if st.button("Clear conversation"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.experimental_rerun()

# Session state
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

st.markdown(f"**Session id:** `{st.session_state.session_id}`  •  {datetime.utcnow().isoformat()} UTC")

# Show chat history
st.subheader("Conversation")
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"👤 **You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"🤖 **CalmFriend:** {msg['content']}")

# Input box
user_text = st.text_area("Share something (or ask for support):", height=120)

if st.button("Send"):
    if user_text.strip():
        # Check for crisis
        if simple_crisis_check(user_text):
            st.error(
                "⚠️ I’m really sorry you’re feeling this way. I can’t provide emergency support. "
                "If you are in immediate danger, please contact your local emergency services now."
            )
            st.session_state.messages.append({"role": "user", "content": user_text})
        else:
            st.session_state.messages.append({"role": "user", "content": user_text})
            with st.spinner("Thinking... 💭"):
                try:
                    reply = call_chat_model(st.session_state.messages, model=model_name, temperature=temperature)
                except Exception as e:
                    reply = f"⚠️ Error: {e}"
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.experimental_rerun()
    else:
        st.warning("Please type something before sending.")

