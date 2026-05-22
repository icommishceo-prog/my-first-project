"""
Backtest report — prints summary table and saves equity curve to CSV.
"""

import csv
from pathlib import Path
from agent.backtest.metrics import BacktestMetrics
from agent.backtest.engine import BacktestBar
from loguru import logger

RESULTS_DIR = Path("data/backtest")


def print_summary(results: list[BacktestMetrics]) -> None:
    header = (
        f"\n{'=' * 90}\n"
        f"  BACKTEST RESULTS\n"
        f"{'=' * 90}\n"
        f"  {'Ticker':<8} {'Total%':>7} {'Ann%':>7} {'Sharpe':>7} {'MaxDD%':>8} "
        f"{'Calmar':>7} {'Win%':>6} {'AvgW%':>6} {'AvgL%':>6} {'PF':>6} {'Trades':>7}\n"
        f"  {'-' * 84}"
    )
    print(header)
    for m in sorted(results, key=lambda x: x.sharpe_ratio, reverse=True):
        print(
            f"  {m.ticker:<8} {m.total_return_pct:>+7.1f} {m.annual_return_pct:>+7.1f} "
            f"{m.sharpe_ratio:>7.3f} {m.max_drawdown_pct:>+8.1f} "
            f"{m.calmar_ratio:>7.3f} {m.win_rate_pct:>5.1f}% "
            f"{m.avg_win_pct:>+6.2f} {m.avg_loss_pct:>+6.2f} "
            f"{m.profit_factor:>6.2f} {m.num_trades:>7}"
        )
    print(f"{'=' * 90}\n")


def save_equity_curve(ticker: str, bars: list[BacktestBar]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{ticker}_equity.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "close", "action", "score", "position", "cash", "equity"])
        for b in bars:
            writer.writerow([
                b.date.date(), round(b.close, 2), b.action,
                b.score, b.position, b.cash, b.equity,
            ])
    logger.info(f"Equity curve saved → {path}")
    return path
