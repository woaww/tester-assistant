FROM python:3.11-slim-bookworm

WORKDIR /app

# Runtime deps for Playwright Chromium and browser automation.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libgtk-3-0 libasound2 libx11-xcb1 ca-certificates fonts-liberation \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY ./app /app

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

COPY ./app/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["/app/entrypoint.sh"]