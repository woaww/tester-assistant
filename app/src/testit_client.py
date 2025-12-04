# app/testit_client.py
import re
import requests
from typing import List, Optional, Tuple
from testit_api_client import ApiClient, ApiException
# from testit_api_client import ApiClient, ApiException
# from testit_api_client.api.sections_api import SectionsApi
from testit_api_client.api import work_items_api, sections_api
from testit_api_client.model.work_item_entity_type_api_model import WorkItemEntityTypeApiModel
from testit_api_client.model.tag_model import TagModel
from testit_api_client.model.work_item_state_api_model import WorkItemStateApiModel
from testit_api_client.model.work_item_priority_api_model import WorkItemPriorityApiModel
# from testit_api_client.model.create_work_item_api_model import CreateWorkItemApiModel
from testit_api_client.model.work_item_api_result import WorkItemApiResult
from testit_api_client.model.api_v2_work_items_post_request import ApiV2WorkItemsPostRequest
from testit_api_client.model.create_section_request import CreateSectionRequest
from testit_api_client.api import project_sections_api
from testit_api_client.configuration import Configuration
from testit_api_client.api.projects_api import ProjectsApi
from .models import (TestCaseCreateModel, SectionCreateModel, 
                     ProjectSearchResponse, StepModel)
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

                payload = ApiV2WorkItemsPostRequest( #CreateWorkItemApiModel
                    entity_type_name=WorkItemEntityTypeApiModel("TestCases"),
                    project_id=case_data.project_id,
                    section_id=case_data.section_id,
                    name=case_data.name,
                    priority=WorkItemPriorityApiModel(case_data.priority),
                    state=WorkItemStateApiModel(case_data.state),
                    steps=steps_payload,
                    precondition_steps=precondition_steps_payload,
                    postcondition_steps=case_data.postcondition_steps,
                    description=description, 
                    duration=case_data.duration if case_data.duration is not None else 60, 
                    attributes=case_data.attributes or {},
                    tags=[TagModel(name="ai-assistant")], 
                    links=case_data.links or [] 
                )

                response = api.api_v2_work_items_post(
                    api_v2_work_items_post_request=payload)  #create_work_item_request
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

        # Разделение по пустым строкам между кейсами (одна или более пустых строк)
        # Предполагается: каждый кейс отделён хотя бы одной пустой строкой
        tokens = re.split(r'\n\s*\n+', tc.strip())
        tokens = [t.strip() for t in tokens if t.strip()]

        # Если разделения не было — попробуем разбить по началу нового кейса: **1. **Название...
        if len(tokens) == 1:
            # Разделяем по шаблону: **<число>. **Название...
            tokens = re.split(r'\n(?=\*\*\d+\. \*\*)', tc.strip())
            tokens = [t.strip() for t in tokens if t.strip()]

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            case_data = {
                "name": "Unnamed Test Case",
                "preconditions": [],
                "steps": [],  # список строк-действий
                "expected": ""
            }

            # --- 1. Извлечение названия ---
            name_match = re.search(
                r'^\s*\*\*(\d+\.)\s*\*\*Название тест-кейса:\*\*\s*(.+?)(?:\n|$)',
                token,
                re.IGNORECASE | re.DOTALL
            )
            if name_match:
                case_data["name"] = name_match.group(2).strip()
            else:
                # Резервный вариант: найти первую строку и вытащить название
                first_line = token.split('\n')[0].strip()
                clean_name = re.sub(r'^\s*\*\*\d+\.\s*\*\*', '', first_line)
                clean_name = re.sub(r'Название.*?:\s*', '', clean_name, flags=re.IGNORECASE)
                clean_name = re.sub(r'\*\*', '', clean_name)
                case_data["name"] = clean_name.strip() or "Unnamed Test Case"

            # Удаляем форматирование ** для упрощения дальнейшего парсинга
            clean_token = re.sub(r'\*\*', '', token)

            # --- 2. Предусловия ---
            precond_match = re.search(
                r'Предусловия[:\s]*(.+?)(?=Шаги[:\s]*$|Шаги[:\s]*\n|\Z)',
                clean_token,
                re.IGNORECASE | re.DOTALL
            )
            if precond_match:
                precond_text = precond_match.group(1).strip()
                sentences = re.split(r'(?<=[.!?])\s+', precond_text)
                case_data["preconditions"] = [s.strip() for s in sentences if s.strip()]

            # --- 3. Шаги ---
            steps_match = re.search(
                r'Шаги[:\s]*\n((?:\s*\d+\..*?(?:\n|$))+)',
                clean_token,
                re.IGNORECASE | re.DOTALL
            )
            if steps_match:
                steps_block = steps_match.group(1).strip()
                # Извлекаем шаги: "1. действие", "2. действие" и т.д.
                step_lines = re.findall(r'\d+\.\s*(.+?)(?=(?:\n\s*\d+\.|\Z))', steps_block, re.DOTALL)
                case_data["steps"] = [re.sub(r'\s+', ' ', line.strip()) for line in step_lines if line.strip()]
            else:
                # Если шагов нет — пропускаем кейс
                LOGGER.warning(f"No steps found in test case: {case_data['name']}")
                continue

            # --- 4. Ожидаемый результат ---
            expected_match = re.search(
                r'Ожидаемый результат[:\s]*(.+?)(?=\n\s*$|\Z)',
                clean_token,
                re.IGNORECASE | re.DOTALL
            )
            if expected_match:
                expected_text = expected_match.group(1).strip()
                expected_text = re.sub(r'\s+', ' ', expected_text)
                case_data["expected"] = expected_text.rstrip('.')
            else:
                case_data["expected"] = "Результат не указан"

            # --- Формирование модели ---
            if not case_data["steps"]:
                LOGGER.warning(f"No steps in test case: {case_data['name']}")
                continue

            # Подготовка precondition_steps
            precondition_steps = [
                {"action": text, "expected": None}
                for text in case_data["preconditions"]
            ]

            # Подготовка шагов: все шаги без expected, кроме последнего
            steps_models = []
            n_steps = len(case_data["steps"])

            for i, step_action in enumerate(case_data["steps"]):
                expected = case_data["expected"] if i == n_steps - 1 else None
                steps_models.append(StepModel(action=step_action, expected=expected).model_dump())

            # Создание тест-кейса
            test_case_model = TestCaseCreateModel(
                project_id="",
                section_id="",
                name=case_data["name"],
                steps=steps_models,
                precondition_steps=precondition_steps,
                postcondition_steps=[],
                expected_result=""  # теперь не используется, т.к. результат в последнем шаге
            )
            cases.append(test_case_model)

        return cases
    
    def get_section_id_by_name(self, section_name: str, project_id: str = UtilitsParsing.PROJECT_ID):
        """
        Находит ID секции по её названию.
        :param project_id: ID проекта
        :param section_name: Название секции (чувствительно к регистру)
        :return: ID секции или None
        """
        try:
            with ApiClient(
                self.configuration,
                header_name='Authorization',
                header_value='PrivateToken ' + self.token
            ) as api_client:
                # Используем Sections API

                sections_api = project_sections_api.ProjectSectionsApi(api_client)
                # sections_api = SectionsApi(api_client)

                # Получаем все секции проекта
                response = sections_api.get_sections_by_project_id(project_id)

                # Рекурсивная функция поиска
                def find_section(sections):
                    for section in sections:
                        if section.name == section_name:
                            return section.id
                        # Рекурсия по подсекциям
                        if hasattr(section, "sub_sections") and section.sub_sections:
                            result = find_section(section.sub_sections)
                            if result:
                                return result
                    return None

                return find_section(response)

        except Exception as e:
            LOGGER.error(f"Error fetching section ID for '{section_name}': {e}")
            raise

    def get_project_id_by_name(self, project_name: str) -> Optional[str]:
        """
        Находит ID проекта по его названию.
        :param project_name: Название проекта (чувствительно к регистру)
        :return: ID проекта или None
        """
        try:
            with ApiClient(
                self.configuration,
                header_name='Authorization',
                header_value='PrivateToken ' + self.token
            ) as api_client:
                
                projects_api = ProjectsApi(api_client)

                # Получаем список всех проектов
                response = projects_api.get_all_projects()

                # Ищем проект по имени
                for project in response:
                    if project.name == project_name:
                        return project.id

                # Если не нашли
                LOGGER.warning(f"Project with name '{project_name}' not found.")
                return None

        except Exception as e:
            LOGGER.error(f"Error fetching project ID for '{project_name}': {e}")
            raise