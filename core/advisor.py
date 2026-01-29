"""
Sovereignty Advisor - Generates structured improvement recommendations.

Uses the existing Claude client from api.agent to produce JSON-formatted
advice based on wallet analysis results.
"""

import json
import logging
import traceback

import anthropic

from core.secrets import get_secret

logger = logging.getLogger("core.advisor")


def generate_sovereignty_advice(analysis_result: dict) -> dict:
    """
    Generate structured sovereignty improvement advice from analysis results.

    Args:
        analysis_result: Full analysis dict with keys: address, categories,
            sovereignty_data, is_participating, etc.

    Returns:
        Dict with keys: overall_assessment, score_interpretation,
        recommendations (list, max 5), next_milestone
    """
    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is required for AI advisor. "
            "See .env.example for configuration instructions."
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Extract key data
    categories = analysis_result.get("categories", {})
    sovereignty_data = analysis_result.get("sovereignty_data")

    total_usd = 0.0
    category_totals = {}
    for cat_name in ["hard_money", "algo", "dollars", "shitcoin"]:
        cat_total = sum(a.get("usd_value", 0) for a in categories.get(cat_name, []))
        category_totals[cat_name] = cat_total
        total_usd += cat_total

    # Build percentages
    pcts = {}
    for cat_name, cat_total in category_totals.items():
        pcts[cat_name] = (cat_total / total_usd * 100) if total_usd > 0 else 0

    # Sovereignty tier info
    sovereignty_ratio = None
    sovereignty_status = None
    if sovereignty_data:
        sovereignty_ratio = sovereignty_data.get("sovereignty_ratio")
        sovereignty_status = sovereignty_data.get("sovereignty_status")

    is_participating = analysis_result.get("is_participating", False)

    prompt = f"""You are a Financial Sovereignty Advisor analyzing an Algorand wallet.

PHILOSOPHY: Hard Money Maximalism - only Bitcoin, Gold, and Silver are true sovereignty assets.

WALLET DATA:
- Total Portfolio: ${total_usd:,.2f}
- Hard Money (BTC, Gold, Silver): {pcts['hard_money']:.1f}% (${category_totals['hard_money']:,.2f})
- Algorand: {pcts['algo']:.1f}% (${category_totals['algo']:,.2f})
- Stablecoins: {pcts['dollars']:.1f}% (${category_totals['dollars']:,.2f})
- Speculative: {pcts['shitcoin']:.1f}% (${category_totals['shitcoin']:,.2f})
- Consensus Participation: {"Yes" if is_participating else "No"}
- Sovereignty Ratio: {sovereignty_ratio if sovereignty_ratio is not None else "Not calculated"}
- Sovereignty Status: {sovereignty_status if sovereignty_status else "Unknown"}

STATUS LEVELS (ratio = years of expenses covered):
- Generationally Sovereign (≥20)
- Antifragile (≥6)
- Robust (≥3)
- Fragile (≥1)
- Vulnerable (<1)

IMPORTANT: This is ONLY their on-chain Algorand wallet. They likely hold more assets elsewhere.

Respond with ONLY valid JSON (no markdown, no code fences) in this exact structure:
{{
  "overall_assessment": "A 2-3 sentence assessment of their sovereignty position",
  "score_interpretation": "A 1-2 sentence interpretation of their sovereignty ratio and status",
  "recommendations": [
    "Specific actionable recommendation 1",
    "Specific actionable recommendation 2",
    "Specific actionable recommendation 3"
  ],
  "next_milestone": "Description of the next sovereignty milestone to reach and what it would take"
}}

Include at most 5 recommendations. Be direct, use hard money maximalist perspective.
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            temperature=0.5,
            system="You are a hard money maximalist financial advisor. Respond with valid JSON only.",
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()

        # Parse JSON response
        advice = json.loads(raw)

        # Validate expected keys
        required_keys = ["overall_assessment", "score_interpretation", "recommendations", "next_milestone"]
        for key in required_keys:
            if key not in advice:
                advice[key] = "" if key != "recommendations" else []

        # Enforce max 5 recommendations
        if len(advice.get("recommendations", [])) > 5:
            advice["recommendations"] = advice["recommendations"][:5]

        return advice

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse advisor JSON response: {e}")
        logger.debug(f"Raw response: {raw}")
        return {
            "overall_assessment": "Unable to generate structured advice at this time.",
            "score_interpretation": "",
            "recommendations": [],
            "next_milestone": "",
        }
    except Exception as e:
        logger.exception(f"Advisor generation failed: {e}")
        raise
