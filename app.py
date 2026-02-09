"""
Investor Insights: How Legends Would Invest Today
===================================================
A Streamlit app that simulates how famous investors would invest today
based on their real historical strategies, using real financial data.

Users pick investors, weight them, enter a budget, and get a suggested
portfolio allocation with dollar amounts and share counts.

DISCLAIMER: This is for educational/simulation purposes only.
            Not financial advice. Consult professionals for investments.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
from typing import Dict, Tuple, Any

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

INVESTOR_NAMES = list(INVESTOR_BIOS.keys())

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
    """Fetch stock info and 1-year history from yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
            return {"error": f"No data found for ticker '{ticker}'."}
        hist = t.history(period="1y")
        return {"info": info, "history": hist}
    except Exception as e:
        return {"error": str(e)}


def get_price(info: Dict) -> float:
    return _get(info, "currentPrice") or _get(info, "regularMarketPrice") or _get(info, "previousClose", 0.0)


def compute_extras(info: Dict, hist: pd.DataFrame) -> Dict[str, Any]:
    """Derive additional metrics not directly in info."""
    extras: Dict[str, Any] = {}
    if not hist.empty:
        first = hist["Close"].iloc[0]
        last = hist["Close"].iloc[-1]
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


# ---------------------------------------------------------------------------
# Strategy scoring functions — each returns (score 0-100, explanation)
# ---------------------------------------------------------------------------

def score_buffett(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    pe = _get(info, "trailingPE")
    roe = _get(info, "returnOnEquity")
    dte = _get(info, "debtToEquity")
    fcf = _get(info, "freeCashflow")
    trail_eps = _get(info, "trailingEps")
    fwd_eps = _get(info, "forwardEps")

    if pe is not None and pe < 15:
        score += 30; reasons.append(f"Low P/E ({pe:.1f})")
    if roe is not None and roe > 0.15:
        score += 20; reasons.append(f"High ROE ({roe*100:.1f}%)")
    if dte is not None and dte < 50:
        score += 20; reasons.append(f"Low D/E ({dte:.1f})")
    if fcf is not None and fcf > 0:
        score += 15; reasons.append("Positive FCF")
    if trail_eps and fwd_eps and trail_eps > 0 and fwd_eps > trail_eps:
        score += 15; reasons.append("Growing EPS")
    return min(score, 100), "; ".join(reasons) or "Low match on value metrics."


def score_lynch(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    peg = extras.get("pegRatio")
    pe = _get(info, "trailingPE")
    eg = _get(info, "earningsGrowth")
    rg = _get(info, "revenueGrowth")
    insider = _get(info, "heldPercentInsiders")

    if peg is not None and peg < 1:
        score += 30; reasons.append(f"PEG < 1 ({peg:.2f})")
    if eg is not None and eg > 0.15:
        score += 20; reasons.append(f"Earnings growth {eg*100:.1f}%")
    if pe is not None and 10 <= pe <= 20:
        score += 20; reasons.append(f"Reasonable P/E ({pe:.1f})")
    if insider is not None and insider > 0.10:
        score += 15; reasons.append(f"Insider own {insider*100:.1f}%")
    if rg is not None and rg > 0.10:
        score += 15; reasons.append(f"Sales growth {rg*100:.1f}%")
    return min(score, 100), "; ".join(reasons) or "Limited GARP indicators."


def score_dalio(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    beta = _get(info, "beta")
    dy = _get(info, "dividendYield")
    cr = _get(info, "currentRatio")
    sector = extras.get("sector_lower", "")

    if beta is not None and beta < 1:
        score += 30; reasons.append(f"Low beta ({beta:.2f})")
    if dy is not None and dy > 0.02:
        score += 20; reasons.append(f"Div yield {dy*100:.1f}%")
    if cr is not None and cr > 2:
        score += 20; reasons.append(f"Current ratio {cr:.1f}")
    if any(r in sector for r in ["consumer defensive", "utilities", "healthcare", "industrials"]):
        score += 15; reasons.append(f"Resilient sector")
    if beta is not None and beta < 0.8:
        score += 15; reasons.append("Very low correlation")
    return min(score, 100), "; ".join(reasons) or "Limited all-weather indicators."


def score_lundberg(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    pb = _get(info, "priceToBook")
    roa = _get(info, "returnOnAssets")
    payout = _get(info, "payoutRatio")
    margin = _get(info, "profitMargins")
    rng = extras.get("52w_range_pct")

    if pb is not None and pb < 1.5:
        score += 30; reasons.append(f"Low P/B ({pb:.2f})")
    if roa is not None and roa > 0.08:
        score += 20; reasons.append(f"ROA {roa*100:.1f}%")
    if payout is not None and payout > 0.30:
        score += 20; reasons.append(f"Payout {payout*100:.0f}%")
    if rng is not None and rng < 50:
        score += 15; reasons.append(f"Low volatility ({rng:.0f}%)")
    if margin is not None and margin > 0.10:
        score += 15; reasons.append(f"Margin {margin*100:.1f}%")
    return min(score, 100), "; ".join(reasons) or "Limited conservative value signals."


def score_gardell(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    target = _get(info, "targetMeanPrice")
    price = get_price(info)
    roe = _get(info, "returnOnEquity")
    assets = _get(info, "totalAssets")
    eg = _get(info, "earningsGrowth")
    float_s = _get(info, "floatShares")
    shares = _get(info, "sharesOutstanding")
    ret52 = extras.get("52w_change")

    if target and price and price > 0 and (target - price) / price > 0.20:
        score += 30; reasons.append(f"Analyst upside {(target-price)/price*100:.0f}%")
    if ret52 is not None and ret52 < 0:
        score += 20; reasons.append(f"Underperforming ({ret52:.1f}%)")
    if float_s and shares and shares > 0 and float_s / shares > 0.50:
        score += 20; reasons.append("High free float")
    if roe is not None and roe < 0.10 and assets and assets > 0:
        score += 15; reasons.append("Weak governance proxy")
    if eg is not None and eg < 0:
        score += 15; reasons.append("Turnaround potential")
    return min(score, 100), "; ".join(reasons) or "Limited activist signals."


def score_jacob_wallenberg(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    roe = _get(info, "returnOnEquity")
    dte = _get(info, "debtToEquity")
    dy = _get(info, "dividendYield")
    eg = _get(info, "earningsGrowth")
    beta = _get(info, "beta")

    if roe is not None and roe > 0.12:
        score += 25; reasons.append(f"ROE {roe*100:.1f}%")
    if dte is not None and dte < 100:
        score += 20; reasons.append(f"Low D/E ({dte:.1f})")
    if dy is not None and dy > 0.015:
        score += 20; reasons.append(f"Div yield {dy*100:.1f}%")
    if eg is not None and eg > 0.10:
        score += 20; reasons.append(f"Earnings growth {eg*100:.1f}%")
    if beta is not None and beta < 1.2:
        score += 15; reasons.append(f"Low beta ({beta:.2f})")
    return min(score, 100), "; ".join(reasons) or "Limited stability signals."


def score_schorling(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    margin = _get(info, "profitMargins")
    rg = _get(info, "revenueGrowth")
    roa = _get(info, "returnOnAssets")
    mcap = _get(info, "marketCap")
    fcf = _get(info, "freeCashflow")

    if margin is not None and margin > 0.15:
        score += 25; reasons.append(f"Margin {margin*100:.1f}%")
    if rg is not None and rg > 0.10:
        score += 25; reasons.append(f"Sales growth {rg*100:.1f}%")
    if roa is not None and roa > 0.10:
        score += 20; reasons.append(f"ROA {roa*100:.1f}%")
    if mcap is not None and mcap > 1e10:
        score += 15; reasons.append("Market leader")
    if fcf is not None and fcf > 0:
        score += 15; reasons.append("Positive FCF")
    return min(score, 100), "; ".join(reasons) or "Limited specialist-leader signals."


def score_bennet(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    pb = _get(info, "priceToBook")
    roe = _get(info, "returnOnEquity")
    payout = _get(info, "payoutRatio")
    margin = _get(info, "profitMargins")
    dte = _get(info, "debtToEquity")

    if pb is not None and pb < 2:
        score += 25; reasons.append(f"P/B {pb:.2f}")
    if roe is not None and roe > 0.10:
        score += 20; reasons.append(f"ROE {roe*100:.1f}%")
    if payout is not None and payout > 0.25:
        score += 20; reasons.append(f"Payout {payout*100:.0f}%")
    if margin is not None and margin > 0.08:
        score += 20; reasons.append(f"Margin {margin*100:.1f}%")
    if dte is not None and dte < 80:
        score += 15; reasons.append(f"Low debt ({dte:.1f})")
    return min(score, 100), "; ".join(reasons) or "Limited sustainable-value signals."


def score_soros(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    beta = _get(info, "beta")
    pe = _get(info, "trailingPE")
    ret52 = extras.get("52w_change")
    vol = _get(info, "volume")
    avg_vol = extras.get("avg_volume")

    if beta is not None and beta > 1.2:
        score += 25; reasons.append(f"High beta ({beta:.2f})")
    if ret52 is not None and ret52 > 20:
        score += 25; reasons.append(f"Momentum ({ret52:.0f}%)")
    if vol and avg_vol and avg_vol > 0 and vol > avg_vol:
        score += 20; reasons.append("High volume")
    if pe is not None and (pe > 25 or pe < 10):
        score += 15; reasons.append(f"Reflexivity (P/E {pe:.1f})")
    sector = extras.get("sector_lower", "")
    if any(s in sector for s in ["energy", "financial", "basic materials"]):
        score += 15; reasons.append("Macro-sensitive sector")
    return min(score, 100), "; ".join(reasons) or "Limited macro signals."


def score_icahn(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    pe = _get(info, "trailingPE")
    pb = _get(info, "priceToBook")
    cash = _get(info, "totalCash")
    mcap = _get(info, "marketCap")
    ret52 = extras.get("52w_change")
    roe = _get(info, "returnOnEquity")
    assets = _get(info, "totalAssets")

    if pe is not None and pe < 12:
        score += 30; reasons.append(f"Low P/E ({pe:.1f})")
    if pb is not None and pb < 1:
        score += 25; reasons.append(f"Low P/B ({pb:.2f})")
    if cash and mcap and mcap > 0 and (cash / mcap) > 0.10:
        score += 20; reasons.append(f"Cash rich ({cash/mcap*100:.0f}%)")
    if ret52 is not None and ret52 < 0:
        score += 15; reasons.append(f"Underperforming ({ret52:.1f}%)")
    if roe is not None and roe < 0.10 and assets and assets > 0:
        score += 10; reasons.append("Activist potential")
    return min(score, 100), "; ".join(reasons) or "Limited contrarian signals."


def score_marcus_wallenberg(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    eg = _get(info, "earningsGrowth")
    cr = _get(info, "currentRatio")
    dte = _get(info, "debtToEquity")
    beta = _get(info, "beta")
    sector = extras.get("sector_lower", "")

    if eg is not None and eg > 0.12:
        score += 25; reasons.append(f"Earnings growth {eg*100:.1f}%")
    if cr is not None and cr > 1.5:
        score += 20; reasons.append(f"Current ratio {cr:.1f}")
    if dte is not None and dte < 80:
        score += 20; reasons.append(f"Low debt ({dte:.1f})")
    if any(s in sector for s in ["technology", "healthcare"]):
        score += 20; reasons.append("Innovation sector")
    if beta is not None and beta < 1:
        score += 15; reasons.append(f"Low beta ({beta:.2f})")
    return min(score, 100), "; ".join(reasons) or "Limited stewardship signals."


def score_cathie_wood(info: Dict, extras: Dict) -> Tuple[int, str]:
    score, reasons = 0, []
    rg = _get(info, "revenueGrowth")
    fwd_pe = _get(info, "forwardPE")
    beta = _get(info, "beta")
    ret52 = extras.get("52w_change")
    sector = extras.get("sector_lower", "")

    if rg is not None and rg > 0.20:
        score += 30; reasons.append(f"Revenue growth {rg*100:.1f}%")
    if fwd_pe is not None and fwd_pe > 30:
        score += 20; reasons.append(f"High fwd P/E ({fwd_pe:.1f})")
    if any(d in sector for d in ["technology", "healthcare", "communication", "financial services"]):
        score += 20; reasons.append("Disruptive sector")
    if beta is not None and beta > 1.5:
        score += 15; reasons.append(f"High beta ({beta:.2f})")
    if ret52 is not None and ret52 > 15:
        score += 15; reasons.append(f"Momentum ({ret52:.0f}%)")
    return min(score, 100), "; ".join(reasons) or "Limited disruptive signals."


INVESTOR_STRATEGIES = {
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


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------

def analyse_stock(ticker: str) -> Dict[str, Any]:
    """Fetch data and score against all investor strategies."""
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

    scores, explanations = {}, {}
    for name, func in INVESTOR_STRATEGIES.items():
        s, e = func(info, extras)
        scores[name] = s
        explanations[name] = e

    result["scores"] = scores
    result["explanations"] = explanations
    return result


def compute_portfolio(results, weights: Dict[str, float], budget: float):
    """
    Given analysed stocks, investor weights, and a dollar budget,
    compute a weighted composite score for each stock, then allocate
    the budget proportionally.

    Returns a DataFrame with allocation details.
    """
    valid = [r for r in results if "error" not in r]
    if not valid:
        return pd.DataFrame()

    # Normalise weights so they sum to 1
    total_w = sum(weights.values())
    if total_w == 0:
        return pd.DataFrame()
    norm = {k: v / total_w for k, v in weights.items()}

    rows = []
    for r in valid:
        composite = sum(r["scores"].get(inv, 0) * w for inv, w in norm.items())
        rows.append({
            "Ticker": r["ticker"],
            "Name": r["name"],
            "Price": r["price"],
            "Currency": r["currency"],
            "Composite Score": round(composite, 1),
            "scores": r["scores"],
            "explanations": r["explanations"],
        })

    df = pd.DataFrame(rows)

    # Allocate budget proportionally to composite score
    total_score = df["Composite Score"].sum()
    if total_score == 0:
        df["Allocation %"] = 0.0
        df["Amount"] = 0.0
        df["Shares"] = 0
    else:
        df["Allocation %"] = (df["Composite Score"] / total_score * 100).round(1)
        df["Amount"] = (df["Composite Score"] / total_score * budget).round(2)
        df["Shares"] = df.apply(
            lambda row: int(row["Amount"] // row["Price"]) if row["Price"] > 0 else 0,
            axis=1,
        )
        df["Leftover"] = (df["Amount"] - df["Shares"] * df["Price"]).round(2)

    df = df.sort_values("Composite Score", ascending=False).reset_index(drop=True)
    return df


def fmt(val, pct=False):
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
    st.set_page_config(page_title="Investor Insights", page_icon="📊", layout="wide")

    st.title("Investor Insights: How Legends Would Invest Today")
    st.markdown(
        "Pick your favourite investors, set their influence, enter your budget, "
        "and get a **suggested portfolio allocation** based on real data."
    )

    # ================================================================
    # SIDEBAR — Investor weights + bios
    # ================================================================
    with st.sidebar:
        st.header("1. Pick & Weight Investors")
        st.caption(
            "Use sliders to set how much influence each investor's strategy "
            "has on your portfolio. Set to 0 to exclude."
        )

        weights: Dict[str, float] = {}
        for inv_name in INVESTOR_NAMES:
            with st.expander(inv_name, expanded=False):
                st.caption(INVESTOR_BIOS[inv_name])
                weights[inv_name] = st.slider(
                    f"Weight", 0, 100, 0,
                    key=f"w_{inv_name}",
                    help=f"How much should {inv_name}'s strategy influence your portfolio?",
                )

        st.divider()
        st.header("2. Investment Budget")
        budget = st.number_input(
            "Amount to invest ($)", min_value=0.0, value=10000.0, step=500.0,
            help="Enter the total amount you want to invest.",
        )

        # Quick-pick presets
        st.divider()
        st.subheader("Quick Presets")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("All Equal"):
                for inv_name in INVESTOR_NAMES:
                    st.session_state[f"w_{inv_name}"] = 50
                st.rerun()
        with col_b:
            if st.button("Reset to 0"):
                for inv_name in INVESTOR_NAMES:
                    st.session_state[f"w_{inv_name}"] = 0
                st.rerun()

    # ================================================================
    # MAIN AREA — Ticker input + results
    # ================================================================
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

    # Check at least one investor is weighted
    active_investors = {k: v for k, v in weights.items() if v > 0}

    st.write(f"**Tickers:** {', '.join(tickers)}")
    if active_investors:
        inv_summary = ", ".join(f"{k} ({v}%)" for k, v in active_investors.items())
        st.write(f"**Active investors:** {inv_summary}")
        st.write(f"**Budget:** ${budget:,.2f}")
    else:
        st.info("Set at least one investor weight in the sidebar to get portfolio suggestions.")

    # ---- Analyse ----
    if st.button("Analyse & Build Portfolio", type="primary"):
        results = []
        progress = st.progress(0, text="Fetching data...")
        for i, ticker in enumerate(tickers):
            progress.progress(i / len(tickers), text=f"Analysing {ticker}...")
            results.append(analyse_stock(ticker))
        progress.progress(1.0, text="Done!")
        st.session_state["results"] = results

    if "results" not in st.session_state:
        st.info("Click **Analyse & Build Portfolio** to start.")
        st.stop()

    results = st.session_state["results"]
    errors = [r for r in results if "error" in r]
    valid = [r for r in results if "error" not in r]
    for e in errors:
        st.error(f"**{e['ticker']}**: {e['error']}")
    if not valid:
        st.stop()

    # ================================================================
    # PORTFOLIO ALLOCATION (the main new feature)
    # ================================================================
    if active_investors and budget > 0:
        st.header("Suggested Portfolio Allocation")

        portfolio_df = compute_portfolio(results, active_investors, budget)

        if portfolio_df.empty:
            st.warning("Could not compute portfolio. Check investor weights.")
        else:
            # Summary cards
            cols = st.columns(len(portfolio_df) if len(portfolio_df) <= 5 else 5)
            for i, (_, row) in enumerate(portfolio_df.head(5).iterrows()):
                with cols[i]:
                    st.metric(
                        label=row["Ticker"],
                        value=f"${row['Amount']:,.2f}",
                        delta=f"{row['Allocation %']}% | {row['Shares']} shares",
                    )

            # Full table
            display_df = portfolio_df[["Ticker", "Name", "Composite Score", "Allocation %",
                                       "Amount", "Shares", "Price", "Currency"]].copy()
            display_df = display_df.rename(columns={
                "Amount": "Invest ($)",
                "Price": "Share Price",
            })
            st.dataframe(
                display_df.style.format({
                    "Composite Score": "{:.1f}",
                    "Allocation %": "{:.1f}%",
                    "Invest ($)": "${:,.2f}",
                    "Share Price": "{:.2f}",
                }).background_gradient(subset=["Composite Score"], cmap="RdYlGn", vmin=0, vmax=100),
                use_container_width=True,
                hide_index=True,
            )

            # Leftover cash
            total_invested = (portfolio_df["Shares"] * portfolio_df["Price"]).sum()
            leftover = budget - total_invested
            st.write(f"**Total invested:** ${total_invested:,.2f}  |  "
                     f"**Remaining cash:** ${leftover:,.2f}")

            # Donut chart
            st.subheader("Allocation Breakdown")
            donut_df = portfolio_df[["Ticker", "Allocation %"]].copy()
            donut = (
                alt.Chart(donut_df)
                .mark_arc(innerRadius=60)
                .encode(
                    theta=alt.Theta("Allocation %:Q"),
                    color=alt.Color("Ticker:N", legend=alt.Legend(title="Stock")),
                    tooltip=["Ticker", "Allocation %"],
                )
                .properties(height=350)
            )
            st.altair_chart(donut, use_container_width=True)

    # ================================================================
    # KEY METRICS
    # ================================================================
    st.header("Stock Metrics")
    metrics_rows = []
    for r in valid:
        metrics_rows.append({
            "Ticker": r["ticker"],
            "Name": r["name"],
            "Price": f"{r['price']:.2f} {r['currency']}",
            "P/E": fmt(r["P/E"]),
            "Fwd P/E": fmt(r["Fwd P/E"]),
            "P/B": fmt(r["P/B"]),
            "ROE": fmt(r["ROE"], pct=True),
            "ROA": fmt(r["ROA"], pct=True),
            "D/E": fmt(r["D/E"]),
            "Div Yield": fmt(r["Div Yield"], pct=True),
            "Beta": fmt(r["Beta"]),
            "52w Chg": fmt(r["52w Chg%"]) + ("%" if r["52w Chg%"] is not None else ""),
            "Sector": r["Sector"],
        })
    st.dataframe(pd.DataFrame(metrics_rows), use_container_width=True, hide_index=True)

    # ================================================================
    # SCORE HEATMAP
    # ================================================================
    st.header("All Investor Scores")
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

    # ================================================================
    # BAR CHART
    # ================================================================
    st.header("Score Comparison")
    chart_data = []
    for r in valid:
        for inv in INVESTOR_NAMES:
            chart_data.append({"Ticker": r["ticker"], "Investor": inv, "Score": r["scores"][inv]})
    chart_df = pd.DataFrame(chart_data)

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("Investor:N", sort=INVESTOR_NAMES, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
            color="Ticker:N",
            xOffset="Ticker:N",
            tooltip=["Ticker", "Investor", "Score"],
        )
        .properties(height=450)
    )
    st.altair_chart(chart, use_container_width=True)

    # ================================================================
    # DETAILED EXPLANATIONS
    # ================================================================
    st.header("Detailed Explanations")
    for r in valid:
        with st.expander(f"{r['ticker']} — {r['name']}"):
            for inv in INVESTOR_NAMES:
                s = r["scores"][inv]
                e = r["explanations"][inv]
                clr = "green" if s >= 60 else ("orange" if s >= 30 else "red")
                st.markdown(f"**{inv}** — Score: :{clr}[**{s}**]")
                st.caption(e)

    # ================================================================
    # DISCLAIMER
    # ================================================================
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
