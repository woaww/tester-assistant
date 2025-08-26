FROM registry.ahml.ru/eisgs/docker-images/python:3.11-slim-buster

# ARG PIP_INDEX_URL: https://nexus.ahml.ru/repository/pypi-proxy/simple/
ARG PIP_INDEX_URL: https://nexus.dev.domoy.ru/repository/pip-remote-pypi/simple

WORKDIR /app

COPY ./app .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8513

ENTRYPOINT streamlit run app.py --server.port=8513 --server.address=0.0.0.0
