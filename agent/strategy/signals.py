"""
Signal generators — wrap indicators into BUY/HOLD/SELL decisions.

Every generator returns a Signal dataclass with:
  action:   "BUY" | "HOLD" | "SELL"
  strength: float in [0.0, 1.0]  — how strong the conviction is
  reason:   human-readable explanation
  source:   which generator produced it
"""

from dataclasses import dataclass
import pandas as pd
from agent.strategy.indicators import sma, rsi, macd


@dataclass
class Signal:
    ticker: str
    action: str       # BUY | HOLD | SELL
    strength: float   # 0.0 - 1.0
    reason: str
    source: str


def sma_crossover_signal(ticker: str, df: pd.DataFrame, fast: int = 50, slow: int = 200) -> Signal:
    """
    Classic Golden Cross / Death Cross — Buffett-friendly long-term trend filter.
    """
    if len(df) < slow + 1:
        return Signal(ticker, "HOLD", 0.0, f"insufficient data ({len(df)} < {slow + 1} bars)", "sma_crossover")

    fast_ma = sma(df["Close"], fast)
    slow_ma = sma(df["Close"], slow)

    today_fast, today_slow = fast_ma.iloc[-1], slow_ma.iloc[-1]
    prev_fast, prev_slow = fast_ma.iloc[-2], slow_ma.iloc[-2]

    if prev_fast <= prev_slow and today_fast > today_slow:
        return Signal(ticker, "BUY", 0.8, f"Golden cross: {fast}MA crossed above {slow}MA", "sma_crossover")
    if prev_fast >= prev_slow and today_fast < today_slow:
        return Signal(ticker, "SELL", 0.8, f"Death cross: {fast}MA crossed below {slow}MA", "sma_crossover")

    # Trend bias when no crossover today
    if today_fast > today_slow:
        return Signal(ticker, "HOLD", 0.3, f"Uptrend ({fast}MA > {slow}MA), no crossover", "sma_crossover")
    return Signal(ticker, "HOLD", 0.3, f"Downtrend ({fast}MA < {slow}MA), no crossover", "sma_crossover")


def rsi_signal(ticker: str, df: pd.DataFrame, window: int = 14, oversold: int = 30, overbought: int = 70) -> Signal:
    """Mean-reversion signal — Simons-style: buy oversold, sell overbought."""
    if len(df) < window + 1:
        return Signal(ticker, "HOLD", 0.0, "insufficient data", "rsi")

    val = rsi(df["Close"], window).iloc[-1]

    if val < oversold:
        strength = min(1.0, (oversold - val) / oversold)
        return Signal(ticker, "BUY", strength, f"RSI oversold at {val:.1f}", "rsi")
    if val > overbought:
        strength = min(1.0, (val - overbought) / (100 - overbought))
        return Signal(ticker, "SELL", strength, f"RSI overbought at {val:.1f}", "rsi")
    return Signal(ticker, "HOLD", 0.2, f"RSI neutral at {val:.1f}", "rsi")


def macd_signal(ticker: str, df: pd.DataFrame) -> Signal:
    """MACD histogram zero-cross — momentum confirmation."""
    if len(df) < 35:
        return Signal(ticker, "HOLD", 0.0, "insufficient data", "macd")

    hist = macd(df["Close"])["hist"]
    today, prev = hist.iloc[-1], hist.iloc[-2]

    if prev <= 0 and today > 0:
        return Signal(ticker, "BUY", 0.7, f"MACD histogram crossed positive ({today:.3f})", "macd")
    if prev >= 0 and today < 0:
        return Signal(ticker, "SELL", 0.7, f"MACD histogram crossed negative ({today:.3f})", "macd")
    return Signal(ticker, "HOLD", 0.2, f"MACD histogram = {today:.3f}, no cross", "macd")
