"""
Mock data generator for offline/sandboxed testing.
Produces realistic synthetic OHLCV data + fundamentals so the full pipeline
can be validated without a live network connection.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def mock_ohlcv(
    ticker: str,
    days: int = 252,
    start_price: float = 150.0,
    volatility: float = 0.015,
) -> pd.DataFrame:
    """
    Geometric Brownian Motion price series — statistically realistic.
    """
    np.random.seed(abs(hash(ticker)) % (2**31))
    dates = pd.date_range(end=datetime.today(), periods=days, freq="B")
    daily_returns = np.random.normal(0.0003, volatility, days)
    closes = start_price * np.cumprod(1 + daily_returns)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.005, days)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.005, days)))
    opens = np.roll(closes, 1)
    opens[0] = start_price
    volumes = np.random.randint(5_000_000, 50_000_000, days).astype(float)

    return pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    }, index=dates)


MOCK_FUNDAMENTALS = {
    "AAPL":  {"pe_ratio": 28.5, "pb_ratio": 45.2, "roe": 1.47, "debt_to_equity": 174.0, "market_cap": 2_900_000_000_000, "dividend_yield": 0.005, "sector": "Technology", "industry": "Consumer Electronics"},
    "MSFT":  {"pe_ratio": 33.1, "pb_ratio": 12.8, "roe": 0.38, "debt_to_equity": 39.0,  "market_cap": 3_100_000_000_000, "dividend_yield": 0.007, "sector": "Technology", "industry": "Software"},
    "GOOGL": {"pe_ratio": 22.4, "pb_ratio": 5.9,  "roe": 0.27, "debt_to_equity": 8.0,   "market_cap": 2_000_000_000_000, "dividend_yield": None,  "sector": "Communication Services", "industry": "Internet Content"},
    "AMZN":  {"pe_ratio": 40.2, "pb_ratio": 8.1,  "roe": 0.21, "debt_to_equity": 60.0,  "market_cap": 1_900_000_000_000, "dividend_yield": None,  "sector": "Consumer Cyclical", "industry": "Internet Retail"},
    "NVDA":  {"pe_ratio": 55.0, "pb_ratio": 30.0, "roe": 0.55, "debt_to_equity": 41.0,  "market_cap": 2_500_000_000_000, "dividend_yield": 0.001, "sector": "Technology", "industry": "Semiconductors"},
}


def mock_fundamentals(ticker: str) -> dict:
    base = MOCK_FUNDAMENTALS.get(ticker, {
        "pe_ratio": 20.0, "pb_ratio": 3.0, "roe": 0.15,
        "debt_to_equity": 50.0, "market_cap": 100_000_000_000,
        "dividend_yield": 0.02, "sector": "Unknown", "industry": "Unknown",
    })
    return {"ticker": ticker, **base}
