"""
Fuentes alternativas gratuitas para metricas on-chain:
  - Blockchain.com Charts API  -> nuevas direcciones (Signal 3)
  - CoinMetrics Community API  -> fee revenue en BTC (Signal 4)
Ambas sin API key, confirmadas funcionales.
"""
import requests
import pandas as pd
from typing import Optional
from .cache import read_cache, write_cache


def get_new_addresses() -> Optional[pd.Series]:
    """
    Direcciones unicas activas por dia desde Blockchain.com.
    Nota: es 'unique addresses' (activas), no estrictamente 'nuevas',
    pero es el proxy mas cercano disponible gratis.
    Signal 3 — condicion: SMA(30) > SMA(365) por 60+ dias consecutivos.
    """
    cached = read_cache("blockchain_new_addresses")
    if cached is not None:
        return pd.Series(
            cached["values"],
            index=pd.to_datetime(cached["dates"]),
        )
    try:
        r = requests.get(
            "https://api.blockchain.info/charts/n-unique-addresses",
            params={"timespan": "2years", "format": "json", "cors": "true"},
            timeout=15,
        )
        r.raise_for_status()
        raw = r.json().get("values", [])
        dates  = [pd.Timestamp(v["x"], unit="s").strftime("%Y-%m-%d") for v in raw]
        values = [float(v["y"]) for v in raw]
        write_cache("blockchain_new_addresses", {"dates": dates, "values": values})
        series = pd.Series(values, index=pd.to_datetime(dates))
        series.index.name = "date"
        return series
    except Exception:
        return None


def get_fee_revenue() -> Optional[pd.Series]:
    """
    Total de fees pagados en BTC por dia (FeeTotNtv) desde CoinMetrics Community.
    Signal 4 — condicion: SMA(90) > SMA(365).
    """
    cached = read_cache("coinmetrics_fee_revenue")
    if cached is not None:
        return pd.Series(
            cached["values"],
            index=pd.to_datetime(cached["dates"]),
        )
    try:
        r = requests.get(
            "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics",
            params={
                "assets": "btc",
                "metrics": "FeeTotNtv",
                "frequency": "1d",
                "limit_per_asset": "730",
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        pairs = [
            (item["time"][:10], float(item["FeeTotNtv"]))
            for item in data
            if item.get("FeeTotNtv") not in (None, "", "None")
        ]
        if not pairs:
            return None
        dates, values = zip(*pairs)
        write_cache("coinmetrics_fee_revenue", {"dates": list(dates), "values": list(values)})
        series = pd.Series(list(values), index=pd.to_datetime(list(dates)))
        series.index.name = "date"
        return series
    except Exception:
        return None
