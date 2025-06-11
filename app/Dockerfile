FROM registry.ahml.ru/eisgs/docker-images/python:3.11-slim-buster

WORKDIR /app

COPY ./app .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8513

ENTRYPOINT streamlit run app.py --server.port=8513 --server.address=0.0.0.0
