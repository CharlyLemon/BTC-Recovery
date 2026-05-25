"""
Disk-backed JSON cache with TTL.
Patron reutilizado de crypto_analyzer/modules/onchain_fetcher.py
"""
import json
import time
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path(__file__).parent.parent / "cache"
PRICE_TTL   = 3_600      # 1 hora  — datos de precio
ONCHAIN_TTL = 86_400     # 24 horas — datos on-chain (limite BGeometrics: 15 req/dia)


def _path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def read_cache(key: str, ttl: int = ONCHAIN_TTL) -> Optional[Any]:
    """Devuelve el valor cacheado si no ha expirado, None si no existe o expiro."""
    p = _path(key)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if time.time() - data["ts"] < ttl:
            return data["value"]
    except Exception:
        pass
    return None


def write_cache(key: str, value: Any) -> None:
    """Escribe {ts, value} en cache/<key>.json."""
    p = _path(key)
    try:
        p.write_text(
            json.dumps({"ts": time.time(), "value": value}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def cache_age_str(key: str) -> str:
    """Devuelve la edad del cache como string legible, ej: '3h 12m'."""
    p = _path(key)
    if not p.exists():
        return "sin cache"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        age = int(time.time() - data["ts"])
        h, m = divmod(age // 60, 60)
        return f"{h}h {m}m"
    except Exception:
        return "desconocido"
