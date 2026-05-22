"""
Stop-loss calculator — answers: "at what price do we exit to limit damage?"

Two mechanisms run in parallel; the tighter stop wins:
  1. ATR-based dynamic stop: entry - (atr_multiplier × ATR)  — adapts to volatility
  2. Hard percentage stop:   entry × (1 - stop_loss_pct)     — absolute floor
"""

import pandas as pd
from agent.strategy.indicators import atr


def calculate_stop(
    entry_price: float,
    df: pd.DataFrame,
    atr_multiplier: float = 2.0,
    atr_window: int = 14,
    hard_stop_pct: float = 0.08,
) -> dict:
    """
    Returns a dict with:
      atr_stop:    price level from ATR-based rule
      hard_stop:   price level from hard percentage rule
      stop_price:  the tighter (higher) of the two — actual stop to use
      stop_type:   "atr" or "hard" — which rule is binding
      risk_per_share: entry_price - stop_price
    """
    hard_stop = round(entry_price * (1 - hard_stop_pct), 4)

    if df is None or len(df) < atr_window + 1:
        return {
            "atr_stop": None,
            "hard_stop": hard_stop,
            "stop_price": hard_stop,
            "stop_type": "hard",
            "risk_per_share": round(entry_price - hard_stop, 4),
        }

    current_atr = atr(df, window=atr_window).iloc[-1]
    atr_stop = round(entry_price - atr_multiplier * current_atr, 4)

    # Tighter stop = higher price (less distance from entry)
    if atr_stop > hard_stop:
        stop_price, stop_type = atr_stop, "atr"
    else:
        stop_price, stop_type = hard_stop, "hard"

    return {
        "atr_stop": atr_stop,
        "hard_stop": hard_stop,
        "stop_price": stop_price,
        "stop_type": stop_type,
        "risk_per_share": round(entry_price - stop_price, 4),
    }
