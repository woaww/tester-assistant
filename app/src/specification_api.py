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
        # if not isinstance(spec, dict):
        #     raise SpecificationParserErrorRead #from error

        # if 'openapi' not in spec and 'swagger' not in spec:
        #     spec['openapi'] = '3.0.0'
        
        has_openapi = 'openapi' in spec
        has_swagger = 'swagger' in spec

        # Если нет ни openapi, ни swagger — добавляем 3.0.3
        if not has_openapi and not has_swagger:
            spec['openapi'] = '3.0.0'
        elif has_openapi:
            version = spec['openapi']
            # Если версия начинается с 3.1 или другой неподдерживаемой — понижаем до 3.0.3
            if version.startswith('3.1.') or version == '3.1.0':
                spec['openapi'] = '3.0.0'
            # Можно также обработать другие 3.x, если нужно
            elif not version.startswith('3.0.'):
                # На всякий случай — всё, что не 3.0.x, тоже понижаем
                spec['openapi'] = '3.0.0'

        # if 'tags' not in spec:
        #     spec['tags'] = 'None' #[]

        if 'info' not in spec:
            spec['info'] = {}

        if 'version' not in spec['info']:
            spec['info']['version'] = '1.0.0'

        if 'title' not in spec['info']:
            spec['info']['title'] = 'Без названия'
        
        if 'description' not in spec['info']:
            spec['info']['description'] = 'Без описания'

        return spec
    

#     import yaml
# from typing import Any, Dict, Optional
# from prance import ResolvingParser
# from prance.util import resolution  # для обработки ошибок


    def _load_specification(self):
        """
        Загружает спецификацию API:
        - Сначала пытается разрешить все $ref с помощью prance.
        - При ошибке возвращает исходную спецификацию как словарь (фоллбэк),
        где можно вручную работать с $ref или извлекать данные по ключам.

        :return: Полностью резолвнутая спецификация ИЛИ исходная структура со всеми данными.
                В любом случае — словарь, пригодный для анализа.
        """
        spec = self._load_spec()
        fixed_spec = self._fix_spec(spec)

        # === Попытка 1: использовать prance для полного резолвинга ===
        try:
            parser = ResolvingParser(
                spec_string=yaml.dump(fixed_spec),
                # recursion_limit=50,
                # strict_mode=False,
            )
            if parser.specification:
                return parser #.specification  # ← полностью разрешённая спецификация
            else:
                raise ValueError("Prance parsed specification is empty")
        except Exception as e:
            print(f"⚠️ Prance failed to resolve specification: {e}. Falling back to raw dict.")

        # === Фоллбэк: возвращаем fixed_spec как есть (без разворачивания $ref) ===
        # Пользователь сможет сам извлекать данные, например:
        #   spec['paths']['/users/{id}']['get']['responses']['200']['description']
        #
        # Важно: $ref остаются как строки, но структура доступна.
        return fixed_spec

    # def _load_specification(self) -> ResolvingParser:
    #     """
    #     Загружает и валидирует спецификацию API с помощью prance.
        
    #     :return: Объект ResolvingParser с разрешенными ссылками.
    #     """
    #     # try:
    #     spec = self._load_spec()
    #     fixed_spec = self._fix_spec(spec)
    #     print(fixed_spec)

    #     parser = ResolvingParser(spec_string=yaml.dump(fixed_spec))


    #     # Проверяем, что спецификация валидна
    #     if not parser.specification:
    #         raise SpecificationParserEmptyError
        
    #     return parser
        
    #     # except Exception as error:
    #     #     raise SpecificationParserErrorParse from error
    
    # def has_endpoint(self, path: str, http_method: str) -> bool:
    #     """
    #     Проверяет, есть ли в спецификации указанный эндпоинт
    #     (путь + HTTP-метод).
        
    #     :param path: API-путь, например "/pets"
    #     :param http_method: HTTP-метод, например "get", "post", "put"
    #     :return: True, если эндпоинт существует
    #     """
    #     if self.parser.specification:
    #         spec_data = self.parser.specification
    #     else: 
    #         spec_data = self.parser
    #     paths = spec_data.get("paths", {})

    #     path_item = paths.get(path)   # словарь { method: {описание} }
    #     if not path_item:
    #         return False

    #     # проверяем именно нижний регистр, т.к. OpenAPI использует методы в lowercase
    #     return http_method.lower() in path_item.keys()
    
    # def get_endpoint_spec(self, path: str, http_method: str) -> dict:
    #     """
    #     Возвращает описание эндпоинта (или пустой словарь, если его нет).
    #     """
    #     spec_data = self.parser.specification
    #     return spec_data.get("paths", {}).get(path, {}).get(http_method.lower(), {})


    def has_endpoint(self, path: str, http_method: str) -> bool:
        """
        Проверяет, есть ли в спецификации указанный эндпоинт (путь + HTTP-метод).
        
        :param path: API-путь, например "/pets"
        :param http_method: HTTP-метод, например "get", "post", "put"
        :return: True, если эндпоинт существует
        """
        spec_data = self._get_spec_data()
        paths = spec_data.get("paths", {})

        path_item = paths.get(path)
        if not path_item:
            return False

        return http_method.lower() in path_item


    def get_endpoint_spec(self, path: str, http_method: str) -> dict:
        """
        Возвращает описание эндпоинта (или пустой словарь, если его нет).
        """
        spec_data = self._get_spec_data()
        return spec_data.get("paths", {}).get(path, {}).get(http_method.lower(), {})


    def _get_spec_data(self) -> dict:
        """
        Возвращает словарь со спецификацией:
        - Если parser — это ResolvingParser с specification — возвращает parser.specification
        - Иначе — возвращает parser как словарь (случай фоллбэка)
        """
        try:
            # Если parser — объект prance.ResolvingParser и у него есть specification
            if hasattr(self.parser, 'specification') and self.parser.specification:
                return self.parser.specification
        except Exception:
            pass  # на всякий случай

        # Фоллбэк: считаем, что self.parser — это уже словарь (fixed_spec)
        return getattr(self.parser, 'specification', self.parser)  # подстраховка
