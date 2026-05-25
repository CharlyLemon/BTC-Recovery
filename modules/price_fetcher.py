"""
Precio BTC/USDT desde Binance REST API publica (sin ccxt, sin API key).
Endpoint: GET https://api.binance.com/api/v3/klines
"""
import requests
import pandas as pd
from typing import Optional
from .cache import read_cache, write_cache, PRICE_TTL

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"


def fetch_btc_daily(limit: int = 400) -> pd.DataFrame:
    """
    Descarga velas diarias BTC/USDT de Binance via REST (sin ccxt).
    Cache de 1 hora. Devuelve DataFrame con indice DatetimeIndex
    y columnas: open, high, low, close, volume.
    """
    cached = read_cache("btc_daily", ttl=PRICE_TTL)
    if cached is not None:
        df = pd.DataFrame(cached, columns=["ts", "open", "high", "low", "close", "volume"])
        df.index = pd.to_datetime(df["ts"], unit="ms")
        df.index.name = "date"
        return df[["open", "high", "low", "close", "volume"]]

    try:
        r = requests.get(
            BINANCE_KLINES,
            params={"symbol": "BTCUSDT", "interval": "1d", "limit": limit},
            timeout=15,
        )
        r.raise_for_status()
        raw = r.json()  # lista de listas: [openTime, open, high, low, close, volume, ...]
        ohlcv = [
            [int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])]
            for row in raw
        ]
        write_cache("btc_daily", ohlcv)
        df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
        df.index = pd.to_datetime(df["ts"], unit="ms")
        df.index.name = "date"
        return df[["open", "high", "low", "close", "volume"]]
    except Exception as e:
        raise RuntimeError(f"Error obteniendo precio de Binance: {e}") from e


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
