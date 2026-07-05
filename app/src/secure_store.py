from __future__ import annotations

from dataclasses import dataclass

try:
    import keyring  # type: ignore
except Exception:  # pragma: no cover
    keyring = None


SERVICE_NAME = "tester-assistant-vkr"


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


def is_keyring_available() -> bool:
    return keyring is not None


def save_credentials(key: str, creds: Credentials) -> None:
    if keyring is None:
        raise RuntimeError("keyring is not installed")
    keyring.set_password(SERVICE_NAME, f"{key}:username", creds.username)
    keyring.set_password(SERVICE_NAME, f"{key}:password", creds.password)


def load_credentials(key: str) -> Credentials | None:
    if keyring is None:
        return None
    username = keyring.get_password(SERVICE_NAME, f"{key}:username")
    password = keyring.get_password(SERVICE_NAME, f"{key}:password")
    if not username or not password:
        return None
    return Credentials(username=username, password=password)


def clear_credentials(key: str) -> None:
    if keyring is None:
        return
    try:
        keyring.delete_password(SERVICE_NAME, f"{key}:username")
    except Exception:
        pass
    try:
        keyring.delete_password(SERVICE_NAME, f"{key}:password")
    except Exception:
        pass

