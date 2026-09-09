"""
Continuity – Production Memory Agent
Must boot even if ADK / MCP is not ready (Streamlit Cloud healthz).
"""

from __future__ import annotations

import os
import sys
import traceback
import uuid
from pathlib import Path

# Repo root on path so `agents` imports work when this file lives in app/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="Continuity – Production Memory Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass


def _apply_streamlit_secrets() -> None:
    keys = [
        "GOOGLE_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_PORT",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_PASSWORD",
        "CLICKHOUSE_SECURE",
        "CLICKHOUSE_DATABASE",
        "CLICKHOUSE_ALLOW_WRITE_ACCESS",
    ]
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in keys:
        try:
            val = secrets.get(key)
        except Exception:
            continue
        if val:
            os.environ[key] = str(val)


_apply_streamlit_secrets()

st.markdown(
    """
<style>
    .stApp { background: linear-gradient(180deg, #0f0f12 0%, #1a1a22 100%); }
    .main-header {
        font-size: 2.4rem; font-weight: 700;
        background: linear-gradient(90deg, #e8d5a3, #c9a227);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub-header { color: #a0a0b0; font-size: 1.05rem; margin-bottom: 1.2rem; }
</style>
""",
    unsafe_allow_html=True,
)


def _secret_status(name: str) -> str:
    return "set" if os.getenv(name) else "MISSING"


def query_clickhouse(sql: str):
    import clickhouse_connect

    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", ""),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
    )
    return client.query(sql)


def fallback_answer(prompt: str) -> str:
    """Deterministic ClickHouse-backed answer if the Gemini agent cannot start."""
    try:
        notes = query_clickhouse(
            """
            SELECT severity, note_type, shot_id, description, reported_by
            FROM production_memory.continuity_notes
            WHERE production_id = 'prod_neon_harbor' AND resolved = 0
            ORDER BY severity DESC, created_at
            """
        )
        costs = query_clickhouse(
            """
            SELECT category, sum(amount_usd) AS spend
            FROM production_memory.cost_events
            WHERE production_id = 'prod_neon_harbor'
            GROUP BY category
            ORDER BY spend DESC
            """
        )
        sched = query_clickhouse(
            """
            SELECT title, status, start_time, notes
            FROM production_memory.schedule_events
            WHERE production_id = 'prod_neon_harbor'
            ORDER BY start_time
            """
        )
    except Exception as e:
        return (
            f"Could not reach ClickHouse: {e}\n\n"
            "Add CLICKHOUSE_* secrets in Streamlit Cloud → App settings → Secrets."
        )

    lines = [
        "## Neon Harbor — production memory",
        "",
        f"Prompt: {prompt}",
        "",
        "### Open continuity notes",
    ]
    for row in notes.result_rows:
        lines.append(f"- **{row[0]} / {row[1]}** ({row[2]}): {row[3]} — {row[4]}")
    lines += ["", "### Spend by category"]
    for row in costs.result_rows:
        lines.append(f"- {row[0]}: ${float(row[1]):,.0f}")
    lines += ["", "### Schedule"]
    for row in sched.result_rows:
        lines.append(f"- {row[0]} [{row[1]}] {row[2]} — {row[3]}")
    lines += [
        "",
        "_Fallback mode: live ClickHouse query. Gemini/ADK agent did not start on this host._",
    ]
    return "\n".join(lines)


def run_agent_sync(prompt: str) -> str:
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from agents.continuity_agent import root_agent

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="continuity",
            session_service=session_service,
        )
        session = session_service.create_session(
            app_name="continuity",
            user_id="demo_user",
            session_id=str(uuid.uuid4()),
        )
        content = types.Content(role="user", parts=[types.Part(text=prompt)])
        final_text = []
        for event in runner.run(
            user_id="demo_user",
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        final_text.append(part.text)
        if final_text:
            return "\n".join(final_text)
        return fallback_answer(prompt)
    except Exception:
        tb = traceback.format_exc()
        return fallback_answer(prompt) + "\n\n<details><summary>Agent error</summary>\n\n```\n" + tb + "\n```\n</details>"


with st.sidebar:
    st.markdown("### 🎬 Continuity")
    st.caption("Production Memory Agent")
    st.markdown("---")
    st.markdown("**Secrets**")
    st.write(f"GOOGLE_API_KEY: `{_secret_status('GOOGLE_API_KEY')}`")
    st.write(f"CLICKHOUSE_HOST: `{_secret_status('CLICKHOUSE_HOST')}`")
    st.write(f"CLICKHOUSE_PASSWORD: `{_secret_status('CLICKHOUSE_PASSWORD')}`")
    st.markdown("---")
    st.markdown("**Quick Prompts**")
    prompts = [
        "Give me a full status of Neon Harbor. Any open critical issues?",
        "Explain the continuity problems between scene 12 and scene 18.",
        "How much have we spent on VFX so far and what is still coming?",
        "Recommend how to fix the coat continuity issue before we wrap scene 18.",
    ]
    for p in prompts:
        if st.button(p[:56] + ("…" if len(p) > 56 else ""), key=p[:24], use_container_width=True):
            st.session_state.pending_prompt = p

st.markdown('<div class="main-header">Continuity</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Long-term production memory for film &amp; television. '
    "ClickHouse is the memory. Gemini is the reasoning.</div>",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "I'm Continuity — production memory for **Neon Harbor**.\n\n"
                "Ask about continuity notes, schedule risk, or VFX spend."
            ),
        }
    ]

if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")
    st.session_state.messages.append({"role": "user", "content": prompt})
    reply = run_agent_sync(prompt)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Ask about continuity, schedule, budget, assets…"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        reply = run_agent_sync(user_input)
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
