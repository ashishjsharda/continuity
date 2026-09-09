# Continuity – Production Memory Agent
# Cloud Run ready

FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution (also used by mcp-clickhouse)
RUN pip install --no-cache-dir uv

# Copy project
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Install ADK + Streamlit extra
RUN uv pip install --system "google-adk>=1.0.0" streamlit clickhouse-connect

COPY . .

# Streamlit config
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8080

# Cloud Run sets PORT; we default to 8080
CMD streamlit run app/streamlit_app.py --server.port=${PORT:-8080} --server.address=0.0.0.0
