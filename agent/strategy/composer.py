"""
Strategy composer — combine multiple Signals into a single decision per ticker.

Simons-style ensembling: each generator gets a weight, decisions are scored
on signed conviction (BUY=+strength, SELL=-strength, HOLD=0), then thresholded.
"""

from dataclasses import dataclass
from typing import Callable
import pandas as pd
from agent.strategy.signals import Signal, sma_crossover_signal, rsi_signal, macd_signal


@dataclass
class Decision:
    ticker: str
    action: str        # BUY | HOLD | SELL
    score: float       # signed weighted score, range [-1.0, +1.0]
    contributions: list[Signal]


# Default ensemble — equal-weighted trend + mean-reversion + momentum
DEFAULT_GENERATORS: list[tuple[Callable, float]] = [
    (sma_crossover_signal, 0.4),  # trend filter — Buffett's "stay with the trend"
    (rsi_signal, 0.3),            # mean reversion — Simons
    (macd_signal, 0.3),           # momentum confirmation
]

BUY_THRESHOLD = 0.35
SELL_THRESHOLD = -0.35


def decide(ticker: str, df: pd.DataFrame, generators=DEFAULT_GENERATORS) -> Decision:
    """Run all generators on one ticker, combine into a single Decision."""
    signals = [(gen(ticker, df), weight) for gen, weight in generators]

    score = 0.0
    for sig, weight in signals:
        if sig.action == "BUY":
            score += sig.strength * weight
        elif sig.action == "SELL":
            score -= sig.strength * weight

    if score >= BUY_THRESHOLD:
        action = "BUY"
    elif score <= SELL_THRESHOLD:
        action = "SELL"
    else:
        action = "HOLD"

    return Decision(ticker, action, round(score, 3), [s for s, _ in signals])


def decide_all(price_data: dict[str, pd.DataFrame]) -> list[Decision]:
    """Run the ensemble across every ticker in the cleaned watchlist data."""
    return [decide(ticker, df) for ticker, df in price_data.items()]
