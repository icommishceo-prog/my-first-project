"""
Slack alerting — posts trade alerts and daily digests to a Slack channel
via Incoming Webhooks. No bot token needed; just set SLACK_WEBHOOK_URL in .env.

If SLACK_WEBHOOK_URL is unset, all sends are logged and skipped gracefully —
the agent never crashes due to a missing Slack config.
"""

import os
import json
import requests
from loguru import logger

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_TIMEOUT_S = 5


# ── Low-level sender ───────────────────────────────────────────────────────────

def _post(payload: dict) -> bool:
    """POST a Block Kit payload to Slack. Returns True on success."""
    if not SLACK_WEBHOOK_URL:
        logger.debug(f"[SLACK DRY-RUN] {json.dumps(payload, indent=2)[:300]}")
        return False
    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=SLACK_TIMEOUT_S,
        )
        if resp.status_code == 200:
            logger.debug("Slack: message delivered")
            return True
        logger.warning(f"Slack: HTTP {resp.status_code} — {resp.text[:120]}")
    except requests.RequestException as e:
        logger.warning(f"Slack: send failed — {e}")
    return False


# ── Message builders ───────────────────────────────────────────────────────────

def _divider():
    return {"type": "divider"}


def _section(text: str):
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _fields(*items):
    return {
        "type": "section",
        "fields": [{"type": "mrkdwn", "text": t} for t in items],
    }


# ── Public alert functions ─────────────────────────────────────────────────────

def alert_fill(ticker: str, action: str, shares: int, price: float,
               stop_price: float, kelly_pct: float) -> bool:
    """
    Immediate alert when an order fills.
    Posted right after fill confirmation — no waiting for end-of-cycle digest.
    """
    emoji = ":large_green_circle:" if action == "BUY" else ":large_red_circle:"
    blocks = [
        _section(f"{emoji} *{action} order filled — {ticker}*"),
        _fields(
            f"*Shares:* {shares}",
            f"*Fill price:* ${price:.2f}",
            f"*Stop:* ${stop_price:.2f}" if stop_price else "*Stop:* n/a",
            f"*Kelly:* {kelly_pct:.1%}",
        ),
        _divider(),
    ]
    logger.info(f"Slack: fill alert — {action} {shares} {ticker} @ ${price:.2f}")
    return _post({"blocks": blocks})


def alert_stop_triggered(ticker: str, current_price: float, stop_price: float,
                         est_pnl: float) -> bool:
    """Alert when a stop-loss is breached — highest priority message."""
    blocks = [
        _section(f":rotating_light: *STOP TRIGGERED — {ticker}*"),
        _fields(
            f"*Current price:* ${current_price:.2f}",
            f"*Stop level:* ${stop_price:.2f}",
            f"*Est. P&L:* ${est_pnl:+,.2f}",
        ),
        _divider(),
    ]
    logger.warning(f"Slack: stop alert — {ticker} @ {current_price:.2f} <= {stop_price:.2f}")
    return _post({"blocks": blocks})


def alert_daily_digest(
    portfolio_value: float,
    cash: float,
    realized_pnl: float,
    total_return_pct: float,
    open_positions: list[dict],   # [{"ticker", "shares", "unrealized_pnl", "unrealized_pct"}]
    buys: list[str],
    sells: list[str],
    fills_count: int,
) -> bool:
    """End-of-cycle digest — posted once per run after all fills confirmed."""
    ret_emoji = ":chart_with_upwards_trend:" if total_return_pct >= 0 else ":chart_with_downwards_trend:"

    pos_lines = "\n".join(
        f"• `{p['ticker']}` {p['shares']:.0f} shares  "
        f"{p['unrealized_pnl']:+.2f} ({p['unrealized_pct']:+.1f}%)"
        for p in sorted(open_positions, key=lambda x: x["unrealized_pnl"], reverse=True)
    ) or "_No open positions_"

    signal_text = ""
    if buys:
        signal_text += f":green_circle: BUY: {', '.join(f'`{t}`' for t in buys)}  "
    if sells:
        signal_text += f":red_circle: SELL: {', '.join(f'`{t}`' for t in sells)}"
    if not signal_text:
        signal_text = "_All HOLD_"

    blocks = [
        _section(f"{ret_emoji} *Daily Agent Digest*"),
        _fields(
            f"*Portfolio value:* ${portfolio_value:,.2f}",
            f"*Cash:* ${cash:,.2f}",
            f"*Realized P&L:* ${realized_pnl:+,.2f}",
            f"*Total return:* {total_return_pct:+.2f}%",
        ),
        _divider(),
        _section(f"*Open Positions ({len(open_positions)})*\n{pos_lines}"),
        _divider(),
        _section(f"*Signals:* {signal_text}"),
        _section(f"*Orders filled this cycle:* {fills_count}"),
        _divider(),
    ]
    logger.info("Slack: daily digest posted")
    return _post({"blocks": blocks})
