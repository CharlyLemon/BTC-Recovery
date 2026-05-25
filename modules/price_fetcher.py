"""
Precio BTC/USDT desde múltiples fuentes públicas sin API key.
Orden de prioridad:
  1. Binance.com  — global
  2. Binance US   — servidores en EE.UU. (Streamlit Cloud)
  3. Kraken       — sin restricciones geográficas, backup confiable
"""
import requests
import pandas as pd
from typing import Optional
from .cache import read_cache, write_cache, PRICE_TTL

_TIMEOUT = 15  # segundos


# ── Parsers por fuente ────────────────────────────────────────────────────────

def _parse_ohlcv(raw: list) -> pd.DataFrame:
    """Convierte lista de listas OHLCV [ts_ms, o, h, l, c, v] a DataFrame."""
    ohlcv = [
        [int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])]
        for row in raw
    ]
    write_cache("btc_daily", ohlcv)
    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df["ts"], unit="ms")
    df.index.name = "date"
    return df[["open", "high", "low", "close", "volume"]]


def _fetch_from_binance(base_url: str, limit: int) -> pd.DataFrame:
    """Intenta descargar desde un endpoint de Binance (com o us)."""
    r = requests.get(
        f"{base_url}/api/v3/klines",
        params={"symbol": "BTCUSDT", "interval": "1d", "limit": limit},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return _parse_ohlcv(r.json())


def _fetch_from_kraken(limit: int) -> pd.DataFrame:
    """
    Descarga OHLC diario de Kraken (par XBTUSD).
    Kraken devuelve hasta 720 velas diarias — sin restricciones geográficas.
    """
    r = requests.get(
        "https://api.kraken.com/0/public/OHLC",
        params={"pair": "XBTUSD", "interval": 1440},  # 1440 min = 1 dia
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"Kraken API error: {data['error']}")

    # La clave del par puede ser 'XXBTZUSD' o 'XBTUSD'
    result = data.get("result", {})
    pair_key = next((k for k in result if k != "last"), None)
    if not pair_key:
        raise RuntimeError("Kraken: respuesta sin datos OHLC")

    # Kraken: [time_s, open, high, low, close, vwap, volume, count]
    raw = result[pair_key][-limit:]
    ohlcv = [
        [int(row[0]) * 1000, float(row[1]), float(row[2]), float(row[3]),
         float(row[4]), float(row[6])]
        for row in raw
    ]
    write_cache("btc_daily", ohlcv)
    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df["ts"], unit="ms")
    df.index.name = "date"
    return df[["open", "high", "low", "close", "volume"]]


# ── Función principal con fallback ────────────────────────────────────────────

def fetch_btc_daily(limit: int = 400) -> pd.DataFrame:
    """
    Descarga velas diarias BTC/USD con fallback automático entre fuentes.
    Cache de 1 hora. Devuelve DataFrame con indice DatetimeIndex
    y columnas: open, high, low, close, volume.
    """
    # 1. Intentar desde cache
    cached = read_cache("btc_daily", ttl=PRICE_TTL)
    if cached is not None:
        df = pd.DataFrame(cached, columns=["ts", "open", "high", "low", "close", "volume"])
        df.index = pd.to_datetime(df["ts"], unit="ms")
        df.index.name = "date"
        return df[["open", "high", "low", "close", "volume"]]

    # 2. Intentar fuentes en orden
    sources = [
        ("Binance.com", lambda: _fetch_from_binance("https://api.binance.com", limit)),
        ("Binance US",  lambda: _fetch_from_binance("https://api.binance.us",  limit)),
        ("Kraken",      lambda: _fetch_from_kraken(limit)),
    ]

    errors = []
    for name, fn in sources:
        try:
            return fn()
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue

    raise RuntimeError(
        "Todas las fuentes de precio fallaron:\n" + "\n".join(errors)
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_current_price(price_df: Optional[pd.DataFrame] = None) -> float:
    if price_df is None:
        price_df = fetch_btc_daily()
    return float(price_df["close"].iloc[-1])


def compute_sma(series: pd.Series, window: int) -> pd.Series:
    """Media movil simple. NaN en las primeras (window-1) filas."""
    return series.rolling(window=window, min_periods=window).mean()


def compute_ema(series: pd.Series, window: int) -> pd.Series:
    """Media movil exponencial."""
    return series.ewm(span=window, adjust=False).mean()
