"""
P&L tracker — mark-to-market open positions and accumulate realized gains.

PortfolioLedger is the single source of truth for financial state.
It persists across cycles by being passed through the run loop.
"""

from dataclasses import dataclass, field
from loguru import logger
import pandas as pd


@dataclass
class PositionPnL:
    ticker: str
    shares: float
    avg_entry: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pct: float


@dataclass
class PortfolioLedger:
    starting_cash: float
    cash: float
    realized_pnl: float = 0.0
    trade_log: list = field(default_factory=list)  # list of closed trade dicts

    # open positions: {ticker: {shares, avg_entry, stop_price, sector}}
    open_positions: dict = field(default_factory=dict)

    def open(self, ticker: str, shares: int, entry_price: float,
              stop_price: float, sector: str = "Unknown"):
        cost = shares * entry_price
        self.cash -= cost
        existing = self.open_positions.get(ticker)
        if existing:
            total_shares = existing["shares"] + shares
            avg_entry = (existing["shares"] * existing["avg_entry"] + cost) / total_shares
            self.open_positions[ticker] = {**existing, "shares": total_shares, "avg_entry": avg_entry}
        else:
            self.open_positions[ticker] = {
                "shares": shares, "avg_entry": entry_price,
                "stop_price": stop_price, "sector": sector,
            }
        logger.info(f"Ledger: opened {shares} {ticker} @ {entry_price:.2f} | cash={self.cash:,.2f}")

    def close(self, ticker: str, exit_price: float, reason: str = "signal"):
        pos = self.open_positions.pop(ticker, None)
        if not pos:
            return
        proceeds = pos["shares"] * exit_price
        cost_basis = pos["shares"] * pos["avg_entry"]
        pnl = proceeds - cost_basis
        self.cash += proceeds
        self.realized_pnl += pnl
        self.trade_log.append({
            "ticker": ticker, "shares": pos["shares"],
            "entry": pos["avg_entry"], "exit": exit_price,
            "pnl": round(pnl, 2), "reason": reason,
        })
        logger.info(f"Ledger: closed {ticker} @ {exit_price:.2f} | PnL={pnl:+.2f} | reason={reason}")

    def mark_to_market(self, price_data: dict[str, pd.DataFrame]) -> list[PositionPnL]:
        results = []
        for ticker, pos in self.open_positions.items():
            df = price_data.get(ticker)
            if df is None:
                continue
            current_price = float(df["Close"].iloc[-1])
            market_value = pos["shares"] * current_price
            cost_basis = pos["shares"] * pos["avg_entry"]
            unrealized = market_value - cost_basis
            results.append(PositionPnL(
                ticker=ticker,
                shares=pos["shares"],
                avg_entry=pos["avg_entry"],
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=round(unrealized, 2),
                unrealized_pct=round(unrealized / cost_basis * 100, 2),
            ))
        return results

    def total_value(self, price_data: dict) -> float:
        mtm = self.mark_to_market(price_data)
        invested = sum(p.market_value for p in mtm)
        return self.cash + invested

    def total_return_pct(self, price_data: dict) -> float:
        return (self.total_value(price_data) / self.starting_cash - 1) * 100
