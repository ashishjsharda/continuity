# Continuity

**Production Memory Agent for Film & Television**

> Built for the **Agentic Cinema: Lights. Camera. Code.** hackathon (ClickHouse track)

Continuity is a multi-step Gemini agent that treats **ClickHouse as the long-term memory and analytical backbone** of a media production. It helps 1st ADs, script supervisors, and producers catch continuity breaks, timeline paradoxes, and budget risk *before* they become expensive reshoots.

---

## Why this exists

On a real set, continuity notes live in binders, Slack threads, and the script supervisor’s brain. Budget burn is tracked in a different spreadsheet. Schedule is in yet another system. When something breaks (wardrobe mismatch, prop timeline error, VFX cost spike), the discovery is often too late.

Continuity collapses that into one queryable memory layer and gives an agent the ability to reason across it.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gemini Agent (ADK)                       │
│         Continuity – Production Memory Agent                │
└──────────────────────────┬──────────────────────────────────┘
                           │  MCP (stdio / tools)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Official mcp-clickhouse server                 │
│         list_databases · list_tables · run_query            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     ClickHouse Cloud                        │
│  productions · shots · assets · continuity_notes            │
│  schedule_events · cost_events · agent_actions              │
└─────────────────────────────────────────────────────────────┘
```

**Runtime requirement satisfied:** the agent calls the official ClickHouse MCP server (`mcp-clickhouse`) at runtime. All production state is read (and optionally written) through it.

## Quick Start

### 1. ClickHouse Cloud

New accounts get **$400 in credits** via the hackathon promo:

https://console.clickhouse.cloud/signUp?promo=SIGNUP100

1. Create a service
2. Run the schema: `schema/production_schema.sql`
3. Load seed data: `data/seed_production.sql`

### 2. Local setup

```bash
git clone <this-repo>
cd continuity
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in CLICKHOUSE_* and GOOGLE_API_KEY / Vertex credentials
```

### 3. Run the UI (recommended for demos)

```bash
# Streamlit chat interface
streamlit run app/streamlit_app.py
```

Open http://localhost:8501 (or the port Streamlit prints).

Alternative (ADK native UI):
```bash
uv run --with google-adk adk web
```

### 4. Deploy to Cloud Run (hosted URL for judges)

```bash
# Make sure gcloud is authenticated and project is set
chmod +x scripts/deploy_cloud_run.sh
./scripts/deploy_cloud_run.sh
```

Or manually:
```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/continuity-agent
gcloud run deploy continuity-agent \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/continuity-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi
```

Store secrets (ClickHouse + Google key) in Secret Manager and reference them with `--set-secrets`.

## Demo Production: “Neon Harbor”

A mid-budget neo-noir currently in principal photography.

Key friction the agent can surface:

| Issue | Severity | Impact |
|-------|----------|--------|
| Scuffed trench coat appears in alley (12A) but clean coat is being used in interrogation (18A) | Critical | Continuity jump if intercut |
| Hero watch stopped at 10:17 while dialogue later references “just after midnight” | Critical | Timeline paradox |
| VFX rain already cost $137k and rooftop sequence still unshot | Warning | Budget exposure |
| Makeup aging on flashback needs review before pickup | Warning | Reshoot risk |

## Example Prompts

```
Give me a status of Neon Harbor right now. Any open critical issues?

Explain the continuity problems between scene 12 and the current interrogation scene.

How much have we spent on VFX so far and what’s still coming?

Recommend the cheapest way to fix the coat continuity issue before we wrap scene 18.
```

## Project Structure

```
continuity/
├── agents/
│   └── continuity_agent.py     # ADK LlmAgent + MCP toolset
├── schema/
│   └── production_schema.sql   # ClickHouse tables
├── data/
│   └── seed_production.sql     # Realistic synthetic production
├── demo/
│   └── demo_script.md          # 3-minute video outline
├── scripts/
│   └── run_agent.py
├── .env.example
├── requirements.txt
├── LICENSE                     # MIT
└── README.md
```

## Judging Alignment

| Criterion | How Continuity addresses it |
|-----------|-----------------------------|
| **Technological Implementation** | Real runtime use of Google ADK + official `mcp-clickhouse`. Multi-step tool calling. |
| **Design** | Complete product experience: schema, seed data, agent persona, demo script, audit trail. |
| **Potential Impact** | Solves a real, expensive problem for filmmakers and studio crews. |
| **Quality of the Idea** | ClickHouse as *agent memory* rather than just a query engine is non-obvious and powerful. |

## License

MIT — see `LICENSE`.

---

Built with Gemini, Google Agent Development Kit, and ClickHouse for the Agentic Cinema hackathon.
