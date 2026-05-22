"""
Stop-loss enforcer — runs every cycle BEFORE strategy signals.

Compares each open position's current price against its stored stop_price.
If breached, injects a synthetic SELL Decision directly into the decision list
so the Risk Manager and Executor handle it identically to a signal-driven exit.
"""

import pandas as pd
from loguru import logger

from agent.strategy.signals import Signal
from agent.strategy.composer import Decision
from agent.monitoring.pnl import PortfolioLedger


def check_stops(
    ledger: PortfolioLedger,
    price_data: dict[str, pd.DataFrame],
) -> list[Decision]:
    """
    Return a list of synthetic SELL Decisions for any position that has
    breached its stop. These are prepended to the strategy decision list.
    """
    stop_sells = []
    for ticker, pos in ledger.open_positions.items():
        df = price_data.get(ticker)
        if df is None:
            continue
        current_price = float(df["Close"].iloc[-1])
        stop_price = pos.get("stop_price", 0.0)
        if stop_price and current_price <= stop_price:
            logger.warning(
                f"STOP TRIGGERED: {ticker} current={current_price:.2f} "
                f"<= stop={stop_price:.2f} | injecting SELL"
            )
            stop_sells.append(Decision(
                ticker=ticker,
                action="SELL",
                score=-1.0,
                contributions=[Signal(
                    ticker=ticker, action="SELL", strength=1.0,
                    reason=f"stop breached: {current_price:.2f} <= {stop_price:.2f}",
                    source="stop_enforcer",
                )],
            ))
    if not stop_sells:
        logger.debug("Stop enforcer: no stops breached")
    return stop_sells
