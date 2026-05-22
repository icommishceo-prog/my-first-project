"""
Daily run scheduler — orchestrates the full agent cycle on a timer.

Default schedule (US Eastern):
  09:25  — fetch data (pre-market, 5 min before open)
  09:30  — run strategy + risk + execution
  16:05  — post-market digest + stop check

For cloud deployment, replace schedule with a cron job or AWS EventBridge rule
targeting main.run_full_cycle() directly.
"""

import schedule
import time
from datetime import datetime
from loguru import logger


def is_weekday() -> bool:
    return datetime.now().weekday() < 5   # Mon–Fri only


def run_cycle(cycle_fn):
    """Guard: only execute on weekdays."""
    if not is_weekday():
        logger.info("Scheduler: weekend — skipping cycle")
        return
    logger.info("Scheduler: triggering agent cycle")
    try:
        cycle_fn()
    except Exception as e:
        logger.error(f"Scheduler: cycle failed — {e}")


def start(cycle_fn, pre_market_time: str = "09:25", post_market_time: str = "16:05"):
    """
    Block and run cycle_fn on schedule indefinitely.
    cycle_fn should be main.run_full_cycle or equivalent.
    """
    logger.info(f"Scheduler started — cycle at {pre_market_time} ET (weekdays only)")
    schedule.every().day.at(pre_market_time).do(run_cycle, cycle_fn)
    schedule.every().day.at(post_market_time).do(run_cycle, cycle_fn)

    while True:
        schedule.run_pending()
        time.sleep(30)
