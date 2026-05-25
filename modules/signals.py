"""
Las 8 senales del dashboard 'Recovering from a Bitcoin Bear'.
Cada funcion devuelve (bool | None, str):
  True  = verde (bullish)
  False = rojo  (bearish)
  None  = datos no disponibles (tile gris)
"""
import pandas as pd
import numpy as np
from typing import Optional
from .price_fetcher import compute_sma, compute_ema


# ── Signal 1: Precio > SMA 200 dias ───────────────────────────────────────────

def signal_price_sma200(price_df: pd.DataFrame) -> tuple:
    """
    Verde si el precio actual supera la media movil de 200 dias.
    Fuente: Binance (siempre disponible).
    """
    try:
        close  = price_df["close"]
        sma200 = compute_sma(close, 200)
        current = float(close.iloc[-1])
        ma_val  = float(sma200.iloc[-1])
        is_green = current > ma_val
        msg = f"${current:,.0f} {'>' if is_green else '<'} SMA200 ${ma_val:,.0f}"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando SMA200")


# ── Signal 2: Precio > Realized Price ─────────────────────────────────────────

def signal_realized_price(
    price_df: pd.DataFrame,
    realized_price: Optional[pd.Series],
) -> tuple:
    """
    Verde si el precio actual supera el precio realizado.
    Fuente: BGeometrics /v1/realized-price.
    """
    if realized_price is None:
        return (None, "Datos no disponibles")
    try:
        current  = float(price_df["close"].iloc[-1])
        rp_today = float(realized_price.iloc[-1])
        is_green = current > rp_today
        msg = f"${current:,.0f} {'>' if is_green else '<'} Realized ${rp_today:,.0f}"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando senal")


# ── Signal 3: Momentum de nuevas direcciones ──────────────────────────────────

def signal_new_address_momentum(new_addr: Optional[pd.Series]) -> tuple:
    """
    Verde si SMA(30) > SMA(365) durante 60+ dias consecutivos.
    Fuente: Blockchain.com n-unique-addresses.
    Requiere >= 365 puntos de datos.
    """
    if new_addr is None:
        return (None, "Datos no disponibles")
    try:
        if len(new_addr) < 365:
            return (None, f"Datos insuficientes ({len(new_addr)} dias, necesita 365)")
        sma30  = compute_sma(new_addr, 30)
        sma365 = compute_sma(new_addr, 365)
        above  = (sma30 > sma365).dropna()
        # Verificar que los ultimos 60 dias sean todos True
        if len(above) < 60:
            return (None, "Datos insuficientes para 60 dias")
        last_60 = above.iloc[-60:]
        is_green = bool(last_60.all())
        days_above = int(above[::-1].cumprod().sum())  # dias consecutivos al final
        msg = f"SMA30 {'>' if sma30.iloc[-1] > sma365.iloc[-1] else '<'} SMA365 | {days_above} dias consecutivos"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando senal")


# ── Signal 4: Momentum de fee revenue ────────────────────────────────────────

def signal_fee_revenue_momentum(fee_rev: Optional[pd.Series]) -> tuple:
    """
    Verde si el Z-Score de 2 años del fee revenue > 0.
    Logica original (Glassnode): '2yr Fee Revenue Z-Score > 0'.
    Un Z-Score positivo indica que el fee revenue actual esta por encima
    de su media de 2 años, señal de bloques llenos y demanda creciente.
    Fuente: CoinMetrics FeeTotNtv (730 dias = ventana de 2 años).
    """
    if fee_rev is None:
        return (None, "Datos no disponibles")
    try:
        if len(fee_rev) < 30:
            return (None, f"Datos insuficientes ({len(fee_rev)} dias)")
        mean = float(fee_rev.mean())
        std  = float(fee_rev.std())
        if std == 0:
            return (None, "Desviacion estandar cero — datos sin variacion")
        z = (float(fee_rev.iloc[-1]) - mean) / std
        is_green = z > 0
        msg = f"Z-Score 2yr = {z:+.2f} ({'>' if is_green else '<'} 0) | {fee_rev.iloc[-1]:.4f} BTC hoy"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando senal")


# ── Signal 5: aSOPR ──────────────────────────────────────────────────────────
# Orden correcto segun original Glassnode: aSOPR (#5) precede a Realized P/L Ratio (#6).

def signal_asopr(asopr: Optional[pd.Series]) -> tuple:
    """
    Verde si SMA(30) del aSOPR > 1.0.
    Logica original (Glassnode): 'aSOPR (30D-SMA) > 1.0'.
    Indica que los outputs gastados on-chain realizan, en promedio, ganancias.
    SMA de 30 dias (no 90) segun especificacion original.
    Fuente: BGeometrics /v1/asopr.
    """
    if asopr is None:
        return (None, "Datos no disponibles")
    try:
        sma30 = compute_sma(asopr, 30)
        val   = float(sma30.iloc[-1])
        is_green = val > 1.0
        msg = f"SMA30 aSOPR = {val:.4f} ({'>' if is_green else '<'} 1.0)"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando senal")


# ── Signal 6: Realized P/L Ratio ─────────────────────────────────────────────

def signal_realized_pnl_ratio(rplr: Optional[pd.Series]) -> tuple:
    """
    Verde si SMA(30) del Realized P/L Ratio > 1.0.
    Logica original (Glassnode): 'Realized P/L Ratio (30D-SMA) > 1.0'.
    Indica que el volumen USD de ganancias realizadas supera las perdidas realizadas.
    A diferencia de aSOPR, pondera por volumen (whales tienen mas peso que shrimps).
    Fuente: BGeometrics /v1/realized-profit-loss-ratio (HTTP 500 en servidor).
    """
    if rplr is None:
        return (None, "Sin datos — BGeometrics devuelve HTTP 500 en este endpoint")
    try:
        sma30 = compute_sma(rplr, 30)
        val   = float(sma30.iloc[-1])
        is_green = val > 1.0
        msg = f"SMA30 RPLR = {val:.3f} ({'>' if is_green else '<'} 1.0)"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando senal")


# ── Signal 7: RHODL Multiple / MVRV proxy ─────────────────────────────────────

def signal_hodl_multiple(hodl: Optional[pd.Series]) -> tuple:
    """
    Verde si MVRV actual > MVRV hace 90 dias (tendencia alcista de 90 dias).
    Logica original (Glassnode): 'RHODL Multiple in Uptrend over 90-days'.
    Proxy: usamos MVRV (/v1/mvrv de BGeometrics) porque RHODL no esta disponible
    en APIs publicas gratuitas. Ambos capturan el balance de riqueza entre
    holders de corto y largo plazo.
    """
    if hodl is None:
        return (None, "Sin datos — esperando reset de rate limit BGeometrics")
    try:
        if len(hodl) < 92:
            return (None, "Datos insuficientes (< 92 dias)")
        current  = float(hodl.iloc[-1])
        ago_90   = float(hodl.iloc[-91])
        is_green = current > ago_90
        pct      = (current / ago_90 - 1) * 100
        msg = f"Actual {current:.4f} vs hace 90d {ago_90:.4f} ({pct:+.1f}%)"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando senal")


# ── Signal 8: Supply in Profit uptrend ───────────────────────────────────────

def signal_supply_in_profit(sip: Optional[pd.Series]) -> tuple:
    """
    Verde si EMA(90) actual > EMA(90) hace 30 dias.
    Fuente: BGeometrics /v1/supply-profit (supplyProfitBtc). CONFIRMADO.
    """
    if sip is None:
        return (None, "Datos no disponibles")
    try:
        if len(sip) < 122:  # 90 + 32 minimo
            return (None, f"Datos insuficientes ({len(sip)} dias)")
        ema90    = compute_ema(sip, 90)
        current  = float(ema90.iloc[-1])
        ago_30   = float(ema90.iloc[-31])
        is_green = current > ago_30
        pct      = (current / ago_30 - 1) * 100
        current_btc = float(sip.iloc[-1])
        msg = f"{current_btc/1e6:.2f}M BTC en profit | EMA90 {pct:+.1f}% en 30d"
        return (is_green, msg)
    except Exception:
        return (None, "Error calculando senal")


# ── Evaluador compuesto ───────────────────────────────────────────────────────

SIGNAL_LABELS = [
    "Price > 200D SMA",        # 1 — Pricing model tecnico
    "Price > Realized Price",  # 2 — Pricing model on-chain
    "New Address Momentum",    # 3 — Actividad de red
    "Fee Revenue Z-Score",     # 4 — Congestion de red
    "aSOPR",                   # 5 — Rentabilidad (igual peso shrimps/whales)
    "Realized P/L Ratio",      # 6 — Rentabilidad (ponderado por volumen USD)
    "HODL Multiple (MVRV)",    # 7 — Balance de riqueza HODLers (proxy RHODL)
    "Supply in Profit",        # 8 — Dinamicas de oferta
]


def evaluate_all_signals(data: dict) -> dict:
    """
    Evalua las 8 senales y devuelve el score compuesto.

    data keys requeridos:
      price_df, realized_price, new_addresses, fee_revenue,
      realized_pnl_ratio, asopr, hodl_multiple, supply_in_profit

    Retorna:
      {
        "signals":    [(label, bool|None, msg), ...],  # 8 items
        "score":      int,   # cantidad de True
        "possible":   int,   # cantidad de senales con datos (no None)
        "threshold_5": bool, # score >= 5
        "all_green":  bool,  # score == 8 y possible == 8
      }
    """
    price_df = data.get("price_df")

    raw = [
        signal_price_sma200(price_df),                               # 1
        signal_realized_price(price_df, data.get("realized_price")), # 2
        signal_new_address_momentum(data.get("new_addresses")),      # 3
        signal_fee_revenue_momentum(data.get("fee_revenue")),        # 4
        signal_asopr(data.get("asopr")),                             # 5
        signal_realized_pnl_ratio(data.get("realized_pnl_ratio")),  # 6
        signal_hodl_multiple(data.get("hodl_multiple")),             # 7
        signal_supply_in_profit(data.get("supply_in_profit")),       # 8
    ]

    signals   = [(SIGNAL_LABELS[i], raw[i][0], raw[i][1]) for i in range(8)]
    score     = sum(1 for _, v, _ in signals if v is True)
    possible  = sum(1 for _, v, _ in signals if v is not None)

    return {
        "signals":     signals,
        "score":       score,
        "possible":    possible,
        "threshold_5": score >= 5,
        "all_green":   score == 8 and possible == 8,
    }
