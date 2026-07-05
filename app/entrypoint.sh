#!/bin/bash
set -e

Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 1

cd /app

export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_HEADLESS=true

exec streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false

