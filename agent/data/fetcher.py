"""
Component 1: Data Ingestion Layer
Fetches OHLCV price data and key fundamentals for a watchlist of tickers.
"""

import yfinance as yf
import pandas as pd
from loguru import logger
from typing import Optional


def fetch_ohlcv(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> Optional[pd.DataFrame]:
    """
    Pull OHLCV data for a single ticker.

    Args:
        ticker:   Stock symbol, e.g. "AAPL"
        period:   Lookback window — "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
        interval: Bar size      — "1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo"

    Returns:
        DataFrame with columns [Open, High, Low, Close, Volume] or None on failure.
    """
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return None
        df.index = pd.to_datetime(df.index)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        logger.info(f"Fetched {len(df)} bars for {ticker} ({interval}, {period})")
        return df
    except Exception as e:
        logger.error(f"fetch_ohlcv failed for {ticker}: {e}")
        return None


def fetch_fundamentals(ticker: str) -> dict:
    """
    Pull key fundamental metrics for value/quality screening.

    Returns a dict with PE, PB, ROE, debt_to_equity, market_cap, dividend_yield.
    Missing fields default to None — callers must handle None gracefully.
    """
    try:
        info = yf.Ticker(ticker).info
        fundamentals = {
            "ticker": ticker,
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "market_cap": info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
        logger.info(f"Fetched fundamentals for {ticker}: PE={fundamentals['pe_ratio']:.1f}"
                    if fundamentals["pe_ratio"] else f"Fetched fundamentals for {ticker}: PE=N/A")
        return fundamentals
    except Exception as e:
        logger.error(f"fetch_fundamentals failed for {ticker}: {e}")
        return {"ticker": ticker}


def fetch_watchlist(
    tickers: list[str],
    period: str = "1y",
    interval: str = "1d",
) -> dict[str, pd.DataFrame]:
    """
    Batch-fetch OHLCV data for a list of tickers.

    Returns a dict mapping ticker -> DataFrame (skips failures silently).
    """
    results = {}
    for ticker in tickers:
        df = fetch_ohlcv(ticker, period=period, interval=interval)
        if df is not None:
            results[ticker] = df
    logger.info(f"Watchlist fetch complete: {len(results)}/{len(tickers)} tickers loaded")
    return results
