# Recovering From a Bitcoin Bear — Dashboard

This dashboard is designed to aide with identification of transitional periods between a Bitcoin Bear, and a more healthy market trend. It seeks confluence between the following on-chain analysis concepts, aligned with improving network fundamentals:

1. Spot Prices trading above key Pricing Models (both technical and on-chain)
2. Increasing momentum in network utilization (higher on-chain activity, increased network congestion, more fee revenue)
3. Market Profitability Returning (indicating seller exhaustion, profits are being taken and market is absorbing sell-side)
4. Balance of USD Wealth is in favor of longer-term HODLers (indicating that high conviction holders are the dominant owners of the coin supply)

> This chart will turn **light blue** when 5-of-8 indicators are triggered, and **dark blue** when all 8 are triggered. The black curve presents the number of triggered indicators (indexed to 1). Each colored bar is associated with a concept listed above and will activate when both input conditions are met.
>
> **Hint:** As a larger number of indicator bars align at the same time (confluence), the greater the probability that Bitcoin is experiencing a period of relative market strength.

---

## Pricing Models

### 🔔 Signal #1: Price Trading Above 200-day SMA

Since the 200-day SMA is so widely observed by market analysts, it tends to carry significant weight on investor psychology when it is broken convincingly. Often it is considered as a minimum macro bull/bear threshold level.

### 🔔 Signal #2: Price Trading Above Realized Price

When spot prices trade and remain above the Realized Price, it signifies that the average Bitcoin investor is now holding an unrealized profit, and are now under a smaller degree of acute financial stress.

**Indicator Result**

This metric will flash when both of these conditions are met, indicating spot prices are now trading above both key pricing models. This combines both on-chain and technical analysis.

---

## New Address Momentum

### 🔔 Signal: Monthly Activity > Yearly Activity

Early bull markets are often characterized by an uptick in daily new users, more transaction throughput, and increased demand for blockspace.

When the faster 30-day SMA of New Addresses breaks above the 365-day SMA, it indicates a near term expansion in on-chain activity. Sustained periods of this condition are typical of improving network fundamentals and growing utilization.

**Indicator Result**

This metric will flash when this condition is met, indicating that New Address Momentum is constructive.

---

## Fee Revenue Momentum

### 🔔 Signal: 2yr Fee Revenue Z-Score > 0

A sustained uptick in fee revenue as a proportion of the total reward indicates that Bitcoin blocks are full, and there is growing demand for transaction activity. Given the constrained blocksize of Bitcoin, this has historically provided a valuable early indicator of a macro trend shift in the network demand profile.

**Indicator Result**

This metric will flash when this condition is met, indicating that the Fee Revenue Z-Score is positive and constructive.

---

## aSOPR in Profit

### 🔔 Signal: aSOPR (30D-SMA) > 1.0

aSOPR breaking and holding above 1.0 signifies that the market is now, on average, realizing profits in on-chain spends. This generally aligns with both a healthier inflow of demand (to absorb profit taking), and a more constructive opinion of the asset.

Since aSOPR only considers the profit/loss on a per spent output basis (no coin volume considered), it equally weights shrimps and whales, providing a view of the widest cross-section of the market.

> **Hint:** A medium-term moving average of 30-days is selected for this metric as it provides a slower, but higher conviction signal that a sustained recovery may be underway.

**Indicator Result**

This metric will flash when this condition is met, indicating that the average spent output is realizing a profit.

---

## Realized P/L Ratio

### 🔔 Signal: Realized P/L Ratio (30D-SMA) > 1.0

Realized P/L Ratio breaking and holding above 1.0 signifies that the market is now realizing a greater proportion of USD denominated profits than losses. This generally signifies that sellers with unrealized losses have been exhausted, and a healthier inflow of demand exists to absorb profit taking.

Unlike the aSOPR model above, this indicator accounts for the total realized profit/loss. Thus larger transactors (like whales) will carry greater influence than smaller ones (like shrimp).

> **Hint:** A medium-term moving average of 30-days is selected for this metric as it provides a slower, but higher conviction signal that a sustained recovery may be underway.

**Indicator Result**

This metric will flash when this condition is met, indicating that the USD denominated volume of Realized Profits exceeds Realized Losses.

---

## RHODL Multiple (90-Day)

### 🔔 Signal: RHODL Multiple in Uptrend over 90-days

The RHODL Ratio is an oscillator capturing the balance between USD denominated value held in 1-week old coins, compared to 1y–2y old coins.

- **Higher Values** indicate a dominance in 1-week old coins.
- **Lower Values** indicate a dominance in 1y–2y old coins.

The RHODL Multiple is calculated as `RHODL / sma(RHODL, 365)` to form a horizontal oscillator.

When the RHODL Multiple transitions into an uptrend over a 90-day window, it indicates that USD denominated wealth is starting to shift back towards new demand inflows. This indicates profits are being taken, the market is capable of absorbing them, and that longer-term holders are starting to spend coins.

> **Hint:** This metric will flash when this condition is met, indicating that the RHODL Multiple is trending higher over a 90-day window.

---

## BTC Supply in Profit Uptrend

### 🔔 Signal: Supply in Profit Trend (90D-EMA) is Positive

During positive market trends, the volume of BTC supply that was acquired at lower prices tends to increase, putting more supply into an unrealized profit. As investors take profits, coins are revalued to higher realized prices, and if the market trend reverses, these coins move into an unrealized loss.

Macro trend shifts in the volume of Supply in Profit can signal when a heavy concentration of investor cost basis has recently transitioned between unrealized profit or loss. Often these occur near macro market cycle changes.

> **Hint:** A longer-term 90-day EMA basis is selected for this metric as it provides a slower, but higher conviction signal that a macro market transition may be underway.

**Indicator Result**

This metric will flash when this condition is met, indicating that the average spent output is realizing a profit.

---

## Dashboard Introduction Guide

> *Published: 14 January 2023*

Bitcoin has rallied from $16.5k to $21.0k over the last week, giving the market long-awaited relief after the painful 2022 bear market. Whilst this is encouraging for the bulls, it is important to keep ourselves grounded in the fundamentals.

### Analysis tools for navigating bear markets:

- Key Pricing models with psychological significance.
- On-chain activity as a gauge on network usage.
- Profitability to indicate the changing of the tides.
- Supply dynamics indicating a favourable balance of wealth.
