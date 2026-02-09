"""
Investor Insights: How Legends Would Invest Today
===================================================
Step-based portfolio builder inspired by the Investor Skills Engine.
Pick markets, pick investors, configure weights, get a blended portfolio
with exact share counts and costs — all from real yfinance data.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
import math
from typing import Dict, Tuple, Any, List

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG + CUSTOM CSS
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="Investor Insights", page_icon="📊", layout="wide")

st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp { background-color: #0c0c14; }
    section[data-testid="stSidebar"] { background-color: #10101a; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .step-label {
        font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
        color: rgba(255,255,255,0.4); font-weight: 600; margin-bottom: 12px;
        font-family: monospace;
    }
    .market-card, .investor-card {
        padding: 12px 16px; border-radius: 10px; cursor: pointer;
        transition: all 0.2s ease; border: 1.5px solid rgba(255,255,255,0.07);
        background: rgba(255,255,255,0.02);
    }
    .market-card-selected, .investor-card-selected {
        background: rgba(255,255,255,0.08) !important;
        border: 1.5px solid rgba(255,255,255,0.3) !important;
    }
    .metric-box {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 16px; text-align: right;
    }
    .result-card {
        background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px; padding: 24px; margin-bottom: 20px;
    }
    div[data-testid="stExpander"] { border-color: rgba(255,255,255,0.08) !important; }
    .disclaimer-text {
        font-size: 11px; color: rgba(255,255,255,0.3); line-height: 1.7; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# MARKETS
# ═══════════════════════════════════════════════════════════════

MARKETS = {
    "sweden": {
        "label": "Sverige", "flag": "🇸🇪", "hint": "OMX Stockholm",
        "tickers": ["INVE-B.ST", "VOLV-B.ST", "ERIC-B.ST", "ASSA-B.ST", "ATCO-A.ST",
                     "SEB-A.ST", "SHB-A.ST", "HEXA-B.ST", "SAND.ST", "ABB.ST",
                     "ALFA.ST", "ESSITY-B.ST", "SWED-A.ST", "SKF-B.ST", "TELIA.ST",
                     "ELUX-B.ST", "KINV-B.ST", "LUND-B.ST", "GETI-B.ST", "NIBE-B.ST"],
    },
    "us": {
        "label": "USA", "flag": "🇺🇸", "hint": "S&P 500 / Nasdaq",
        "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "TSLA",
                     "UNH", "JNJ", "V", "JPM", "PG", "MA", "HD", "DIS", "NFLX",
                     "ADBE", "CRM", "PFE"],
    },
    "europe": {
        "label": "Europa", "flag": "🇪🇺", "hint": "Euronext / FTSE / DAX",
        "tickers": ["ASML.AS", "MC.PA", "SAP.DE", "SIE.DE", "NESN.SW", "ROG.SW",
                     "NOVN.SW", "AZN.L", "SHEL.L", "ULVR.L", "OR.PA", "TTE.PA",
                     "BAS.DE", "ALV.DE", "DTE.DE", "BAYN.DE", "BMW.DE", "VOW3.DE",
                     "AI.PA", "BN.PA"],
    },
    "asia": {
        "label": "Asien", "flag": "🇯🇵", "hint": "Nikkei / Hang Seng",
        "tickers": ["7203.T", "6758.T", "9984.T", "6861.T", "8306.T",
                     "9433.T", "6501.T", "7267.T", "4502.T", "6902.T",
                     "TSM", "005930.KS", "000660.KS", "2330.TW", "9988.HK"],
    },
    "custom": {
        "label": "Egna ticker", "flag": "✏️", "hint": "Ange egna tickers",
        "tickers": [],
    },
}

# ═══════════════════════════════════════════════════════════════
# INVESTORS
# ═══════════════════════════════════════════════════════════════

INVESTORS = [
    {
        "id": "buffett", "name": "Warren Buffett", "strategy": "Value Investing",
        "color": "#48bb78",
        "bio": "Warren Buffett (born 1930) is an American investor, CEO of Berkshire Hathaway. Known as the 'Oracle of Omaha,' he buys undervalued companies with strong competitive moats, consistent earnings, and excellent management. Favorite holding period: forever.",
    },
    {
        "id": "lynch", "name": "Peter Lynch", "strategy": "Growth at Reasonable Price",
        "color": "#f6ad55",
        "bio": "Peter Lynch (born 1944) managed Fidelity's Magellan Fund 1977-1990, achieving 29% annual returns. He advocated 'invest in what you know' — everyday companies with growth potential at fair prices. Sought tenbaggers.",
    },
    {
        "id": "soros", "name": "George Soros", "strategy": "Global Macro",
        "color": "#b794f4",
        "bio": "George Soros (born 1930) is a Hungarian-American billionaire, founder of Soros Fund Management. Known for breaking the Bank of England in 1992. Applies reflexivity theory — markets influenced by perceptions creating feedback loops.",
    },
    {
        "id": "dalio", "name": "Ray Dalio", "strategy": "Risk Parity",
        "color": "#4fd1c5",
        "bio": "Ray Dalio (born 1949) founded Bridgewater Associates, the world's largest hedge fund. Pioneered risk parity and 'All Weather' portfolios. Emphasizes economic cycles, diversification, and balancing risk across environments.",
    },
    {
        "id": "wood", "name": "Cathie Wood", "strategy": "Disruptive Innovation",
        "color": "#a78bfa",
        "bio": "Cathie Wood (born 1955) is founder/CEO/CIO of ARK Invest. Specializes in disruptive tech: AI, genomics, robotics, blockchain, EVs. Uses Wright's Law for cost modeling. 5-year horizon, revenue growth over profitability.",
    },
    {
        "id": "icahn", "name": "Carl Icahn", "strategy": "Activist Contrarian",
        "color": "#f56565",
        "bio": "Carl Icahn (born 1936) is an American billionaire activist investor. He targets undervalued companies, pushing for board changes, spin-offs, buybacks, or sales to maximize shareholder value. Thinks like an owner.",
    },
    {
        "id": "templeton", "name": "John Templeton", "strategy": "Global Value",
        "color": "#a0c45a",
        "bio": "Sir John Templeton (1912-2008) pioneered international investing. His principle: seek 'maximum pessimism' — buy markets and companies everyone else has abandoned. Willing to hold 5+ years. Contrarian global thinker.",
    },
    {
        "id": "livermore", "name": "Jesse Livermore", "strategy": "Momentum & Speculation",
        "color": "#fc8181",
        "bio": "Jesse Livermore (1877-1940) was a legendary early 20th century trader. Pioneer of tape reading and momentum trading. Rules: follow the trend, pyramid winners, cut losers fast. 'The market is always right.'",
    },
    {
        "id": "lundberg", "name": "Fredrik Lundberg", "strategy": "Patient Value (Nordic)",
        "color": "#68d391",
        "bio": "Fredrik Lundberg (born 1951) is Sweden's Warren Buffett. Through Lundbergs AB he built a portfolio of Nordic quality companies — Handelsbanken, Sandvik, Skanska, Husqvarna. Extremely patient, buys and holds for decades.",
    },
    {
        "id": "wallenberg", "name": "Marcus Wallenberg", "strategy": "Industrial Dynasty",
        "color": "#90cdf4",
        "bio": "Marcus Wallenberg (born 1956) represents Sweden's most powerful investor dynasty. Through Investor AB they control ABB, Atlas Copco, SEB, Ericsson, AstraZeneca. Active long-term industrial ownership thinking in generations.",
    },
    {
        "id": "gardell", "name": "Christer Gardell", "strategy": "European Activist",
        "color": "#fbb6ce",
        "bio": "Christer Gardell (born 1960) co-founded Cevian Capital, Europe's largest activist fund. Targets undervalued companies, pushing for operational changes and restructuring to unlock value. Data-driven and persistent.",
    },
    {
        "id": "bennet", "name": "Carl Bennet", "strategy": "Sustainable Long-Term",
        "color": "#fbd38d",
        "bio": "Carl Bennet (born 1951) is a Swedish industrialist focusing on active ownership in medtech and industrials. Prioritizes sustainability, knowledge-driven growth, and long-term success. Owner of Getinge, Elanders, Lifco.",
    },
]

INV_BY_ID = {inv["id"]: inv for inv in INVESTORS}

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _get(info: dict, key: str, default=None):
    val = info.get(key, default)
    return default if val is None or val == "N/A" else val


def get_price(info: dict) -> float:
    return _get(info, "currentPrice") or _get(info, "regularMarketPrice") or _get(info, "previousClose", 0.0)


def fmt_sek(n):
    if n >= 1_000_000:
        return f"{n:,.0f}".replace(",", " ")
    return f"{n:,.0f}".replace(",", " ")


def fmt_pct(n, decimals=1):
    return f"{n:.{decimals}f}%"


# ═══════════════════════════════════════════════════════════════
# DATA FETCHING (cached)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)
def fetch_stock_data(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
            return {"error": f"No data for '{ticker}'"}
        hist = t.history(period="1y")
        return {"info": info, "history": hist}
    except Exception as e:
        return {"error": str(e)}


def compute_extras(info: dict, hist: pd.DataFrame) -> dict:
    extras = {}
    if not hist.empty:
        first, last = hist["Close"].iloc[0], hist["Close"].iloc[-1]
        extras["52w_change"] = (last - first) / first * 100 if first and first > 0 else None
        hi, lo = hist["Close"].max(), hist["Close"].min()
        extras["52w_range_pct"] = (hi - lo) / hi * 100 if hi and hi > 0 else None
        extras["avg_volume"] = hist["Volume"].mean()
    else:
        extras["52w_change"] = extras["52w_range_pct"] = extras["avg_volume"] = None

    peg = _get(info, "pegRatio")
    if peg is None:
        pe = _get(info, "trailingPE")
        growth = _get(info, "earningsQuarterlyGrowth") or _get(info, "earningsGrowth")
        if pe and growth and growth > 0:
            peg = pe / (growth * 100)
    extras["pegRatio"] = peg
    sector = _get(info, "sector", "")
    extras["sector_lower"] = sector.lower() if sector else ""
    return extras


# ═══════════════════════════════════════════════════════════════
# SCORING FUNCTIONS — one per investor
# ═══════════════════════════════════════════════════════════════

def score_buffett(info, extras):
    s, r = 0, []
    pe = _get(info, "trailingPE")
    roe = _get(info, "returnOnEquity")
    dte = _get(info, "debtToEquity")
    fcf = _get(info, "freeCashflow")
    te, fe = _get(info, "trailingEps"), _get(info, "forwardEps")
    if pe is not None and pe < 15: s += 30; r.append(f"Low P/E ({pe:.1f})")
    if roe is not None and roe > 0.15: s += 20; r.append(f"High ROE ({roe*100:.1f}%)")
    if dte is not None and dte < 50: s += 20; r.append(f"Low D/E ({dte:.1f})")
    if fcf is not None and fcf > 0: s += 15; r.append("Positive FCF")
    if te and fe and te > 0 and fe > te: s += 15; r.append("Growing EPS")
    return min(s, 100), "; ".join(r) or "Low match on value metrics."


def score_lynch(info, extras):
    s, r = 0, []
    peg = extras.get("pegRatio")
    pe = _get(info, "trailingPE")
    eg = _get(info, "earningsGrowth")
    rg = _get(info, "revenueGrowth")
    ins = _get(info, "heldPercentInsiders")
    if peg is not None and peg < 1: s += 30; r.append(f"PEG < 1 ({peg:.2f})")
    if eg is not None and eg > 0.15: s += 20; r.append(f"Earnings growth {eg*100:.1f}%")
    if pe is not None and 10 <= pe <= 20: s += 20; r.append(f"Reasonable P/E ({pe:.1f})")
    if ins is not None and ins > 0.10: s += 15; r.append(f"Insider {ins*100:.1f}%")
    if rg is not None and rg > 0.10: s += 15; r.append(f"Sales growth {rg*100:.1f}%")
    return min(s, 100), "; ".join(r) or "Limited GARP signals."


def score_soros(info, extras):
    s, r = 0, []
    beta = _get(info, "beta")
    pe = _get(info, "trailingPE")
    ret52 = extras.get("52w_change")
    vol = _get(info, "volume")
    avg_vol = extras.get("avg_volume")
    if beta is not None and beta > 1.2: s += 25; r.append(f"High beta ({beta:.2f})")
    if ret52 is not None and ret52 > 20: s += 25; r.append(f"Momentum ({ret52:.0f}%)")
    if vol and avg_vol and avg_vol > 0 and vol > avg_vol: s += 20; r.append("High volume")
    if pe is not None and (pe > 25 or pe < 10): s += 15; r.append(f"Reflexivity (P/E {pe:.1f})")
    sec = extras.get("sector_lower", "")
    if any(x in sec for x in ["energy", "financial", "basic materials"]): s += 15; r.append("Macro sector")
    return min(s, 100), "; ".join(r) or "Limited macro signals."


def score_dalio(info, extras):
    s, r = 0, []
    beta = _get(info, "beta")
    dy = _get(info, "dividendYield")
    cr = _get(info, "currentRatio")
    sec = extras.get("sector_lower", "")
    if beta is not None and beta < 1: s += 30; r.append(f"Low beta ({beta:.2f})")
    if dy is not None and dy > 0.02: s += 20; r.append(f"Div yield {dy*100:.1f}%")
    if cr is not None and cr > 2: s += 20; r.append(f"Current ratio {cr:.1f}")
    if any(x in sec for x in ["consumer defensive", "utilities", "healthcare", "industrials"]): s += 15; r.append("Resilient sector")
    if beta is not None and beta < 0.8: s += 15; r.append("Very low correlation")
    return min(s, 100), "; ".join(r) or "Limited all-weather signals."


def score_wood(info, extras):
    s, r = 0, []
    rg = _get(info, "revenueGrowth")
    fpe = _get(info, "forwardPE")
    beta = _get(info, "beta")
    ret52 = extras.get("52w_change")
    sec = extras.get("sector_lower", "")
    if rg is not None and rg > 0.20: s += 30; r.append(f"Revenue growth {rg*100:.1f}%")
    if fpe is not None and fpe > 30: s += 20; r.append(f"High fwd P/E ({fpe:.1f})")
    if any(d in sec for d in ["technology", "healthcare", "communication", "financial services"]): s += 20; r.append("Disruptive sector")
    if beta is not None and beta > 1.5: s += 15; r.append(f"High beta ({beta:.2f})")
    if ret52 is not None and ret52 > 15: s += 15; r.append(f"Momentum ({ret52:.0f}%)")
    return min(s, 100), "; ".join(r) or "Limited disruption signals."


def score_icahn(info, extras):
    s, r = 0, []
    pe = _get(info, "trailingPE")
    pb = _get(info, "priceToBook")
    cash = _get(info, "totalCash")
    mcap = _get(info, "marketCap")
    ret52 = extras.get("52w_change")
    roe = _get(info, "returnOnEquity")
    assets = _get(info, "totalAssets")
    if pe is not None and pe < 12: s += 30; r.append(f"Low P/E ({pe:.1f})")
    if pb is not None and pb < 1: s += 25; r.append(f"Low P/B ({pb:.2f})")
    if cash and mcap and mcap > 0 and (cash / mcap) > 0.10: s += 20; r.append(f"Cash rich ({cash/mcap*100:.0f}%)")
    if ret52 is not None and ret52 < 0: s += 15; r.append(f"Underperforming ({ret52:.1f}%)")
    if roe is not None and roe < 0.10 and assets and assets > 0: s += 10; r.append("Activist potential")
    return min(s, 100), "; ".join(r) or "Limited contrarian signals."


def score_templeton(info, extras):
    s, r = 0, []
    pe = _get(info, "trailingPE")
    pb = _get(info, "priceToBook")
    ret52 = extras.get("52w_change")
    dy = _get(info, "dividendYield")
    eg = _get(info, "earningsGrowth")
    if pe is not None and pe < 12: s += 30; r.append(f"Low P/E ({pe:.1f})")
    if ret52 is not None and ret52 < -10: s += 25; r.append(f"Maximum pessimism ({ret52:.0f}%)")
    if pb is not None and pb < 1.5: s += 20; r.append(f"Low P/B ({pb:.2f})")
    if dy is not None and dy > 0.03: s += 15; r.append(f"High div yield {dy*100:.1f}%")
    if eg is not None and eg > 0.05: s += 10; r.append("Earnings recovery")
    return min(s, 100), "; ".join(r) or "Limited deep-value signals."


def score_livermore(info, extras):
    s, r = 0, []
    ret52 = extras.get("52w_change")
    beta = _get(info, "beta")
    vol = _get(info, "volume")
    avg_vol = extras.get("avg_volume")
    rg = _get(info, "revenueGrowth")
    if ret52 is not None and ret52 > 30: s += 30; r.append(f"Strong momentum ({ret52:.0f}%)")
    elif ret52 is not None and ret52 > 15: s += 20; r.append(f"Good momentum ({ret52:.0f}%)")
    if beta is not None and beta > 1.3: s += 25; r.append(f"High beta ({beta:.2f})")
    if vol and avg_vol and avg_vol > 0 and vol > avg_vol * 1.5: s += 20; r.append("Breakout volume")
    elif vol and avg_vol and avg_vol > 0 and vol > avg_vol: s += 10; r.append("Above avg volume")
    if rg is not None and rg > 0.15: s += 15; r.append(f"Revenue growth {rg*100:.1f}%")
    return min(s, 100), "; ".join(r) or "Limited momentum signals."


def score_lundberg(info, extras):
    s, r = 0, []
    pb = _get(info, "priceToBook")
    roa = _get(info, "returnOnAssets")
    payout = _get(info, "payoutRatio")
    margin = _get(info, "profitMargins")
    rng = extras.get("52w_range_pct")
    if pb is not None and pb < 1.5: s += 30; r.append(f"Low P/B ({pb:.2f})")
    if roa is not None and roa > 0.08: s += 20; r.append(f"ROA {roa*100:.1f}%")
    if payout is not None and payout > 0.30: s += 20; r.append(f"Payout {payout*100:.0f}%")
    if rng is not None and rng < 50: s += 15; r.append(f"Low volatility ({rng:.0f}%)")
    if margin is not None and margin > 0.10: s += 15; r.append(f"Margin {margin*100:.1f}%")
    return min(s, 100), "; ".join(r) or "Limited Nordic value signals."


def score_wallenberg(info, extras):
    s, r = 0, []
    eg = _get(info, "earningsGrowth")
    cr = _get(info, "currentRatio")
    dte = _get(info, "debtToEquity")
    beta = _get(info, "beta")
    sec = extras.get("sector_lower", "")
    if eg is not None and eg > 0.12: s += 25; r.append(f"Earnings growth {eg*100:.1f}%")
    if cr is not None and cr > 1.5: s += 20; r.append(f"Current ratio {cr:.1f}")
    if dte is not None and dte < 80: s += 20; r.append(f"Low debt ({dte:.1f})")
    if any(x in sec for x in ["technology", "healthcare", "industrials"]): s += 20; r.append("Innovation sector")
    if beta is not None and beta < 1: s += 15; r.append(f"Low beta ({beta:.2f})")
    return min(s, 100), "; ".join(r) or "Limited dynasty signals."


def score_gardell(info, extras):
    s, r = 0, []
    target = _get(info, "targetMeanPrice")
    price = get_price(info)
    roe = _get(info, "returnOnEquity")
    assets = _get(info, "totalAssets")
    eg = _get(info, "earningsGrowth")
    ret52 = extras.get("52w_change")
    if target and price and price > 0 and (target - price) / price > 0.20:
        s += 30; r.append(f"Analyst upside {(target-price)/price*100:.0f}%")
    if ret52 is not None and ret52 < 0: s += 20; r.append(f"Underperforming ({ret52:.1f}%)")
    fs = _get(info, "floatShares"); so = _get(info, "sharesOutstanding")
    if fs and so and so > 0 and fs / so > 0.50: s += 20; r.append("High free float")
    if roe is not None and roe < 0.10 and assets and assets > 0: s += 15; r.append("Governance weakness")
    if eg is not None and eg < 0: s += 15; r.append("Turnaround potential")
    return min(s, 100), "; ".join(r) or "Limited activist signals."


def score_bennet(info, extras):
    s, r = 0, []
    pb = _get(info, "priceToBook")
    roe = _get(info, "returnOnEquity")
    payout = _get(info, "payoutRatio")
    margin = _get(info, "profitMargins")
    dte = _get(info, "debtToEquity")
    if pb is not None and pb < 2: s += 25; r.append(f"P/B {pb:.2f}")
    if roe is not None and roe > 0.10: s += 20; r.append(f"ROE {roe*100:.1f}%")
    if payout is not None and payout > 0.25: s += 20; r.append(f"Payout {payout*100:.0f}%")
    if margin is not None and margin > 0.08: s += 20; r.append(f"Margin {margin*100:.1f}%")
    if dte is not None and dte < 80: s += 15; r.append(f"Low debt ({dte:.1f})")
    return min(s, 100), "; ".join(r) or "Limited sustainable signals."


SCORE_FUNCTIONS = {
    "buffett": score_buffett, "lynch": score_lynch, "soros": score_soros,
    "dalio": score_dalio, "wood": score_wood, "icahn": score_icahn,
    "templeton": score_templeton, "livermore": score_livermore,
    "lundberg": score_lundberg, "wallenberg": score_wallenberg,
    "gardell": score_gardell, "bennet": score_bennet,
}


# ═══════════════════════════════════════════════════════════════
# ANALYSIS + PORTFOLIO BLENDING
# ═══════════════════════════════════════════════════════════════

def analyse_stock(ticker: str) -> dict:
    data = fetch_stock_data(ticker)
    if "error" in data:
        return {"ticker": ticker, "error": data["error"]}
    info, hist = data["info"], data["history"]
    extras = compute_extras(info, hist)
    price = get_price(info)
    currency = _get(info, "currency", "")

    scores, explanations = {}, {}
    for inv_id, func in SCORE_FUNCTIONS.items():
        sc, ex = func(info, extras)
        scores[inv_id] = sc
        explanations[inv_id] = ex

    return {
        "ticker": ticker,
        "name": _get(info, "shortName", ticker),
        "price": price,
        "currency": currency,
        "sector": _get(info, "sector", "N/A"),
        "pe": _get(info, "trailingPE"),
        "pb": _get(info, "priceToBook"),
        "roe": _get(info, "returnOnEquity"),
        "div_yield": _get(info, "dividendYield"),
        "beta": _get(info, "beta"),
        "scores": scores,
        "explanations": explanations,
    }


def blend_and_allocate(stock_results: list, weights: dict, budget: float, max_stocks: int, currency: str = "SEK"):
    """
    Compute weighted composite scores, allocate budget proportionally,
    calculate share counts and costs.
    """
    valid = [r for r in stock_results if "error" not in r and r["price"] > 0]
    if not valid:
        return []

    total_w = sum(weights.values())
    if total_w == 0:
        return []
    norm = {k: v / total_w for k, v in weights.items() if v > 0}

    # Compute composite score for each stock
    rows = []
    for r in valid:
        composite = sum(r["scores"].get(inv_id, 0) * w for inv_id, w in norm.items())
        contributors = []
        for inv_id, w in norm.items():
            sc = r["scores"].get(inv_id, 0)
            if sc > 0:
                contributors.append({
                    "investor_id": inv_id,
                    "score": sc,
                    "weight": weights.get(inv_id, 0),
                    "contribution": sc * w,
                    "reason": r["explanations"].get(inv_id, ""),
                })
        rows.append({
            "ticker": r["ticker"],
            "name": r["name"],
            "price": r["price"],
            "currency": r["currency"],
            "composite": round(composite, 1),
            "contributors": sorted(contributors, key=lambda c: c["contribution"], reverse=True),
        })

    # Sort by composite, take top max_stocks
    rows.sort(key=lambda x: x["composite"], reverse=True)
    rows = rows[:max_stocks]

    # Normalize allocations to 100%
    total_score = sum(r["composite"] for r in rows)
    if total_score == 0:
        return rows

    for r in rows:
        r["allocation"] = r["composite"] / total_score * 100

    # Calculate shares
    for r in rows:
        target_amount = budget * (r["allocation"] / 100)
        r["target_amount"] = target_amount
        r["shares"] = int(target_amount // r["price"]) if r["price"] > 0 else 0
        r["cost"] = r["shares"] * r["price"]

    # Redistribute remainder — buy extra shares where cheapest
    total_cost = sum(r["cost"] for r in rows)
    remainder = budget - total_cost
    max_remainder = budget * 0.10
    safety = 0
    while remainder > max_remainder and safety < 200:
        safety += 1
        bought = False
        for r in rows:
            if r["price"] <= remainder:
                r["shares"] += 1
                r["cost"] += r["price"]
                remainder -= r["price"]
                bought = True
                if remainder <= max_remainder:
                    break
        if not bought:
            break

    total_cost = sum(r["cost"] for r in rows)
    remainder = budget - total_cost

    return rows, total_cost, remainder


# ═══════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════

if "selected_markets" not in st.session_state:
    st.session_state.selected_markets = []
if "selected_investors" not in st.session_state:
    st.session_state.selected_investors = []
if "market_configs" not in st.session_state:
    st.session_state.market_configs = {}
if "results" not in st.session_state:
    st.session_state.results = None
if "custom_tickers" not in st.session_state:
    st.session_state.custom_tickers = "AAPL, MSFT, TSLA"


# ═══════════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div style="margin-bottom: 8px;">
    <span style="font-size: 10px; font-family: monospace; letter-spacing: 0.15em;
    text-transform: uppercase; color: rgba(255,255,255,0.35); font-weight: 600;">
    Investor Insights Engine</span>
</div>
""", unsafe_allow_html=True)
st.markdown("# Build Your Portfolio With the Legends")
st.markdown(
    '<p style="font-size: 14px; color: rgba(255,255,255,0.55); line-height: 1.6;">'
    "Select markets and investors, configure the mix per market, and generate "
    "blended portfolios with exact share counts — all from real financial data.</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# STEP 01 — SELECT MARKETS
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="step-label">01 — Select Markets</div>', unsafe_allow_html=True)

market_cols = st.columns(len(MARKETS))
for i, (mid, mdata) in enumerate(MARKETS.items()):
    with market_cols[i]:
        selected = mid in st.session_state.selected_markets
        label = f"{mdata['flag']} {mdata['label']}"
        if st.button(
            label,
            key=f"market_{mid}",
            use_container_width=True,
            type="primary" if selected else "secondary",
        ):
            if selected:
                st.session_state.selected_markets.remove(mid)
            else:
                st.session_state.selected_markets.append(mid)
                if mid not in st.session_state.market_configs:
                    st.session_state.market_configs[mid] = {
                        "mode": "equal", "weights": {}, "amount": 100000, "max_stocks": 10,
                    }
            st.rerun()

if st.session_state.selected_markets:
    tags = " ".join(
        f"`{MARKETS[m]['flag']} {MARKETS[m]['label']}`"
        for m in st.session_state.selected_markets
    )
    st.markdown(f"**Selected:** {tags}")

# Custom tickers input
if "custom" in st.session_state.selected_markets:
    st.session_state.custom_tickers = st.text_input(
        "Enter comma-separated tickers",
        value=st.session_state.custom_tickers,
        help="e.g. AAPL, MSFT, VOLV-B.ST",
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# STEP 02 — SELECT INVESTORS
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="step-label">02 — Select Investors</div>', unsafe_allow_html=True)

# Select all / deselect all
sa_col1, sa_col2, _ = st.columns([1, 1, 4])
with sa_col1:
    if st.button("Select All", key="sel_all"):
        st.session_state.selected_investors = [inv["id"] for inv in INVESTORS]
        st.rerun()
with sa_col2:
    if st.button("Deselect All", key="desel_all"):
        st.session_state.selected_investors = []
        st.rerun()

# Investor grid — 3 columns
inv_cols = st.columns(3)
for i, inv in enumerate(INVESTORS):
    col = inv_cols[i % 3]
    with col:
        selected = inv["id"] in st.session_state.selected_investors
        check = "✅" if selected else "⬜"
        btn_label = f"{check} **{inv['name']}**\n\n`{inv['strategy']}`"
        if st.button(
            f"{check} {inv['name']} — {inv['strategy']}",
            key=f"inv_{inv['id']}",
            use_container_width=True,
        ):
            if selected:
                st.session_state.selected_investors.remove(inv["id"])
            else:
                st.session_state.selected_investors.append(inv["id"])
            st.rerun()

if st.session_state.selected_investors:
    st.markdown(
        f"**{len(st.session_state.selected_investors)}** of "
        f"**{len(INVESTORS)}** investors selected"
    )

# Investor bios expander
with st.expander("Investor Bios & Info"):
    for inv in INVESTORS:
        if inv["id"] in st.session_state.selected_investors:
            st.markdown(
                f'<div style="margin-bottom: 12px; padding: 10px 14px; '
                f'border-left: 3px solid {inv["color"]}; '
                f'background: rgba(255,255,255,0.02); border-radius: 0 8px 8px 0;">'
                f'<strong style="color: {inv["color"]};">{inv["name"]}</strong> '
                f'<span style="font-size: 11px; color: rgba(255,255,255,0.4); '
                f'font-family: monospace;">({inv["strategy"]})</span><br>'
                f'<span style="font-size: 13px; color: rgba(255,255,255,0.7);">{inv["bio"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# STEP 03 — CONFIGURE EACH MARKET
# ═══════════════════════════════════════════════════════════════

if st.session_state.selected_markets and st.session_state.selected_investors:
    st.markdown('<div class="step-label">03 — Configure Each Market</div>', unsafe_allow_html=True)

    for mid in st.session_state.selected_markets:
        mdata = MARKETS[mid]
        cfg = st.session_state.market_configs.get(mid, {
            "mode": "equal", "weights": {}, "amount": 100000, "max_stocks": 10,
        })

        st.markdown(
            f'<div style="font-size: 18px; font-weight: 700; margin-bottom: 4px;">'
            f'{mdata["flag"]} {mdata["label"]}'
            f'<span style="font-size: 11px; color: rgba(255,255,255,0.35); '
            f'font-family: monospace; margin-left: 10px;">{mdata["hint"]}</span></div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns([1.5, 1, 1.5])

        with c1:
            cfg["amount"] = st.number_input(
                "Investment Amount",
                min_value=0, value=cfg.get("amount", 100000), step=10000,
                key=f"amt_{mid}",
                help="Total amount to invest in this market",
            )

        with c2:
            cfg["max_stocks"] = st.slider(
                "Max Stocks", 5, 20, cfg.get("max_stocks", 10), key=f"max_{mid}",
            )

        with c3:
            mode_options = ["Equal Weight", "Manual"]
            current_idx = 0 if cfg.get("mode", "equal") == "equal" else 1
            mode_choice = st.radio(
                "Investor Mix", mode_options, index=current_idx,
                key=f"mode_{mid}", horizontal=True,
            )
            cfg["mode"] = "equal" if mode_choice == "Equal Weight" else "manual"

        # Investor weights
        active_inv = [inv for inv in INVESTORS if inv["id"] in st.session_state.selected_investors]

        if cfg["mode"] == "equal":
            eq_w = round(100 / len(active_inv), 1) if active_inv else 0
            cfg["weights"] = {inv["id"]: eq_w for inv in active_inv}
            weight_text = "  |  ".join(
                f"**{inv['name']}**: {eq_w:.1f}%" for inv in active_inv
            )
            st.markdown(f"*Equal weight:* {weight_text}")

        elif cfg["mode"] == "manual":
            st.markdown("**Set weights (should sum to 100%):**")
            wcols = st.columns(min(len(active_inv), 4))
            for j, inv in enumerate(active_inv):
                with wcols[j % min(len(active_inv), 4)]:
                    w = cfg["weights"].get(inv["id"], round(100 / len(active_inv), 1))
                    cfg["weights"][inv["id"]] = st.number_input(
                        inv["name"], min_value=0.0, max_value=100.0,
                        value=float(w), step=5.0,
                        key=f"w_{mid}_{inv['id']}",
                    )
            total_w = sum(cfg["weights"].get(inv["id"], 0) for inv in active_inv)
            if abs(total_w - 100) > 1:
                st.warning(f"Weights sum to **{total_w:.1f}%** — should be 100%")
            else:
                st.success(f"Weights sum: {total_w:.1f}% ✓")

        st.session_state.market_configs[mid] = cfg
        st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# GENERATE BUTTON
# ═══════════════════════════════════════════════════════════════

can_generate = (
    len(st.session_state.selected_markets) > 0
    and len(st.session_state.selected_investors) > 0
)

if not can_generate:
    st.info("Select at least one **market** and one **investor** to generate portfolios.")
else:
    n_markets = len(st.session_state.selected_markets)
    btn_text = f"Generate Portfolio{'s' if n_markets > 1 else ''} for {n_markets} Market{'s' if n_markets > 1 else ''}"

    if st.button(btn_text, type="primary", use_container_width=True):
        all_results = {}

        # Gather all tickers per market
        market_tickers = {}
        for mid in st.session_state.selected_markets:
            if mid == "custom":
                tickers = [t.strip().upper() for t in st.session_state.custom_tickers.split(",") if t.strip()]
            else:
                tickers = MARKETS[mid]["tickers"]
            market_tickers[mid] = tickers

        total_tickers = sum(len(t) for t in market_tickers.values())
        progress = st.progress(0, text="Fetching data...")
        done = 0

        for mid in st.session_state.selected_markets:
            tickers = market_tickers[mid]
            cfg = st.session_state.market_configs.get(mid, {
                "mode": "equal", "weights": {}, "amount": 100000, "max_stocks": 10,
            })

            stock_results = []
            for ticker in tickers:
                progress.progress(
                    done / total_tickers,
                    text=f"Analysing {ticker} ({MARKETS[mid]['label']})...",
                )
                stock_results.append(analyse_stock(ticker))
                done += 1

            # Get weights
            active_inv = [inv for inv in INVESTORS if inv["id"] in st.session_state.selected_investors]
            if cfg["mode"] == "equal":
                eq_w = 100 / len(active_inv) if active_inv else 0
                weights = {inv["id"]: eq_w for inv in active_inv}
            else:
                weights = {inv["id"]: cfg["weights"].get(inv["id"], 0) for inv in active_inv}

            result = blend_and_allocate(
                stock_results, weights, cfg["amount"], cfg["max_stocks"],
            )

            all_results[mid] = {
                "portfolio": result[0] if result else [],
                "total_cost": result[1] if result else 0,
                "remainder": result[2] if result else cfg["amount"],
                "weights": weights,
                "stock_results": stock_results,
            }

        progress.progress(1.0, text="Done!")
        st.session_state.results = all_results

# ═══════════════════════════════════════════════════════════════
# STEP 04 — RESULTS
# ═══════════════════════════════════════════════════════════════

if st.session_state.results:
    st.markdown('<div class="step-label">04 — Your Portfolios</div>', unsafe_allow_html=True)

    grand_invested = 0
    grand_remainder = 0

    for mid, res in st.session_state.results.items():
        mdata = MARKETS[mid]
        portfolio = res["portfolio"]
        total_cost = res["total_cost"]
        remainder = res["remainder"]
        weights = res["weights"]

        grand_invested += total_cost
        grand_remainder += remainder

        if not portfolio:
            st.warning(f"{mdata['flag']} {mdata['label']}: No valid stocks found.")
            continue

        st.markdown(
            f'### {mdata["flag"]} {mdata["label"]}'
            f'<span style="font-size: 12px; color: rgba(255,255,255,0.4); '
            f'font-family: monospace; margin-left: 12px;">'
            f'{len(portfolio)} stocks</span>',
            unsafe_allow_html=True,
        )

        # Investor mix summary
        active_weights = {k: v for k, v in weights.items() if v > 0}
        mix_tags = "  ".join(
            f'`{INV_BY_ID[inv_id]["name"]}: {w:.0f}%`'
            for inv_id, w in sorted(active_weights.items(), key=lambda x: -x[1])
        )
        st.markdown(f"**Investor mix:** {mix_tags}")

        # Portfolio table
        max_alloc = max(r["allocation"] for r in portfolio) if portfolio else 1

        table_html = """
        <div style="overflow-x: auto; margin: 12px 0;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; font-family: monospace;">
        <thead>
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
            <th style="padding: 10px 8px; text-align: left; color: rgba(255,255,255,0.45); font-size: 10px; letter-spacing: 0.06em; font-weight: 600;">COMPANY</th>
            <th style="padding: 10px 8px; text-align: left; color: rgba(255,255,255,0.45); font-size: 10px; letter-spacing: 0.06em; font-weight: 600;">TICKER</th>
            <th style="padding: 10px 8px; text-align: left; color: rgba(255,255,255,0.45); font-size: 10px; letter-spacing: 0.06em; font-weight: 600;">WEIGHT</th>
            <th style="padding: 10px 8px; text-align: left; color: rgba(255,255,255,0.45); font-size: 10px; letter-spacing: 0.06em; font-weight: 600; width: 18%;"></th>
            <th style="padding: 10px 8px; text-align: right; color: rgba(255,255,255,0.45); font-size: 10px; letter-spacing: 0.06em; font-weight: 600;">PRICE</th>
            <th style="padding: 10px 8px; text-align: right; color: rgba(255,255,255,0.45); font-size: 10px; letter-spacing: 0.06em; font-weight: 600;">SHARES</th>
            <th style="padding: 10px 8px; text-align: right; color: rgba(255,255,255,0.45); font-size: 10px; letter-spacing: 0.06em; font-weight: 600;">COST</th>
        </tr>
        </thead>
        <tbody>
        """

        for i, stock in enumerate(portfolio):
            hue = (i * 137.5) % 360
            bar_pct = (stock["allocation"] / max_alloc * 100) if max_alloc > 0 else 0
            price_str = f"{stock['price']:,.2f}"
            cost_str = f"{stock['cost']:,.0f}"

            table_html += f"""
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                <td style="padding: 9px 8px; color: rgba(255,255,255,0.8); font-weight: 600; font-family: system-ui, sans-serif; font-size: 12px;">{stock['name']}</td>
                <td style="padding: 9px 8px; color: rgba(255,255,255,0.4); font-size: 11px;">{stock['ticker']}</td>
                <td style="padding: 9px 8px; color: rgba(255,255,255,0.75); font-weight: 600; white-space: nowrap;">{stock['allocation']:.1f}%</td>
                <td style="padding: 9px 8px 9px 0;">
                    <div style="height: 6px; border-radius: 3px; width: {bar_pct}%; min-width: 2px;
                    background-color: hsl({hue}, 42%, 52%); transition: width 0.3s ease;"></div>
                </td>
                <td style="padding: 9px 8px; text-align: right; color: rgba(255,255,255,0.55);">{price_str} {stock['currency']}</td>
                <td style="padding: 9px 8px; text-align: right; color: #fff; font-weight: 700;">{stock['shares']}</td>
                <td style="padding: 9px 8px; text-align: right; color: rgba(255,255,255,0.8); font-weight: 600;">{cost_str}</td>
            </tr>
            """

        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

        # Totals row
        t1, t2 = st.columns(2)
        with t1:
            st.markdown(
                f'<div style="text-align: left;">'
                f'<div style="font-size: 10px; font-family: monospace; color: rgba(255,255,255,0.45); '
                f'letter-spacing: 0.06em; font-weight: 600;">INVESTED</div>'
                f'<div style="font-size: 22px; font-weight: 800; font-family: monospace; color: #fff;">'
                f'{fmt_sek(total_cost)}</div></div>',
                unsafe_allow_html=True,
            )
        with t2:
            st.markdown(
                f'<div style="text-align: right;">'
                f'<div style="font-size: 10px; font-family: monospace; color: rgba(255,255,255,0.45); '
                f'letter-spacing: 0.06em; font-weight: 600;">REMAINING</div>'
                f'<div style="font-size: 22px; font-weight: 800; font-family: monospace; color: rgba(255,255,255,0.5);">'
                f'{fmt_sek(remainder)}</div></div>',
                unsafe_allow_html=True,
            )

        # Contributor breakdown
        with st.expander("Show investor contribution per stock"):
            for stock in portfolio:
                if stock.get("contributors"):
                    contribs = "  ".join(
                        f'`{INV_BY_ID.get(c["investor_id"], {}).get("name", c["investor_id"])}: '
                        f'{c["contribution"]:.1f}pts`'
                        for c in stock["contributors"][:5]
                    )
                    st.markdown(f"**{stock['ticker']}** — {contribs}")
                    for c in stock["contributors"][:3]:
                        inv_name = INV_BY_ID.get(c["investor_id"], {}).get("name", "")
                        st.caption(f"  {inv_name}: {c['reason']}")

        st.markdown("---")

    # Grand totals
    if len(st.session_state.results) > 1:
        st.markdown(
            f'<div style="display: flex; justify-content: space-between; align-items: center; '
            f'padding: 22px 24px; background: rgba(255,255,255,0.03); '
            f'border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; '
            f'flex-wrap: wrap; gap: 16px;">'
            f'<div>'
            f'<div style="font-size: 10px; font-family: monospace; color: rgba(255,255,255,0.45); '
            f'letter-spacing: 0.06em; font-weight: 600;">TOTAL INVESTED</div>'
            f'<div style="font-size: 22px; font-weight: 800; font-family: monospace;">'
            f'{fmt_sek(grand_invested)}</div></div>'
            f'<div style="text-align: right;">'
            f'<div style="font-size: 10px; font-family: monospace; color: rgba(255,255,255,0.45); '
            f'letter-spacing: 0.06em; font-weight: 600;">TOTAL REMAINING</div>'
            f'<div style="font-size: 22px; font-weight: 800; font-family: monospace; color: rgba(255,255,255,0.5);">'
            f'{fmt_sek(grand_remainder)}</div></div></div>',
            unsafe_allow_html=True,
        )

    # Score comparison chart
    st.markdown("### Score Comparison")
    chart_data = []
    for mid, res in st.session_state.results.items():
        for stock in res["portfolio"]:
            for c in stock.get("contributors", []):
                inv_name = INV_BY_ID.get(c["investor_id"], {}).get("name", c["investor_id"])
                chart_data.append({
                    "Ticker": stock["ticker"],
                    "Investor": inv_name,
                    "Score": c["score"],
                })

    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        investor_order = [inv["name"] for inv in INVESTORS if inv["id"] in st.session_state.selected_investors]
        chart = (
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X("Investor:N", sort=investor_order, axis=alt.Axis(labelAngle=-45)),
                y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
                color="Ticker:N",
                xOffset="Ticker:N",
                tooltip=["Ticker", "Investor", "Score"],
            )
            .properties(height=400)
        )
        st.altair_chart(chart, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# DISCLAIMER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    '<p class="disclaimer-text">'
    "Prices are approximate. The portfolios are simulations based on famous investors' "
    "known philosophies and <strong>do not constitute financial advice</strong>. "
    "All investing involves risk — always verify prices, availability, and do your own "
    "analysis before trading."
    "</p>",
    unsafe_allow_html=True,
)
