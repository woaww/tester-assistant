"""
SQLAlchemy модели для системы управления корпоративными данными о локаторах.

Модели:
- Project — проект/веб-приложение (сайт, портал и т.д.)
- Page — конкретная веб-страница в рамках проекта
- LocatorRun — один запуск генерации локаторов
- Locator — сгенерированный локатор для элемента
- Element — snapshot DOM-элемента на момент генерации
- LocatorHistory — история изменений локаторов (версионирование)
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


# ======================== ENUMS ========================


class RunMode(str, enum.Enum):
    """Режим извлечения элементов."""

    BY_SELECTORS = "by_selectors"
    BY_DESCRIPTION = "by_description"
    BY_PARENT = "by_parent"


class LocatorStage(str, enum.Enum):
    """Этап генерации локатора."""

    GENERATED = "generated"
    FIXED = "fixed"


class ChangeReason(str, enum.Enum):
    """Причина изменения локатора."""

    PAGE_UPDATE = "page_update"
    MANUAL = "manual"
    AUTO_FIX = "auto_fix"
    RE_GENERATION = "re_generation"


# ======================== MODELS ========================


class Project(Base):
    """
    Проект/веб-приложение — логическая группировка страниц.

    Пример: "Личный кабинет сотрудника", "Портал поставщиков",
    "Форма авторизации Госуслуги" и т.д.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Связи
    pages: Mapped[list["Page"]] = relationship(
        "Page", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Page(Base):
    """
    Конкретная веб-страница в рамках проекта.

    Хранит URL и метаданные о последнем сканировании.
    """

    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    elements_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Связи
    project: Mapped["Project"] = relationship("Project", back_populates="pages")
    runs: Mapped[list["LocatorRun"]] = relationship(
        "LocatorRun", back_populates="page", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Page(id={self.id}, url='{self.url}')>"


class LocatorRun(Base):
    """
    Один запуск генерации локаторов.

    Хранит конфигурацию запуска, метрики, тайминги.
    """

    __tablename__ = "locator_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_mode: Mapped[RunMode] = mapped_column(
        Enum(RunMode), nullable=False, comment="Режим извлечения элементов"
    )
    llm_config: Mapped[dict] = mapped_column(
        JSONB, nullable=True, comment="Конфигурация LLM (model, temperature, и т.д.)"
    )
    auth_config: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Конфигурация авторизации"
    )
    metrics: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Метрики: accuracy, fix_rate, correctness",
    )
    timings: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Тайминги каждого этапа"
    )
    total_elements: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_locators: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_locators: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fixed_locators: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    artifacts_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Путь к файлам артефактов (скриншоты, raw LLM)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи
    page: Mapped["Page"] = relationship("Page", back_populates="runs")
    locators: Mapped[list["Locator"]] = relationship(
        "Locator", back_populates="run", cascade="all, delete-orphan"
    )
    elements: Mapped[list["Element"]] = relationship(
        "Element", back_populates="run", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LocatorRun(id={self.id}, page_id={self.page_id}, mode={self.run_mode.value})>"


class Locator(Base):
    """
    Сгенерированный локатор для одного элемента.

    Хранит XPath, описание, результат валидации, Selenide-элемент.
    """

    __tablename__ = "locators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("locator_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    element_snapshot_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Ссылка на element_snapshot для связи"
    )
    xpath: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    stage: Mapped[LocatorStage] = mapped_column(
        Enum(LocatorStage), nullable=False, comment="Этап: generated или fixed"
    )
    validation: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Результат валидации: exists, count"
    )
    selenide_element: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Java Selenide PageObject поле"
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="true если count == 1"
    )
    version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="Версия локатора (для отслеживания изменений)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи
    run: Mapped["LocatorRun"] = relationship("LocatorRun", back_populates="locators")
    history_entries: Mapped[list["LocatorHistory"]] = relationship(
        "LocatorHistory", back_populates="locator", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Locator(id={self.id}, xpath='{self.xpath[:50]}...', stage={self.stage.value})>"


class Element(Base):
    """
    Snapshot DOM-элемента на момент генерации локатора.

    Хранит полную информацию об элементе для последующего анализа
    и повторной генерации локаторов.
    """

    __tablename__ = "elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("locator_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    attributes: Mapped[dict] = mapped_column(
        JSONB, nullable=True, comment="Все атрибуты элемента"
    )
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    own_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_info: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Информация о родительском элементе"
    )
    siblings: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Соседние элементы (prev/next)"
    )
    bbox: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Координаты и размеры: x, y, width, height"
    )
    css_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи
    run: Mapped["LocatorRun"] = relationship("LocatorRun", back_populates="elements")

    def __repr__(self):
        return f"<Element(id={self.id}, tag='{self.tag}')>"


class LocatorHistory(Base):
    """
    История изменений локаторов.

    Записывает каждое изменение: старый xpath → новый xpath,
    причина изменения, ссылка на запуск, в котором произошло изменение.
    """

    __tablename__ = "locator_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    locator_id: Mapped[int] = mapped_column(
        ForeignKey("locators.id", ondelete="CASCADE"), nullable=False, index=True
    )
    old_xpath: Mapped[str] = mapped_column(Text, nullable=True)
    new_xpath: Mapped[str] = mapped_column(Text, nullable=False)
    change_reason: Mapped[ChangeReason] = mapped_column(
        Enum(ChangeReason), nullable=False, comment="Причина изменения"
    )
    change_description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Описание изменения (опционально)"
    )
    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("locator_runs.id", ondelete="SET NULL"),
        nullable=True,
        comment="Запуск, в котором произошло изменение",
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи
    locator: Mapped["Locator"] = relationship("Locator", back_populates="history_entries")

    def __repr__(self):
        return (
            f"<LocatorHistory(id={self.id}, locator_id={self.locator_id}, "
            f"reason={self.change_reason.value})>"
        )

