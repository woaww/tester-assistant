import yaml
import requests
from prance import ResolvingParser
from src.exceptions import (SpecificationParserEmptyError, SpecificationParserErrorParse,
                        SpecificationParserErrorRead)

class SpecificationParser:
    def __init__(self, spec_url_or_path: str):
        self.spec_url_or_path = spec_url_or_path
        self.parser = self._load_specification()

    def _load_spec(self):
        """Загружает спецификацию как Python-словарь, независимо от источника."""
        try:
            if self.spec_url_or_path.startswith("http"):
                # Загрузка из URL
                response = requests.get(self.spec_url_or_path)
                response.raise_for_status()
                raw_content = response.text
                try:
                    return yaml.safe_load(raw_content)  # попытка загрузить как YAML
                except Exception:
                    import json
                    return json.loads(raw_content) 
        except Exception as error:
            raise SpecificationParserErrorRead from error
        
    def _fix_spec(self, spec: dict) -> dict:
        """Добавляет минимальные требуемые поля, если их нет."""
        if not isinstance(spec, dict):
            raise SpecificationParserErrorRead #from error

        if 'openapi' not in spec and 'swagger' not in spec:
            spec['openapi'] = '3.0.0'

        if 'info' not in spec:
            spec['info'] = {}

        if 'version' not in spec['info']:
            spec['info']['version'] = '1.0.0'

        if 'title' not in spec['info']:
            spec['info']['title'] = 'Без названия'

        return spec
    
    def _load_specification(self) -> ResolvingParser:
        """
        Загружает и валидирует спецификацию API с помощью prance.
        
        :return: Объект ResolvingParser с разрешенными ссылками.
        """
        try:
            spec = self._load_spec()
            fixed_spec = self._fix_spec(spec)

            parser = ResolvingParser(spec_string=yaml.dump(fixed_spec))
            
            # Проверяем, что спецификация валидна
            if not parser.specification:
                raise SpecificationParserEmptyError
            
            return parser
        
        except Exception as error:
            raise SpecificationParserErrorParse from error

    # def parse_specification(self, method_name: str) -> str:
    #     """
    #     Парсит спецификацию API и формирует текстовое описание.
        
    #     :return: Описание спецификации в текстовом формате.
    #     """
    #     spec_data = self.parser.specification
    #     info = spec_data.get("info", {})
    #     title = info.get("title", "Без названия")
    #     description = info.get("description", "")
    #     paths = spec_data.get("paths", {})

    #     paths_description = paths.get(method_name, {})
        
    #     # paths_text = "\n".join(paths_description)
    #     return f"Титул: {title}\nОписание: {description}\n\nРучка:\n{paths_description}"
    
    def has_endpoint(self, path: str, http_method: str) -> bool:
        """
        Проверяет, есть ли в спецификации указанный эндпоинт
        (путь + HTTP-метод).
        
        :param path: API-путь, например "/pets"
        :param http_method: HTTP-метод, например "get", "post", "put"
        :return: True, если эндпоинт существует
        """
        spec_data = self.parser.specification
        paths = spec_data.get("paths", {})

        path_item = paths.get(path)   # словарь { method: {описание} }
        if not path_item:
            return False

        # проверяем именно нижний регистр, т.к. OpenAPI использует методы в lowercase
        return http_method.lower() in path_item.keys()
    
    def get_endpoint_spec(self, path: str, http_method: str) -> dict:
        """
        Возвращает описание эндпоинта (или пустой словарь, если его нет).
        """
        spec_data = self.parser.specification
        return spec_data.get("paths", {}).get(path, {}).get(http_method.lower(), {})
