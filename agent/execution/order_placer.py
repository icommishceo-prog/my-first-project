"""
Converts RiskAdjustedOrders into broker calls.

MVP: market orders only (fills guaranteed, slippage accepted).
Phase 2 upgrade: limit orders at bid+1tick for large caps.
"""

from dataclasses import dataclass
from loguru import logger

from agent.risk.manager import RiskAdjustedOrder
from agent.execution.broker import BrokerClient


@dataclass
class PlacedOrder:
    ticker: str
    action: str
    shares: int
    order_id: str
    status: str
    stop_price: float


def place(order: RiskAdjustedOrder, broker: BrokerClient) -> PlacedOrder | None:
    """Submit one RiskAdjustedOrder to the broker. Returns PlacedOrder or None on error."""
    if order.shares <= 0:
        logger.warning(f"{order.ticker}: skipping order with 0 shares")
        return None

    side = "buy" if order.action == "BUY" else "sell"
    try:
        result = broker.place_market_order(order.ticker, order.shares, side)
        return PlacedOrder(
            ticker=order.ticker,
            action=order.action,
            shares=order.shares,
            order_id=result["id"],
            status=result["status"],
            stop_price=order.stop_price,
        )
    except Exception as e:
        logger.error(f"{order.ticker}: order placement failed — {e}")
        return None


def place_all(orders: list[RiskAdjustedOrder], broker: BrokerClient) -> list[PlacedOrder]:
    """Place all risk-approved orders. Skips failures without aborting the batch."""
    placed = []
    for order in orders:
        result = place(order, broker)
        if result:
            placed.append(result)
    logger.info(f"Order placer: {len(placed)}/{len(orders)} orders submitted")
    return placed
