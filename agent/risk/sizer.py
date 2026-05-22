"""
Position sizer — answers: "how many shares should we buy?"

Uses half-Kelly Criterion with a hard cap from config.
Kelly formula: f* = (b*p - q) / b
  b = avg_win / avg_loss  (reward-to-risk ratio)
  p = historical win rate
  q = 1 - p

Half-Kelly (f*/2) is used by default to reduce variance — practitioners
consistently find full Kelly too aggressive for real portfolios.
"""

from dataclasses import dataclass
import math


@dataclass
class SizeResult:
    shares: int
    position_value: float
    kelly_fraction: float
    capped: bool          # True if Kelly recommendation was clipped by MAX_POSITION_PCT


def kelly_size(
    portfolio_value: float,
    entry_price: float,
    win_rate: float = 0.55,
    avg_win_pct: float = 0.08,
    avg_loss_pct: float = 0.04,
    max_position_pct: float = 0.05,
    half_kelly: bool = True,
) -> SizeResult:
    """
    Size a position using (half-)Kelly Criterion.

    Default assumptions are conservative placeholders until real trade history
    is available to calibrate win_rate, avg_win_pct, avg_loss_pct.
    """
    if entry_price <= 0 or portfolio_value <= 0:
        return SizeResult(0, 0.0, 0.0, False)

    b = avg_win_pct / avg_loss_pct   # reward-to-risk ratio
    q = 1 - win_rate
    kelly_f = (b * win_rate - q) / b

    if half_kelly:
        kelly_f /= 2

    kelly_f = max(0.0, kelly_f)
    capped = kelly_f > max_position_pct
    final_f = min(kelly_f, max_position_pct)

    position_value = portfolio_value * final_f
    shares = math.floor(position_value / entry_price)

    return SizeResult(
        shares=shares,
        position_value=round(shares * entry_price, 2),
        kelly_fraction=round(final_f, 4),
        capped=capped,
    )
