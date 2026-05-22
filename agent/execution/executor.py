"""
Execution orchestrator — place orders, await fills, update position state.
"""

from loguru import logger

from agent.risk.manager import RiskAdjustedOrder
from agent.execution.broker import BrokerClient
from agent.execution.order_placer import place_all
from agent.execution.fill_tracker import await_fills, PositionState


def execute(
    orders: list[RiskAdjustedOrder],
    position_state: PositionState,
    price_data: dict,
    fundamentals: dict,
    dry_run: bool = True,
) -> tuple[list, PositionState]:
    """
    Place all orders, await fills, update position_state.
    Returns (fill_results, updated_position_state).
    """
    if not orders:
        logger.info("Executor: no orders to place")
        return [], position_state

    logger.info(f"=== Component 4: Execution ({'DRY RUN' if dry_run else 'LIVE'}) ===")
    broker = BrokerClient(dry_run=dry_run)
    placed = place_all(orders, broker)
    fills = await_fills(placed, broker)

    for fill in fills:
        entry_price = price_data.get(fill.ticker, {})
        if hasattr(entry_price, "iloc"):
            entry_price = float(entry_price["Close"].iloc[-1])
        else:
            entry_price = 0.0
        sector = fundamentals.get(fill.ticker, {}).get("sector", "Unknown")
        position_state.apply_fill(fill, entry_price, sector)

    filled_count = sum(1 for f in fills if f.status == "filled")
    logger.info(f"Executor complete: {filled_count}/{len(orders)} fills confirmed")
    return fills, position_state
