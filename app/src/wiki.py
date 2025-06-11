from atlassian import Confluence

from bs4 import BeautifulSoup
import re
# import os
from urllib.parse import urlparse

from src.text_constants import * 

class WikiClient:
    def __init__(self, token):
        """
        Инициализация клиента для работы с Confluence.
        
        :param token: Токен доступа к Confluence
        """
        self.token = token
        self.confluence = Confluence(
            url=URL_WIKI,
            token=self.token
        )

    def is_wiki_url(self, text: str) -> bool:
        """Проверяет, является ли введённый текст ссылкой на страницу Вики."""
        parsed = self._parse_url(text)
        return "confluence" in parsed.netloc or "wiki" in parsed.netloc

    def _parse_url(self, url: str):
        """Парсит URL и возвращает объект urlparse."""
        return urlparse(url)

    # def extract_page_id_from_url(self, url: str) -> str:
    #     """Извлекает ID страницы из URL."""
    #     parsed = self._parse_url(url)
    #     path_parts = parsed.path.split('/')
    #     for part in path_parts:
    #         if part.isdigit():
    #             return part
    #     return url  # Если ID не найден, вернём исходный URL
    
    def extract_page_id(self, url):
    # Используем регулярное выражение для поиска pageId
    
        match = re.search(PATTER_PAGE_ID, url)
        if match:
            return match.group(1)
        else:
            return ERROR_EXTRACT_LINK_WIKI

    def get_wiki_page(self, page_id: str) -> dict:
        """Получает данные страницы из Confluence по её ID."""
        try:
            page = self.confluence.get_page_by_id(page_id, expand='body.storage')
            return page
        except Exception as e:
            raise RuntimeError(f"{ERROR_GET_DATA_PAGE}{str(e)}")

    def extract_table_content(self, html_content: str) -> str:
        """Извлекает содержимое таблиц из HTML-кода и формирует строку."""
        parsed_html = BeautifulSoup(html_content, 'html.parser')
        test_str = KEY_EMPTY_KEY

        def extract_text(selector):
            elements = parsed_html.select(selector)
            if elements:
                return KEY_FOR_SPACE.join([e.get_text(strip=True) for e in elements])
            return KEY_EMPTY_KEY

        # Селекторы для поиска нужных ячеек по заголовкам
        test_str += extract_text(SELECTOR_STR_PREDUSLOVIE) + KEY_FOR_SPACE
        test_str += extract_text(SELECTOR_STR_MAIN_USLOVIE) + KEY_FOR_SPACE
        test_str += extract_text(SELECTOR_STR_ALT_USLOVIE) + KEY_FOR_SPACE
        test_str += extract_text(SELECTOR_STR_SCENARIO) + KEY_FOR_SPACE
        test_str += extract_text(SELECTOR_STR_POSTUSLOVIE) + KEY_FOR_SPACE

        # Если не найдены нужные разделы и заголовок содержит "ТИМ" или "US"
        if (NOT_HEADERS_TIM in self.page_title and test_str.strip() == KEY_EMPTY_KEY) or \
            (NOT_HEADERS_US in self.page_title and test_str.strip() == KEY_EMPTY_KEY):
            text = parsed_html.get_text(separator=KEY_FOR_SPACE, strip=True)
            test_str = self.prepare_string(text)

        return test_str.strip()

    def prepare_string(self, text: str) -> str:
        """Очищает и готовит текст к использованию."""
        return re.sub(r'\s+', KEY_FOR_SPACE, text).strip()

    def get_wiki_scenario(self, page_id: str) -> str:
        """
        Получает сценарий из Confluence по ID страницы.
        
        :param page_id: ID страницы
        :return: Строка с сценарием
        """
        separator = page_id.split('=', 1)
        page_id = separator[1] if len(separator) > 1 else page_id

        try:
            page = self.get_wiki_page(page_id)
            self.page_title = page.get(KEY_TITLE, KEY_EMPTY_KEY)

            html_content = page['body']['storage']['value']
            scenario = self.extract_table_content(html_content)
            return scenario
        except Exception as e:
            raise RuntimeError(f"{ERROR_WIKI_GET_SCENARIO}{str(e)}")

