"""
Stock Investment Agent — entry point.
Run:  python main.py           # uses live Yahoo Finance data
Run:  python main.py --mock    # uses synthetic data (offline/sandbox mode)
"""

import sys
from loguru import logger
from config import WATCHLIST, DEFAULT_PERIOD, DEFAULT_INTERVAL

USE_MOCK = "--mock" in sys.argv


def run_data_ingestion():
    logger.info(f"=== Component 1: Data Ingestion ({'MOCK' if USE_MOCK else 'LIVE'}) ===")

    if USE_MOCK:
        from agent.data.mock import mock_ohlcv, mock_fundamentals
        price_data = {t: mock_ohlcv(t) for t in WATCHLIST}
        get_fundamentals = mock_fundamentals
    else:
        from agent.data.fetcher import fetch_watchlist, fetch_fundamentals
        price_data = fetch_watchlist(WATCHLIST, period=DEFAULT_PERIOD, interval=DEFAULT_INTERVAL)
        get_fundamentals = fetch_fundamentals

    from agent.data.validator import validate, clean

    # Validate + clean each ticker's data
    clean_data = {}
    for ticker, df in price_data.items():
        if validate(df, ticker):
            clean_data[ticker] = clean(df)

    logger.info(f"Clean data ready for {len(clean_data)} tickers")

    # Spot-check fundamentals on first ticker
    if WATCHLIST:
        fundamentals = get_fundamentals(WATCHLIST[0])
        logger.info(f"Sample fundamentals: {fundamentals}")

    return clean_data


if __name__ == "__main__":
    data = run_data_ingestion()

    for ticker, df in list(data.items())[:3]:
        print(f"\n--- {ticker} (last 3 rows) ---")
        print(df[["Open", "High", "Low", "Close", "Volume"]].tail(3).to_string())
