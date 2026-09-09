"""
Continuity – Production Memory Agent
Streamlit front-end for the Agentic Cinema (ClickHouse track) submission.
"""

import os
import uuid
import asyncio
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Continuity – Production Memory Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS – clean cinematic feel
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0f0f12 0%, #1a1a22 100%);
    }
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #e8d5a3, #c9a227);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #a0a0b0;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .status-card {
        background: #1e1e28;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .critical { border-left: 4px solid #e74c3c; }
    .warning  { border-left: 4px solid #f39c12; }
    .info     { border-left: 4px solid #3498db; }
    .stChatMessage {
        background: #1e1e28;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎬 Continuity")
    st.caption("Production Memory Agent")
    st.markdown("---")

    st.markdown("**Demo Production**")
    st.markdown("`Neon Harbor`  \nNeo-noir · Principal Photography")

    st.markdown("---")
    st.markdown("**Quick Prompts**")
    prompts = [
        "Give me a full status of Neon Harbor. Any open critical issues?",
        "Explain the continuity problems between the alley sequence (scene 12) and the current interrogation (scene 18).",
        "How much have we spent on VFX so far and what is still coming for the rooftop?",
        "Recommend the cheapest way to fix the coat continuity issue before we wrap scene 18.",
        "Show me all open continuity notes ordered by severity.",
    ]
    for p in prompts:
        if st.button(p[:60] + ("…" if len(p) > 60 else ""), key=p[:30], use_container_width=True):
            st.session_state.pending_prompt = p

    st.markdown("---")
    st.caption("Powered by Gemini + Google ADK  \nClickHouse MCP · Agentic Cinema 2026")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">Continuity</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Long-term production memory for film & television. '
    'ClickHouse is the memory. Gemini is the reasoning.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Lazy-load the ADK agent (heavy import)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_agent():
    """Load the Continuity agent once per session."""
    from agents.continuity_agent import root_agent
    return root_agent


def run_agent_sync(prompt: str) -> str:
    """
    Run a single turn against the ADK agent.
    Uses the runner pattern for simplicity in Streamlit.
    """
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        agent = get_agent()
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="continuity",
            session_service=session_service,
        )

        # Create a session
        session = session_service.create_session(
            app_name="continuity",
            user_id="demo_user",
            session_id=str(uuid.uuid4()),
        )

        # Build the message
        content = types.Content(role="user", parts=[types.Part(text=prompt)])

        # Collect the final response
        final_text = []
        for event in runner.run(
            user_id="demo_user",
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text.append(part.text)

        return "\n".join(final_text) if final_text else "No response generated."

    except Exception as e:
        return f"⚠️ Agent error: {type(e).__name__}: {e}\n\nMake sure ClickHouse credentials and GOOGLE_API_KEY are set in `.env`."


# ---------------------------------------------------------------------------
# Chat state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "I'm Continuity — your production memory agent.\n\n"
                "I have live access to the **Neon Harbor** production database via ClickHouse.\n"
                "Ask me about continuity notes, schedule risk, VFX spend, or any production state.\n\n"
                "Try one of the quick prompts in the sidebar, or just start asking."
            ),
        }
    ]

# Handle pending prompt from sidebar
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Querying production memory…"):
        reply = run_agent_sync(prompt)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("Ask about continuity, schedule, budget, assets…"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Reasoning over production memory…"):
            reply = run_agent_sync(user_input)
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
