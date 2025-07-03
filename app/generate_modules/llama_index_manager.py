# from llama_index.core import VectorStoreIndex, Document
# from llama_index.core.storage import StorageContext
# from llama_index.core.storage.docstore import SimpleDocumentStore
# from llama_index.core.storage.index_store import SimpleIndexStore
# from llama_index.core.vector_stores import SimpleVectorStore

# class LlamaIndexManager:
#     def __init__(self):
#         """
#         Инициализация менеджера для работы с LlamaIndex в оперативной памяти.
#         """
#         self.storage_context = self._create_storage_context()
#         self.index = self._load_or_create_index()

#     def _create_storage_context(self):
#         """
#         Создает контекст хранения данных в оперативной памяти.
#         """
#         # Создаем простые хранилища для документов, индексов и векторов
#         docstore = SimpleDocumentStore()
#         index_store = SimpleIndexStore()
#         vector_store = SimpleVectorStore()

#         # Создаем контекст хранения
#         storage_context = StorageContext.from_defaults(
#             docstore=docstore,
#             index_store=index_store,
#             vector_store=vector_store
#         )
#         return storage_context

#     def _load_or_create_index(self):
#         """
#         Создает новый индекс в оперативной памяти.
#         """
#         # Начальный документ для индекса
#         documents = [Document(text="Начало работы. Нет сгенерированных тест-кейсов.")]
#         index = VectorStoreIndex.from_documents(documents, storage_context=self.storage_context)
#         return index

#     def add_document(self, text: str, test_type: str):
#         """
#         Добавляет новый документ в индекс с меткой типа тест-кейса.
        
#         :param text: Текст документа для добавления.
#         :param test_type: Тип тест-кейса ("wiki" или "api").
#         """
#         # Добавляем метку типа тест-кейса к тексту
#         labeled_text = f"[{test_type.upper()}] {text}"
#         document = Document(text=labeled_text)
#         self.index.insert(document)

#     def query_index(self, query: str, test_type: str = None) -> str:
#         """
#         Выполняет запрос к индексу с возможностью фильтрации по типу тест-кейса.
        
#         :param query: Запрос для поиска в индексе.
#         :param test_type: Тип тест-кейса для фильтрации ("wiki" или "api").
#         :return: Результат запроса.
#         """
#         if test_type:
#             query = f"[{test_type.upper()}] {query}"  # Добавляем метку типа к запросу
#         response = self.index.as_query_engine().query(query)
#         return response.response

#     def summarize_index(self, test_type: str = None) -> str:
#         """
#         Создает сводку всех документов в индексе с возможностью фильтрации по типу тест-кейса.
        
#         :param test_type: Тип тест-кейса для фильтрации ("wiki" или "api").
#         :return: Сводка содержимого индекса.
#         """
#         summary_query = "Предоставь краткую сводку всех тест-кейсов."
#         if test_type:
#             summary_query = f"[{test_type.upper()}] {summary_query}"  # Добавляем метку типа к запросу
#         response = self.index.as_query_engine().query(summary_query)
#         return response.response