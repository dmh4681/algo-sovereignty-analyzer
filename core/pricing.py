import requests
from typing import Optional

def get_algo_price() -> Optional[float]:
    """Fetch live ALGO price from CoinGecko API"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=algorand&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data['algorand']['usd']
    except Exception:
        # Silently fail and return None - caller should handle fallback
        return None
