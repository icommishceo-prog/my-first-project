"""
Daily digest — prints a structured summary after each agent cycle.
Designed to be copy-pasteable into Slack or email in Phase 2.
"""

from datetime import datetime
from loguru import logger

from agent.monitoring.pnl import PortfolioLedger, PositionPnL
from agent.strategy.composer import Decision
from agent.risk.manager import RiskAdjustedOrder
from agent.execution.fill_tracker import FillResult


def render(
    ledger: PortfolioLedger,
    price_data: dict,
    decisions: list[Decision],
    orders: list[RiskAdjustedOrder],
    fills: list[FillResult],
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mtm = ledger.mark_to_market(price_data)
    total_val = ledger.total_value(price_data)
    total_ret = ledger.total_return_pct(price_data)

    lines = [
        f"{'=' * 56}",
        f"  STOCK AGENT DAILY DIGEST  —  {now}",
        f"{'=' * 56}",
        f"  Portfolio value : ${total_val:>12,.2f}",
        f"  Cash            : ${ledger.cash:>12,.2f}",
        f"  Realized P&L    : ${ledger.realized_pnl:>+12,.2f}",
        f"  Total return    : {total_ret:>+10.2f}%",
        f"",
        f"  OPEN POSITIONS ({len(mtm)})",
        f"  {'Ticker':<8} {'Shares':>6} {'Entry':>8} {'Price':>8} {'Unreal P&L':>12} {'%':>7}",
        f"  {'-' * 54}",
    ]

    for p in sorted(mtm, key=lambda x: x.unrealized_pnl, reverse=True):
        lines.append(
            f"  {p.ticker:<8} {p.shares:>6.0f} {p.avg_entry:>8.2f} "
            f"{p.current_price:>8.2f} {p.unrealized_pnl:>+12.2f} {p.unrealized_pct:>+6.1f}%"
        )

    buys  = [d for d in decisions if d.action == "BUY"]
    sells = [d for d in decisions if d.action == "SELL"]
    holds = [d for d in decisions if d.action == "HOLD"]
    filled = [f for f in fills if f.status == "filled"]

    lines += [
        f"",
        f"  SIGNALS   BUY={len(buys)}  SELL={len(sells)}  HOLD={len(holds)}",
    ]
    for d in buys + sells:
        lines.append(f"    {d.action:<5} {d.ticker:<8} score={d.score:+.3f}")

    lines += [
        f"",
        f"  ORDERS    approved={len(orders)}  filled={len(filled)}",
    ]
    for f in filled:
        lines.append(f"    {f.action:<5} {f.shares:>4} {f.ticker:<8} stop=${f.stop_price:.2f}")

    if ledger.trade_log:
        lines += [f"", f"  RECENT CLOSED TRADES"]
        for t in ledger.trade_log[-5:]:
            lines.append(
                f"    {t['ticker']:<8} {t['shares']:>4} shares  "
                f"entry={t['entry']:.2f}  exit={t['exit']:.2f}  "
                f"P&L={t['pnl']:>+8.2f}  [{t['reason']}]"
            )

    lines.append(f"{'=' * 56}")
    report = "\n".join(lines)
    logger.info(f"Digest generated ({len(mtm)} positions, {len(filled)} fills)")
    return report
