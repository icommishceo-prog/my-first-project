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


# Default ensemble — technical (80%) + fundamental quality screen (20%)
DEFAULT_GENERATORS: list[tuple[Callable, float]] = [
    (sma_crossover_signal, 0.35),  # trend filter — Buffett's "stay with the trend"
    (rsi_signal, 0.25),            # mean reversion — Simons
    (macd_signal, 0.25),           # momentum confirmation
    # fundamental_signal injected at runtime (needs per-ticker fundamentals dict)
]

BUY_THRESHOLD = 0.35
SELL_THRESHOLD = -0.35


def decide(
    ticker: str,
    df: pd.DataFrame,
    generators=DEFAULT_GENERATORS,
    fundamentals: dict | None = None,
) -> Decision:
    """Run all generators on one ticker, combine into a single Decision."""
    signals = [(gen(ticker, df), weight) for gen, weight in generators]

    # Inject fundamental signal if fundamentals provided
    if fundamentals:
        from agent.strategy.fundamental_signal import fundamental_signal
        sig = fundamental_signal(ticker, fundamentals.get(ticker, {}))
        signals.append((sig, 0.15))

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


def decide_all(
    price_data: dict[str, pd.DataFrame],
    fundamentals: dict | None = None,
) -> list[Decision]:
    """Run the ensemble across every ticker in the cleaned watchlist data."""
    return [decide(ticker, df, fundamentals=fundamentals) for ticker, df in price_data.items()]
