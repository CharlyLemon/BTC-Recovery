"""
BTC Bear Recovery Dashboard
Replica del dashboard 'Recovering from a Bitcoin Bear' de Glassnode.
Combina 8 senales on-chain para identificar confluencias de recuperacion.

Ejecutar: streamlit run app.py
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

from modules.price_fetcher import fetch_btc_daily, compute_sma, compute_ema
from modules.bgeometrics_fetcher import (
    get_realized_price, get_asopr, get_supply_in_profit,
    get_realized_pnl_ratio, get_hodl_multiple,
)
from modules.alt_fetcher import get_new_addresses, get_fee_revenue
from modules.signals import evaluate_all_signals
from modules.cache import cache_age_str

# ── Configuracion de pagina ───────────────────────────────────────────────────

st.set_page_config(
    layout="wide",
    page_title="BTC Bear Recovery",
    page_icon="B",
)

# ── CSS para tiles de senales ─────────────────────────────────────────────────

st.markdown("""
<style>
.signal-tile {
    border-radius: 10px;
    padding: 14px 16px;
    margin: 4px 0;
    min-height: 88px;
    transition: opacity .2s;
}
.signal-tile:hover { opacity: .9; }
.signal-green { background-color: #162e22; border: 1px solid #2d7a50; }
.signal-red   { background-color: #2e1616; border: 1px solid #8b3333; }
.signal-grey  { background-color: #1e1e1e; border: 1px solid #3a3a3a; }
.signal-num   { font-size: 10px; font-weight: 700; color: #555;
                text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
.signal-label { font-size: 12px; font-weight: 600; color: #bbb;
                margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
.signal-value { font-size: 13px; font-weight: 400; color: #ddd; line-height: 1.4; }
.signal-icon  { font-size: 16px; }
.score-badge  { font-size: 32px; font-weight: 800; padding: 6px 20px;
                border-radius: 24px; display: inline-block; letter-spacing: -1px; }
.phase-banner { padding: 10px 16px; border-radius: 8px; margin: 8px 0;
                font-size: 14px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Carga de datos (cacheado por Streamlit 1 hora) ────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Cargando datos on-chain...")
def load_all_data() -> dict:
    price_df          = fetch_btc_daily(limit=400)
    realized_price    = get_realized_price()
    asopr             = get_asopr()
    supply_in_profit  = get_supply_in_profit()
    new_addresses     = get_new_addresses()
    fee_revenue       = get_fee_revenue()
    realized_pnl_ratio = get_realized_pnl_ratio()
    hodl_multiple     = get_hodl_multiple()
    return {
        "price_df":          price_df,
        "realized_price":    realized_price,
        "asopr":             asopr,
        "supply_in_profit":  supply_in_profit,
        "new_addresses":     new_addresses,
        "fee_revenue":       fee_revenue,
        "realized_pnl_ratio": realized_pnl_ratio,
        "hodl_multiple":     hodl_multiple,
    }


# ── Helpers de visualizacion ──────────────────────────────────────────────────

def score_color(score: int) -> str:
    """Color del badge segun score sobre 8 senales totales."""
    if score >= 8: return "#1a3a8b"   # azul fuerte  — 8/8 todo verde
    if score >= 5: return "#2855c8"   # azul         — 5-7 umbral alcanzado
    if score >= 3: return "#c47c0a"   # naranja      — 3-4 transicion
    return "#8b2020"                  # rojo         — 0-2 bajista


def market_phase(score: int) -> tuple[str, str]:
    """Etiqueta y color de fase de mercado segun score."""
    if score >= 8: return "💙 Mercado Alcista Confirmado", "#1a3a8b"
    if score >= 5: return "🔵 Recuperacion en Curso",      "#2855c8"
    if score >= 3: return "🟠 Transicion / Indecision",    "#c47c0a"
    return "🔴 Mercado Bajista",                           "#8b2020"


def signal_tile_html(label: str, value, msg: str, num: int = None) -> str:
    if value is True:
        cls, icon = "signal-green", "✅"
    elif value is False:
        cls, icon = "signal-red",   "🔴"
    else:
        cls, icon = "signal-grey",  "⚫"
    num_row = f'<div class="signal-num">Señal {num}</div>' if num else ""
    return f"""
<div class="signal-tile {cls}">
  {num_row}
  <div class="signal-label">
    <span>{label}</span>
    <span class="signal-icon">{icon}</span>
  </div>
  <div class="signal-value">{msg}</div>
</div>"""


def build_price_chart(
    price_df: pd.DataFrame,
    realized_price,
    score_history: pd.Series = None,
) -> go.Figure:
    """
    Grafica de precio BTC con:
    - Linea de precio de cierre
    - SMA 200 dias (naranja)
    - Realized Price (morado, si disponible)
    - Bandas de color de fondo basadas en score historico (senales 1+2)
    """
    fig = go.Figure()

    # Bandas de fondo (score historico con senales 1 y 2)
    if score_history is not None and len(score_history) > 0:
        _add_score_bands(fig, score_history)

    # Precio de cierre
    fig.add_trace(go.Scatter(
        x=price_df.index, y=price_df["close"],
        name="BTC Price", line=dict(color="#f7931a", width=2),
        hovertemplate="$%{y:,.0f}<extra>BTC</extra>",
    ))

    # SMA 200
    sma200 = compute_sma(price_df["close"], 200)
    fig.add_trace(go.Scatter(
        x=price_df.index, y=sma200,
        name="SMA 200", line=dict(color="#ffa500", width=1.5, dash="dash"),
        hovertemplate="$%{y:,.0f}<extra>SMA200</extra>",
    ))

    # Realized Price
    if realized_price is not None:
        rp_aligned = realized_price.reindex(price_df.index, method="ffill")
        fig.add_trace(go.Scatter(
            x=rp_aligned.index, y=rp_aligned.values,
            name="Realized Price", line=dict(color="#9b59b6", width=1.5, dash="dot"),
            hovertemplate="$%{y:,.0f}<extra>Realized</extra>",
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=True, gridcolor="#333"),
        yaxis=dict(showgrid=True, gridcolor="#333", tickprefix="$",
                   tickformat=",.0f", side="right"),
        hovermode="x unified",
    )
    return fig


def _add_score_bands(fig: go.Figure, score_history: pd.Series):
    """Agrega bandas de fondo azul claro (>=1) y azul oscuro (==2)."""
    for threshold, color in [
        (1, "rgba(100,149,237,0.12)"),  # azul claro: score >= 1
        (2, "rgba(0,0,139,0.22)"),      # azul oscuro: score == 2
    ]:
        if threshold == 1:
            mask = score_history >= threshold
        else:
            mask = score_history == threshold

        in_band = False
        start   = None
        dates   = score_history.index

        for i, (dt, val) in enumerate(zip(dates, mask)):
            if val and not in_band:
                start   = dt
                in_band = True
            elif not val and in_band:
                fig.add_vrect(
                    x0=start, x1=dates[i - 1],
                    fillcolor=color, layer="below", line_width=0,
                )
                in_band = False
        if in_band:
            fig.add_vrect(
                x0=start, x1=dates[-1],
                fillcolor=color, layer="below", line_width=0,
            )


def compute_score_history(price_df: pd.DataFrame, realized_price) -> pd.Series:
    """
    Calcula score historico diario usando senales 1 y 2 (series temporales completas).
    Score 0, 1 o 2 por dia.
    """
    sma200 = compute_sma(price_df["close"], 200)
    s1 = (price_df["close"] > sma200).astype(int)

    if realized_price is not None:
        rp = realized_price.reindex(price_df.index, method="ffill")
        s2 = (price_df["close"] > rp).astype(int).fillna(0)
    else:
        s2 = pd.Series(0, index=price_df.index)

    return (s1 + s2).fillna(0)


def mini_chart(series: pd.Series, title: str, ref_line: float = None) -> go.Figure:
    """Grafica pequena para los expanders de cada metrica on-chain."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values,
        line=dict(color="#4169e1", width=1.5),
        name=title,
    ))
    if ref_line is not None:
        fig.add_hline(y=ref_line, line_dash="dash", line_color="#ff4444",
                      annotation_text=f"Referencia: {ref_line}")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=250,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        xaxis=dict(showgrid=True, gridcolor="#333"),
        yaxis=dict(showgrid=True, gridcolor="#333", side="right"),
    )
    return fig


# ── Layout principal ──────────────────────────────────────────────────────────

def main():
    # Cargar datos
    with st.spinner("Conectando con fuentes de datos..."):
        data = load_all_data()

    result = evaluate_all_signals(data)
    price_df = data["price_df"]

    # ── Header ────────────────────────────────────────────────────────────────
    col_title, col_score, col_price = st.columns([3, 1, 1])

    with col_title:
        st.title("BTC Bear Recovery")
        st.caption("Replica del dashboard 'Recovering from a Bitcoin Bear' de Glassnode")

    with col_score:
        score    = result["score"]
        possible = result["possible"]
        color    = score_color(score)
        unavail  = 8 - possible
        unavail_txt = (
            f'<br><small style="color:#888;">({unavail} sin datos)</small>'
            if unavail > 0 else ""
        )
        st.markdown(
            f'<div style="text-align:center; margin-top:16px;">'
            f'<span class="score-badge" style="background:{color}; color:white;">'
            f'{score}<span style="font-size:18px;font-weight:500;">/8</span></span>'
            f'{unavail_txt}'
            f'<br><small style="color:#aaa;">señales bullish</small></div>',
            unsafe_allow_html=True,
        )

    with col_price:
        current_price = float(price_df["close"].iloc[-1])
        st.metric(
            label="BTC/USDT",
            value=f"${current_price:,.0f}",
            delta=f"{((current_price / price_df['close'].iloc[-2]) - 1) * 100:.2f}% 24h",
        )

    st.divider()

    # ── Banner de fase de mercado + barra de progreso ─────────────────────────
    phase_label, phase_color = market_phase(score)
    needed = max(0, 5 - score)
    needed_txt = f" — faltan **{needed}** para el umbral" if needed > 0 else " — umbral superado ✓"

    st.markdown(
        f'<div class="phase-banner" style="background:{phase_color}22; border:1px solid {phase_color}55; color:#eee;">'
        f'{phase_label}{needed_txt}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.progress(score / 8, text=f"{score}/8 señales bullish")

    # ── Grid de 8 senales (4x2) ───────────────────────────────────────────────
    st.subheader("Señales de Recuperacion")
    signals = result["signals"]

    row1 = st.columns(4)
    row2 = st.columns(4)

    for i, col in enumerate(row1 + row2):
        if i < len(signals):
            label, value, msg = signals[i]
            with col:
                st.markdown(signal_tile_html(label, value, msg, num=i + 1), unsafe_allow_html=True)

    st.divider()

    # ── Grafica de precio con bandas ──────────────────────────────────────────
    st.subheader("Precio BTC con Señales de Recuperacion")
    st.caption(
        "Banda azul claro: precio > SMA200 O > Realized Price | "
        "Banda azul oscuro: precio > SMA200 Y > Realized Price"
    )

    score_hist = compute_score_history(price_df, data.get("realized_price"))
    fig = build_price_chart(price_df, data.get("realized_price"), score_hist)
    st.plotly_chart(fig, use_container_width=True)

    # ── Sub-graficas on-chain (expandibles) ───────────────────────────────────
    st.subheader("Métricas On-Chain — Detalle")

    # (titulo, series, linea_ref, mensaje_si_no_hay_datos)
    series_map = [
        (
            "New Addresses — Señal 3",
            data.get("new_addresses"),
            None,
            None,
        ),
        (
            "Fee Revenue Z-Score — Señal 4",
            data.get("fee_revenue"),
            None,
            None,
        ),
        (
            "aSOPR — Señal 5",
            data.get("asopr"),
            1.0,
            None,
        ),
        (
            "Realized P/L Ratio — Señal 6",
            data.get("realized_pnl_ratio"),
            1.0,
            (
                "⚠️ **BGeometrics devuelve HTTP 500** en `/v1/realized-profit-loss-ratio` "
                "(error del lado del servidor, no es rate limit). "
                "La señal se activará automáticamente cuando el proveedor lo repare."
            ),
        ),
        (
            "MVRV / HODL Multiple — Señal 7",
            data.get("hodl_multiple"),
            None,
            None,
        ),
        (
            "Supply in Profit BTC — Señal 8",
            data.get("supply_in_profit"),
            None,
            None,
        ),
    ]

    for title, series, ref, err_msg in series_map:
        if series is not None and len(series) > 0:
            with st.expander(f"📈 {title}  —  {len(series):,} días de datos"):
                fig_mini = mini_chart(series.iloc[-400:], title, ref_line=ref)
                st.plotly_chart(fig_mini, use_container_width=True)
        else:
            with st.expander(f"⚫ {title}  —  sin datos"):
                msg = err_msg or "Datos no disponibles para esta señal."
                st.warning(msg)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.divider()
    col_src, col_cache = st.columns([2, 1])
    with col_src:
        st.caption(
            "**Fuentes:** Binance (precio) · "
            "BGeometrics (realized price, aSOPR, MVRV, supply profit) · "
            "Blockchain.com (new addresses) · CoinMetrics (fee revenue)"
        )
        st.caption(
            "Réplica del dashboard *Recovering from a Bitcoin Bear* de Glassnode · "
            "Datos on-chain actualizados cada 24h · Precio cada 1h"
        )
    with col_cache:
        cache_keys = {
            "Precio":         "btc_daily",
            "Realized Price": "bgeo_realized_price",
            "aSOPR":          "bgeo_asopr",
            "MVRV":           "bgeo_mvrv",
            "Supply Profit":  "bgeo_supply_profit",
            "New Addresses":  "blockchain_new_addresses",
            "Fee Revenue":    "coinmetrics_fee_revenue",
        }
        age_lines = [f"**{k}:** {cache_age_str(v)}" for k, v in cache_keys.items()]
        st.caption("  \n".join(age_lines))
        st.caption(f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    main()
