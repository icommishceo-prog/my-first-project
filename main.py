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


def run_strategy(price_data):
    logger.info("=== Component 2: Strategy Engine ===")
    from agent.strategy.composer import decide_all
    decisions = decide_all(price_data)
    for d in decisions:
        logger.info(f"{d.ticker}: {d.action} (score={d.score:+.3f}) "
                    f"[{', '.join(s.source + '→' + s.action for s in d.contributions)}]")
    return decisions


def run_risk(decisions, price_data, portfolio_value=100_000, current_positions=None):
    logger.info("=== Component 3: Risk Manager ===")
    from agent.risk.manager import process_all
    from agent.data.mock import mock_fundamentals

    fundamentals = {t: mock_fundamentals(t) for t in price_data} if USE_MOCK else {}
    orders = process_all(
        decisions=decisions,
        price_data=price_data,
        portfolio_value=portfolio_value,
        current_positions=current_positions or {},
        fundamentals=fundamentals,
    )
    return orders, fundamentals


def run_execution(orders, price_data, fundamentals, dry_run=True):
    from agent.execution.executor import execute
    from agent.execution.fill_tracker import PositionState
    fills, state = execute(
        orders=orders,
        position_state=PositionState(),
        price_data=price_data,
        fundamentals=fundamentals,
        dry_run=dry_run,
    )
    return fills, state


if __name__ == "__main__":
    data = run_data_ingestion()
    decisions = run_strategy(data)
    orders, fundamentals = run_risk(decisions, data)
    fills, position_state = run_execution(orders, data, fundamentals, dry_run=True)

    buys = [d for d in decisions if d.action == "BUY"]
    sells = [d for d in decisions if d.action == "SELL"]
    print(f"\n=== Strategy : {len(buys)} BUY | {len(sells)} SELL | "
          f"{len(decisions) - len(buys) - len(sells)} HOLD ===")
    print(f"=== Risk orders approved : {len(orders)} ===")
    print(f"=== Execution fills confirmed : {sum(1 for f in fills if f.status == 'filled')} ===")
