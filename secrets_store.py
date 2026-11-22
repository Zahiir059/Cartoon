"""API keys are kept in the OS credential vault (Windows Credential Manager) via `keyring`.
They are never written to disk by this app and never hardcoded. If no vault is available the
key lives in memory for the current session only."""
import os

SERVICE = "CartoonAI"
_session: dict[str, str] = {}


def _kr():
    try:
        import keyring
        return keyring
    except Exception:
        return None


def get_token(name: str = "replicate") -> str | None:
    if name in _session:
        return _session[name]
    k = _kr()
    if k:
        try:
            v = k.get_password(SERVICE, name)
            if v:
                return v
        except Exception:
            pass
    return os.environ.get("REPLICATE_API_TOKEN") if name == "replicate" else None


def set_token(token: str, name: str = "replicate") -> str:
    """Returns 'vault' or 'session' describing where the key was kept."""
    token = token.strip()
    k = _kr()
    if k:
        try:
            k.set_password(SERVICE, name, token)
            _session.pop(name, None)
            return "vault"
        except Exception:
            pass
    _session[name] = token
    return "session"


def delete_token(name: str = "replicate"):
    _session.pop(name, None)
    k = _kr()
    if k:
        try:
            k.delete_password(SERVICE, name)
        except Exception:
            pass
