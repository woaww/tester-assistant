FROM registry.ahml.ru/eisgs/docker-images/python:3.11-slim-buster

# ARG PIP_INDEX_URL=https://nexus.ahml.ru/repository/pypi-proxy/simple/ 
ARG PIP_INDEX_URL=https://nexus.dev.domoy.ru/repository/pip-remote-pypi/simple

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libgtk-3-0 libasound2 ca-certificates fonts-liberation \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY ./app .

RUN python -m pip install --upgrade pip && \
    PIP_INDEX_URL=${PIP_INDEX_URL} pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium


COPY ./app/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    mkdir -p /root/.streamlit && \
    echo '[browser]' > /root/.streamlit/config.toml && \
    echo 'gatherUsageStats = false' >> /root/.streamlit/config.toml && \
    echo '[server]' >> /root/.streamlit/config.toml && \
    echo 'headless = true' >> /root/.streamlit/config.toml && \
    echo 'address = "0.0.0.0"' >> /root/.streamlit/config.toml && \
    echo 'port = 8513' >> /root/.streamlit/config.toml

EXPOSE 8513

ENTRYPOINT ["/app/entrypoint.sh"]