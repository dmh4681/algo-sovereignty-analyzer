# Claude AI Agent Documentation

> SovereigntyCoach - AI-powered financial advice using Claude

## Overview

The `SovereigntyCoach` class (`api/agent.py`) provides AI-powered financial sovereignty coaching using Anthropic's Claude API. It analyzes wallet compositions and provides personalized advice from a "hard money maximalist" perspective.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SovereigntyCoach                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐                                           │
│  │   Anthropic SDK  │                                           │
│  │  (claude-sonnet) │                                           │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  generate_advice()                           ││
│  │                                                              ││
│  │  1. Extract metrics from analysis                           ││
│  │  2. Calculate category percentages                          ││
│  │  3. Format holdings for prompt                              ││
│  │  4. Construct coaching prompt                               ││
│  │  5. Call Claude API with persona                            ││
│  │  6. Return formatted advice                                 ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Class: SovereigntyCoach

### Constructor

```python
def __init__(self):
    """
    Initialize the Claude-powered sovereignty coach.

    Requires:
        ANTHROPIC_API_KEY environment variable

    Raises:
        ValueError: If ANTHROPIC_API_KEY not set

    Example:
        import os
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
        coach = SovereigntyCoach()
    """
```

### generate_advice(analysis) → str

Generate personalized financial sovereignty advice.

```python
def generate_advice(self, analysis: dict) -> str:
    """
    Generate AI-powered financial advice based on wallet analysis.

    The coach provides a "Sovereignty Assessment" with:
    1. The Verdict: A-F grade on on-chain sovereignty
    2. The Good: What user is doing right
    3. The Bad: Mistakes and areas for improvement
    4. Actionable Advice: 3 specific steps to improve

    Args:
        analysis: Wallet analysis dict containing:
            - total_usd: Total portfolio value
            - categories: {
                "hard_money": [...],
                "algo": [...],
                "dollars": [...],
                "shitcoin": [...]
              }

    Returns:
        Markdown-formatted advice string

    Model Configuration:
        - Model: claude-sonnet-4-20250514
        - Max tokens: 1000
        - Temperature: 0.7 (some creativity)

    Example:
        advice = coach.generate_advice({
            "total_usd": 25000,
            "categories": {
                "hard_money": [{"name": "goBTC", "usd_value": 5000}],
                "algo": [{"name": "ALGO", "usd_value": 12500}],
                "dollars": [{"name": "USDC", "usd_value": 5000}],
                "shitcoin": [{"name": "MEME", "usd_value": 2500}]
            }
        })
        print(advice)
    """
```

---

## Prompt Engineering

### System Prompt

The coach operates with a specific persona:

```python
system = """
You are a maximalist financial coach. You believe in Bitcoin, Gold,
and Algorand as the rails. You despise fiat currency and excessive
gambling on meme coins.
"""
```

### User Prompt Template

The advice request includes context and structure:

```
You are a ruthless but helpful Financial Sovereignty Coach...

IMPORTANT CONTEXT:
- You are ONLY seeing this user's ON-CHAIN Algorand wallet.
- They likely hold additional assets elsewhere (cold storage, etc.)
- The "ALGO" category includes liquid staking (xALGO, fALGO) - NOT shitcoins
- Base assessment on what you CAN see, acknowledge limitations

Algorand Wallet Analysis:
- Total On-Chain Value: $25,000.00
- Hard Money (BTC, Gold, Silver): 20.0%
- Algorand (ALGO + liquid staking): 50.0%
- Stablecoins (USDC, USDT): 20.0%
- Speculative Assets (Shitcoins): 10.0%

Specific Holdings:
HARD_MONEY:
- goBTC: $5,000.00

ALGO:
- Algorand (PARTICIPATING): $12,500.00

[...continued...]

Provide a "Sovereignty Assessment":
1. **The Verdict**: Grade A-F on ON-CHAIN sovereignty
2. **The Good**: What they're doing right
3. **The Bad**: Call out mistakes
4. **Actionable Advice**: 3 specific improvement steps

Tone:
- Direct, no-nonsense, slightly aggressive but caring
- Use terms: "fiat slavery", "hard money", "time preference"
- "ngmi" if bad, "wgmi" if good
- Markdown formatting
- Acknowledge this only covers Algorand wallet
```

---

## Response Examples

### High Sovereignty Score (Grade A)

```markdown
## Sovereignty Assessment

### The Verdict: A-

You're doing it right, anon. Strong hard money allocation with
meaningful participation in Algorand consensus. WGMI.

### The Good

✅ **20% Hard Money Allocation** - goBTC in self-custody on Algorand.
   This is real sovereignty.

✅ **Algorand Participation** - Your ALGO is online earning rewards
   while securing the network. Based.

✅ **Liquid Staking** - xALGO position shows understanding of yield
   without sacrificing custody.

### The Bad

⚠️ **20% Stablecoins** - USDC can be frozen by Circle. Consider
   converting some to hard money.

### Actionable Advice

1. **Increase hard money to 30%** - Swap half your USDC to goBTC
2. **Extend participation keys** - Ensure voting keys don't expire
3. **Document your seed phrases** - Sovereignty requires backup plans

---
*Note: This assessment covers your Algorand wallet only. You may hold
additional BTC in cold storage or other assets elsewhere.*
```

### Low Sovereignty Score (Grade D)

```markdown
## Sovereignty Assessment

### The Verdict: D

Anon, we need to talk. You're gambling with your future. NGMI at
this rate.

### The Good

✅ At least you're on-chain and self-custodying. That's step one.

### The Bad

❌ **60% Shitcoins** - MEMEDOG and RUGTOKEN? This is casino behavior.
   Time to grow up.

❌ **0% Hard Money** - No Bitcoin, no gold. You're 100% exposed to
   fiat debasement and alt-coin volatility.

❌ **Not Participating** - Your ALGO isn't even online. Free money
   sitting on the table.

### Actionable Advice

1. **Exit shitcoins immediately** - Convert to ALGO or goBTC
2. **Get online** - Enable consensus participation today
3. **Start DCA into Bitcoin** - Even $50/week changes everything

You have until the next halving to fix this. Clock is ticking.

---
*Note: This covers your Algorand wallet only. Hoping you have a
hardware wallet somewhere with actual Bitcoin.*
```

---

## Integration with API

The coach is used in the `/agent/advice` endpoint:

```python
# api/routes.py

@router.post("/agent/advice")
async def get_advice(request: AdviceRequest):
    """
    Generate AI-powered sovereignty advice.

    Request Body:
        {
            "analysis": { ... full analysis result ... }
        }

    Returns:
        {
            "advice": "## Sovereignty Assessment\n\n..."
        }
    """
    try:
        coach = SovereigntyCoach()
        advice = coach.generate_advice(request.analysis)
        return {"advice": advice}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Error Handling

The coach handles API errors gracefully:

```python
try:
    message = self.client.messages.create(...)
    return message.content[0].text
except Exception as e:
    print(f"ERROR: Failed to generate advice: {e}")
    traceback.print_exc()
    return f"My connection to the sovereignty network is interrupted. (Error: {str(e)})"
```

**Common Errors:**
- Invalid API key → ValueError on initialization
- Rate limiting → Returned in error message
- Network issues → Returned in error message

---

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Model (hardcoded, but could be configurable)
# MODEL=claude-sonnet-4-20250514
```

### Model Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| model | claude-sonnet-4-20250514 | Latest Sonnet for quality/speed balance |
| max_tokens | 1000 | Sufficient for detailed advice |
| temperature | 0.7 | Allow creativity while staying coherent |

---

## Testing

```python
import os
from api.agent import SovereigntyCoach

# Set API key
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

# Initialize
coach = SovereigntyCoach()

# Test with sample analysis
analysis = {
    "total_usd": 10000,
    "categories": {
        "hard_money": [{"name": "goBTC", "usd_value": 2000}],
        "algo": [{"name": "ALGO", "usd_value": 5000}],
        "dollars": [{"name": "USDC", "usd_value": 2000}],
        "shitcoin": [{"name": "MEME", "usd_value": 1000}]
    }
}

advice = coach.generate_advice(analysis)
print(advice)
```

---

## Cost Considerations

| Operation | Tokens | Approx Cost |
|-----------|--------|-------------|
| Input (prompt) | ~800 | ~$0.003 |
| Output (advice) | ~600 | ~$0.009 |
| **Per Analysis** | ~1400 | ~$0.012 |

At $0.012 per analysis, 1000 analyses = $12.

---

## Future Enhancements

1. **Streaming Responses**: Stream advice for better UX
2. **Historical Context**: Include past analyses for trend advice
3. **Multi-language**: Support for non-English advice
4. **Customizable Persona**: Let users choose coaching style

---

*Last Updated: 2026-01-15*
