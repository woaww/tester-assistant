from jira import JIRA
from urllib.parse import urlparse
from src.text_constants import UtilitsParsing, Keys, LoggerMsg, JIRA_TOKEN

class JiraClient:

    def __init__(self):
        '''
        :param token:
        Инициализируем jira
        '''
        self.jira = JIRA(server=UtilitsParsing.URL_JIRA, token_auth=JIRA_TOKEN)

    def _parse_url(self, url: str):
        """Парсит URL и возвращает объект urlparse."""
        return urlparse(url)
    
    def extract_ticket_id(self, url: str) -> str:
        """
        Извлекает идентификатор тикета из URL Jira.
        
        :param url: Ссылка на тикет
        :return: ID тикета
        """
        parsed = self._parse_url(url)
        return parsed.path.strip("/").split("/")[-1]

    def get_issue_summary(self, ticket_id: str) -> str:
        '''
        :param ticket:
        :return: issue_summary
        Получаем содержимое описания тикета по переданному идентификатору(ticket)
        '''
        try:
            issue = self.jira.issue(ticket_id)
            return issue.fields.summary or Keys.EMPTY
        except Exception as e:
            raise RuntimeError(f"{LoggerMsg.ERROR_JIRA_GET_SUMMARY}{str(e)}")

    def get_issue_description(self, ticket_id: str) -> str:
        '''
        :param ticket:
        :return: issue_description
        Получаем название тикета по переданному идентификатору(ticket)
        '''
        try:
            issue = self.jira.issue(ticket_id)
            return issue.fields.description or Keys.EMPTY
        except Exception as e:
            raise RuntimeError(f"{LoggerMsg.ERROR_JIRA_GET_DESCRIPTION}{str(e)}")

