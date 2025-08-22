# app/logger.py
import logging
import os
import sys
import json
from functools import wraps
import traceback
from datetime import datetime
from src.models import FunctionCallLog, FunctionResultLog, FunctionErrorLog
from src.text_constants import LoggerMsg

# === 1. Кастомный Formatter: только если есть meta → сериализуем, иначе убираем из формата ===
class ConditionalJSONFormatter(logging.Formatter):
    def format(self, record):
        # Если в record есть meta — сериализуем в JSON
        if hasattr(record, "meta"):
            record.meta = json.dumps(
                record.meta, ensure_ascii=False, default=str)
        else:
            # Если meta нет — убираем его из формата
            self._style._fmt = self._style._fmt.replace("%(meta)s", "null")
        return super().format(record)


# === 2. Формат: meta опциональный, но по умолчанию — null ===
LOG_FORMAT = (
    '{"level": "%(levelname)s", '
    '"filename": "%(filename)s", '
    '"lineno": %(lineno)d, '
    # '"funcName": "%(funcName)s", '
    '"message": %(message)s, '
    '"meta": %(meta)s}'  # ← будет null, если meta нет
)
LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# === 3. Создаём свой обработчик с кастомным форматтером ===
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(
    ConditionalJSONFormatter(LOG_FORMAT, LOG_DATETIME_FORMAT))

# === 4. Создаём отдельный логгер с префиксом, чтобы не мешать другим ===
LOGGER = logging.getLogger("myapp")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(stream_handler)
# ВАЖНО: отключаем пропагацию, чтобы не дублировать логи в root
LOGGER.propagate = False


def shorten_traceback(exc_traceback, project_root=None):
    tb_list = traceback.extract_tb(exc_traceback)
    if project_root:
        tb_list = [frame for frame in tb_list if project_root in frame.filename]
    frame = tb_list[-1] if tb_list else traceback.extract_tb(exc_traceback)[-1]
    filename = frame.filename.split("\\")[-1]  # basename
    lineno = frame.lineno
    func_name = frame.name
    exc_type, exc_value, _ = sys.exc_info()
    error_msg = str(exc_value)
    return f"{filename}:{lineno} in {func_name} — {error_msg}"

def log_function_call(allowed_kwargs=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            safe_kwargs = kwargs if allowed_kwargs is None else {
                k: kwargs[k] for k in allowed_kwargs if k in kwargs
            }
            start_time = datetime.now()

            # === Определяем реальный вызывающий файл и строку ===
            import inspect
            frame = inspect.currentframe().f_back
            caller_filename = frame.f_code.co_filename
            caller_lineno = frame.f_lineno
            caller_func_name = frame.f_code.co_name

            def log_with_caller(level, msg, extra=None):
                record = LOGGER.makeRecord(
                    name=LOGGER.name,
                    level=level,
                    fn=caller_filename,
                    lno=caller_lineno,
                    msg=msg,
                    args=(),
                    exc_info=None,
                    func=caller_func_name,
                    extra=extra
                )
                LOGGER.handle(record)

            try:
                call_data = FunctionCallLog(function=func.__name__, kwargs=safe_kwargs)
                log_with_caller(
                    logging.INFO,
                    LoggerMsg.INFO_START,
                    extra={"meta": call_data.model_dump()}
                )

                result = func(*args, **kwargs)

                execution_time = (datetime.now() - start_time).total_seconds()
                result_data = FunctionResultLog(
                    function=func.__name__,
                    execution_time=execution_time
                )
                log_with_caller(
                    logging.INFO,
                    LoggerMsg.INFO_END,
                    extra={"meta": result_data.model_dump()}
                )

                return result

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()

                tb_list = traceback.extract_tb(exc_traceback)
                frame_error = tb_list[-1]  # где произошла ошибка

                error_data = FunctionErrorLog(
                    function=func.__name__,
                    kwargs=safe_kwargs,
                    error=str(e),
                    traceback=f"{os.path.basename(frame_error.filename)}:{frame_error.lineno} in {frame_error.name} — {str(e)}"
                )

                log_with_caller(
                    logging.ERROR,
                    LoggerMsg.ERROR,
                    extra={"meta": error_data.model_dump()}
                )
                raise

        return wrapper
    return decorator