# BTC Bear Recovery Dashboard — Estado del Proyecto
**Ultima actualizacion:** 2026-05-25

---

## Que es esto
Replica del dashboard "Recovering from a Bitcoin Bear" de Glassnode.
Muestra 8 senales on-chain que confluyen para identificar recuperaciones del mercado bajista de BTC.
- **Ubicacion:** `C:\Users\SEI\btc-bear-recovery\`
- **Stack:** Python 3.12 + Streamlit + Plotly
- **Para correr:** `cd C:\Users\SEI\btc-bear-recovery && streamlit run app.py`

---

## Estado de las 8 Senales

| # | Senal | Fuente | Estado | Archivo |
|---|-------|--------|--------|---------|
| 1 | Price > 200D SMA | Binance/ccxt | LISTA | `modules/price_fetcher.py` |
| 2 | Price > Realized Price | BGeometrics `/v1/realized-price` | LISTA | `modules/bgeometrics_fetcher.py` |
| 3 | New Address Momentum | Blockchain.com `n-unique-addresses` | LISTA | `modules/alt_fetcher.py` |
| 4 | Fee Revenue Z-Score (2yr) | CoinMetrics `FeeTotNtv` | LISTA | `modules/alt_fetcher.py`, `modules/signals.py` |
| 5 | aSOPR (SMA30 > 1.0) | BGeometrics `/v1/asopr` | LISTA | `modules/bgeometrics_fetcher.py` |
| 6 | Realized P/L Ratio (SMA30 > 1.0) | BGeometrics `/v1/realized-profit-loss-ratio` | **BLOQUEADA** (HTTP 500 servidor) | `modules/bgeometrics_fetcher.py` |
| 7 | HODL Multiple (MVRV proxy) | BGeometrics `/v1/mvrv` | **LISTA** | `modules/bgeometrics_fetcher.py` |
| 8 | Supply in Profit | BGeometrics `/v1/supply-profit` | LISTA | `modules/bgeometrics_fetcher.py` |

**7/8 senales listas. Signal 5 bloqueada por bug del servidor BGeometrics.**

---

## Lo que Falta (Tareas Pendientes)

### Tarea A — Signal 5: Realized P/L Ratio (BLOQUEADA por BGeometrics)
- El endpoint `/v1/realized-profit-loss-ratio` devuelve HTTP 500 **de forma persistente**
  (verificado 2026-05-21 y 2026-05-25). Es un bug del servidor de BGeometrics, no rate limit.
- La funcion `get_realized_pnl_ratio()` ya intenta el endpoint — si BGeometrics lo arregla,
  funcionara automaticamente sin cambios de codigo.
- Tile aparecera en gris ("Pendiente") hasta que el servidor responda correctamente.

**Opcional — Plan B con CoinMetrics:**
Si BGeometrics no lo arregla, implementar en `modules/alt_fetcher.py`:
```python
# Realized P/L Ratio aproximado via CoinMetrics
# Campo: RealizedProfit / RealizedLoss -> ratio
```
Y actualizar `app.py` para usar el nuevo fetcher en Signal 5.

---

### Tarea B — Signal 7: RESUELTA (2026-05-25)
- **SOLUCIONADO:** `/v1/mvrv` devuelve HTTP 200 con datos historicos. ✅
- Implementado como proxy de HODL Multiple en `get_hodl_multiple()`.
- Logica: `mvrv[-1] > mvrv[-91]` (tendencia alcista en 90 dias).
- Campo de valor autodetectado por `_fetch` (primer campo no-fecha).

---

## Archivos del Proyecto

```
C:\Users\SEI\btc-bear-recovery\
├── app.py                      # Dashboard Streamlit principal
├── requirements.txt            # Dependencias Python
├── .gitignore
├── ESTADO_PROYECTO.md          # Este archivo
├── modules\
│   ├── cache.py                # Cache JSON en disco (PRICE_TTL=1h, ONCHAIN_TTL=24h)
│   ├── price_fetcher.py        # Precio Binance + SMA/EMA
│   ├── bgeometrics_fetcher.py  # API BGeometrics (senales 2,5,6,7,8)
│   ├── alt_fetcher.py          # Blockchain.com + CoinMetrics (senales 3,4)
│   └── signals.py              # Logica de las 8 senales + evaluate_all_signals()
└── cache\                      # Archivos JSON cacheados (ignorados por git)
```

---

## Como Probar

```powershell
# 1. Ir al proyecto
cd C:\Users\SEI\btc-bear-recovery

# 2. Probar modulos individualmente (requiere internet)
python -c "from modules.price_fetcher import fetch_btc_daily; df=fetch_btc_daily(); print(df.tail(3))"
python -c "from modules.bgeometrics_fetcher import get_realized_price; s=get_realized_price(); print(s.tail(3) if s is not None else 'None')"
python -c "from modules.bgeometrics_fetcher import get_supply_in_profit; s=get_supply_in_profit(); print(s.tail(3) if s is not None else 'None')"

# 3. Lanzar el dashboard
streamlit run app.py
```

---

## Limites de Rate de BGeometrics
- **10 req/hora**, 15 req/dia (sin API key)
- El cache de 24h asegura que no se supere el limite en uso normal
- Si ves HTTP 429, esperar ~1 hora antes de probar nuevos slugs

---

## Notas Tecnicas
- Los archivos JSON estaticos en `charts.bgeometrics.com/files/` estan **desactualizados** 
  (ultimo dato: abril 2022). Usar SOLO la API REST `api.bgeometrics.com/v1/`.
- El campo de `supply-profit` es `supplyProfitBtc` (BTC absoluto, ~12.5M actualmente).
  Para convertir a porcentaje: `/ 21_000_000 * 100`.
- La grafica historica de fondo usa solo senales 1 y 2 (unicas series temporales completas confirmadas).
