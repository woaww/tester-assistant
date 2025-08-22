# app/testit_client.py
import re
import requests
from typing import List, Optional, Tuple
from testit_api_client import ApiClient, ApiException
from testit_api_client.api import work_items_api, sections_api
from testit_api_client.model.work_item_entity_types import WorkItemEntityTypes
from testit_api_client.model.work_item_states import WorkItemStates
from testit_api_client.model.work_item_priority_model import WorkItemPriorityModel
from testit_api_client.model.create_work_item_request import CreateWorkItemRequest
from testit_api_client.model.create_section_request import CreateSectionRequest
from testit_api_client.configuration import Configuration

from .models import TestCaseCreateModel, SectionCreateModel, ProjectSearchResponse, StepModel
from .logger import log_function_call, LOGGER
from .text_constants import UtilitsParsing, TESTIT_TOKEN


class TestItClient:
    def __init__(self):
        self.token = TESTIT_TOKEN
        self.configuration = Configuration(host=UtilitsParsing.URL_TESTIT)
        self.configuration.verify_ssl = False
        self.base_url = UtilitsParsing.URL_TESTIT

    @log_function_call(allowed_kwargs=["project_id", "section_id", "name", "steps"])
    def create_testcase(self, case_data: TestCaseCreateModel) -> str:
        """
        Создаёт тест-кейс с шагами, предусловиями и описанием.
        :param case_data: модель с данными
        :return: global_id созданного кейса
        """
        try:
            with ApiClient(
                self.configuration,
                header_name='Authorization',
                header_value='PrivateToken ' + self.token
            ) as api_client:
                api = work_items_api.WorkItemsApi(api_client)

                # Формируем шаги
                steps_payload = [
                    {"action": step["action"], "expected": step["expected"]}
                    for step in case_data.steps
                ]

                precondition_steps_payload = [
                    {"action": step["action"], "expected": step["expected"]}
                    for step in case_data.precondition_steps
                ]

                # Используем expected_result как описание
                description = case_data.expected_result or ""

                payload = CreateWorkItemRequest(
                    entity_type_name=WorkItemEntityTypes("TestCases"),
                    project_id=case_data.project_id,
                    section_id=case_data.section_id,
                    name=case_data.name,
                    priority=WorkItemPriorityModel(case_data.priority),
                    state=WorkItemStates(case_data.state),
                    steps=steps_payload,
                    precondition_steps=precondition_steps_payload,
                    postcondition_steps=case_data.postcondition_steps,
                    description=description,
                    duration=case_data.duration if case_data.duration is not None else 60,
                    attributes=case_data.attributes or {},
                    tags=case_data.tags or [],
                    links=case_data.links or []
                )

                response = api.create_work_item(
                    create_work_item_request=payload)
                return response.global_id

        except ApiException as e:
            LOGGER.error(
                f"API error creating test case '{case_data.name}': {e}")
            raise
        except Exception as e:
            LOGGER.error(
                f"Unexpected error creating test case '{case_data.name}': {e}")
            raise

    @log_function_call(allowed_kwargs=["project_id", "parent_id", "name"])
    def create_section(self, section_data: SectionCreateModel) -> str:
        """Создаёт секцию."""
        try:
            with ApiClient(
                self.configuration,
                header_name='Authorization',
                header_value='PrivateToken ' + self.token
            ) as api_client:
                api = sections_api.SectionsApi(api_client)
                payload = CreateSectionRequest(
                    project_id=section_data.project_id,
                    parent_id=section_data.parent_id,
                    name=section_data.name,
                    attachments=[]
                )
                response = api.create_section(create_section_request=payload)
                return response.id
        except ApiException as e:
            LOGGER.error(
                f"API error creating section '{section_data.name}': {e}")
            raise

    def _ensure_step_order(self, raw_steps: List[str]) -> List[str]:
        """Сортирует шаги по номеру, если они пронумерованы."""
        numbered = []
        for step in raw_steps:
            match = re.match(r'^(\d+)\.\s*(.*)', step.strip())
            if match:
                num = int(match.group(1))
                text = match.group(2).strip()
            else:
                num = float('inf')
                text = step.strip()
            numbered.append((num, text))
        numbered.sort()
        return [text for _, text in numbered]

    @log_function_call(allowed_kwargs=["tc"])
    def parse_case(self, tc: str) -> List[TestCaseCreateModel]:
        cases = []

        tc = tc.strip()

        tokens = re.split(r'\n-{3,}\n', tc)
        tokens = [t.strip() for t in tokens if t.strip()]

        if len(tokens) == 1:
            tokens = re.split(r'\n\s*\d+\.\s+', tc)
            tokens = [t.strip() for t in tokens if t.strip()]
            # Удаляем нумерацию из начала первого токена
            if tokens:
                tokens[0] = re.sub(r'^\s*\d+\.\s*', '', tokens[0])

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            case_data = {"name": "", "preconditions": [],
                         "steps": [], "expected": ""}

            # 1. Название
            first_line = token.split('\n')[0].strip()
            name_match = re.search(r'^\s*\d+\.\s*\*\*(.*?)\*\*[:\s]', 
                                   first_line, 
                                   re.IGNORECASE)
            if name_match:
                case_data["name"] = name_match.group(1).strip()
            else:
                # Вариант 2: просто текст после номера
                clean_name = re.sub(r'^\s*\d+\.\s*', '', first_line)  # удаляем 1.
                clean_name = re.sub(r'\*\*.*?\*\*', '', clean_name)   # удаляем **...**
                clean_name = re.sub(r'\s*[:\s].*$', '', clean_name)   # удаляем после :
                case_data["name"] = clean_name.strip() or "Unnamed Test Case"

            body = re.sub(r'\*\*', '', token)

            # 2. Предусловия
            precond_match = re.search(
                r'Предусловия[:\s]*(.+?)(?=\s*Шаги|$)',
                body, 
                re.IGNORECASE | re.DOTALL)
            
            if precond_match:
                precond_text = precond_match.group(1).strip()
                sentences = re.split(r'(?<=[.!?])\s+', precond_text)
                case_data["preconditions"] = [s.strip()
                                              for s in sentences if s.strip()]

            # 3. Шаги
            steps_match = re.search(
                r'Шаги[:\s]*(.+?)(?=\s*Ожидаемый результат|$)',
                body, 
                re.IGNORECASE | re.DOTALL)
            
            if steps_match:
                steps_text = steps_match.group(1).strip()
                step_lines = re.findall(r'\d+\.\s*(.+?)(?=\n\s*\d+\.|\Z)', 
                                        steps_text, 
                                        re.DOTALL)
                case_data["steps"] = [line.strip() for line in step_lines if line.strip()]

            else:
                action_match = re.search(
                    r'(Выполнить [^.\n]+?\.?)', 
                    body, 
                    re.IGNORECASE)
                
                if action_match:
                    case_data["steps"] = [action_match.group(1).strip()]

            # 4. Ожидаемый результат
            expected_match = re.search(
                r'Ожидаемый результат[:\s]*(.+?)(?=\n|$)', 
                body, 
                re.IGNORECASE | re.DOTALL)
            
            if expected_match:
                expected_text = expected_match.group(1).strip()
                expected_text = re.sub(r'\s+', ' ', expected_text)
                case_data["expected"] = expected_text.strip(' .')

            if not case_data["steps"]:
                LOGGER.warning(f"No steps in test case: {case_data['name']}")
                continue

            precondition_steps = [
                {"action": text, "expected": None}
                for text in case_data["preconditions"]
            ]

            steps_models = [StepModel(action=step, 
                                      expected=case_data["expected"]).model_dump() for step in case_data["steps"]]

            test_case_model = TestCaseCreateModel(
                project_id="",
                section_id="",
                name=case_data["name"],
                steps=steps_models,
                precondition_steps=precondition_steps,
                postcondition_steps=[],
                # precondition_steps=case_data["preconditions"],
                expected_result=case_data["expected"]
            )
            cases.append(test_case_model)

        return cases

    # @log_function_call(allowed_kwargs=["case_name"])
    # def send_testit_func(
    #     self,
    #     testCases: str,
    #     # testit_project: str,
    #     # testit_section: str,
    #     case_name: str
    # ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    #     """
    #     Основной метод: создаёт секцию и тест-кейсы.
    #     :return: (project_id, global_project_id, new_section_id)
    #     """
    #     try:
    #         # self.get_project_id(testit_project)
    #         project_id = UtilitsParsing.PROJECT_ID
    #         # self.get_global_project_id(testit_project)
    #         global_project_id = UtilitsParsing.PROJECT_ID
    #         testit_section = UtilitsParsing.SECTION_TESTIT

    #         new_section = self.create_section(SectionCreateModel(
    #             project_id=project_id,
    #             parent_id=testit_section,
    #             name=case_name
    #         ))

    #         parsed_cases = self.parse_case(testCases)
    #         for case in parsed_cases:
    #             case.project_id = project_id
    #             case.section_id = new_section
    #             try:
    #                 self.create_testcase(case)
    #             except Exception as e:
    #                 LOGGER.error(
    #                     f"Failed to create test case '{case.name}': {e}")
    #                 continue  # Продолжаем, не падаем

    #         return project_id, global_project_id, new_section

    #     except Exception as e:
    #         LOGGER.error(f"Error in send_testit_func: {e}")
    #         return "", "", ""

    # def _search_project(self, search_value: str) -> Optional[ProjectSearchResponse]:
    #     url = f"{self.base_url}/api/v2/projects/search"
    #     headers = {
    #         "Accept": "application/json",
    #         "Content-Type": "application/json; charset=utf-8",
    #         "Authorization": f"PrivateToken {self.token}"
    #     }
    #     try:
    #         response = requests.post(url, json={"name": search_value}, headers=headers, verify=False)
    #         response.raise_for_status()
    #         data = response.json()
    #         if data:
    #             return ProjectSearchResponse(**data[0])
    #         return None
    #     except Exception as e:
    #         LOGGER.error(f"Failed to search project '{search_value}': {e}")
    #         return None

    # @log_function_call(allowed_kwargs=["search_value"])
    # def get_project_id(self, search_value: str) -> Optional[str]:
    #     res = self._search_project(search_value)
    #     return res.id if res else None

    # @log_function_call(allowed_kwargs=["search_value"])
    # def get_global_project_id(self, search_value: str) -> Optional[str]:
    #     res = self._search_project(search_value)
    #     return res.globalId if res else None
