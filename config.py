"""
Central config — all environment variables and agent-wide constants live here.
Copy .env.example to .env and fill in your API keys before running.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Broker (Alpaca paper trading by default) ---
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# --- Watchlist ---
WATCHLIST = os.getenv("WATCHLIST", "AAPL,MSFT,GOOGL,AMZN,META,NVDA,BRK-B,JPM,UNH,V").split(",")

# --- Data defaults ---
DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"

# --- Risk defaults ---
MAX_POSITION_PCT = 0.05   # max 5% of portfolio per position
STOP_LOSS_PCT = 0.08      # 8% hard stop-loss per position
