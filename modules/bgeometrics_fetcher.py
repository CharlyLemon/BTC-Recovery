"""
Cliente REST para BGeometrics API (api.bgeometrics.com/v1).
Tier gratuito: 10 req/hora, 15 req/dia — sin API key.

Endpoints CONFIRMADOS (verificados 2026-05-25):
  /v1/realized-price               -> campo: realizedPrice
  /v1/asopr                        -> campo: asopr
  /v1/sopr                         -> campo: sopr
  /v1/supply-profit                -> campo: supplyProfitBtc  (Signal 8)
  /v1/mvrv                         -> campo: autodetectado    (Signal 7)
  /v1/nupl                         -> campo: autodetectado    (referencia)

Endpoints INESTABLES (slug existe, servidor da 500):
  Signal 5: /v1/realized-profit-loss-ratio  (HTTP 500 del lado de BGeometrics)
"""
import requests
import pandas as pd
from typing import Optional
from .cache import read_cache, write_cache

BASE_URL = "https://api.bgeometrics.com/v1"
TIMEOUT  = 15  # segundos


def _fetch(endpoint: str, cache_key: str, value_field: str = None) -> Optional[pd.Series]:
    """
    Descarga una serie temporal de BGeometrics.
    - endpoint: ej. '/realized-price'
    - cache_key: clave unica para el cache en disco
    - value_field: nombre del campo con el valor numerico. Si es None, se autodetecta.
    Devuelve pd.Series con indice DatetimeIndex, o None si falla.
    """
    # 1. Intentar desde cache
    cached = read_cache(cache_key)
    if cached is not None:
        return pd.Series(
            cached["values"],
            index=pd.to_datetime(cached["dates"]),
        )

    # 2. Llamada a la API
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        if not isinstance(data, list) or len(data) == 0:
            return None

        # Autodetectar campo de valor si no se especifico
        field = value_field
        if field is None or field not in data[0]:
            candidates = [k for k in data[0].keys() if k not in ("d", "unixTs")]
            if not candidates:
                return None
            field = candidates[0]

        dates  = [item["d"] for item in data]
        values = [item[field] for item in data]

        write_cache(cache_key, {"dates": dates, "values": values})
        series = pd.Series(values, index=pd.to_datetime(dates))
        series.index.name = "date"
        return series

    except Exception:
        return None


# ── Endpoints confirmados ──────────────────────────────────────────────────────

def get_realized_price() -> Optional[pd.Series]:
    """Precio realizado de BTC (USD). Signal 2."""
    return _fetch("/realized-price", "bgeo_realized_price", "realizedPrice")


def get_asopr() -> Optional[pd.Series]:
    """Adjusted Spent Output Profit Ratio. Signal 6."""
    return _fetch("/asopr", "bgeo_asopr", "asopr")


def get_sopr() -> Optional[pd.Series]:
    """Spent Output Profit Ratio (referencia / fallback)."""
    return _fetch("/sopr", "bgeo_sopr", "sopr")


def get_supply_in_profit() -> Optional[pd.Series]:
    """
    Supply in Profit en BTC (~12.5M BTC actualmente). Signal 8.
    Confirmado: /v1/supply-profit, campo supplyProfitBtc.
    """
    return _fetch("/supply-profit", "bgeo_supply_profit", "supplyProfitBtc")


# ── Endpoints PENDIENTES (stubs) ───────────────────────────────────────────────

def get_realized_pnl_ratio() -> Optional[pd.Series]:
    """
    Realized Profit/Loss Ratio. Signal 5.
    Endpoint /v1/realized-profit-loss-ratio existe (no es 404) pero BGeometrics
    devuelve HTTP 500 (bug del lado del servidor). Se intenta igualmente —
    _fetch devuelve None si falla, lo que produce tile gris en el dashboard.
    Cuando BGeometrics lo arregle, funcionara automaticamente.
    """
    return _fetch("/realized-profit-loss-ratio", "bgeo_rplr", None)


def get_hodl_multiple() -> Optional[pd.Series]:
    """
    MVRV como proxy de HODL Multiple. Signal 7.
    Confirmado 2026-05-25: /v1/mvrv devuelve HTTP 200 con datos historicos.
    Campo de valor autodetectado (primer campo que no sea 'd' ni 'unixTs').
    Logica en signals.py: verde si mvrv[-1] > mvrv[-91] (tendencia alcista 90d).
    """
    return _fetch("/mvrv", "bgeo_mvrv", None)
