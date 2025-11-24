import os
import anthropic
from pydantic import BaseModel

class AdviceRequest(BaseModel):
    address: str
    analysis: dict

class SovereigntyCoach:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        print(f"DEBUG: Loading SovereigntyCoach. API Key present: {bool(api_key)}")
        if api_key:
            print(f"DEBUG: API Key starts with: {api_key[:10]}...")
        else:
            print("ERROR: ANTHROPIC_API_KEY is missing!")
            
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            print("DEBUG: Anthropic client initialized successfully")
        except Exception as e:
            print(f"ERROR: Failed to initialize Anthropic client: {e}")
            raise

    def generate_advice(self, analysis: dict) -> str:
        """
        Generates financial sovereignty advice based on portfolio analysis.
        """
        
        # Extract key metrics
        total_usd = analysis.get('total_usd', 0)
        categories = analysis.get('categories', {})
        
        # Calculate totals from lists
        hard_money = sum(a.get('usd_value', 0) for a in categories.get('hard_money', []))
        algo = sum(a.get('usd_value', 0) for a in categories.get('algo', []))
        stablecoins = sum(a.get('usd_value', 0) for a in categories.get('dollars', [])) # Note: key is 'dollars' in analyzer.py
        shitcoins = sum(a.get('usd_value', 0) for a in categories.get('shitcoin', []))
        
        # Recalculate total_usd if not provided or 0 (just to be safe)
        if total_usd == 0:
            total_usd = hard_money + algo + stablecoins + shitcoins
        
        # Calculate percentages
        if total_usd > 0:
            hard_money_pct = (hard_money / total_usd) * 100
            algo_pct = (algo / total_usd) * 100
            stable_pct = (stablecoins / total_usd) * 100
            shitcoin_pct = (shitcoins / total_usd) * 100
        else:
            hard_money_pct = algo_pct = stable_pct = shitcoin_pct = 0

        # Construct the prompt
        prompt = f"""
        You are a ruthless but helpful Financial Sovereignty Coach. Your goal is to wake people up to the reality of fiat debasement and the importance of self-custody and hard money.
        
        You are analyzing a user's Algorand portfolio:
        - Total Value: ${total_usd:,.2f}
        - Hard Money (BTC, Gold, Silver): {hard_money_pct:.1f}%
        - Algorand (ALGO): {algo_pct:.1f}%
        - Stablecoins (USDC, USDT): {stable_pct:.1f}%
        - Speculative Assets (Shitcoins): {shitcoin_pct:.1f}%
        
        Specific Holdings:
        {self._format_holdings(categories)}
        
        Provide a "Sovereignty Assessment" for this user.
        1.  **The Verdict**: Give them a harsh but fair grade (A-F) on their sovereignty.
        2.  **The Good**: Acknowledge what they are doing right (e.g., self-custody, holding BTC).
        3.  **The Bad**: Call out their mistakes (e.g., too much gambling, holding fiat stablecoins which can be frozen).
        4.  **Actionable Advice**: Give 3 specific steps to improve their score.
        
        Tone:
        - Direct, no-nonsense, slightly aggressive but ultimately caring.
        - Use terms like "fiat slavery", "hard money", "time preference", "ngmi" (if bad), "wgmi" (if good).
        - Be concise. Use Markdown formatting.
        """

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7,
                system="You are a maximalist financial coach. You believe in Bitcoin, Gold, and Algorand as the rails. You despise fiat currency and excessive gambling on meme coins.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"ERROR: Failed to generate advice: {e}")
            import traceback
            traceback.print_exc()
            return f"My connection to the sovereignty network is interrupted. (Error: {str(e)})"

    def _format_holdings(self, categories):
        text = ""
        for cat_name, assets in categories.items():
            if assets:
                text += f"\n{cat_name.upper()}:\n"
                for asset in assets[:3]: # Top 3 per category
                    text += f"- {asset.get('name', 'Unknown')}: ${asset.get('usd_value', 0):,.2f}\n"
        return text
