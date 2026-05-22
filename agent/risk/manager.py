"""
Risk Manager orchestrator — converts Strategy Decisions into RiskAdjustedOrders.

Pipeline per BUY decision:
  Decision → kelly_size() → calculate_stop() → check_order() → RiskAdjustedOrder

SELL decisions pass through directly (exit sizing is always full position).
HOLD decisions are dropped.
"""

from dataclasses import dataclass
from loguru import logger
import pandas as pd

from agent.strategy.composer import Decision
from agent.risk.sizer import kelly_size
from agent.risk.stops import calculate_stop
from agent.risk.portfolio_guard import check_order


@dataclass
class RiskAdjustedOrder:
    ticker: str
    action: str          # BUY | SELL
    shares: int
    entry_price: float
    stop_price: float
    stop_type: str
    risk_per_share: float
    kelly_fraction: float
    guard_reason: str


def process(
    decision: Decision,
    df: pd.DataFrame,
    portfolio_value: float,
    current_positions: dict,
    sector: str = "Unknown",
) -> RiskAdjustedOrder | None:
    """
    Convert one Decision into a RiskAdjustedOrder, or None if rejected/HOLD.
    """
    if decision.action == "HOLD":
        return None

    entry_price = df["Close"].iloc[-1]

    if decision.action == "SELL":
        # Exit full position — stop not applicable
        held = current_positions.get(decision.ticker, {})
        shares = int(held.get("value", 0) / entry_price) if held else 0
        if shares == 0:
            logger.debug(f"{decision.ticker}: SELL signal but no position held — skip")
            return None
        logger.info(f"{decision.ticker}: SELL {shares} shares @ {entry_price:.2f}")
        return RiskAdjustedOrder(
            ticker=decision.ticker, action="SELL",
            shares=shares, entry_price=entry_price,
            stop_price=0.0, stop_type="n/a",
            risk_per_share=0.0, kelly_fraction=0.0,
            guard_reason="exit full position",
        )

    # BUY path
    size = kelly_size(portfolio_value, entry_price)
    stop = calculate_stop(entry_price, df)
    guard = check_order(
        ticker=decision.ticker,
        sector=sector,
        proposed_shares=size.shares,
        entry_price=entry_price,
        portfolio_value=portfolio_value,
        current_positions=current_positions,
    )

    if not guard.approved or guard.adjusted_shares == 0:
        logger.warning(f"{decision.ticker}: BUY rejected by guard — {guard.reason}")
        return None

    final_shares = guard.adjusted_shares
    logger.info(
        f"{decision.ticker}: BUY {final_shares} shares @ {entry_price:.2f} | "
        f"stop={stop['stop_price']:.2f} ({stop['stop_type']}) | "
        f"kelly={size.kelly_fraction:.2%} | guard: {guard.reason}"
    )
    return RiskAdjustedOrder(
        ticker=decision.ticker, action="BUY",
        shares=final_shares, entry_price=entry_price,
        stop_price=stop["stop_price"], stop_type=stop["stop_type"],
        risk_per_share=stop["risk_per_share"],
        kelly_fraction=size.kelly_fraction,
        guard_reason=guard.reason,
    )


def process_all(
    decisions: list[Decision],
    price_data: dict[str, pd.DataFrame],
    portfolio_value: float,
    current_positions: dict,
    fundamentals: dict[str, dict] | None = None,
) -> list[RiskAdjustedOrder]:
    """Run process() across all decisions, skip HOLDs and rejected orders."""
    orders = []
    for d in decisions:
        df = price_data.get(d.ticker)
        if df is None:
            continue
        sector = (fundamentals or {}).get(d.ticker, {}).get("sector", "Unknown")
        order = process(d, df, portfolio_value, current_positions, sector)
        if order:
            orders.append(order)
    logger.info(f"Risk Manager: {len(orders)} orders approved from {len(decisions)} decisions")
    return orders
