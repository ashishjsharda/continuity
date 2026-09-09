#!/usr/bin/env python3
"""
Quick local runner for Continuity agent using ADK web UI or CLI.
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.continuity_agent import root_agent

if __name__ == "__main__":
    print("Continuity agent loaded.")
    print("Agent name:", root_agent.name)
    print("Model:", root_agent.model)
    print("\nTo run the interactive ADK web UI:")
    print("  uv run --with google-adk adk web")
    print("\nOr use the API server:")
    print("  uv run --with google-adk adk api_server")
    print("\nMake sure your .env is configured with ClickHouse + Google credentials.")
