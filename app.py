"""
Investor Insights: How Legends Would Invest Today
===================================================
Step-based portfolio builder. Pick markets, pick investors, configure
weights, get blended portfolios with share counts, risk metrics,
backtesting, correlation analysis, and more.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
import json
import io
from typing import Dict, Tuple, Any

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="Investor Insights", page_icon="📊", layout="wide")

# ═══════════════════════════════════════════════════════════════
# LANGUAGE / I18N
# ═══════════════════════════════════════════════════════════════

LANG_EN = {
    "title": "Build Your Portfolio With the Legends",
    "subtitle": "Select markets and investors, configure the mix per market, and generate blended portfolios with exact share counts — all from real financial data.",
    "step1": "01 — Select Markets",
    "step2": "02 — Select Investors",
    "step3": "03 — Configure Each Market",
    "step4": "04 — Your Portfolios",
    "select_all": "Select All",
    "deselect_all": "Deselect All",
    "investor_bios": "Investor Bios & Info",
    "investment_amount": "Investment Amount",
    "max_stocks": "Max Stocks",
    "investor_mix": "Investor Mix",
    "equal_weight": "Equal Weight",
    "manual": "Manual",
    "min_score": "Min Score Threshold",
    "sector_filter": "Sector Filter",
    "all_sectors": "All Sectors",
    "generate": "Generate Portfolio",
    "generate_multi": "Generate Portfolios for {n} Markets",
    "select_prompt": "Select at least one **market** and one **investor** to generate portfolios.",
    "invested": "INVESTED",
    "remaining": "REMAINING",
    "total_invested": "TOTAL INVESTED",
    "total_remaining": "TOTAL REMAINING",
    "company": "COMPANY",
    "ticker": "TICKER",
    "weight": "WEIGHT",
    "price": "PRICE",
    "shares": "SHARES",
    "cost": "COST",
    "sector_breakdown": "Sector Breakdown",
    "risk_metrics": "Portfolio Risk Metrics",
    "score_comparison": "Score Comparison",
    "backtest": "Historical Backtest (1 Year)",
    "correlation": "Stock Correlation Matrix",
    "contributors": "Show investor contribution per stock",
    "export_csv": "Download Portfolio CSV",
    "save_config": "Save Configuration",
    "load_config": "Load Configuration",
    "compare_mode": "Side-by-Side Comparison",
    "compare_a": "Mix A",
    "compare_b": "Mix B",
    "no_stocks": "No valid stocks found.",
    "stocks": "stocks",
    "of": "of",
    "selected": "selected",
    "investors_selected": "investors selected",
    "weights_sum": "Weights sum",
    "should_be_100": "should be 100%",
    "disclaimer": "Prices are approximate. The portfolios are simulations based on famous investors' known philosophies and <strong>do not constitute financial advice</strong>. All investing involves risk — always verify prices, availability, and do your own analysis before trading.",
    "sector_warning": "High concentration: {pct}% in {sector}. Consider diversifying.",
    "beta": "Wtd Beta",
    "avg_pe": "Avg P/E",
    "avg_div": "Avg Div Yield",
    "num_stocks": "Stocks",
    "backtest_return": "Simulated 1Y Return",
    "lang_label": "Language",
}

LANG_SV = {
    "title": "Bygg din portfölj med legendarernas hjälp",
    "subtitle": "Välj marknader och investerare, konfigurera mix per marknad och generera blendade portföljer med exakt antal aktier — allt från riktig finansdata.",
    "step1": "01 — Välj marknader",
    "step2": "02 — Välj investerare",
    "step3": "03 — Konfigurera varje marknad",
    "step4": "04 — Dina portföljer",
    "select_all": "Välj alla",
    "deselect_all": "Avmarkera alla",
    "investor_bios": "Investerarprofiler",
    "investment_amount": "Investeringsbelopp",
    "max_stocks": "Max antal aktier",
    "investor_mix": "Investerar-mix",
    "equal_weight": "Lika vikt",
    "manual": "Manuell",
    "min_score": "Minsta poängtröskel",
    "sector_filter": "Sektorfilter",
    "all_sectors": "Alla sektorer",
    "generate": "Generera portfölj",
    "generate_multi": "Generera portföljer för {n} marknader",
    "select_prompt": "Välj minst en **marknad** och en **investerare** för att generera portföljer.",
    "invested": "INVESTERAT",
    "remaining": "KVAR",
    "total_invested": "TOTALT INVESTERAT",
    "total_remaining": "TOTALT KVAR",
    "company": "BOLAG",
    "ticker": "TICKER",
    "weight": "VIKT",
    "price": "PRIS",
    "shares": "ANTAL",
    "cost": "KOSTNAD",
    "sector_breakdown": "Sektorfördelning",
    "risk_metrics": "Portföljens riskmetrik",
    "score_comparison": "Poängjämförelse",
    "backtest": "Historisk backtest (1 år)",
    "correlation": "Aktiekorrelationsmatris",
    "contributors": "Visa investerarbidrag per aktie",
    "export_csv": "Ladda ner portfölj CSV",
    "save_config": "Spara konfiguration",
    "load_config": "Ladda konfiguration",
    "compare_mode": "Jämförelse sida vid sida",
    "compare_a": "Mix A",
    "compare_b": "Mix B",
    "no_stocks": "Inga giltiga aktier hittades.",
    "stocks": "aktier",
    "of": "av",
    "selected": "valda",
    "investors_selected": "investerare valda",
    "weights_sum": "Viktsumma",
    "should_be_100": "ska vara 100%",
    "disclaimer": "Priser är ungefärliga. Portföljerna är AI-genererade simuleringar baserade på investerarnas kända filosofier och utgör <strong>inte finansiell rådgivning</strong>. All investering innebär risk — verifiera alltid priser, tillgänglighet och gör din egen analys innan handel.",
    "sector_warning": "Hög koncentration: {pct}% i {sector}. Överväg att diversifiera.",
    "beta": "Vtd Beta",
    "avg_pe": "Snitt P/E",
    "avg_div": "Snitt Utd",
    "num_stocks": "Aktier",
    "backtest_return": "Simulerad 1-årsavkastning",
    "lang_label": "Språk",
}


def t(key):
    lang = st.session_state.get("lang", "en")
    d = LANG_SV if lang == "sv" else LANG_EN
    return d.get(key, LANG_EN.get(key, key))


# ═══════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .stApp { background-color: #0c0c14; }
    section[data-testid="stSidebar"] { background-color: #10101a; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .step-label {
        font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
        color: rgba(255,255,255,0.4); font-weight: 600; margin-bottom: 12px;
        font-family: monospace;
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
        "label": "Sverige 🇸🇪", "flag": "🇸🇪", "hint": "OMX Stockholm",
        "tickers": ["INVE-B.ST", "VOLV-B.ST", "ERIC-B.ST", "ASSA-B.ST", "ATCO-A.ST",
                     "SEB-A.ST", "SHB-A.ST", "HEXA-B.ST", "SAND.ST", "ABB.ST",
                     "ALFA.ST", "ESSITY-B.ST", "SWED-A.ST", "SKF-B.ST", "TELIA.ST",
                     "ELUX-B.ST", "KINV-B.ST", "LUND-B.ST", "GETI-B.ST", "NIBE-B.ST"],
    },
    "nordic": {
        "label": "Norden 🇳🇴", "flag": "🇳🇴", "hint": "OMX Nordic",
        "tickers": ["NOVO-B.CO", "MAERSK-B.CO", "DSV.CO", "CARL-B.CO", "ORSTED.CO",
                     "NESTE.HE", "FORTUM.HE", "UPM.HE", "EQNR.OL", "DNB.OL",
                     "MOWI.OL", "TEL.OL", "ORK.OL", "YARA.OL", "SALM.OL"],
    },
    "us": {
        "label": "USA 🇺🇸", "flag": "🇺🇸", "hint": "S&P 500 / Nasdaq",
        "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "TSLA",
                     "UNH", "JNJ", "V", "JPM", "PG", "MA", "HD", "DIS", "NFLX",
                     "ADBE", "CRM", "PFE"],
    },
    "europe": {
        "label": "Europa 🇪🇺", "flag": "🇪🇺", "hint": "Euronext / FTSE / DAX",
        "tickers": ["ASML.AS", "MC.PA", "SAP.DE", "SIE.DE", "NESN.SW", "ROG.SW",
                     "NOVN.SW", "AZN.L", "SHEL.L", "ULVR.L", "OR.PA", "TTE.PA",
                     "BAS.DE", "ALV.DE", "DTE.DE", "BAYN.DE", "BMW.DE", "VOW3.DE",
                     "AI.PA", "BN.PA"],
    },
    "asia": {
        "label": "Asien 🇯🇵", "flag": "🇯🇵", "hint": "Nikkei / Hang Seng / KOSPI",
        "tickers": ["7203.T", "6758.T", "9984.T", "6861.T", "8306.T",
                     "9433.T", "6501.T", "7267.T", "4502.T", "6902.T",
                     "TSM", "005930.KS", "000660.KS", "2330.TW", "9988.HK"],
    },
    "emerging": {
        "label": "Emerging 🌍", "flag": "🌍", "hint": "Brazil, India, etc.",
        "tickers": ["VALE", "PBR", "ITUB", "BABA", "JD", "PDD", "INFY", "WIT",
                     "HDB", "IBN", "NU", "GRAB", "SE", "MELI", "STNE"],
    },
    "global": {
        "label": "Global 🌐", "flag": "🌐", "hint": "All markets mix",
        "tickers": ["AAPL", "MSFT", "NVDA", "ASML.AS", "MC.PA", "TSM", "NOVO-B.CO",
                     "NESN.SW", "7203.T", "INVE-B.ST", "BABA", "SHEL.L", "SAP.DE",
                     "JNJ", "MELI", "ABB.ST", "EQNR.OL", "HDB", "AZN.L", "VALE"],
    },
    "custom": {
        "label": "Custom ✏️", "flag": "✏️", "hint": "Enter your own tickers",
        "tickers": [],
    },
}

# ═══════════════════════════════════════════════════════════════
# INVESTORS
# ═══════════════════════════════════════════════════════════════

INVESTORS = [
    {"id": "buffett", "name": "Warren Buffett", "strategy": "Value Investing",
     "color": "#48bb78", "wiki": "Warren_Buffett",
     "bio": "Warren Buffett (born 1930) — CEO of Berkshire Hathaway. 'Oracle of Omaha.' Buys undervalued companies with strong moats, consistent earnings, excellent management. Holds forever."},
    {"id": "lynch", "name": "Peter Lynch", "strategy": "Growth at Reasonable Price",
     "color": "#f6ad55", "wiki": "Peter_Lynch",
     "bio": "Peter Lynch (born 1944) — managed Magellan Fund 1977-1990, 29% annual returns. 'Invest in what you know.' Seeks tenbaggers at fair prices."},
    {"id": "soros", "name": "George Soros", "strategy": "Global Macro",
     "color": "#b794f4", "wiki": "George_Soros",
     "bio": "George Soros (born 1930) — founder of Soros Fund Management. Reflexivity theory. Broke the Bank of England 1992. Macro imbalances and asymmetric bets."},
    {"id": "dalio", "name": "Ray Dalio", "strategy": "Risk Parity",
     "color": "#4fd1c5", "wiki": "Ray_Dalio",
     "bio": "Ray Dalio (born 1949) — founder of Bridgewater, world's largest hedge fund. Pioneered risk parity and All Weather portfolios. Economic cycles and diversification."},
    {"id": "wood", "name": "Cathie Wood", "strategy": "Disruptive Innovation",
     "color": "#a78bfa", "wiki": "Cathie_Wood",
     "bio": "Cathie Wood (born 1955) — founder of ARK Invest. AI, genomics, robotics, blockchain, EVs. Wright's Law. 5-year horizon, revenue growth over profitability."},
    {"id": "icahn", "name": "Carl Icahn", "strategy": "Activist Contrarian",
     "color": "#f56565", "wiki": "Carl_Icahn",
     "bio": "Carl Icahn (born 1936) — legendary activist investor. Targets undervalued companies, pushes for spin-offs, buybacks, management changes. Thinks like an owner."},
    {"id": "templeton", "name": "John Templeton", "strategy": "Global Value",
     "color": "#a0c45a", "wiki": "John_Templeton",
     "bio": "Sir John Templeton (1912-2008) — pioneer of international investing. 'Maximum pessimism' — buy what everyone abandoned. Patient, 5+ year contrarian."},
    {"id": "livermore", "name": "Jesse Livermore", "strategy": "Momentum & Speculation",
     "color": "#fc8181", "wiki": "Jesse_Livermore",
     "bio": "Jesse Livermore (1877-1940) — legendary tape reader and momentum trader. Follow the trend, pyramid winners, cut losers fast. 'The market is always right.'"},
    {"id": "lundberg", "name": "Fredrik Lundberg", "strategy": "Patient Value (Nordic)",
     "color": "#68d391", "wiki": "Fredrik_Lundberg",
     "bio": "Fredrik Lundberg (born 1951) — Sweden's Buffett. Lundbergs AB portfolio of Nordic quality: Handelsbanken, Sandvik, Skanska. Buys and holds for decades."},
    {"id": "wallenberg", "name": "Marcus Wallenberg", "strategy": "Industrial Dynasty",
     "color": "#90cdf4", "wiki": "Marcus_Wallenberg_(born_1956)",
     "bio": "Marcus Wallenberg (born 1956) — Sweden's most powerful dynasty. Investor AB controls ABB, Atlas Copco, SEB, Ericsson, AstraZeneca. Thinks in generations."},
    {"id": "gardell", "name": "Christer Gardell", "strategy": "European Activist",
     "color": "#fbb6ce", "wiki": "Christer_Gardell",
     "bio": "Christer Gardell (born 1960) — co-founded Cevian Capital, Europe's largest activist fund. Targets undervalued companies, pushes for restructuring."},
    {"id": "bennet", "name": "Carl Bennet", "strategy": "Sustainable Long-Term",
     "color": "#fbd38d", "wiki": "Carl_Bennet_(industrialist)",
     "bio": "Carl Bennet (born 1951) — Swedish industrialist. Active ownership in medtech/industrials. Sustainability, knowledge-driven growth. Getinge, Lifco."},
]

INV_BY_ID = {inv["id"]: inv for inv in INVESTORS}

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _get(info, key, default=None):
    val = info.get(key, default)
    return default if val is None or val == "N/A" else val

def get_price(info):
    return _get(info, "currentPrice") or _get(info, "regularMarketPrice") or _get(info, "previousClose", 0.0)

def fmt_num(n):
    return f"{n:,.0f}".replace(",", " ")

# ═══════════════════════════════════════════════════════════════
# WIKIPEDIA PHOTOS (cached)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_wiki_photo(wiki_slug):
    """Fetch thumbnail URL from Wikipedia API."""
    try:
        import urllib.request
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_slug}"
        req = urllib.request.Request(url, headers={"User-Agent": "InvestorInsights/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("thumbnail", {}).get("source")
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════
# DATA FETCHING (cached)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)
def fetch_stock_data(ticker):
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
            return {"error": f"No data for '{ticker}'"}
        hist = tk.history(period="1y")
        return {"info": info, "history": hist}
    except Exception as e:
        return {"error": str(e)}

def compute_extras(info, hist):
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
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def score_buffett(info, extras):
    s, r = 0, []
    pe = _get(info, "trailingPE"); roe = _get(info, "returnOnEquity")
    dte = _get(info, "debtToEquity"); fcf = _get(info, "freeCashflow")
    te, fe = _get(info, "trailingEps"), _get(info, "forwardEps")
    if pe is not None and pe < 15: s += 30; r.append(f"Low P/E ({pe:.1f})")
    if roe is not None and roe > 0.15: s += 20; r.append(f"High ROE ({roe*100:.1f}%)")
    if dte is not None and dte < 50: s += 20; r.append(f"Low D/E ({dte:.1f})")
    if fcf is not None and fcf > 0: s += 15; r.append("Positive FCF")
    if te and fe and te > 0 and fe > te: s += 15; r.append("Growing EPS")
    return min(s, 100), "; ".join(r) or "Low match."

def score_lynch(info, extras):
    s, r = 0, []
    peg = extras.get("pegRatio"); pe = _get(info, "trailingPE")
    eg = _get(info, "earningsGrowth"); rg = _get(info, "revenueGrowth")
    ins = _get(info, "heldPercentInsiders")
    if peg is not None and peg < 1: s += 30; r.append(f"PEG<1 ({peg:.2f})")
    if eg is not None and eg > 0.15: s += 20; r.append(f"EG {eg*100:.1f}%")
    if pe is not None and 10 <= pe <= 20: s += 20; r.append(f"P/E {pe:.1f}")
    if ins is not None and ins > 0.10: s += 15; r.append(f"Insider {ins*100:.1f}%")
    if rg is not None and rg > 0.10: s += 15; r.append(f"Sales +{rg*100:.1f}%")
    return min(s, 100), "; ".join(r) or "Limited GARP."

def score_soros(info, extras):
    s, r = 0, []
    beta = _get(info, "beta"); pe = _get(info, "trailingPE")
    ret52 = extras.get("52w_change"); vol = _get(info, "volume"); avg_vol = extras.get("avg_volume")
    if beta is not None and beta > 1.2: s += 25; r.append(f"Beta {beta:.2f}")
    if ret52 is not None and ret52 > 20: s += 25; r.append(f"Mom +{ret52:.0f}%")
    if vol and avg_vol and avg_vol > 0 and vol > avg_vol: s += 20; r.append("High vol")
    if pe is not None and (pe > 25 or pe < 10): s += 15; r.append(f"Reflex P/E {pe:.1f}")
    sec = extras.get("sector_lower", "")
    if any(x in sec for x in ["energy", "financial", "basic materials"]): s += 15; r.append("Macro sector")
    return min(s, 100), "; ".join(r) or "Limited macro."

def score_dalio(info, extras):
    s, r = 0, []
    beta = _get(info, "beta"); dy = _get(info, "dividendYield"); cr = _get(info, "currentRatio")
    sec = extras.get("sector_lower", "")
    if beta is not None and beta < 1: s += 30; r.append(f"Beta {beta:.2f}")
    if dy is not None and dy > 0.02: s += 20; r.append(f"Div {dy*100:.1f}%")
    if cr is not None and cr > 2: s += 20; r.append(f"CR {cr:.1f}")
    if any(x in sec for x in ["consumer defensive", "utilities", "healthcare", "industrials"]): s += 15; r.append("Resilient")
    if beta is not None and beta < 0.8: s += 15; r.append("Low corr")
    return min(s, 100), "; ".join(r) or "Limited all-weather."

def score_wood(info, extras):
    s, r = 0, []
    rg = _get(info, "revenueGrowth"); fpe = _get(info, "forwardPE")
    beta = _get(info, "beta"); ret52 = extras.get("52w_change"); sec = extras.get("sector_lower", "")
    if rg is not None and rg > 0.20: s += 30; r.append(f"Rev +{rg*100:.1f}%")
    if fpe is not None and fpe > 30: s += 20; r.append(f"Fwd P/E {fpe:.1f}")
    if any(d in sec for d in ["technology", "healthcare", "communication", "financial services"]): s += 20; r.append("Disruptive")
    if beta is not None and beta > 1.5: s += 15; r.append(f"Beta {beta:.2f}")
    if ret52 is not None and ret52 > 15: s += 15; r.append(f"Mom +{ret52:.0f}%")
    return min(s, 100), "; ".join(r) or "Limited disruption."

def score_icahn(info, extras):
    s, r = 0, []
    pe = _get(info, "trailingPE"); pb = _get(info, "priceToBook")
    cash = _get(info, "totalCash"); mcap = _get(info, "marketCap")
    ret52 = extras.get("52w_change"); roe = _get(info, "returnOnEquity"); assets = _get(info, "totalAssets")
    if pe is not None and pe < 12: s += 30; r.append(f"P/E {pe:.1f}")
    if pb is not None and pb < 1: s += 25; r.append(f"P/B {pb:.2f}")
    if cash and mcap and mcap > 0 and (cash / mcap) > 0.10: s += 20; r.append(f"Cash {cash/mcap*100:.0f}%")
    if ret52 is not None and ret52 < 0: s += 15; r.append(f"Down {ret52:.1f}%")
    if roe is not None and roe < 0.10 and assets and assets > 0: s += 10; r.append("Activist opp")
    return min(s, 100), "; ".join(r) or "Limited contrarian."

def score_templeton(info, extras):
    s, r = 0, []
    pe = _get(info, "trailingPE"); pb = _get(info, "priceToBook")
    ret52 = extras.get("52w_change"); dy = _get(info, "dividendYield"); eg = _get(info, "earningsGrowth")
    if pe is not None and pe < 12: s += 30; r.append(f"P/E {pe:.1f}")
    if ret52 is not None and ret52 < -10: s += 25; r.append(f"Pessimism {ret52:.0f}%")
    if pb is not None and pb < 1.5: s += 20; r.append(f"P/B {pb:.2f}")
    if dy is not None and dy > 0.03: s += 15; r.append(f"Div {dy*100:.1f}%")
    if eg is not None and eg > 0.05: s += 10; r.append("Recovery")
    return min(s, 100), "; ".join(r) or "Limited deep-value."

def score_livermore(info, extras):
    s, r = 0, []
    ret52 = extras.get("52w_change"); beta = _get(info, "beta")
    vol = _get(info, "volume"); avg_vol = extras.get("avg_volume"); rg = _get(info, "revenueGrowth")
    if ret52 is not None and ret52 > 30: s += 30; r.append(f"Mom +{ret52:.0f}%")
    elif ret52 is not None and ret52 > 15: s += 20; r.append(f"Mom +{ret52:.0f}%")
    if beta is not None and beta > 1.3: s += 25; r.append(f"Beta {beta:.2f}")
    if vol and avg_vol and avg_vol > 0 and vol > avg_vol * 1.5: s += 20; r.append("Breakout vol")
    elif vol and avg_vol and avg_vol > 0 and vol > avg_vol: s += 10; r.append("Above avg vol")
    if rg is not None and rg > 0.15: s += 15; r.append(f"Rev +{rg*100:.1f}%")
    return min(s, 100), "; ".join(r) or "Limited momentum."

def score_lundberg(info, extras):
    s, r = 0, []
    pb = _get(info, "priceToBook"); roa = _get(info, "returnOnAssets")
    payout = _get(info, "payoutRatio"); margin = _get(info, "profitMargins"); rng = extras.get("52w_range_pct")
    if pb is not None and pb < 1.5: s += 30; r.append(f"P/B {pb:.2f}")
    if roa is not None and roa > 0.08: s += 20; r.append(f"ROA {roa*100:.1f}%")
    if payout is not None and payout > 0.30: s += 20; r.append(f"Payout {payout*100:.0f}%")
    if rng is not None and rng < 50: s += 15; r.append(f"Low vol ({rng:.0f}%)")
    if margin is not None and margin > 0.10: s += 15; r.append(f"Margin {margin*100:.1f}%")
    return min(s, 100), "; ".join(r) or "Limited Nordic value."

def score_wallenberg(info, extras):
    s, r = 0, []
    eg = _get(info, "earningsGrowth"); cr = _get(info, "currentRatio")
    dte = _get(info, "debtToEquity"); beta = _get(info, "beta"); sec = extras.get("sector_lower", "")
    if eg is not None and eg > 0.12: s += 25; r.append(f"EG {eg*100:.1f}%")
    if cr is not None and cr > 1.5: s += 20; r.append(f"CR {cr:.1f}")
    if dte is not None and dte < 80: s += 20; r.append(f"D/E {dte:.1f}")
    if any(x in sec for x in ["technology", "healthcare", "industrials"]): s += 20; r.append("Innovation")
    if beta is not None and beta < 1: s += 15; r.append(f"Beta {beta:.2f}")
    return min(s, 100), "; ".join(r) or "Limited dynasty."

def score_gardell(info, extras):
    s, r = 0, []
    target = _get(info, "targetMeanPrice"); price = get_price(info)
    roe = _get(info, "returnOnEquity"); assets = _get(info, "totalAssets")
    eg = _get(info, "earningsGrowth"); ret52 = extras.get("52w_change")
    if target and price and price > 0 and (target - price) / price > 0.20:
        s += 30; r.append(f"Upside {(target-price)/price*100:.0f}%")
    if ret52 is not None and ret52 < 0: s += 20; r.append(f"Down {ret52:.1f}%")
    fs = _get(info, "floatShares"); so = _get(info, "sharesOutstanding")
    if fs and so and so > 0 and fs / so > 0.50: s += 20; r.append("Free float")
    if roe is not None and roe < 0.10 and assets and assets > 0: s += 15; r.append("Governance")
    if eg is not None and eg < 0: s += 15; r.append("Turnaround")
    return min(s, 100), "; ".join(r) or "Limited activist."

def score_bennet(info, extras):
    s, r = 0, []
    pb = _get(info, "priceToBook"); roe = _get(info, "returnOnEquity")
    payout = _get(info, "payoutRatio"); margin = _get(info, "profitMargins"); dte = _get(info, "debtToEquity")
    if pb is not None and pb < 2: s += 25; r.append(f"P/B {pb:.2f}")
    if roe is not None and roe > 0.10: s += 20; r.append(f"ROE {roe*100:.1f}%")
    if payout is not None and payout > 0.25: s += 20; r.append(f"Payout {payout*100:.0f}%")
    if margin is not None and margin > 0.08: s += 20; r.append(f"Margin {margin*100:.1f}%")
    if dte is not None and dte < 80: s += 15; r.append(f"D/E {dte:.1f}")
    return min(s, 100), "; ".join(r) or "Limited sustainable."

SCORE_FN = {
    "buffett": score_buffett, "lynch": score_lynch, "soros": score_soros,
    "dalio": score_dalio, "wood": score_wood, "icahn": score_icahn,
    "templeton": score_templeton, "livermore": score_livermore,
    "lundberg": score_lundberg, "wallenberg": score_wallenberg,
    "gardell": score_gardell, "bennet": score_bennet,
}

# ═══════════════════════════════════════════════════════════════
# ANALYSIS + BLENDING
# ═══════════════════════════════════════════════════════════════

def analyse_stock(ticker):
    data = fetch_stock_data(ticker)
    if "error" in data:
        return {"ticker": ticker, "error": data["error"]}
    info, hist = data["info"], data["history"]
    extras = compute_extras(info, hist)
    price = get_price(info)
    scores, explanations = {}, {}
    for inv_id, func in SCORE_FN.items():
        sc, ex = func(info, extras)
        scores[inv_id] = sc
        explanations[inv_id] = ex
    return {
        "ticker": ticker, "name": _get(info, "shortName", ticker),
        "price": price, "currency": _get(info, "currency", ""),
        "sector": _get(info, "sector", "N/A"),
        "pe": _get(info, "trailingPE"), "pb": _get(info, "priceToBook"),
        "roe": _get(info, "returnOnEquity"), "div_yield": _get(info, "dividendYield"),
        "beta": _get(info, "beta"),
        "scores": scores, "explanations": explanations,
    }


def blend_and_allocate(stock_results, weights, budget, max_stocks, min_score=0, sector_filter=None):
    valid = [r for r in stock_results if "error" not in r and r["price"] > 0]
    if sector_filter and sector_filter != "All Sectors" and sector_filter != "Alla sektorer":
        valid = [r for r in valid if r.get("sector", "") == sector_filter]
    if not valid:
        return [], 0, budget

    total_w = sum(weights.values())
    if total_w == 0:
        return [], 0, budget
    norm = {k: v / total_w for k, v in weights.items() if v > 0}

    rows = []
    for r in valid:
        composite = sum(r["scores"].get(inv_id, 0) * w for inv_id, w in norm.items())
        if composite < min_score:
            continue
        contributors = []
        for inv_id, w in norm.items():
            sc = r["scores"].get(inv_id, 0)
            if sc > 0:
                contributors.append({
                    "investor_id": inv_id, "score": sc,
                    "weight": weights.get(inv_id, 0), "contribution": sc * w,
                    "reason": r["explanations"].get(inv_id, ""),
                })
        rows.append({
            "ticker": r["ticker"], "name": r["name"], "price": r["price"],
            "currency": r["currency"], "sector": r.get("sector", "N/A"),
            "composite": round(composite, 1),
            "pe": r.get("pe"), "beta": r.get("beta"), "div_yield": r.get("div_yield"),
            "contributors": sorted(contributors, key=lambda c: c["contribution"], reverse=True),
        })

    rows.sort(key=lambda x: x["composite"], reverse=True)
    rows = rows[:max_stocks]

    total_score = sum(r["composite"] for r in rows)
    if total_score == 0:
        return rows, 0, budget

    for r in rows:
        r["allocation"] = r["composite"] / total_score * 100

    for r in rows:
        target = budget * (r["allocation"] / 100)
        r["shares"] = int(target // r["price"]) if r["price"] > 0 else 0
        r["cost"] = r["shares"] * r["price"]

    # Redistribute remainder
    total_cost = sum(r["cost"] for r in rows)
    remainder = budget - total_cost
    safety = 0
    while remainder > budget * 0.10 and safety < 200:
        safety += 1
        bought = False
        for r in rows:
            if r["price"] <= remainder:
                r["shares"] += 1
                r["cost"] += r["price"]
                remainder -= r["price"]
                bought = True
                if remainder <= budget * 0.10:
                    break
        if not bought:
            break

    total_cost = sum(r["cost"] for r in rows)
    remainder = budget - total_cost
    return rows, total_cost, remainder


# ═══════════════════════════════════════════════════════════════
# BACKTEST
# ═══════════════════════════════════════════════════════════════

def compute_backtest(portfolio, stock_results):
    """Simulate 1-year return if you had bought this portfolio a year ago."""
    histories = {}
    for sr in stock_results:
        if "error" not in sr:
            data = fetch_stock_data(sr["ticker"])
            if "error" not in data and not data["history"].empty:
                histories[sr["ticker"]] = data["history"]["Close"]

    if not histories:
        return None

    # Find common date range
    all_dates = None
    for ticker, series in histories.items():
        if all_dates is None:
            all_dates = set(series.index)
        else:
            all_dates &= set(series.index)

    if not all_dates or len(all_dates) < 10:
        return None

    sorted_dates = sorted(all_dates)

    # Weighted portfolio return
    total_alloc = sum(s["allocation"] for s in portfolio)
    if total_alloc == 0:
        return None

    portfolio_returns = pd.Series(0.0, index=sorted_dates)
    for stock in portfolio:
        ticker = stock["ticker"]
        if ticker not in histories:
            continue
        w = stock["allocation"] / total_alloc
        prices = histories[ticker].reindex(sorted_dates).ffill()
        if prices.iloc[0] > 0:
            stock_ret = (prices / prices.iloc[0] - 1) * w
            portfolio_returns = portfolio_returns + stock_ret

    return portfolio_returns


# ═══════════════════════════════════════════════════════════════
# CORRELATION
# ═══════════════════════════════════════════════════════════════

def compute_correlation(portfolio, stock_results):
    """Compute correlation matrix of daily returns for portfolio stocks."""
    histories = {}
    for sr in stock_results:
        if "error" not in sr:
            data = fetch_stock_data(sr["ticker"])
            if "error" not in data and not data["history"].empty:
                histories[sr["ticker"]] = data["history"]["Close"]

    tickers_in_portfolio = [s["ticker"] for s in portfolio if s["ticker"] in histories]
    if len(tickers_in_portfolio) < 2:
        return None

    price_df = pd.DataFrame({t: histories[t] for t in tickers_in_portfolio})
    returns_df = price_df.pct_change().dropna()
    if len(returns_df) < 10:
        return None
    return returns_df.corr()


# ═══════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════

for key, default in [
    ("selected_markets", []), ("selected_investors", []),
    ("market_configs", {}), ("results", None),
    ("custom_tickers", "AAPL, MSFT, TSLA"), ("lang", "en"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ═══════════════════════════════════════════════════════════════
# HEADER + LANGUAGE TOGGLE
# ═══════════════════════════════════════════════════════════════

hcol1, hcol2 = st.columns([6, 1])
with hcol1:
    st.markdown("""
    <div style="margin-bottom: 8px;">
        <span style="font-size: 10px; font-family: monospace; letter-spacing: 0.15em;
        text-transform: uppercase; color: rgba(255,255,255,0.35); font-weight: 600;">
        Investor Insights Engine</span>
    </div>
    """, unsafe_allow_html=True)
with hcol2:
    lang_choice = st.selectbox(
        t("lang_label"), ["English", "Svenska"],
        index=0 if st.session_state.lang == "en" else 1,
        key="lang_select", label_visibility="collapsed",
    )
    new_lang = "sv" if lang_choice == "Svenska" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

st.markdown(f"# {t('title')}")
st.markdown(
    f'<p style="font-size: 14px; color: rgba(255,255,255,0.55); line-height: 1.6;">{t("subtitle")}</p>',
    unsafe_allow_html=True,
)

# Save / Load config
with st.expander(f"💾 {t('save_config')} / {t('load_config')}"):
    sc1, sc2 = st.columns(2)
    with sc1:
        config_data = {
            "markets": st.session_state.selected_markets,
            "investors": st.session_state.selected_investors,
            "configs": st.session_state.market_configs,
            "custom_tickers": st.session_state.custom_tickers,
            "lang": st.session_state.lang,
        }
        st.download_button(
            t("save_config"), json.dumps(config_data, indent=2),
            "investor_config.json", "application/json",
        )
    with sc2:
        uploaded = st.file_uploader(t("load_config"), type="json", key="config_upload")
        if uploaded:
            try:
                loaded = json.loads(uploaded.read().decode())
                st.session_state.selected_markets = loaded.get("markets", [])
                st.session_state.selected_investors = loaded.get("investors", [])
                st.session_state.market_configs = loaded.get("configs", {})
                st.session_state.custom_tickers = loaded.get("custom_tickers", "")
                st.session_state.lang = loaded.get("lang", "en")
                st.success("Configuration loaded!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load: {e}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# STEP 01 — SELECT MARKETS
# ═══════════════════════════════════════════════════════════════

st.markdown(f'<div class="step-label">{t("step1")}</div>', unsafe_allow_html=True)

market_cols = st.columns(len(MARKETS))
for i, (mid, mdata) in enumerate(MARKETS.items()):
    with market_cols[i]:
        selected = mid in st.session_state.selected_markets
        if st.button(
            mdata["label"], key=f"m_{mid}",
            use_container_width=True,
            type="primary" if selected else "secondary",
        ):
            if selected:
                st.session_state.selected_markets.remove(mid)
            else:
                st.session_state.selected_markets.append(mid)
                if mid not in st.session_state.market_configs:
                    st.session_state.market_configs[mid] = {
                        "mode": "equal", "weights": {}, "amount": 100000,
                        "max_stocks": 10, "min_score": 0, "sector_filter": None,
                    }
            st.rerun()

if "custom" in st.session_state.selected_markets:
    st.session_state.custom_tickers = st.text_input(
        "Enter comma-separated tickers", value=st.session_state.custom_tickers,
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# STEP 02 — SELECT INVESTORS (with photos)
# ═══════════════════════════════════════════════════════════════

st.markdown(f'<div class="step-label">{t("step2")}</div>', unsafe_allow_html=True)

sa1, sa2, _ = st.columns([1, 1, 4])
with sa1:
    if st.button(t("select_all"), key="sa"):
        st.session_state.selected_investors = [inv["id"] for inv in INVESTORS]
        st.rerun()
with sa2:
    if st.button(t("deselect_all"), key="da"):
        st.session_state.selected_investors = []
        st.rerun()

inv_cols = st.columns(3)
for i, inv in enumerate(INVESTORS):
    with inv_cols[i % 3]:
        sel = inv["id"] in st.session_state.selected_investors
        check = "✅" if sel else "⬜"
        if st.button(f"{check} {inv['name']} — {inv['strategy']}", key=f"i_{inv['id']}", use_container_width=True):
            if sel:
                st.session_state.selected_investors.remove(inv["id"])
            else:
                st.session_state.selected_investors.append(inv["id"])
            st.rerun()

if st.session_state.selected_investors:
    st.markdown(f"**{len(st.session_state.selected_investors)}** {t('of')} **{len(INVESTORS)}** {t('investors_selected')}")

with st.expander(t("investor_bios")):
    for inv in INVESTORS:
        if inv["id"] in st.session_state.selected_investors:
            photo_url = fetch_wiki_photo(inv.get("wiki", ""))
            img_html = ""
            if photo_url:
                img_html = (
                    f'<img src="{photo_url}" style="width:60px; height:60px; '
                    f'border-radius:10px; object-fit:cover; border:2px solid {inv["color"]}33; '
                    f'margin-right:14px; float:left;" />'
                )
            st.markdown(
                f'<div style="margin-bottom:14px; padding:12px 14px; overflow:hidden; '
                f'border-left:3px solid {inv["color"]}; '
                f'background:rgba(255,255,255,0.02); border-radius:0 8px 8px 0;">'
                f'{img_html}'
                f'<strong style="color:{inv["color"]};">{inv["name"]}</strong> '
                f'<span style="font-size:11px; color:rgba(255,255,255,0.4); '
                f'font-family:monospace;">({inv["strategy"]})</span><br>'
                f'<span style="font-size:13px; color:rgba(255,255,255,0.7);">{inv["bio"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# STEP 03 — CONFIGURE EACH MARKET
# ═══════════════════════════════════════════════════════════════

if st.session_state.selected_markets and st.session_state.selected_investors:
    st.markdown(f'<div class="step-label">{t("step3")}</div>', unsafe_allow_html=True)

    # Collect available sectors from all markets for filtering
    ALL_SECTORS = ["All Sectors" if st.session_state.lang == "en" else "Alla sektorer"]

    for mid in st.session_state.selected_markets:
        mdata = MARKETS[mid]
        cfg = st.session_state.market_configs.get(mid, {
            "mode": "equal", "weights": {}, "amount": 100000,
            "max_stocks": 10, "min_score": 0, "sector_filter": None,
        })

        st.markdown(f"### {mdata['label']}")
        st.caption(mdata["hint"])

        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])

        with c1:
            cfg["amount"] = st.number_input(
                t("investment_amount"), min_value=0, value=cfg.get("amount", 100000),
                step=10000, key=f"amt_{mid}",
            )
        with c2:
            cfg["max_stocks"] = st.slider(
                t("max_stocks"), 5, 20, cfg.get("max_stocks", 10), key=f"ms_{mid}",
            )
        with c3:
            cfg["min_score"] = st.slider(
                t("min_score"), 0, 60, cfg.get("min_score", 0), step=5, key=f"minscore_{mid}",
                help="Exclude stocks with composite score below this threshold",
            )
        with c4:
            mode_opts = [t("equal_weight"), t("manual")]
            cur = 0 if cfg.get("mode", "equal") == "equal" else 1
            mc = st.radio(t("investor_mix"), mode_opts, index=cur, key=f"mode_{mid}", horizontal=True)
            cfg["mode"] = "equal" if mc == mode_opts[0] else "manual"

        # Sector filter
        sector_opts = ALL_SECTORS + [
            "Technology", "Healthcare", "Financial Services", "Industrials",
            "Consumer Cyclical", "Consumer Defensive", "Energy", "Basic Materials",
            "Communication Services", "Utilities", "Real Estate",
        ]
        cfg["sector_filter"] = st.selectbox(
            t("sector_filter"), sector_opts,
            index=0, key=f"sf_{mid}",
        )

        active_inv = [inv for inv in INVESTORS if inv["id"] in st.session_state.selected_investors]

        if cfg["mode"] == "equal":
            eq_w = round(100 / len(active_inv), 1) if active_inv else 0
            cfg["weights"] = {inv["id"]: eq_w for inv in active_inv}
            st.caption(f"*{t('equal_weight')}:* " + " | ".join(f"{inv['name']}: {eq_w:.1f}%" for inv in active_inv))
        else:
            st.markdown(f"**{t('weights_sum')} → 100%:**")
            wcols = st.columns(min(len(active_inv), 4))
            for j, inv in enumerate(active_inv):
                with wcols[j % min(len(active_inv), 4)]:
                    w = cfg["weights"].get(inv["id"], round(100 / len(active_inv), 1))
                    cfg["weights"][inv["id"]] = st.number_input(
                        inv["name"], 0.0, 100.0, float(w), 5.0, key=f"w_{mid}_{inv['id']}",
                    )
            tw = sum(cfg["weights"].get(inv["id"], 0) for inv in active_inv)
            if abs(tw - 100) > 1:
                st.warning(f"{t('weights_sum')}: **{tw:.1f}%** — {t('should_be_100')}")
            else:
                st.success(f"{t('weights_sum')}: {tw:.1f}% ✓")

        st.session_state.market_configs[mid] = cfg
        st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# COMPARISON MODE
# ═══════════════════════════════════════════════════════════════

if st.session_state.selected_markets and st.session_state.selected_investors:
    with st.expander(f"🔄 {t('compare_mode')}"):
        st.markdown("Compare two different investor mixes on the same market.")
        cmp_market = st.selectbox(
            "Market to compare",
            st.session_state.selected_markets,
            format_func=lambda m: MARKETS[m]["label"],
            key="cmp_mkt",
        )
        active_inv = [inv for inv in INVESTORS if inv["id"] in st.session_state.selected_investors]

        ca, cb = st.columns(2)
        weights_a, weights_b = {}, {}
        with ca:
            st.markdown(f"**{t('compare_a')}**")
            for inv in active_inv:
                weights_a[inv["id"]] = st.number_input(
                    inv["name"], 0.0, 100.0, round(100 / len(active_inv), 1), 5.0,
                    key=f"cmpA_{inv['id']}",
                )
        with cb:
            st.markdown(f"**{t('compare_b')}**")
            for inv in active_inv:
                weights_b[inv["id"]] = st.number_input(
                    inv["name"], 0.0, 100.0, 0.0, 5.0,
                    key=f"cmpB_{inv['id']}",
                )

        st.session_state["compare_weights"] = {
            "market": cmp_market, "a": weights_a, "b": weights_b,
        }

# ═══════════════════════════════════════════════════════════════
# GENERATE BUTTON
# ═══════════════════════════════════════════════════════════════

can_gen = len(st.session_state.selected_markets) > 0 and len(st.session_state.selected_investors) > 0

if not can_gen:
    st.info(t("select_prompt"))
else:
    n = len(st.session_state.selected_markets)
    btn_txt = t("generate") if n == 1 else t("generate_multi").replace("{n}", str(n))

    if st.button(btn_txt, type="primary", use_container_width=True):
        all_results = {}
        market_tickers = {}
        for mid in st.session_state.selected_markets:
            if mid == "custom":
                market_tickers[mid] = [t2.strip().upper() for t2 in st.session_state.custom_tickers.split(",") if t2.strip()]
            else:
                market_tickers[mid] = MARKETS[mid]["tickers"]

        total = sum(len(v) for v in market_tickers.values())
        progress = st.progress(0, text="Fetching data...")
        done = 0

        for mid in st.session_state.selected_markets:
            tickers = market_tickers[mid]
            cfg = st.session_state.market_configs.get(mid, {
                "mode": "equal", "weights": {}, "amount": 100000,
                "max_stocks": 10, "min_score": 0, "sector_filter": None,
            })

            stock_results = []
            for ticker in tickers:
                progress.progress(done / total if total > 0 else 0, text=f"Analysing {ticker}...")
                stock_results.append(analyse_stock(ticker))
                done += 1

            active_inv = [inv for inv in INVESTORS if inv["id"] in st.session_state.selected_investors]
            if cfg["mode"] == "equal":
                weights = {inv["id"]: 100 / len(active_inv) for inv in active_inv} if active_inv else {}
            else:
                weights = {inv["id"]: cfg["weights"].get(inv["id"], 0) for inv in active_inv}

            portfolio, tc, rem = blend_and_allocate(
                stock_results, weights, cfg["amount"], cfg["max_stocks"],
                cfg.get("min_score", 0), cfg.get("sector_filter"),
            )

            all_results[mid] = {
                "portfolio": portfolio, "total_cost": tc, "remainder": rem,
                "weights": weights, "stock_results": stock_results,
            }

        # Comparison
        cmp = st.session_state.get("compare_weights")
        if cmp and cmp["market"] in all_results:
            cmp_mid = cmp["market"]
            sr = all_results[cmp_mid]["stock_results"]
            cfg_c = st.session_state.market_configs.get(cmp_mid, {})
            pa, tca, ra = blend_and_allocate(sr, cmp["a"], cfg_c.get("amount", 100000), cfg_c.get("max_stocks", 10))
            pb, tcb, rb = blend_and_allocate(sr, cmp["b"], cfg_c.get("amount", 100000), cfg_c.get("max_stocks", 10))
            all_results["__compare_a"] = {"portfolio": pa, "total_cost": tca, "remainder": ra, "weights": cmp["a"], "stock_results": sr}
            all_results["__compare_b"] = {"portfolio": pb, "total_cost": tcb, "remainder": rb, "weights": cmp["b"], "stock_results": sr}

        progress.progress(1.0, text="Done!")
        st.session_state.results = all_results

# ═══════════════════════════════════════════════════════════════
# STEP 04 — RESULTS
# ═══════════════════════════════════════════════════════════════

if st.session_state.results:
    st.markdown(f'<div class="step-label">{t("step4")}</div>', unsafe_allow_html=True)

    grand_inv, grand_rem = 0, 0

    display_markets = [(mid, res) for mid, res in st.session_state.results.items() if not mid.startswith("__")]

    for mid, res in display_markets:
        mdata = MARKETS.get(mid, {"label": mid, "flag": ""})
        portfolio = res["portfolio"]
        total_cost = res["total_cost"]
        remainder = res["remainder"]
        weights = res["weights"]
        stock_results = res["stock_results"]

        grand_inv += total_cost
        grand_rem += remainder

        if not portfolio:
            st.warning(f"{mdata.get('flag', '')} {mdata['label']}: {t('no_stocks')}")
            continue

        st.markdown(f"### {mdata['label']} — {len(portfolio)} {t('stocks')}")

        # Investor mix tags
        aw = {k: v for k, v in weights.items() if v > 0}
        mix = "  ".join(f"`{INV_BY_ID[k]['name']}: {v:.0f}%`" for k, v in sorted(aw.items(), key=lambda x: -x[1]))
        st.markdown(f"**{t('investor_mix')}:** {mix}")

        # ---- PORTFOLIO TABLE ----
        max_alloc = max(r["allocation"] for r in portfolio)
        tbl = '<div style="overflow-x:auto;margin:12px 0;"><table style="width:100%;border-collapse:collapse;font-size:13px;font-family:monospace;"><thead><tr style="border-bottom:1px solid rgba(255,255,255,0.1);">'
        for h, align in [(t("company"), "left"), (t("ticker"), "left"), (t("weight"), "left"), ("", "left"), (t("price"), "right"), (t("shares"), "right"), (t("cost"), "right")]:
            w = 'width:18%;' if h == "" else ""
            tbl += f'<th style="padding:10px 8px;text-align:{align};color:rgba(255,255,255,0.45);font-size:10px;letter-spacing:0.06em;font-weight:600;{w}">{h}</th>'
        tbl += '</tr></thead><tbody>'

        for i, stock in enumerate(portfolio):
            hue = (i * 137.5) % 360
            bp = stock["allocation"] / max_alloc * 100 if max_alloc > 0 else 0
            tbl += f'''<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                <td style="padding:9px 8px;color:rgba(255,255,255,0.8);font-weight:600;font-family:system-ui;font-size:12px;">{stock["name"]}</td>
                <td style="padding:9px 8px;color:rgba(255,255,255,0.4);font-size:11px;">{stock["ticker"]}</td>
                <td style="padding:9px 8px;color:rgba(255,255,255,0.75);font-weight:600;">{stock["allocation"]:.1f}%</td>
                <td style="padding:9px 8px 9px 0;"><div style="height:6px;border-radius:3px;width:{bp}%;min-width:2px;background:hsl({hue},42%,52%);"></div></td>
                <td style="padding:9px 8px;text-align:right;color:rgba(255,255,255,0.55);">{stock["price"]:,.2f} {stock["currency"]}</td>
                <td style="padding:9px 8px;text-align:right;color:#fff;font-weight:700;">{stock["shares"]}</td>
                <td style="padding:9px 8px;text-align:right;color:rgba(255,255,255,0.8);font-weight:600;">{stock["cost"]:,.0f}</td>
            </tr>'''

        tbl += '</tbody></table></div>'
        st.markdown(tbl, unsafe_allow_html=True)

        # ---- INVESTED / REMAINING ----
        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown(f'<div><div style="font-size:10px;font-family:monospace;color:rgba(255,255,255,0.45);letter-spacing:0.06em;font-weight:600;">{t("invested")}</div><div style="font-size:22px;font-weight:800;font-family:monospace;color:#fff;">{fmt_num(total_cost)}</div></div>', unsafe_allow_html=True)
        with tc2:
            st.markdown(f'<div style="text-align:right;"><div style="font-size:10px;font-family:monospace;color:rgba(255,255,255,0.45);letter-spacing:0.06em;font-weight:600;">{t("remaining")}</div><div style="font-size:22px;font-weight:800;font-family:monospace;color:rgba(255,255,255,0.5);">{fmt_num(remainder)}</div></div>', unsafe_allow_html=True)

        # ---- RISK METRICS ----
        st.markdown(f"**{t('risk_metrics')}**")
        betas = [s["beta"] for s in portfolio if s.get("beta") is not None]
        pes = [s["pe"] for s in portfolio if s.get("pe") is not None]
        divs = [s["div_yield"] for s in portfolio if s.get("div_yield") is not None]

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            wtd_beta = np.average(betas, weights=[s["allocation"] for s in portfolio if s.get("beta") is not None]) if betas else None
            st.metric(t("beta"), f"{wtd_beta:.2f}" if wtd_beta else "N/A")
        with m2:
            avg_pe = np.mean(pes) if pes else None
            st.metric(t("avg_pe"), f"{avg_pe:.1f}" if avg_pe else "N/A")
        with m3:
            avg_div = np.mean(divs) if divs else None
            st.metric(t("avg_div"), f"{avg_div*100:.1f}%" if avg_div else "N/A")
        with m4:
            st.metric(t("num_stocks"), len(portfolio))

        # ---- SECTOR BREAKDOWN ----
        sectors = {}
        for s in portfolio:
            sec = s.get("sector", "N/A")
            sectors[sec] = sectors.get(sec, 0) + s["allocation"]

        st.markdown(f"**{t('sector_breakdown')}**")
        sec_df = pd.DataFrame([{"Sector": k, "Allocation %": round(v, 1)} for k, v in sorted(sectors.items(), key=lambda x: -x[1])])

        # Warning if >40% in one sector
        for sec_name, sec_pct in sectors.items():
            if sec_pct > 40:
                st.warning(t("sector_warning").replace("{pct}", f"{sec_pct:.0f}").replace("{sector}", sec_name))

        donut = alt.Chart(sec_df).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("Allocation %:Q"),
            color=alt.Color("Sector:N"),
            tooltip=["Sector", "Allocation %"],
        ).properties(height=280)
        st.altair_chart(donut, use_container_width=True)

        # ---- BACKTEST ----
        with st.expander(f"📈 {t('backtest')}"):
            bt = compute_backtest(portfolio, stock_results)
            if bt is not None and len(bt) > 0:
                final_ret = bt.iloc[-1] * 100
                st.metric(t("backtest_return"), f"{final_ret:+.1f}%")
                bt_df = bt.reset_index()
                bt_df.columns = ["Date", "Return"]
                bt_df["Return %"] = bt_df["Return"] * 100
                line = alt.Chart(bt_df).mark_area(
                    opacity=0.3, line={"color": "#48bb78"},
                ).encode(
                    x="Date:T", y="Return %:Q",
                    color=alt.value("#48bb78"),
                    tooltip=["Date:T", alt.Tooltip("Return %:Q", format=".1f")],
                ).properties(height=250)
                st.altair_chart(line, use_container_width=True)
            else:
                st.info("Insufficient historical data for backtest.")

        # ---- CORRELATION MATRIX ----
        with st.expander(f"🔗 {t('correlation')}"):
            corr = compute_correlation(portfolio, stock_results)
            if corr is not None:
                # Melt for Altair heatmap
                corr_reset = corr.reset_index().melt(id_vars="index")
                corr_reset.columns = ["Stock A", "Stock B", "Correlation"]
                heatmap = alt.Chart(corr_reset).mark_rect().encode(
                    x=alt.X("Stock A:N", sort=list(corr.columns)),
                    y=alt.Y("Stock B:N", sort=list(corr.columns)),
                    color=alt.Color("Correlation:Q", scale=alt.Scale(scheme="redyellowgreen", domain=[-1, 1])),
                    tooltip=["Stock A", "Stock B", alt.Tooltip("Correlation:Q", format=".2f")],
                ).properties(height=350)
                st.altair_chart(heatmap, use_container_width=True)
            else:
                st.info("Need at least 2 stocks with history for correlation.")

        # ---- CONTRIBUTOR BREAKDOWN ----
        with st.expander(t("contributors")):
            for stock in portfolio:
                if stock.get("contributors"):
                    contribs = "  ".join(
                        f'`{INV_BY_ID.get(c["investor_id"], {}).get("name", "?")}:'
                        f' {c["contribution"]:.1f}pts`'
                        for c in stock["contributors"][:5]
                    )
                    st.markdown(f"**{stock['ticker']}** — {contribs}")
                    for c in stock["contributors"][:3]:
                        st.caption(f"  {INV_BY_ID.get(c['investor_id'], {}).get('name', '')}: {c['reason']}")

        # ---- CSV EXPORT ----
        csv_rows = []
        for s in portfolio:
            csv_rows.append({
                "Ticker": s["ticker"], "Name": s["name"], "Sector": s.get("sector", ""),
                "Allocation %": round(s["allocation"], 1), "Price": round(s["price"], 2),
                "Currency": s["currency"], "Shares": s["shares"], "Cost": round(s["cost"], 2),
                "Composite Score": s["composite"],
            })
        csv_df = pd.DataFrame(csv_rows)
        csv_buf = csv_df.to_csv(index=False)
        st.download_button(
            f"📥 {t('export_csv')} ({mdata['label']})",
            csv_buf, f"portfolio_{mid}.csv", "text/csv",
        )

        st.markdown("---")

    # ---- GRAND TOTALS ----
    if len(display_markets) > 1:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:22px 24px;background:rgba(255,255,255,0.03);'
            f'border:1px solid rgba(255,255,255,0.08);border-radius:14px;flex-wrap:wrap;gap:16px;">'
            f'<div><div style="font-size:10px;font-family:monospace;color:rgba(255,255,255,0.45);'
            f'letter-spacing:0.06em;font-weight:600;">{t("total_invested")}</div>'
            f'<div style="font-size:22px;font-weight:800;font-family:monospace;">{fmt_num(grand_inv)}</div></div>'
            f'<div style="text-align:right;"><div style="font-size:10px;font-family:monospace;'
            f'color:rgba(255,255,255,0.45);letter-spacing:0.06em;font-weight:600;">{t("total_remaining")}</div>'
            f'<div style="font-size:22px;font-weight:800;font-family:monospace;color:rgba(255,255,255,0.5);">'
            f'{fmt_num(grand_rem)}</div></div></div>',
            unsafe_allow_html=True,
        )

    # ---- COMPARISON RESULTS ----
    cmp_a = st.session_state.results.get("__compare_a")
    cmp_b = st.session_state.results.get("__compare_b")
    if cmp_a and cmp_b and cmp_a["portfolio"] and cmp_b["portfolio"]:
        st.markdown(f"### 🔄 {t('compare_mode')}")
        cola, colb = st.columns(2)
        for col, label, data in [(cola, t("compare_a"), cmp_a), (colb, t("compare_b"), cmp_b)]:
            with col:
                st.markdown(f"**{label}**")
                for s in data["portfolio"][:8]:
                    st.markdown(f"- {s['ticker']}: {s['allocation']:.1f}% → {s['shares']} shares ({s['cost']:,.0f})")
                st.metric(t("invested"), fmt_num(data["total_cost"]))

    # ---- SCORE COMPARISON CHART ----
    st.markdown(f"### {t('score_comparison')}")
    chart_data = []
    for mid, res in display_markets:
        for stock in res["portfolio"]:
            for c in stock.get("contributors", []):
                chart_data.append({
                    "Ticker": stock["ticker"],
                    "Investor": INV_BY_ID.get(c["investor_id"], {}).get("name", c["investor_id"]),
                    "Score": c["score"],
                })
    if chart_data:
        cdf = pd.DataFrame(chart_data)
        inv_order = [inv["name"] for inv in INVESTORS if inv["id"] in st.session_state.selected_investors]
        chart = alt.Chart(cdf).mark_bar().encode(
            x=alt.X("Investor:N", sort=inv_order, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100])),
            color="Ticker:N", xOffset="Ticker:N",
            tooltip=["Ticker", "Investor", "Score"],
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# DISCLAIMER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(f'<p class="disclaimer-text">{t("disclaimer")}</p>', unsafe_allow_html=True)
