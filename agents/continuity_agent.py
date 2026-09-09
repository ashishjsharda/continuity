"""
Continuity - Production Memory Agent
Powered by Gemini + Google ADK + official ClickHouse MCP server

This agent treats ClickHouse as the long-term memory and analytical backbone
for a media production. It can:
- Inspect production state (shots, assets, continuity notes, schedule, costs)
- Detect continuity breaks and timeline issues
- Surface budget / schedule risk
- Produce actionable recommendations for the 1st AD, script supervisor, or producer
- Leave an audit trail of its own decisions
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

# ---------------------------------------------------------------------------
# ClickHouse MCP connection (official mcp-clickhouse)
# ---------------------------------------------------------------------------

_OPENSSL_LEGACY_CNF = Path(__file__).resolve().parent / "openssl_legacy.cnf"


def build_clickhouse_mcp() -> McpToolset:
    """
    Connect to the official ClickHouse MCP server via stdio.
    The MCP server is started on-demand by the ADK toolset.
    """
    env = {
        "CLICKHOUSE_HOST": os.getenv("CLICKHOUSE_HOST", "sql-clickhouse.clickhouse.com"),
        "CLICKHOUSE_PORT": os.getenv("CLICKHOUSE_PORT", "8443"),
        "CLICKHOUSE_USER": os.getenv("CLICKHOUSE_USER", "demo"),
        "CLICKHOUSE_PASSWORD": os.getenv("CLICKHOUSE_PASSWORD", ""),
        "CLICKHOUSE_SECURE": os.getenv("CLICKHOUSE_SECURE", "true"),
        "CLICKHOUSE_DATABASE": os.getenv("CLICKHOUSE_DATABASE", "production_memory"),
        # Allow writes so the agent can leave audit records (demo mode)
        "CLICKHOUSE_ALLOW_WRITE_ACCESS": os.getenv("CLICKHOUSE_ALLOW_WRITE_ACCESS", "true"),
        # OpenSSL 3.x refuses the legacy TLS renegotiation ClickHouse Cloud's
        # edge still uses, causing SSLEOFError in this subprocess. Set before
        # spawn so it's in effect at this process's first `ssl` import.
        # See ClickHouse/ClickHouse#93304.
        "OPENSSL_CONF": str(_OPENSSL_LEGACY_CNF),
        # subprocess.Popen with a custom env replaces the environment
        # wholesale, so carry PATH through or `python -m` may fail to
        # resolve the interpreter's own stdlib/site-packages on some hosts.
        "PATH": os.getenv("PATH", ""),
    }

    # Use the same Python that's running Streamlit.
    # Do NOT use `uv` — Streamlit Cloud / many hosts don't have it, and the
    # app dies before binding :8501 (healthz connection refused).
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_clickhouse.main"],
        env=env,
    )

    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=server_params,
            timeout=90.0,
        )
    )


# ---------------------------------------------------------------------------
# System instruction - the "brain" of Continuity
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """
You are Continuity, an elite Production Memory Agent built for film and television productions.

Your job is to act as the long-term memory and analytical co-pilot for the 1st AD, 
script supervisor, and producer. You have live access to the production database 
via ClickHouse tools (list_databases, list_tables, run_query).

## Core Capabilities
1. **Situational Awareness**
   - Summarize current production state for a given production_id
   - List open critical/warning continuity notes
   - Show upcoming schedule and any conflicts

2. **Continuity Analysis**
   - Detect wardrobe, prop, makeup, geography, and timeline mismatches across shots
   - Trace an asset's version history and last-seen location
   - Flag issues that will become expensive if not fixed before pickup days

3. **Risk & Budget**
   - Calculate current spend vs budget by category
   - Identify cost spikes (especially VFX)
   - Highlight sequences that are overrunning

4. **Actionable Recommendations**
   - Propose concrete next steps (e.g. "Use the scuffed coat for the remaining interrogation coverage" or "Schedule the 29A pickup after makeup review")
   - When you make a recommendation or alert, optionally record it in the agent_actions table so the production has an audit trail of AI decisions

## Behavior Rules
- Always start by confirming you can see the production data (list tables or a quick count query).
- Prefer precise SQL. Use production_id = 'prod_neon_harbor' for the demo production unless told otherwise.
- When you find a continuity problem, explain the visual or narrative impact clearly.
- Be concise but complete — production people are time-poor.
- Never invent data. If a query returns nothing, say so.
- You may write to the agent_actions table to log your own recommendations (use a unique action_id).

## Demo Production
Title: Neon Harbor
production_id: prod_neon_harbor
Current phase: Principal photography (interrogation scene in progress, rooftop still to shoot)

Speak like a seasoned script supervisor who also understands the budget.
"""


# ---------------------------------------------------------------------------
# Root Agent
# ---------------------------------------------------------------------------

root_agent = LlmAgent(
    model="gemini-3.6-flash",          # fast + strong for tool use; swap to pro if needed
    name="continuity",
    description="Production Memory Agent that uses ClickHouse as long-term memory for film & TV productions.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[build_clickhouse_mcp()],
)


# Optional: multi-agent version (can be expanded later)
# For the hackathon we keep a single powerful agent that can do multi-step reasoning.
# Future: separate ContinuityChecker, BudgetRisk, ScheduleGuard agents coordinated by a root.
