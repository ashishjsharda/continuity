# Continuity – 3-Minute Demo Script

**Goal:** Show a real multi-step agent that uses ClickHouse MCP at runtime to solve production friction.

## Setup (before recording)
1. ClickHouse Cloud service running with `production_memory` schema + seed data loaded.
2. `.env` configured.
3. Agent running via `adk web` or a simple FastAPI / Streamlit front-end.
4. Screen recording ready (show both chat UI + optional Grafana-style or table view of data if desired).

---

## Demo Flow (≈ 2:45)

**0:00 – 0:20  Hook**
> "In a film production, continuity breaks and budget surprises kill schedules. Continuity is an agent that treats ClickHouse as the production's long-term memory."

Show the Neon Harbor production overview.

**0:20 – 0:55  Situational Awareness**
Prompt:
```
Give me a quick status of Neon Harbor. What is currently shooting and are there any open critical issues?
```
Agent should:
- Query productions + schedule_events + continuity_notes
- Surface the two critical notes (watch timeline + coat mismatch on the active interrogation scene)

**0:55 – 1:40  Deep Continuity Analysis**
Prompt:
```
Walk me through the continuity problems between the alley sequence (scene 12) and the interrogation (scene 18). What will break if we keep going?
```
Agent should:
- Pull shots 12A/B/C and 18A
- Pull the related assets and notes
- Explain the scuffed vs clean coat problem and the watch time paradox
- Give a clear recommendation

**1:40 – 2:20  Risk + Recommendation**
Prompt:
```
Looking at current spend, how exposed are we on VFX for the sequences we've already shot, and what should the producer do before the rooftop days?
```
Agent queries cost_events, groups by category, compares against remaining schedule, and recommends action.

**2:20 – 2:45  Close**
> "Every recommendation is grounded in live ClickHouse data via the official MCP server. The agent can also write its own decisions back into the memory layer so the production has an audit trail."

Show a final query that lists recent agent_actions if you logged any.

---

## Suggested Closing Line
"Continuity turns the chaos of a real production into a queryable, agent-readable memory. Built with Gemini, Google ADK, and ClickHouse."
