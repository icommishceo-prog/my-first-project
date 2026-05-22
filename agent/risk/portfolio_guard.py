"""
Portfolio-level exposure guard — Dalio's risk parity principle applied.

Enforces three hard limits before any order reaches the execution layer:
  1. Single-stock cap    — no ticker > MAX_POSITION_PCT of portfolio
  2. Sector cap          — no sector > MAX_SECTOR_PCT of portfolio
  3. Total exposure cap  — total invested < MAX_TOTAL_EXPOSURE_PCT

If a proposed order would breach any limit, it is rejected with a reason.
"""

from dataclasses import dataclass

MAX_POSITION_PCT = 0.05    # 5% per stock
MAX_SECTOR_PCT = 0.25      # 25% per sector
MAX_TOTAL_EXPOSURE_PCT = 0.95  # stay ≥5% cash


@dataclass
class GuardResult:
    approved: bool
    reason: str
    adjusted_shares: int   # may be reduced to fit within limits (0 = fully rejected)


def check_order(
    ticker: str,
    sector: str,
    proposed_shares: int,
    entry_price: float,
    portfolio_value: float,
    current_positions: dict,    # {ticker: {"value": float, "sector": str}}
) -> GuardResult:
    """
    Validate a proposed BUY order against all three exposure limits.

    current_positions keys must include at minimum:
      {"ticker": {"value": <float>, "sector": <str>}}
    """
    if proposed_shares <= 0:
        return GuardResult(False, "zero or negative shares proposed", 0)

    proposed_value = proposed_shares * entry_price
    total_invested = sum(p["value"] for p in current_positions.values())
    sector_invested = sum(
        p["value"] for p in current_positions.values()
        if p.get("sector") == sector
    )
    current_ticker_value = current_positions.get(ticker, {}).get("value", 0.0)

    # 1. Single-stock cap
    new_ticker_value = current_ticker_value + proposed_value
    if new_ticker_value / portfolio_value > MAX_POSITION_PCT:
        allowed_value = portfolio_value * MAX_POSITION_PCT - current_ticker_value
        allowed_shares = int(allowed_value / entry_price)
        if allowed_shares <= 0:
            return GuardResult(False, f"{ticker} already at {MAX_POSITION_PCT:.0%} cap", 0)
        return GuardResult(
            True,
            f"{ticker} position reduced to hit {MAX_POSITION_PCT:.0%} cap",
            allowed_shares,
        )

    # 2. Sector cap
    new_sector_value = sector_invested + proposed_value
    if new_sector_value / portfolio_value > MAX_SECTOR_PCT:
        allowed_value = portfolio_value * MAX_SECTOR_PCT - sector_invested
        allowed_shares = int(allowed_value / entry_price)
        if allowed_shares <= 0:
            return GuardResult(False, f"Sector '{sector}' at {MAX_SECTOR_PCT:.0%} cap", 0)
        return GuardResult(
            True,
            f"Shares reduced: sector '{sector}' approaching {MAX_SECTOR_PCT:.0%} cap",
            allowed_shares,
        )

    # 3. Total exposure cap
    new_total = total_invested + proposed_value
    if new_total / portfolio_value > MAX_TOTAL_EXPOSURE_PCT:
        allowed_value = portfolio_value * MAX_TOTAL_EXPOSURE_PCT - total_invested
        allowed_shares = int(allowed_value / entry_price)
        if allowed_shares <= 0:
            return GuardResult(False, f"Portfolio at {MAX_TOTAL_EXPOSURE_PCT:.0%} exposure cap", 0)
        return GuardResult(
            True,
            f"Shares reduced: total exposure approaching {MAX_TOTAL_EXPOSURE_PCT:.0%} cap",
            allowed_shares,
        )

    return GuardResult(True, "all limits satisfied", proposed_shares)
