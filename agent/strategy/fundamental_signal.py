"""
Fundamental signal — Buffett-style quality + value screen.

Criteria (all must hold for BUY bias):
  ROE           > ROE_MIN          (business quality — does management earn on equity?)
  P/E ratio     < sector PE median (value — not paying too much)
  Debt/Equity   < DE_MAX           (balance sheet safety)

A partial pass (1-2 criteria met) → HOLD with low strength.
All three fail → SELL bias (overvalued/weak fundamentals).
"""

from agent.strategy.signals import Signal

# Thresholds — Buffett-inspired conservative defaults
ROE_MIN = 0.15          # 15% minimum return on equity
DE_MAX = 150.0          # max debt-to-equity ratio
SECTOR_PE_MEDIANS = {   # rough historical sector medians — update quarterly
    "Technology": 28.0,
    "Consumer Cyclical": 22.0,
    "Consumer Defensive": 20.0,
    "Communication Services": 18.0,
    "Financial Services": 14.0,
    "Healthcare": 22.0,
    "Industrials": 20.0,
    "Energy": 12.0,
    "Utilities": 16.0,
    "Real Estate": 35.0,
    "Basic Materials": 15.0,
    "Unknown": 20.0,
}


def fundamental_signal(ticker: str, fundamentals: dict) -> Signal:
    """
    Evaluate one ticker's fundamentals. fundamentals = dict from fetch_fundamentals().
    Returns a Signal; source="fundamental".
    """
    pe    = fundamentals.get("pe_ratio")
    roe   = fundamentals.get("roe")
    de    = fundamentals.get("debt_to_equity")
    sector = fundamentals.get("sector", "Unknown")
    sector_pe = SECTOR_PE_MEDIANS.get(sector, 20.0)

    criteria = {
        "roe":  roe  is not None and roe  > ROE_MIN,
        "pe":   pe   is not None and pe   < sector_pe,
        "debt": de   is not None and de   < DE_MAX,
    }
    passing = sum(criteria.values())
    available = sum(v is not None for v in [pe, roe, de])

    if available == 0:
        return Signal(ticker, "HOLD", 0.0, "no fundamental data available", "fundamental")

    strength = passing / max(available, 1)

    if passing == 3:
        reason = (f"quality screen passed: ROE={roe:.0%}, "
                  f"PE={pe:.1f}<{sector_pe:.0f}, D/E={de:.0f}")
        return Signal(ticker, "BUY", round(strength, 2), reason, "fundamental")

    if passing == 0:
        reason = (f"quality screen failed: ROE={roe:.0%}, "
                  f"PE={pe:.1f}>={sector_pe:.0f}, D/E={de:.0f}"
                  if roe is not None and pe is not None and de is not None
                  else "multiple fundamentals missing/failing")
        return Signal(ticker, "SELL", round(1 - strength, 2), reason, "fundamental")

    failing = [k for k, v in criteria.items() if not v]
    reason = f"partial pass ({passing}/{available}): failing {failing}"
    return Signal(ticker, "HOLD", round(strength * 0.5, 2), reason, "fundamental")
