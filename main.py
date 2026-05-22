"""
Stock Investment Agent — entry point.
Run:  python main.py           # uses live Yahoo Finance data
Run:  python main.py --mock    # uses synthetic data (offline/sandbox mode)
Run:  python main.py --schedule  # start the daily scheduler (blocks)
"""

import sys
from loguru import logger
from config import WATCHLIST, DEFAULT_PERIOD, DEFAULT_INTERVAL

USE_MOCK = "--mock" in sys.argv
SCHEDULE = "--schedule" in sys.argv

# Ledger and position state persist across cycles when running scheduled
from agent.monitoring.pnl import PortfolioLedger
from agent.execution.fill_tracker import PositionState

PORTFOLIO_VALUE = 100_000.0
_ledger = PortfolioLedger(starting_cash=PORTFOLIO_VALUE, cash=PORTFOLIO_VALUE)
_position_state = PositionState()


def run_data_ingestion():
    logger.info(f"=== Component 1: Data Ingestion ({'MOCK' if USE_MOCK else 'LIVE'}) ===")

    if USE_MOCK:
        from agent.data.mock import mock_ohlcv, mock_fundamentals
        price_data = {t: mock_ohlcv(t) for t in WATCHLIST}
        fundamentals = {t: mock_fundamentals(t) for t in WATCHLIST}
    else:
        from agent.data.fetcher import fetch_watchlist, fetch_fundamentals
        price_data = fetch_watchlist(WATCHLIST, period=DEFAULT_PERIOD, interval=DEFAULT_INTERVAL)
        fundamentals = {t: fetch_fundamentals(t) for t in price_data}

    from agent.data.validator import validate, clean
    clean_data = {}
    for ticker, df in price_data.items():
        if validate(df, ticker):
            clean_data[ticker] = clean(df)

    logger.info(f"Clean data ready for {len(clean_data)} tickers")
    return clean_data, fundamentals


def run_strategy(price_data, ledger: PortfolioLedger):
    logger.info("=== Component 2: Strategy Engine + Stop Enforcer ===")
    from agent.strategy.composer import decide_all
    from agent.monitoring.stop_enforcer import check_stops

    stop_sells = check_stops(ledger, price_data)
    signal_decisions = decide_all(price_data)

    # Stop-enforcer SELLs override any signal on the same ticker
    stop_tickers = {d.ticker for d in stop_sells}
    filtered = [d for d in signal_decisions if d.ticker not in stop_tickers]
    decisions = stop_sells + filtered

    for d in decisions:
        logger.info(f"{d.ticker}: {d.action} (score={d.score:+.3f}) "
                    f"[{', '.join(s.source + '→' + s.action for s in d.contributions)}]")
    return decisions


def run_risk(decisions, price_data, fundamentals, ledger: PortfolioLedger):
    logger.info("=== Component 3: Risk Manager ===")
    from agent.risk.manager import process_all

    orders = process_all(
        decisions=decisions,
        price_data=price_data,
        portfolio_value=ledger.total_value(price_data),
        current_positions={
            t: {"value": p["shares"] * p["avg_entry"], "sector": p.get("sector", "Unknown")}
            for t, p in ledger.open_positions.items()
        },
        fundamentals=fundamentals,
    )
    return orders


def run_execution(orders, price_data, fundamentals, dry_run=True):
    logger.info("=== Component 4: Execution ===")
    from agent.execution.executor import execute

    fills, _ = execute(
        orders=orders,
        position_state=_position_state,
        price_data=price_data,
        fundamentals=fundamentals,
        dry_run=dry_run,
    )
    return fills


def run_monitoring(ledger, price_data, decisions, orders, fills):
    logger.info("=== Component 5: Monitoring ===")
    from agent.monitoring.digest import render

    # Apply fills to ledger
    for fill in fills:
        if fill.status != "filled":
            continue
        df = price_data.get(fill.ticker)
        price = float(df["Close"].iloc[-1]) if df is not None else 0.0
        sector = _position_state.positions.get(fill.ticker, {}).get("sector", "Unknown")
        if fill.action == "BUY":
            matching_order = next((o for o in orders if o.ticker == fill.ticker), None)
            stop = matching_order.stop_price if matching_order else 0.0
            ledger.open(fill.ticker, fill.shares, price, stop, sector)
        elif fill.action == "SELL":
            ledger.close(fill.ticker, price, reason="signal/stop")

    report = render(ledger, price_data, decisions, orders, fills)
    print(report)
    return report


def run_full_cycle():
    data, fundamentals = run_data_ingestion()
    decisions = run_strategy(data, _ledger)
    orders = run_risk(decisions, data, fundamentals, _ledger)
    fills = run_execution(orders, data, fundamentals, dry_run=True)
    run_monitoring(_ledger, data, decisions, orders, fills)


if __name__ == "__main__":
    if SCHEDULE:
        from agent.monitoring.scheduler import start
        logger.info("Starting scheduled agent — Ctrl+C to stop")
        start(run_full_cycle)
    else:
        run_full_cycle()
