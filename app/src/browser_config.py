import sys
import asyncio
from browser_use import Browser, BrowserProfile, ChatOpenAI
from dotenv import load_dotenv

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
MAX_ELEMENTS_PER_CHUNK = 6
MAX_ELEMENTS_PER_FIX_CHUNK = 5
MAX_CHILDREN_ELEMENTS = 400


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
        model="gpt",
        api_key="-",
        base_url="http://localhost:8000/v1",
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
        wait_for_network_idle_page_load_time=5.0,
        maximum_wait_page_load_time=30.0,
        wait_between_actions=1.0,
    )


async def create_browser() -> Browser:
    """Создает и запускает браузер с оптимальными настройками."""
    browser_profile = build_browser_profile()
    browser = Browser(browser_profile=browser_profile)
    await browser.start()
    return browser