"""
Backtest entry point.
Run:  python backtest.py --mock          # synthetic data, quick sanity check
Run:  python backtest.py                 # live Yahoo Finance data
Run:  python backtest.py --tickers AAPL MSFT NVDA   # specific tickers
"""

import sys
from loguru import logger
from config import WATCHLIST

USE_MOCK = "--mock" in sys.argv

# Override watchlist from CLI: python backtest.py --tickers AAPL MSFT
if "--tickers" in sys.argv:
    idx = sys.argv.index("--tickers")
    TICKERS = sys.argv[idx + 1:]
else:
    TICKERS = WATCHLIST


def main():
    logger.info(f"=== BACKTEST ({'MOCK' if USE_MOCK else 'LIVE'}) | {len(TICKERS)} tickers ===")

    # 1. Load data
    if USE_MOCK:
        from agent.data.mock import mock_ohlcv, mock_fundamentals
        price_data   = {t: mock_ohlcv(t, days=500) for t in TICKERS}
        fundamentals = {t: mock_fundamentals(t) for t in TICKERS}
    else:
        from agent.data.fetcher import fetch_watchlist, fetch_fundamentals
        from agent.data.validator import validate, clean
        raw = fetch_watchlist(TICKERS, period="2y", interval="1d")
        price_data = {t: clean(df) for t, df in raw.items() if validate(df, t)}
        fundamentals = {t: fetch_fundamentals(t) for t in price_data}

    # 2. Run walk-forward engine per ticker
    from agent.backtest.engine import run as run_backtest
    from agent.backtest.metrics import calculate
    from agent.backtest.report import print_summary, save_equity_curve

    all_metrics = []
    for ticker, df in price_data.items():
        result = run_backtest(ticker, df, fundamentals=fundamentals)
        if not result:
            continue
        bars, trades = result
        metrics = calculate(ticker, bars, trades)
        all_metrics.append(metrics)
        save_equity_curve(ticker, bars)

    # 3. Print summary table
    if all_metrics:
        print_summary(all_metrics)
        best = max(all_metrics, key=lambda m: m.sharpe_ratio)
        logger.info(
            f"Best Sharpe: {best.ticker} ({best.sharpe_ratio:.3f}) | "
            f"return={best.total_return_pct:+.1f}% | drawdown={best.max_drawdown_pct:.1f}%"
        )
    else:
        logger.warning("No backtest results — check data or warmup bar count")


if __name__ == "__main__":
    main()
