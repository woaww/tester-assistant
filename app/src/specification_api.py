# import yaml
# import requests
from prance import ResolvingParser

class SpecificationParser:
    def __init__(self, spec_url_or_path: str):
        self.spec_url_or_path = spec_url_or_path
        self.parser = self._load_specification()

    def _load_specification(self) -> ResolvingParser:
        """
        Загружает и валидирует спецификацию API с помощью prance.
        
        :return: Объект ResolvingParser с разрешенными ссылками.
        """
        try:
            if self.spec_url_or_path.startswith("http"):
                # Загрузка из URL
                parser = ResolvingParser(self.spec_url_or_path, backend='openapi-spec-validator')
            else:
                # Загрузка из файла
                parser = ResolvingParser(self.spec_url_or_path, backend='openapi-spec-validator')
            
            # Проверяем, что спецификация валидна
            if not parser.specification:
                raise ValueError("Спецификация не загружена или пуста.")
            
            return parser
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке или валидации спецификации: {e}")

    def parse_specification(self) -> str:
        """
        Парсит спецификацию API и формирует текстовое описание.
        
        :return: Описание спецификации в текстовом формате.
        """
        spec_data = self.parser.specification
        info = spec_data.get("info", {})
        title = info.get("title", "Без названия")
        description = info.get("description", "")
        paths = spec_data.get("paths", {})

        # Формируем описание ручек
        paths_description = []
        for path, methods in paths.items():
            for method, details in methods.items():
                summary = details.get("summary", "Нет описания")
                paths_description.append(f"{method.upper()} {path}: {summary}")
        
        paths_text = "\n".join(paths_description)
        return f"Титул: {title}\nОписание: {description}\n\nРучки:\n{paths_text}"

    def get_wiki_explanation(self) -> str:
        """
        Получает дополнительное пояснение из Википедии.
        
        :return: Пояснение из Википедии.
        """
        # Здесь можно добавить логику для получения данных из Википедии
        return "Дополнительное пояснение из Википедии."