"""
Ledger persistence — serialize PortfolioLedger to/from JSON.

Saved to LEDGER_PATH on every fill so the agent survives restarts.
On startup, load_ledger() restores the last known state.
"""

import json
import os
from pathlib import Path
from loguru import logger

from agent.monitoring.pnl import PortfolioLedger

LEDGER_PATH = Path(os.getenv("LEDGER_PATH", "data/ledger.json"))


def save_ledger(ledger: PortfolioLedger) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "starting_cash": ledger.starting_cash,
        "cash": ledger.cash,
        "realized_pnl": ledger.realized_pnl,
        "open_positions": ledger.open_positions,
        "trade_log": ledger.trade_log,
    }
    tmp = LEDGER_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(LEDGER_PATH)   # atomic write — no partial file on crash
    logger.debug(f"Ledger saved → {LEDGER_PATH} ({len(ledger.open_positions)} positions)")


def load_ledger(starting_cash: float = 100_000.0) -> PortfolioLedger:
    if not LEDGER_PATH.exists():
        logger.info(f"No ledger file at {LEDGER_PATH} — starting fresh")
        return PortfolioLedger(starting_cash=starting_cash, cash=starting_cash)

    try:
        payload = json.loads(LEDGER_PATH.read_text())
        ledger = PortfolioLedger(
            starting_cash=payload["starting_cash"],
            cash=payload["cash"],
            realized_pnl=payload.get("realized_pnl", 0.0),
        )
        ledger.open_positions = payload.get("open_positions", {})
        ledger.trade_log = payload.get("trade_log", [])
        logger.info(
            f"Ledger loaded from {LEDGER_PATH}: "
            f"{len(ledger.open_positions)} open positions, "
            f"realized P&L={ledger.realized_pnl:+.2f}"
        )
        return ledger
    except Exception as e:
        logger.error(f"Failed to load ledger ({e}) — starting fresh")
        return PortfolioLedger(starting_cash=starting_cash, cash=starting_cash)
