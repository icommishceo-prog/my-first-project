"""
Data quality guard — run before feeding any DataFrame into the strategy engine.
"""

import pandas as pd
from loguru import logger


REQUIRED_COLUMNS = {"Open", "High", "Low", "Close", "Volume"}
MAX_MISSING_PCT = 0.05  # fail if > 5% of rows have NaNs in Close


def validate(df: pd.DataFrame, ticker: str = "") -> bool:
    """
    Return True if df passes all quality checks, False otherwise.
    Logs the specific failure reason on rejection.
    """
    if df is None or df.empty:
        logger.warning(f"[{ticker}] Validation failed: empty DataFrame")
        return False

    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        logger.warning(f"[{ticker}] Validation failed: missing columns {missing_cols}")
        return False

    missing_close_pct = df["Close"].isna().mean()
    if missing_close_pct > MAX_MISSING_PCT:
        logger.warning(
            f"[{ticker}] Validation failed: {missing_close_pct:.1%} of Close values are NaN "
            f"(threshold {MAX_MISSING_PCT:.1%})"
        )
        return False

    if not isinstance(df.index, pd.DatetimeIndex):
        logger.warning(f"[{ticker}] Validation failed: index is not DatetimeIndex")
        return False

    logger.debug(f"[{ticker}] Validation passed ({len(df)} rows)")
    return True


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Forward-fill then drop any remaining NaNs. Call only after validate() passes.
    """
    return df.ffill().dropna()
