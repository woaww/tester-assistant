import logging
import os

import mlflow

_log = logging.getLogger(__name__)


def init_mlflow() -> None:
    """
    Инициализация MLflow.
    По умолчанию отключено (MLFLOW_ENABLED=false), чтобы локальный запуск
    не зависел от корпоративного трекинг-сервера.
    """
    enabled = os.getenv("MLFLOW_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "").strip() or "file://mlruns"
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "tester-assistant").strip()
    try:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name=experiment_name)
        try:
            mlflow.openai.autolog()
        except Exception:
            # не критично, если конкретная autolog интеграция недоступна
            pass
    except Exception as e:
        _log.warning("MLflow отключён из-за ошибки инициализации: %s", e)


def log_locator_run(
    run_id: str,
    params: dict | None = None,
    metrics: dict | None = None,
    tags: dict | None = None,
) -> None:
    """
    Логирование результатов запуска генерации локаторов в MLflow.
    Безопасно: при любой ошибке не прерывает основной сценарий.
    """
    enabled = os.getenv("MLFLOW_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return

    try:
        with mlflow.start_run(run_name=f"locator_run_{run_id}"):
            if params:
                mlflow.log_params({k: v for k, v in params.items() if v is not None})
            if metrics:
                numeric_metrics = {}
                for k, v in metrics.items():
                    if isinstance(v, (int, float)) and v is not None:
                        numeric_metrics[k] = float(v)
                if numeric_metrics:
                    mlflow.log_metrics(numeric_metrics)
            if tags:
                mlflow.set_tags({k: str(v) for k, v in tags.items() if v is not None})
    except Exception as e:
        _log.warning("MLflow: не удалось записать run: %s", e)

