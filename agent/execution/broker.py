"""
Alpaca broker client — wraps alpaca-py with a dry-run fallback.

If ALPACA_API_KEY / ALPACA_SECRET_KEY are not set, all methods return
simulated responses so the full pipeline runs without credentials.
"""

import os
import time
from loguru import logger

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.models import Order as AlpacaOrder
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("alpaca-py not installed — dry-run mode forced")


class BrokerClient:
    """
    Thin wrapper around Alpaca TradingClient.
    dry_run=True logs orders without sending them (safe for testing).
    """

    def __init__(self, dry_run: bool = False):
        api_key = os.getenv("ALPACA_API_KEY", "")
        secret_key = os.getenv("ALPACA_SECRET_KEY", "")
        paper = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

        self.dry_run = dry_run or not api_key or not secret_key or not ALPACA_AVAILABLE

        if not self.dry_run:
            self._client = TradingClient(
                api_key=api_key,
                secret_key=secret_key,
                paper="paper-api" in paper,
            )
            logger.info(f"BrokerClient connected ({'paper' if 'paper' in paper else 'live'})")
        else:
            self._client = None
            logger.info("BrokerClient: DRY RUN mode (no API keys or alpaca-py unavailable)")

    def get_account(self) -> dict:
        if self.dry_run:
            return {"portfolio_value": 100_000.0, "cash": 100_000.0, "status": "ACTIVE (dry-run)"}
        acct = self._client.get_account()
        return {
            "portfolio_value": float(acct.portfolio_value),
            "cash": float(acct.cash),
            "status": acct.status,
        }

    def place_market_order(self, ticker: str, qty: int, side: str) -> dict:
        """
        Submit a market order. side = "buy" | "sell".
        Returns a dict representing the order (real or simulated).
        """
        if self.dry_run:
            fake_id = f"dry-{ticker}-{side}-{int(time.time())}"
            logger.info(f"[DRY RUN] {side.upper()} {qty} {ticker} @ market → order_id={fake_id}")
            return {"id": fake_id, "status": "filled", "ticker": ticker, "qty": qty, "side": side}

        req = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        order = self._client.submit_order(req)
        logger.info(f"Order submitted: {order.id} | {side.upper()} {qty} {ticker}")
        return {"id": str(order.id), "status": str(order.status), "ticker": ticker, "qty": qty, "side": side}

    def get_order_status(self, order_id: str) -> str:
        """Returns Alpaca order status string, or 'filled' for dry-run orders."""
        if self.dry_run or order_id.startswith("dry-"):
            return "filled"
        order = self._client.get_order_by_id(order_id)
        return str(order.status)

    def get_positions(self) -> dict[str, dict]:
        """Returns {ticker: {qty, market_value, avg_entry}} for all open positions."""
        if self.dry_run:
            return {}
        positions = self._client.get_all_positions()
        return {
            p.symbol: {
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "avg_entry": float(p.avg_entry_price),
            }
            for p in positions
        }
