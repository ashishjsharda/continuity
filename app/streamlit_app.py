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
    .stApp {
        background: linear-gradient(180deg, #0f0f12 0%, #1a1a22 100%);
    }

    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #e8d5a3, #c9a227);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .sub-header {
        color: #a0a0b0;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def _secret_status(name: str) -> str:
    return "set" if os.getenv(name) else "MISSING"


def _clickhouse_pool_manager():
    """
    Legacy TLS fallback for environments where ClickHouse Cloud connections
    hit SSL EOF / legacy renegotiation problems.

    Normal TLS is tried first in query_clickhouse().
    """
    import ssl
    import urllib3

    ctx = ssl.create_default_context()

    if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
        ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT

    return urllib3.PoolManager(ssl_context=ctx)


def query_clickhouse(sql: str):
    """
    Query ClickHouse.

    Strategy:
    1. Try the normal ClickHouse Connect TLS configuration.
    2. If the failure looks SSL/TLS-specific, retry using the legacy SSL
       context required by some modern OpenSSL environments.
    """
    import clickhouse_connect

    host = os.getenv("CLICKHOUSE_HOST", "").strip()
    port = int(os.getenv("CLICKHOUSE_PORT", "8443"))
    username = os.getenv("CLICKHOUSE_USER", "default").strip()
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    database = os.getenv("CLICKHOUSE_DATABASE", "production_memory").strip()
    secure = os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"

    if not host:
        raise RuntimeError("CLICKHOUSE_HOST is not configured.")

    kwargs = dict(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        secure=secure,
        connect_timeout=10,
        send_receive_timeout=30,
    )

    # First try normal ClickHouse Cloud TLS.
    try:
        client = clickhouse_connect.get_client(**kwargs)
        return client.query(sql)

    except Exception as first_error:
        error_text = str(first_error).lower()

        tls_failure = any(
            token in error_text
            for token in (
                "ssl",
                "tls",
                "unexpected_eof",
                "unexpected eof",
                "eof occurred",
                "wrong version number",
                "certificate",
            )
        )

        # Don't hide non-TLS errors such as bad credentials, bad SQL, etc.
        if not tls_failure:
            raise

        # Retry only SSL/TLS failures using the legacy pool manager.
        try:
            client = clickhouse_connect.get_client(
                **kwargs,
                pool_mgr=_clickhouse_pool_manager(),
            )
            return client.query(sql)

        except Exception as second_error:
            raise RuntimeError(
                "ClickHouse connection failed using both standard TLS "
                f"and legacy TLS fallback.\n\n"
                f"Standard TLS error: {first_error}\n\n"
                f"Legacy TLS error: {second_error}"
            ) from second_error


def fallback_answer(prompt: str) -> str:
    """
    Deterministic ClickHouse-backed answer if Gemini / ADK cannot respond.
    """
    try:
        notes = query_clickhouse(
            """
            SELECT
                severity,
                note_type,
                shot_id,
                description,
                reported_by
            FROM production_memory.continuity_notes
            WHERE
                production_id = 'prod_neon_harbor'
                AND resolved = 0
            ORDER BY severity DESC, created_at
            """
        )

        costs = query_clickhouse(
            """
            SELECT
                category,
                sum(amount_usd) AS spend
            FROM production_memory.cost_events
            WHERE production_id = 'prod_neon_harbor'
            GROUP BY category
            ORDER BY spend DESC
            """
        )

        sched = query_clickhouse(
            """
            SELECT
                title,
                status,
                start_time,
                notes
            FROM production_memory.schedule_events
            WHERE production_id = 'prod_neon_harbor'
            ORDER BY start_time
            """
        )

    except Exception as e:
        return (
            f"Could not reach ClickHouse: {e}\n\n"
            "Verify the CLICKHOUSE_* values in Streamlit Cloud "
            "→ App settings → Secrets."
        )

    lines = [
        "## Neon Harbor — production memory",
        "",
        f"Prompt: {prompt}",
        "",
        "### Open continuity notes",
    ]

    if notes.result_rows:
        for row in notes.result_rows:
            lines.append(
                f"- **{row[0]} / {row[1]}** ({row[2]}): "
                f"{row[3]} — {row[4]}"
            )
    else:
        lines.append("- No unresolved continuity notes found.")

    lines += [
        "",
        "### Spend by category",
    ]

    if costs.result_rows:
        for row in costs.result_rows:
            lines.append(f"- {row[0]}: ${float(row[1]):,.0f}")
    else:
        lines.append("- No cost events found.")

    lines += [
        "",
        "### Schedule",
    ]

    if sched.result_rows:
        for row in sched.result_rows:
            lines.append(
                f"- {row[0]} [{row[1]}] {row[2]} — {row[3]}"
            )
    else:
        lines.append("- No schedule events found.")

    lines += [
        "",
        "_Fallback mode: live ClickHouse query. "
        "Gemini/ADK did not return an answer._",
    ]

    return "\n".join(lines)


def run_agent_sync(prompt: str) -> str:
    """
    Run the Google ADK agent synchronously for Streamlit.

    The currently installed ADK version exposes create_session_sync()
    and runner.run(), so we use those rather than mixing async/sync APIs.
    """
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

        session = session_service.create_session_sync(
            app_name="continuity",
            user_id="demo_user",
            session_id=str(uuid.uuid4()),
        )

        content = types.Content(
            role="user",
            parts=[
                types.Part(text=prompt),
            ],
        )

        final_text = []

        for event in runner.run(
            user_id="demo_user",
            session_id=session.id,
            new_message=content,
        ):
            if (
                event.is_final_response()
                and event.content
                and event.content.parts
            ):
                for part in event.content.parts:
                    text = getattr(part, "text", None)

                    if text:
                        final_text.append(text)

        if final_text:
            return "\n".join(final_text)

        return fallback_answer(prompt)

    except Exception as e:
        error_text = str(e)

        # Gemini can temporarily return 503 when capacity is constrained.
        if "503" in error_text or "UNAVAILABLE" in error_text:
            fallback = fallback_answer(prompt)

            if not fallback.startswith("Could not reach ClickHouse"):
                return (
                    fallback
                    + "\n\n"
                    "_Gemini is temporarily busy, so this response "
                    "was generated directly from ClickHouse._"
                )

            return (
                "Gemini is temporarily experiencing high demand. "
                "Please try the question again shortly.\n\n"
                "The ClickHouse fallback also could not connect:\n\n"
                f"{fallback}"
            )

        # Unexpected errors: preserve diagnostic detail.
        tb = traceback.format_exc()

        fallback = fallback_answer(prompt)

        return (
            fallback
            + "\n\n"
            "<details><summary>Agent error</summary>\n\n"
            "```text\n"
            + tb
            + "\n```\n"
            "</details>"
        )


with st.sidebar:
    st.markdown("### 🎬 Continuity")
    st.caption("Production Memory Agent")

    st.markdown("---")

    st.markdown("**Secrets**")

    st.write(
        f"GOOGLE_API_KEY: "
        f"`{_secret_status('GOOGLE_API_KEY')}`"
    )

    st.write(
        f"CLICKHOUSE_HOST: "
        f"`{_secret_status('CLICKHOUSE_HOST')}`"
    )

    st.write(
        f"CLICKHOUSE_PASSWORD: "
        f"`{_secret_status('CLICKHOUSE_PASSWORD')}`"
    )

    st.markdown("---")

    st.markdown("**Quick Prompts**")

    prompts = [
        "Give me a full status of Neon Harbor. Any open critical issues?",
        "Explain the continuity problems between scene 12 and scene 18.",
        "How much have we spent on VFX so far and what is still coming?",
        "Recommend how to fix the coat continuity issue before we wrap scene 18.",
    ]

    for p in prompts:
        label = p[:56] + ("…" if len(p) > 56 else "")

        if st.button(
            label,
            key=p[:24],
            use_container_width=True,
        ):
            st.session_state.pending_prompt = p


st.markdown(
    '<div class="main-header">Continuity</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-header">'
    "Long-term production memory for film &amp; television. "
    "ClickHouse is the memory. Gemini is the reasoning."
    "</div>",
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "I'm Continuity — production memory for "
                "**Neon Harbor**.\n\n"
                "Ask about continuity notes, schedule risk, "
                "or VFX spend."
            ),
        }
    ]


if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    reply = run_agent_sync(prompt)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
        }
    )

    st.rerun()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if user_input := st.chat_input(
    "Ask about continuity, schedule, budget, assets…"
):
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Checking production memory…"):
            reply = run_agent_sync(user_input)

        st.markdown(reply)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
        }
    )
