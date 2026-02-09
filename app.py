"""
Investor Insights: How Legends Would Invest Today
===================================================
A Streamlit app that simulates how famous investors would invest today
based on their real historical strategies, using real financial data.

DISCLAIMER: This is for educational/simulation purposes only.
            Not financial advice. Consult professionals for investments.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
from typing import Dict, Tuple, List, Any

# ---------------------------------------------------------------------------
# Preset ticker lists
# ---------------------------------------------------------------------------
SP500_TOP = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "TSLA", "UNH", "JNJ"]
OMX_TOP = [
    "INVE-B.ST", "VOLV-B.ST", "ERIC-B.ST", "ASSA-B.ST", "ATCO-A.ST",
    "SEB-A.ST", "SHB-A.ST", "HEXA-B.ST", "SAND.ST", "ABB.ST",
]
DEFAULT_TICKERS = "AAPL, MSFT, GOOGL, INVE-B.ST, VOLV-B.ST"

# ---------------------------------------------------------------------------
# Investor bios
# ---------------------------------------------------------------------------
INVESTOR_BIOS: Dict[str, str] = {
    "Warren Buffett": (
        "Warren Buffett (born 1930) is an American investor, CEO of Berkshire "
        "Hathaway. Known as the 'Oracle of Omaha,' he built his fortune through "
        "value investing, buying undervalued companies with strong fundamentals "
        "and holding long-term."
    ),
    "Peter Lynch": (
        "Peter Lynch (born 1944) is an American investor, managed Fidelity's "
        "Magellan Fund from 1977-1990, achieving 29% annual returns. He "
        "advocated investing in familiar companies with growth potential at "
        "fair prices."
    ),
    "Ray Dalio": (
        "Ray Dalio (born 1949) is an American billionaire, founder of "
        "Bridgewater Associates, the world's largest hedge fund. He pioneered "
        "risk parity and all-weather portfolios, emphasizing economic cycles "
        "and diversification."
    ),
    "Fredrik Lundberg": (
        "Fredrik Lundberg (born 1951) is a Swedish billionaire, CEO of "
        "L E Lundbergforetagen AB. Often compared to Buffett, he focuses on "
        "long-term holdings in industrial and financial firms, building value "
        "through conservative management."
    ),
    "Christer Gardell": (
        "Christer Gardell (born 1960) is a Swedish investor, co-founder of "
        "Cevian Capital, Europe's largest activist fund. He targets undervalued "
        "companies, pushing for operational changes and restructuring to "
        "unlock value."
    ),
    "Jacob Wallenberg": (
        "Jacob Wallenberg (born 1956) is a Swedish businessman, chairman of "
        "Investor AB. Part of the Wallenberg family dynasty, he emphasizes "
        "active ownership in sustainable companies, with interests in banking, "
        "industry, and tech."
    ),
    "Melker Schorling": (
        "Melker Schorling (1947-2023) was a Swedish billionaire, founder of "
        "MSAB. He specialized in turning niche industrial companies into "
        "global leaders through entrepreneurship and efficient management."
    ),
    "Carl Bennet": (
        "Carl Bennet (born 1951) is a Swedish industrialist, owner of Carl "
        "Bennet AB. He focuses on active ownership in medtech and industrials, "
        "prioritizing sustainability, knowledge-driven growth, and long-term "
        "success."
    ),
    "George Soros": (
        "George Soros (born 1930) is a Hungarian-American billionaire, founder "
        "of Soros Fund Management. Known for currency speculation (e.g., "
        "breaking the Bank of England in 1992), he applies reflexivity theory "
        "to markets."
    ),
    "Carl Icahn": (
        "Carl Icahn (born 1936) is an American billionaire activist investor, "
        "founder of Icahn Enterprises. He targets undervalued companies, often "
        "pushing for board changes, spin-offs, or sales to maximize "
        "shareholder value."
    ),
    "Marcus Wallenberg": (
        "Marcus 'Husky' Wallenberg (born 1956) is a Swedish banker and "
        "industrialist, vice chair of Investor AB and chair of SEB. From the "
        "Wallenberg family, he served as CEO of Investor AB (1999-2005), "
        "focusing on long-term value in tech, healthcare, and industrials "
        "through active ownership and innovation."
    ),
    "Cathie Wood": (
        "Cathie Wood (born 1955) is an American investor, founder/CEO/CIO of "
        "ARK Invest (2014). With 40+ years in finance (e.g., AllianceBernstein, "
        "Jennison), she specializes in disruptive tech like AI, genomics, "
        "robotics, blockchain, and EVs, via actively managed ETFs."
    ),
}

# ---------------------------------------------------------------------------
# Helper: safely read a metric from yfinance info dict
# ---------------------------------------------------------------------------

def _get(info: Dict[str, Any], key: str, default=None):
    """Return value from info dict; treat None / 'N/A' as *default*."""
    val = info.get(key, default)
    if val is None or val == "N/A":
        return default
    return val


# ---------------------------------------------------------------------------
# Data fetching (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900, show_spinner=False)
def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """Fetch stock info and history from yfinance. Returns a dict with
    'info' and 'history' keys, or an 'error' key on failure."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return {"error": f"No data found for ticker '{ticker}'."}
        hist = t.history(period="1y")
        return {"info": info, "history": hist}
    except Exception as e:
        return {"error": str(e)}


def get_price(info: Dict) -> float:
    """Best-effort current price."""
    return _get(info, "currentPrice") or _get(info, "regularMarketPrice") or _get(info, "previousClose", 0.0)


def compute_extras(info: Dict, hist: pd.DataFrame) -> Dict[str, Any]:
    """Derive additional metrics not always directly in info."""
    extras: Dict[str, Any] = {}

    # 52-week change
    if not hist.empty:
        first = hist["Close"].iloc[0]
        last = hist["Close"].iloc[-1]
        if first and first > 0:
            extras["52w_change"] = (last - first) / first * 100
        hi = hist["Close"].max()
        lo = hist["Close"].min()
        if hi and hi > 0:
            extras["52w_range_pct"] = (hi - lo) / hi * 100
        extras["avg_volume"] = hist["Volume"].mean()
    else:
        extras["52w_change"] = None
        extras["52w_range_pct"] = None
        extras["avg_volume"] = None

    # PEG ratio – use yfinance value or compute
    peg = _get(info, "pegRatio")
    if peg is None:
        pe = _get(info, "trailingPE")
        growth = _get(info, "earningsQuarterlyGrowth") or _get(info, "earningsGrowth")
        if pe and growth and growth > 0:
            peg = pe / (growth * 100)
    extras["pegRatio"] = peg

    # Sector tag (lowercase for matching)
    sector = _get(info, "sector", "")
    extras["sector_lower"] = sector.lower() if sector else ""

    return extras


# ---------------------------------------------------------------------------
# Strategy scoring functions
# Each returns (score: int 0-100, explanation: str)
# ---------------------------------------------------------------------------

def score_buffett(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    pe = _get(info, "trailingPE")
    roe = _get(info, "returnOnEquity")
    dte = _get(info, "debtToEquity")
    fcf = _get(info, "freeCashflow")
    trail_eps = _get(info, "trailingEps")
    fwd_eps = _get(info, "forwardEps")

    if pe is not None and pe < 15:
        score += 30
        reasons.append(f"Low P/E ({pe:.1f} < 15)")
    if roe is not None and roe > 0.15:
        score += 20
        reasons.append(f"High ROE ({roe*100:.1f}% > 15%)")
    if dte is not None and dte < 50:  # yfinance often reports as %
        score += 20
        reasons.append(f"Low debt-to-equity ({dte:.1f})")
    if fcf is not None and fcf > 0:
        score += 15
        reasons.append("Positive free cash flow")
    if trail_eps is not None and fwd_eps is not None and trail_eps > 0 and fwd_eps > trail_eps:
        score += 15
        reasons.append("Earnings growth (forward EPS > trailing)")

    return min(score, 100), "; ".join(reasons) if reasons else "Low match on value metrics."


def score_lynch(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    peg = extras.get("pegRatio")
    pe = _get(info, "trailingPE")
    eg = _get(info, "earningsGrowth")
    rg = _get(info, "revenueGrowth")
    insider = _get(info, "heldPercentInsiders")

    if peg is not None and peg < 1:
        score += 30
        reasons.append(f"PEG < 1 ({peg:.2f})")
    if eg is not None and eg > 0.15:
        score += 20
        reasons.append(f"Earnings growth {eg*100:.1f}% > 15%")
    if pe is not None and 10 <= pe <= 20:
        score += 20
        reasons.append(f"Reasonable P/E ({pe:.1f})")
    if insider is not None and insider > 0.10:
        score += 15
        reasons.append(f"High insider ownership ({insider*100:.1f}%)")
    if rg is not None and rg > 0.10:
        score += 15
        reasons.append(f"Strong sales growth ({rg*100:.1f}%)")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited GARP indicators."


def score_dalio(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    beta = _get(info, "beta")
    div_yield = _get(info, "dividendYield")
    cr = _get(info, "currentRatio")

    if beta is not None and beta < 1:
        score += 30
        reasons.append(f"Low beta ({beta:.2f} < 1)")
    if div_yield is not None and div_yield > 0.02:
        score += 20
        reasons.append(f"Dividend yield {div_yield*100:.1f}% > 2%")
    if cr is not None and cr > 2:
        score += 20
        reasons.append(f"Strong current ratio ({cr:.1f} > 2)")
    # Sector resilience proxy
    sector = extras.get("sector_lower", "")
    resilient = ["consumer defensive", "utilities", "healthcare", "industrials"]
    if any(r in sector for r in resilient):
        score += 15
        reasons.append(f"Resilient sector ({_get(info, 'sector', 'N/A')})")
    if beta is not None and beta < 0.8:
        score += 15
        reasons.append("Very low market correlation")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited all-weather indicators."


def score_lundberg(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    pb = _get(info, "priceToBook")
    roa = _get(info, "returnOnAssets")
    payout = _get(info, "payoutRatio")
    margin = _get(info, "profitMargins")
    range_pct = extras.get("52w_range_pct")

    if pb is not None and pb < 1.5:
        score += 30
        reasons.append(f"Low P/B ({pb:.2f} < 1.5)")
    if roa is not None and roa > 0.08:
        score += 20
        reasons.append(f"High ROA ({roa*100:.1f}% > 8%)")
    if payout is not None and payout > 0.30:
        score += 20
        reasons.append(f"Stable dividend payout ({payout*100:.0f}% > 30%)")
    if range_pct is not None and range_pct < 50:
        score += 15
        reasons.append(f"Low 52w volatility ({range_pct:.0f}% range)")
    if margin is not None and margin > 0.10:
        score += 15
        reasons.append(f"Net income margin {margin*100:.1f}% > 10%")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited conservative value signals."


def score_gardell(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    target = _get(info, "targetMeanPrice")
    price = get_price(info)
    roe = _get(info, "returnOnEquity")
    assets = _get(info, "totalAssets") or _get(info, "totalAssets")
    eg = _get(info, "earningsGrowth")
    float_pct = _get(info, "floatShares")
    shares_out = _get(info, "sharesOutstanding")
    ret52 = extras.get("52w_change")

    if target and price and price > 0 and (target - price) / price > 0.20:
        score += 30
        upside = (target - price) / price * 100
        reasons.append(f"Analyst upside {upside:.0f}% > 20%")
    if ret52 is not None and ret52 < 0:
        score += 20
        reasons.append(f"Underperforming 52w ({ret52:.1f}%)")
    if float_pct and shares_out and shares_out > 0:
        ff = float_pct / shares_out
        if ff > 0.50:
            score += 20
            reasons.append(f"High free float ({ff*100:.0f}%)")
    if roe is not None and roe < 0.10 and assets and assets > 0:
        score += 15
        reasons.append("Low ROE with significant assets (governance weakness)")
    if eg is not None and eg < 0:
        score += 15
        reasons.append("Negative earnings growth – turnaround potential")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited activist signals."


def score_jacob_wallenberg(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    roe = _get(info, "returnOnEquity")
    dte = _get(info, "debtToEquity")
    div_yield = _get(info, "dividendYield")
    eg = _get(info, "earningsGrowth")
    beta = _get(info, "beta")

    if roe is not None and roe > 0.12:
        score += 25
        reasons.append(f"ROE {roe*100:.1f}% > 12%")
    if dte is not None and dte < 100:
        score += 20
        reasons.append(f"Low debt-to-equity ({dte:.1f})")
    if div_yield is not None and div_yield > 0.015:
        score += 20
        reasons.append(f"Dividend yield {div_yield*100:.1f}% > 1.5%")
    if eg is not None and eg > 0.10:
        score += 20
        reasons.append(f"Earnings growth {eg*100:.1f}% > 10%")
    if beta is not None and beta < 1.2:
        score += 15
        reasons.append(f"Low volatility (beta {beta:.2f})")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited long-term stability signals."


def score_schorling(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    margin = _get(info, "profitMargins")
    rg = _get(info, "revenueGrowth")
    roa = _get(info, "returnOnAssets")
    mcap = _get(info, "marketCap")
    fcf = _get(info, "freeCashflow")

    if margin is not None and margin > 0.15:
        score += 25
        reasons.append(f"High profit margin ({margin*100:.1f}% > 15%)")
    if rg is not None and rg > 0.10:
        score += 25
        reasons.append(f"Strong sales growth ({rg*100:.1f}% > 10%)")
    if roa is not None and roa > 0.10:
        score += 20
        reasons.append(f"High ROA ({roa*100:.1f}% > 10%)")
    if mcap is not None and mcap > 1e10:
        score += 15
        reasons.append("Large market cap – market leader proxy")
    if fcf is not None and fcf > 0:
        score += 15
        reasons.append("Positive free cash flow")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited specialist-leader signals."


def score_bennet(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    pb = _get(info, "priceToBook")
    roe = _get(info, "returnOnEquity")
    payout = _get(info, "payoutRatio")
    margin = _get(info, "profitMargins")
    dte = _get(info, "debtToEquity")

    if pb is not None and pb < 2:
        score += 25
        reasons.append(f"Low P/B ({pb:.2f} < 2)")
    if roe is not None and roe > 0.10:
        score += 20
        reasons.append(f"ROE {roe*100:.1f}% > 10%")
    if payout is not None and payout > 0.25:
        score += 20
        reasons.append(f"Stable payout ({payout*100:.0f}% > 25%)")
    if margin is not None and margin > 0.08:
        score += 20
        reasons.append(f"Net margin {margin*100:.1f}% > 8%")
    if dte is not None and dte < 80:
        score += 15
        reasons.append(f"Low debt ({dte:.1f} D/E)")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited sustainable-value signals."


def score_soros(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    beta = _get(info, "beta")
    pe = _get(info, "trailingPE")
    ret52 = extras.get("52w_change")
    vol = _get(info, "volume")
    avg_vol = extras.get("avg_volume")

    if beta is not None and beta > 1.2:
        score += 25
        reasons.append(f"High beta ({beta:.2f} > 1.2)")
    if ret52 is not None and ret52 > 20:
        score += 25
        reasons.append(f"Strong momentum ({ret52:.0f}% 52w change)")
    if vol and avg_vol and avg_vol > 0 and vol > avg_vol:
        score += 20
        reasons.append("Volume above average")
    if pe is not None and (pe > 25 or pe < 10):
        score += 15
        reasons.append(f"Reflexivity signal (P/E {pe:.1f})")
    sector = extras.get("sector_lower", "")
    if any(s in sector for s in ["energy", "financial", "basic materials"]):
        score += 15
        reasons.append(f"Macro-sensitive sector ({_get(info, 'sector', 'N/A')})")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited speculative macro signals."


def score_icahn(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    pe = _get(info, "trailingPE")
    pb = _get(info, "priceToBook")
    cash = _get(info, "totalCash")
    mcap = _get(info, "marketCap")
    ret52 = extras.get("52w_change")
    roe = _get(info, "returnOnEquity")
    assets = _get(info, "totalAssets")

    if pe is not None and pe < 12:
        score += 30
        reasons.append(f"Low P/E ({pe:.1f} < 12)")
    if pb is not None and pb < 1:
        score += 25
        reasons.append(f"Low P/B ({pb:.2f} < 1)")
    if cash and mcap and mcap > 0 and (cash / mcap) > 0.10:
        score += 20
        reasons.append(f"High cash ({cash/mcap*100:.0f}% of market cap)")
    if ret52 is not None and ret52 < 0:
        score += 15
        reasons.append(f"Underperforming ({ret52:.1f}% 52w)")
    if roe is not None and roe < 0.10 and assets and assets > 0:
        score += 10
        reasons.append("Low ROE with assets – activist potential")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited contrarian signals."


def score_marcus_wallenberg(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    eg = _get(info, "earningsGrowth")
    cr = _get(info, "currentRatio")
    dte = _get(info, "debtToEquity")
    beta = _get(info, "beta")
    sector = extras.get("sector_lower", "")

    if eg is not None and eg > 0.12:
        score += 25
        reasons.append(f"Earnings growth {eg*100:.1f}% > 12%")
    if cr is not None and cr > 1.5:
        score += 20
        reasons.append(f"Strong balance sheet (CR {cr:.1f})")
    if dte is not None and dte < 80:
        score += 20
        reasons.append(f"Low debt ({dte:.1f} D/E)")
    if any(s in sector for s in ["technology", "healthcare"]):
        score += 20
        reasons.append(f"Innovation sector ({_get(info, 'sector', 'N/A')})")
    if beta is not None and beta < 1:
        score += 15
        reasons.append(f"Low volatility (beta {beta:.2f})")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited stewardship signals."


def score_cathie_wood(info: Dict, extras: Dict) -> Tuple[int, str]:
    score = 0
    reasons = []
    rg = _get(info, "revenueGrowth")
    fwd_pe = _get(info, "forwardPE")
    beta = _get(info, "beta")
    ret52 = extras.get("52w_change")
    sector = extras.get("sector_lower", "")

    if rg is not None and rg > 0.20:
        score += 30
        reasons.append(f"Revenue growth {rg*100:.1f}% > 20%")
    if fwd_pe is not None and fwd_pe > 30:
        score += 20
        reasons.append(f"High forward P/E ({fwd_pe:.1f}) – growth priced in")
    disruptive = ["technology", "healthcare", "communication", "financial services"]
    if any(d in sector for d in disruptive):
        score += 20
        reasons.append(f"Disruptive sector ({_get(info, 'sector', 'N/A')})")
    if beta is not None and beta > 1.5:
        score += 15
        reasons.append(f"High beta ({beta:.2f})")
    if ret52 is not None and ret52 > 15:
        score += 15
        reasons.append(f"Positive momentum ({ret52:.0f}% 52w)")

    return min(score, 100), "; ".join(reasons) if reasons else "Limited disruptive-innovation signals."


# Mapping investor names to scoring functions
INVESTOR_STRATEGIES: Dict[str, Any] = {
    "Warren Buffett": score_buffett,
    "Peter Lynch": score_lynch,
    "Ray Dalio": score_dalio,
    "Fredrik Lundberg": score_lundberg,
    "Christer Gardell": score_gardell,
    "Jacob Wallenberg": score_jacob_wallenberg,
    "Melker Schorling": score_schorling,
    "Carl Bennet": score_bennet,
    "George Soros": score_soros,
    "Carl Icahn": score_icahn,
    "Marcus Wallenberg": score_marcus_wallenberg,
    "Cathie Wood": score_cathie_wood,
}

INVESTOR_NAMES = list(INVESTOR_STRATEGIES.keys())


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------

def analyse_stock(ticker: str) -> Dict[str, Any]:
    """Fetch data and run all investor strategies for one ticker."""
    data = fetch_stock_data(ticker)
    if "error" in data:
        return {"ticker": ticker, "error": data["error"]}

    info = data["info"]
    hist = data["history"]
    extras = compute_extras(info, hist)
    price = get_price(info)

    result: Dict[str, Any] = {
        "ticker": ticker,
        "name": _get(info, "shortName", ticker),
        "price": price,
        "currency": _get(info, "currency", ""),
        "P/E": _get(info, "trailingPE"),
        "Fwd P/E": _get(info, "forwardPE"),
        "P/B": _get(info, "priceToBook"),
        "ROE": _get(info, "returnOnEquity"),
        "ROA": _get(info, "returnOnAssets"),
        "D/E": _get(info, "debtToEquity"),
        "Div Yield": _get(info, "dividendYield"),
        "Beta": _get(info, "beta"),
        "52w Chg%": extras.get("52w_change"),
        "Sector": _get(info, "sector", "N/A"),
    }

    scores = {}
    explanations = {}
    for name, func in INVESTOR_STRATEGIES.items():
        s, e = func(info, extras)
        scores[name] = s
        explanations[name] = e

    result["scores"] = scores
    result["explanations"] = explanations
    return result


def format_metric(val, pct=False):
    """Format a metric for display."""
    if val is None:
        return "N/A"
    if pct:
        return f"{val*100:.1f}%"
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Investor Insights",
        page_icon="📊",
        layout="wide",
    )

    st.title("Investor Insights: How Legends Would Invest Today")
    st.markdown(
        "Analyse stocks through the lens of **12 famous investors** using "
        "**real financial data**. Enter tickers below or pick a preset."
    )

    # ---- Sidebar: Investor Bios ----
    with st.sidebar:
        st.header("Investor Profiles")
        for name, bio in INVESTOR_BIOS.items():
            with st.expander(name):
                st.write(bio)

    # ---- Ticker input ----
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input(
            "Enter comma-separated stock tickers",
            value=DEFAULT_TICKERS,
            help="Use .ST suffix for Stockholm stocks (e.g. VOLV-B.ST)",
        )
    with col2:
        preset = st.selectbox("Or use preset", ["Custom", "US S&P 500 Top 10", "Swedish OMX Top 10"])

    if preset == "US S&P 500 Top 10":
        tickers = SP500_TOP
    elif preset == "Swedish OMX Top 10":
        tickers = OMX_TOP
    else:
        tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    if not tickers:
        st.warning("Please enter at least one ticker.")
        st.stop()

    st.write(f"**Tickers to analyse:** {', '.join(tickers)}")

    # ---- Analyse button ----
    if st.button("Analyse Stocks", type="primary"):
        results = []
        progress = st.progress(0, text="Fetching data...")
        for i, ticker in enumerate(tickers):
            progress.progress((i) / len(tickers), text=f"Analysing {ticker}...")
            res = analyse_stock(ticker)
            results.append(res)
        progress.progress(1.0, text="Done!")

        # Store in session state so results survive reruns
        st.session_state["results"] = results

    # ---- Display results ----
    if "results" not in st.session_state:
        st.info("Click **Analyse Stocks** to start.")
        st.stop()

    results = st.session_state["results"]

    # Separate errors
    errors = [r for r in results if "error" in r]
    valid = [r for r in results if "error" not in r]

    if errors:
        for e in errors:
            st.error(f"**{e['ticker']}**: {e['error']}")

    if not valid:
        st.stop()

    # ---- Key Metrics Table ----
    st.subheader("Key Metrics")
    metrics_rows = []
    for r in valid:
        metrics_rows.append({
            "Ticker": r["ticker"],
            "Name": r["name"],
            "Price": f"{r['price']:.2f} {r['currency']}",
            "P/E": format_metric(r["P/E"]),
            "Fwd P/E": format_metric(r["Fwd P/E"]),
            "P/B": format_metric(r["P/B"]),
            "ROE": format_metric(r["ROE"], pct=True),
            "ROA": format_metric(r["ROA"], pct=True),
            "D/E": format_metric(r["D/E"]),
            "Div Yield": format_metric(r["Div Yield"], pct=True),
            "Beta": format_metric(r["Beta"]),
            "52w Chg": format_metric(r["52w Chg%"]) + ("%" if r["52w Chg%"] is not None else ""),
            "Sector": r["Sector"],
        })
    st.dataframe(pd.DataFrame(metrics_rows), use_container_width=True, hide_index=True)

    # ---- Scores Table ----
    st.subheader("Investor Strategy Scores (0-100)")
    score_rows = []
    for r in valid:
        row = {"Ticker": r["ticker"]}
        for inv in INVESTOR_NAMES:
            row[inv] = r["scores"][inv]
        score_rows.append(row)
    score_df = pd.DataFrame(score_rows)
    st.dataframe(
        score_df.style.background_gradient(axis=None, cmap="RdYlGn", subset=INVESTOR_NAMES, vmin=0, vmax=100),
        use_container_width=True,
        hide_index=True,
    )

    # ---- Explanations (expandable per stock) ----
    st.subheader("Detailed Explanations")
    for r in valid:
        with st.expander(f"{r['ticker']} – {r['name']}"):
            for inv in INVESTOR_NAMES:
                s = r["scores"][inv]
                e = r["explanations"][inv]
                colour = "green" if s >= 60 else ("orange" if s >= 30 else "red")
                st.markdown(f"**{inv}** — Score: :{colour}[**{s}**]")
                st.caption(e)

    # ---- Visualisation: grouped bar chart ----
    st.subheader("Score Comparison Chart")

    # Build long-form data for Altair
    chart_data = []
    for r in valid:
        for inv in INVESTOR_NAMES:
            chart_data.append({
                "Ticker": r["ticker"],
                "Investor": inv,
                "Score": r["scores"][inv],
            })
    chart_df = pd.DataFrame(chart_data)

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("Investor:N", sort=INVESTOR_NAMES, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Ticker:N"),
            xOffset="Ticker:N",
            tooltip=["Ticker", "Investor", "Score"],
        )
        .properties(height=450)
    )
    st.altair_chart(chart, use_container_width=True)

    # ---- Best Matches Summary ----
    st.subheader("Best Matches")
    st.markdown("Stocks scoring **60+** for each investor:")
    for inv in INVESTOR_NAMES:
        matches = [(r["ticker"], r["scores"][inv]) for r in valid if r["scores"][inv] >= 60]
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            labels = ", ".join(f"{t} ({s})" for t, s in matches)
            st.markdown(f"- **{inv}**: {labels}")

    # ---- Disclaimer ----
    st.divider()
    st.caption(
        "**Disclaimer:** This application uses real financial data from Yahoo Finance "
        "but is strictly for **educational and simulation purposes only**. It does not "
        "constitute financial advice. Investment decisions should be made in consultation "
        "with qualified financial professionals. Past performance does not guarantee "
        "future results."
    )


if __name__ == "__main__":
    main()
