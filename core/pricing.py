import requests
import time
from typing import Optional

def get_algo_price() -> Optional[float]:
    """Fetch live ALGO price from CoinGecko API with retry logic"""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=algorand&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data['algorand']['usd']
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"⚠️  Failed to fetch ALGO price after {max_retries} attempts: {e}")
                return None
            
            # Exponential backoff: 1s, 2s, 4s
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    
    return None
