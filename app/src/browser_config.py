import sys
import asyncio
import os
from browser_use import Browser, BrowserProfile, ChatOpenAI
from dotenv import load_dotenv
from src.llm_provider import get_browser_llm_model, get_llm_api_key, get_llm_base_url

# Настройка политики событий для Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

BROWSER_HEADLESS = False
BROWSER_DISABLE_SECURITY = True
BROWSER_ARGS = [
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-setuid-sandbox",
    "--disable-web-security",
]


DEFAULT_URL = "https://portal.apps.k8s.dev.domoy.ru"

def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except Exception:
        return default


# Дефолты (как раньше), но остаются настраиваемыми через env/UI
MAX_ELEMENTS_PER_CHUNK = _int_env("CHUNK_SIZE", 6)
MAX_ELEMENTS_PER_FIX_CHUNK = _int_env("FIX_CHUNK_SIZE", 5)
MAX_CHILDREN_ELEMENTS = _int_env("MAX_CHILDREN_ELEMENTS", 400)
MAX_TOTAL_ELEMENTS = _int_env("MAX_TOTAL_ELEMENTS", 400)
PAGE_STABILIZE_SECONDS = _int_env("PAGE_STABILIZE_SECONDS", 10)
READY_STATE_TIMEOUT_SECONDS = _int_env("READY_STATE_TIMEOUT_SECONDS", 20)


AVAILABLE_SELECTORS = [
    "a", "abbr", "address", "article", "aside", "audio", "b", "bdi", "bdo", "blockquote",
    "body", "br", "button", "canvas", "caption", "cite", "code", "col", "colgroup", "data",
    "datalist", "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5",
    "h6", "header", "hr", "i", "iframe", "img", "input", "ins", "kbd", "label", "legend",
    "li", "main", "map", "mark", "menu", "meter", "nav", "noscript", "object", "ol",
    "optgroup", "option", "output", "p", "picture", "pre", "progress", "q", "rp", "rt",
    "ruby", "s", "samp", "section", "select", "small", "source", "span", "strong", "sub",
    "summary", "sup", "svg", "table", "tbody", "td", "template", "textarea", "tfoot",
    "th", "thead", "time", "tr", "track", "u", "ul", "var", "video", "wbr",
]

DEFAULT_SELECTORS = ["span"]


def create_llm(temperature: float = 0.7) -> ChatOpenAI:
    """Создает экземпляр LLM с заданной температурой."""
    return ChatOpenAI(
        model=get_browser_llm_model(),
        api_key=get_llm_api_key(),
        base_url=get_llm_base_url(),
        temperature=temperature,
    )


def build_browser_profile() -> BrowserProfile:
    """Создает профиль браузера с оптимальными настройками."""
    return BrowserProfile(
        headless=BROWSER_HEADLESS,
        disable_security=BROWSER_DISABLE_SECURITY,
        args=BROWSER_ARGS,
        is_local=True,
        use_cloud=False,
        enable_default_extensions=False,
        wait_for_network_idle_page_load_time=10.0,
        maximum_wait_page_load_time=30.0,
        wait_between_actions=1.0,
    )


async def create_browser() -> Browser:
    """Создает и запускает браузер с оптимальными настройками."""
    browser_profile = build_browser_profile()
    browser = Browser(browser_profile=browser_profile)
    await browser.start()
    return browser