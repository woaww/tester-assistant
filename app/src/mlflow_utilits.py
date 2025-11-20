import mlflow
import json
from datetime import datetime
# from datetime 
# import datetime
import uuid
from mlflow.tracking import MlflowClient
import tempfile
# import datetime
import os
from typing import Dict, Optional, Any
from mlflow.entities import AssessmentSource, AssessmentSourceType


def init_mlflow():
    mlflow.set_tracking_uri("http://d-gpgpu-a100-01.ct.ahml1.ru:5001")
    client = MlflowClient()
    experiment_name = "tester-assistant"
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        client.create_experiment(experiment_name)
    mlflow.set_experiment(experiment_name=experiment_name)
    mlflow.openai.autolog()

            

def log_to_mlflow(
    url: str,
    path: str,
    method: str,
    response: str,
    rating: str,
    response_time_ms: float,
    model_params: dict = None,
    user_email: str = None
) -> None:
    """
    Логирует взаимодействие с LLM в MLflow c улучшенным отображением.
    """
    run_name = f"LLM_Response_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    unique_id = uuid.uuid4().hex[:8]

    with mlflow.start_run(run_name=run_name):
        # ---------- Параметры ----------
        params = {
            "url": url,
            "path": path,
            "method": method,
        }
        if model_params:
            params.update(model_params)
        mlflow.log_params(params)

        # ---------- Метрики ----------
        mlflow.log_metric("response_time_ms", response_time_ms)
        mlflow.log_metric("rating", 1 if rating == "like" else 0)

        # ---------- Теги ----------
        mlflow.set_tag("status", rating)
        mlflow.set_tag("request_path", path)
        mlflow.set_tag("mlflow.runName", run_name)
        if user_email:
            mlflow.set_tag("user", user_email)

        # ---------- Логируем текст ответа отдельным файлом ----------
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=f"_{unique_id}.txt", encoding="utf-8") as tmp:
            tmp.write(response)
            tmp_path = tmp.name
        mlflow.log_artifact(tmp_path, artifact_path="text_response")
        os.remove(tmp_path)

        # ---------- Логируем JSON-пакет (удобно смотреть в UI) ----------
        response_data = {
            "url": url,
            "path": path,
            "method": method,
            "response": response,
            "rating": rating,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now().isoformat(),
            "model_params": model_params,
            "user_email": user_email
        }

        json_name = f"response_{unique_id}.json"
        with open(json_name, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
        mlflow.log_artifact(json_name, artifact_path="json_payload")
        os.remove(json_name)
