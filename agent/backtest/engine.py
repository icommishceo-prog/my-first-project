"""
Walk-forward engine — iterates bar-by-bar over a single ticker's history.

At each bar i:
  1. Slice df to [:i+1]  — strategy sees only the past, never the future
  2. Run decide()        — get BUY/HOLD/SELL
  3. Simulate fill       — BUY/SELL fills at bar i+1's Open price
  4. Record equity       — mark-to-market at bar i's Close

Returns a list of BacktestBar records (one per bar from warmup onward).
"""

from dataclasses import dataclass, field
import pandas as pd
from loguru import logger

from agent.strategy.composer import decide

WARMUP_BARS = 201        # SMA-200 needs 200 bars; skip bar 0–200
COMMISSION = 1.00        # $ per trade, flat (Alpaca-realistic)


@dataclass
class BacktestBar:
    date: pd.Timestamp
    close: float
    action: str          # BUY | HOLD | SELL
    score: float
    position: int        # shares held after this bar
    cash: float
    equity: float        # cash + position * close


@dataclass
class SimState:
    cash: float
    position: int = 0
    avg_entry: float = 0.0
    trades: list = field(default_factory=list)


def _fill_buy(state: SimState, fill_price: float, max_position_pct: float, portfolio_value: float):
    if state.position > 0:
        return  # already long — no pyramiding in MVP
    budget = portfolio_value * max_position_pct
    shares = int((budget - COMMISSION) / fill_price)
    if shares <= 0:
        return
    cost = shares * fill_price + COMMISSION
    if cost > state.cash:
        shares = int((state.cash - COMMISSION) / fill_price)
        if shares <= 0:
            return
        cost = shares * fill_price + COMMISSION
    state.cash -= cost
    state.position = shares
    state.avg_entry = fill_price
    state.trades.append({"type": "BUY", "price": fill_price, "shares": shares})


def _fill_sell(state: SimState, fill_price: float):
    if state.position <= 0:
        return
    proceeds = state.position * fill_price - COMMISSION
    pnl = (fill_price - state.avg_entry) * state.position - COMMISSION
    state.trades.append({
        "type": "SELL", "price": fill_price,
        "shares": state.position, "pnl": round(pnl, 2),
    })
    state.cash += proceeds
    state.position = 0
    state.avg_entry = 0.0


def run(
    ticker: str,
    df: pd.DataFrame,
    starting_cash: float = 100_000.0,
    max_position_pct: float = 0.05,
    fundamentals: dict | None = None,
) -> list[BacktestBar]:
    """
    Walk-forward backtest for a single ticker.
    Returns list of BacktestBar from WARMUP_BARS onward.
    """
    if len(df) < WARMUP_BARS + 2:
        logger.warning(f"{ticker}: not enough bars ({len(df)}) for backtest — need {WARMUP_BARS + 2}")
        return []

    state = SimState(cash=starting_cash)
    bars: list[BacktestBar] = []

    for i in range(WARMUP_BARS, len(df) - 1):
        window = df.iloc[: i + 1]
        decision = decide(ticker, window, fundamentals=fundamentals)

        # Fill at next bar's Open (i+1)
        next_open = float(df.iloc[i + 1]["Open"])
        portfolio_value = state.cash + state.position * float(window["Close"].iloc[-1])

        if decision.action == "BUY":
            _fill_buy(state, next_open, max_position_pct, portfolio_value)
        elif decision.action == "SELL":
            _fill_sell(state, next_open)

        close = float(window["Close"].iloc[-1])
        equity = state.cash + state.position * close
        bars.append(BacktestBar(
            date=window.index[-1],
            close=close,
            action=decision.action,
            score=decision.score,
            position=state.position,
            cash=round(state.cash, 2),
            equity=round(equity, 2),
        ))

    # Close any open position at last bar
    if state.position > 0:
        last_close = float(df["Close"].iloc[-1])
        _fill_sell(state, last_close)

    logger.info(
        f"{ticker}: backtest complete — {len(bars)} bars, "
        f"{sum(1 for t in state.trades if t['type'] == 'SELL')} trades"
    )
    return bars, state.trades
