"""
Fill tracker — polls broker until orders confirm or timeout expires.

Returns confirmed fills and updates the in-memory position state that
the portfolio guard uses on the next cycle.
"""

import time
from dataclasses import dataclass, field
from loguru import logger

from agent.execution.broker import BrokerClient
from agent.execution.order_placer import PlacedOrder

POLL_INTERVAL_S = 2
MAX_WAIT_S = 60
TERMINAL_STATUSES = {"filled", "canceled", "expired", "rejected"}


@dataclass
class FillResult:
    ticker: str
    action: str
    shares: int
    order_id: str
    status: str       # "filled" | "timeout" | "rejected" | "canceled"
    stop_price: float


@dataclass
class PositionState:
    """In-memory portfolio positions — passed to portfolio_guard each cycle."""
    positions: dict = field(default_factory=dict)  # {ticker: {value, sector}}

    def apply_fill(self, fill: FillResult, entry_price: float, sector: str = "Unknown"):
        if fill.status != "filled":
            return
        if fill.action == "BUY":
            existing = self.positions.get(fill.ticker, {"value": 0.0, "sector": sector})
            existing["value"] = existing.get("value", 0.0) + fill.shares * entry_price
            existing["sector"] = sector
            self.positions[fill.ticker] = existing
        elif fill.action == "SELL":
            self.positions.pop(fill.ticker, None)

    def snapshot(self) -> dict:
        return dict(self.positions)


def await_fills(placed: list[PlacedOrder], broker: BrokerClient) -> list[FillResult]:
    """
    Poll each placed order until it reaches a terminal status or MAX_WAIT_S elapses.
    """
    pending = {p.order_id: p for p in placed}
    results: list[FillResult] = []
    elapsed = 0

    while pending and elapsed < MAX_WAIT_S:
        for order_id in list(pending.keys()):
            status = broker.get_order_status(order_id)
            if status in TERMINAL_STATUSES:
                p = pending.pop(order_id)
                results.append(FillResult(
                    ticker=p.ticker, action=p.action, shares=p.shares,
                    order_id=order_id, status=status, stop_price=p.stop_price,
                ))
                logger.info(f"Fill confirmed: {p.action} {p.shares} {p.ticker} → {status}")

        if pending:
            time.sleep(POLL_INTERVAL_S)
            elapsed += POLL_INTERVAL_S

    # Anything still pending after timeout → mark as timeout
    for order_id, p in pending.items():
        logger.warning(f"{p.ticker}: order {order_id} timed out after {MAX_WAIT_S}s")
        results.append(FillResult(
            ticker=p.ticker, action=p.action, shares=p.shares,
            order_id=order_id, status="timeout", stop_price=p.stop_price,
        ))

    filled = [r for r in results if r.status == "filled"]
    logger.info(f"Fill tracker: {len(filled)}/{len(placed)} orders filled")
    return results
