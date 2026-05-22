"""
Performance metrics — computed from BacktestBar equity curve.

All standard quant metrics: Sharpe, max drawdown, Calmar, win rate.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from agent.backtest.engine import BacktestBar


@dataclass
class BacktestMetrics:
    ticker: str
    total_return_pct: float
    annual_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    calmar_ratio: float
    win_rate_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float     # total_wins / total_losses (>1 = edge exists)
    num_trades: int
    num_bars: int


def calculate(ticker: str, bars: list[BacktestBar], trades: list[dict]) -> BacktestMetrics:
    if not bars:
        return BacktestMetrics(ticker, *([0.0] * 11), 0, 0)

    equity = np.array([b.equity for b in bars])
    starting = equity[0]
    ending = equity[-1]

    # Daily returns
    returns = np.diff(equity) / equity[:-1]
    mean_ret = returns.mean()
    std_ret = returns.std()

    total_ret = (ending / starting - 1) * 100
    trading_days = len(bars)
    years = trading_days / 252
    annual_ret = ((ending / starting) ** (1 / max(years, 0.01)) - 1) * 100

    sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0

    # Max drawdown
    peak = np.maximum.accumulate(equity)
    drawdowns = (equity - peak) / peak * 100
    max_dd = drawdowns.min()

    calmar = annual_ret / abs(max_dd) if max_dd != 0 else 0.0

    # Trade-level stats
    closed = [t for t in trades if t["type"] == "SELL" and "pnl" in t]
    wins  = [t for t in closed if t["pnl"] > 0]
    losses = [t for t in closed if t["pnl"] <= 0]

    win_rate = len(wins) / len(closed) * 100 if closed else 0.0
    avg_win  = np.mean([t["pnl"] / (t["shares"] * t["price"]) * 100 for t in wins])  if wins   else 0.0
    avg_loss = np.mean([t["pnl"] / (t["shares"] * t["price"]) * 100 for t in losses]) if losses else 0.0
    total_wins_usd = sum(t["pnl"] for t in wins)
    total_loss_usd = abs(sum(t["pnl"] for t in losses))
    profit_factor = total_wins_usd / total_loss_usd if total_loss_usd > 0 else float("inf")

    return BacktestMetrics(
        ticker=ticker,
        total_return_pct=round(total_ret, 2),
        annual_return_pct=round(annual_ret, 2),
        sharpe_ratio=round(sharpe, 3),
        max_drawdown_pct=round(max_dd, 2),
        calmar_ratio=round(calmar, 3),
        win_rate_pct=round(win_rate, 1),
        avg_win_pct=round(avg_win, 2),
        avg_loss_pct=round(avg_loss, 2),
        profit_factor=round(profit_factor, 3),
        num_trades=len(closed),
        num_bars=len(bars),
    )
