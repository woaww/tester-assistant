from atlassian import Confluence
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from src.text_constants import (UtilitsParsing, Keys, LoggerMsg)
from src.text_constants import WIKI_TOKEN


class WikiClient:    
    """
    Клиент для работы с Atlassian Confluence.
    Парсит страницы, извлекает текст и таблицы в структурированном виде.
    """

    def __init__(self):
        """
        Инициализирует клиент Confluence.
        Данные аутентификации берутся из переменных окружения или констант.
        """

        self.confluence = Confluence(
            url=UtilitsParsing.URL_WIKI, token=WIKI_TOKEN)

    def is_wiki_url(self, text: str) -> bool:
        """Проверяет, является ли введённый текст ссылкой на страницу Вики."""
        parsed = self._parse_url(text)
        return "confluence" in parsed.netloc or "wiki" in parsed.netloc

    def _parse_url(self, url: str):
        """Парсит URL и возвращает объект urlparse."""
        return urlparse(url)
    
    def extract_page_id(self, url):
    # Используем регулярное выражение для поиска pageId
    
        match = re.search(UtilitsParsing.PATTERN_PAGE_ID, url)
        if match:
            return match.group(1)
        else:
            return LoggerMsg.ERROR_EXTRACT_LINK_WIKI

    def get_wiki_page(self, page_id: str) -> dict:
        """Получает данные страницы из Confluence по её ID."""
        try:
            page = self.confluence.get_page_by_id(page_id, expand='body.storage')
            return page
        except Exception as e:
            raise RuntimeError(f"{LoggerMsg.ERROR_GET_DATA_PAGE}{str(e)}")

    def extract_table_content(self, html_content: str) -> str:
        """Извлекает содержимое таблиц из HTML-кода и формирует строку."""
        parsed_html = BeautifulSoup(html_content, 'html.parser')
        test_str = Keys.EMPTY

        def extract_text(selector):
            elements = parsed_html.select(selector)
            if elements:
                return Keys.SPACE.join([e.get_text(strip=True) for e in elements])
            return Keys.EMPTY

        # Селекторы для поиска нужных ячеек по заголовкам
        test_str += extract_text(UtilitsParsing.SELECTOR_PREDUSLOVIE) + Keys.SPACE
        test_str += extract_text(UtilitsParsing.SELECTOR_MAIN_USLOVIE) + Keys.SPACE
        test_str += extract_text(UtilitsParsing.SELECTOR_ALT_USLOVIE) + Keys.SPACE
        test_str += extract_text(UtilitsParsing.SELECTOR_SCENARIO) + Keys.SPACE
        test_str += extract_text(UtilitsParsing.SELECTOR_POSTUSLOVIE) + Keys.SPACE

        # Если не найдены нужные разделы и заголовок содержит "ТИМ" или "US"
        if (UtilitsParsing.NOT_HEADERS_TIM in self.page_title and test_str.strip() == Keys.EMPTY) or \
            (UtilitsParsing.NOT_HEADERS_US in self.page_title and test_str.strip() == Keys.EMPTY):
            text = parsed_html.get_text(separator=Keys.SPACE, strip=True)
            test_str = self.prepare_string(text)

        return test_str.strip()

    def prepare_string(self, text: str) -> str:
        """Очищает и готовит текст к использованию."""
        return re.sub(r'\s+', Keys.SPACE, text).strip()

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
            self.page_title = page.get(Keys.TITLE, Keys.EMPTY)

            html_content = page['body']['storage']['value']
            scenario = self.extract_table_content(html_content)
            return scenario
        except Exception as e:
            raise RuntimeError(f"{LoggerMsg.ERROR_WIKI_GET_SCENARIO}{str(e)}")

