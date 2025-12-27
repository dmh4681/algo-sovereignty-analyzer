# Phase 2: Network Intelligence - Implementation Prompts

## API Research Summary

Based on investigation of Algorand APIs, here's what's actually available:

### Data Sources

**1. AlgoNode/Nodely Free API** (No API key required)
- Mainnet: `https://mainnet-api.algonode.cloud` or `https://mainnet-api.4160.nodely.dev`
- Free tier has 50ms artificial latency (acceptable for our use case)

**2. Key Endpoints**
- `GET /v2/ledger/supply` - Total supply, online stake, circulating supply
- `GET /v2/accounts/{address}` - Account info including participation status
- `GET /v2/status` - Current network round and status

**3. Account Participation Fields**
Each account has:
- `status`: "Online" or "Offline"
- `participation`: Object with vote-first-valid, vote-last-valid, vote-key-dilution, etc.
- If participation key is expired (vote-last-valid < current round), account is effectively offline

**4. Foundation Addresses** (Published at algorand.foundation/updated-wallet-addresses)
```
RW466IANOKLA36QARHMBX5VCY3PYDR3H2N5XHPDARG6UBOKCIK7WAMLSCA
5NTF3MGWL5B2X426P27FE3AUPOUU3OYSRCLP3O4Y7JI2BFGJWPGUBOB2NI
JEBTS2MKIIN2EWSXPWEWJ4GUMVOYB2JYZ4XCRD4KJPVNAO6YBJTPBBJBE4
T5TGE4UXGMKZBQ3D3SOB34CQDMSRDXO5H6O55663SRD275ZMK6UG7PYNC4
BMZT7U2KSXVGI7LWRJVDM7S7CEPT2VFOBMA45QC25WJ2TRB5P7USAD3TR4
4SN2OPSTRXDAXAG5HY7GVSQUXYL5NXPENLMHRG2SH5Q2ZF5ACXJRGWDYNE
IOSADRTSZUE6WBNXH7ANZANFDQ3GVCVUGZI3IP6T3AQI6RLGLI6TPNJQZA
XNFDTOTUQME3NI2UWDJ5Y6LYOJKHNP4C7BKZYQ5GSDQ7JBXKEJ6HLM3LOE
2TZAMEZZDWFY37QV66HXWQIYWYJIZKE2KP3QNPI2QHHKSMKUZEICNMMUFU
TVUQW6NXMHZFZAV6D7PQMW4DIUL5UB42L2JLIYNGRHH6UW362HGNVI26DY
B223SVF452UWAMMLNIHIUAPHYPX5J3HLVJF6MNOHUJE2NWJBG7C66JILGE
4E7OINW7M6G6OT2SQZ7ZKFPWJ7CAAFTPOG2RZISJ3YZU5VCJQ64ZIROC44
JB2EEILIBYWA3WACBIERYPG5TV6K6IHOWJKDFDHRGSCOEHTMEUUML7YXGE
```

**5. Network Stats (Reference)**
- As of Q1 2025: ~3,075 nodes on Algorand network (per Nodely.io)
- Total supply: 10 billion ALGO (fixed)
- Minimum stake for rewards: 30,000 ALGO
- Minimum to run node: 0.1 ALGO (but no rewards without 30k)

---

## Prompt 1: Create Network Statistics Backend Module

```
Create a Python module to fetch and calculate Algorand network decentralization metrics.

## File: core/network.py

### Requirements

1. **AlgorandNetworkStats Class**
   - Use AlgoNode free API: https://mainnet-api.algonode.cloud
   - No API key required
   - Implement async methods using aiohttp or httpx

2. **Methods to Implement**

```python
from dataclasses import dataclass
from typing import Optional
import httpx

@dataclass
class NetworkStats:
    total_supply: int           # Total ALGO supply (microalgos)
    online_stake: int           # ALGO currently online/participating (microalgos)
    circulating_supply: int     # Circulating supply
    participation_rate: float   # online_stake / total_supply as percentage
    current_round: int          # Current blockchain round
    
@dataclass 
class FoundationStats:
    total_balance: int          # Sum of all Foundation addresses (microalgos)
    online_balance: int         # Foundation stake that is online (microalgos)
    foundation_addresses: list  # List of known Foundation addresses
    foundation_pct_of_supply: float
    foundation_pct_of_online: float

@dataclass
class WalletParticipation:
    address: str
    is_online: bool
    balance: int
    vote_first_valid: Optional[int]
    vote_last_valid: Optional[int]
    is_key_expired: bool        # True if vote_last_valid < current_round
    stake_percentage: float     # This wallet's % of total online stake

class AlgorandNetworkStats:
    ALGOD_URL = "https://mainnet-api.algonode.cloud"
    
    # Known Foundation addresses (from algorand.foundation/updated-wallet-addresses)
    FOUNDATION_ADDRESSES = [
        "RW466IANOKLA36QARHMBX5VCY3PYDR3H2N5XHPDARG6UBOKCIK7WAMLSCA",
        "5NTF3MGWL5B2X426P27FE3AUPOUU3OYSRCLP3O4Y7JI2BFGJWPGUBOB2NI",
        "JEBTS2MKIIN2EWSXPWEWJ4GUMVOYB2JYZ4XCRD4KJPVNAO6YBJTPBBJBE4",
        "T5TGE4UXGMKZBQ3D3SOB34CQDMSRDXO5H6O55663SRD275ZMK6UG7PYNC4",
        "BMZT7U2KSXVGI7LWRJVDM7S7CEPT2VFOBMA45QC25WJ2TRB5P7USAD3TR4",
        "4SN2OPSTRXDAXAG5HY7GVSQUXYL5NXPENLMHRG2SH5Q2ZF5ACXJRGWDYNE",
        "IOSADRTSZUE6WBNXH7ANZANFDQ3GVCVUGZI3IP6T3AQI6RLGLI6TPNJQZA",
        "XNFDTOTUQME3NI2UWDJ5Y6LYOJKHNP4C7BKZYQ5GSDQ7JBXKEJ6HLM3LOE",
        "2TZAMEZZDWFY37QV66HXWQIYWYJIZKE2KP3QNPI2QHHKSMKUZEICNMMUFU",
        "TVUQW6NXMHZFZAV6D7PQMW4DIUL5UB42L2JLIYNGRHH6UW362HGNVI26DY",
        "B223SVF452UWAMMLNIHIUAPHYPX5J3HLVJF6MNOHUJE2NWJBG7C66JILGE",
        "4E7OINW7M6G6OT2SQZ7ZKFPWJ7CAAFTPOG2RZISJ3YZU5VCJQ64ZIROC44",
        "JB2EEILIBYWA3WACBIERYPG5TV6K6IHOWJKDFDHRGSCOEHTMEUUML7YXGE"
    ]
    
    async def get_network_stats(self) -> NetworkStats:
        """Fetch current network supply and participation stats"""
        # GET /v2/ledger/supply
        # GET /v2/status (for current round)
        pass
    
    async def get_foundation_stats(self) -> FoundationStats:
        """Calculate Foundation's stake and participation status"""
        # Fetch each Foundation address balance and status
        # Sum totals, calculate percentages
        pass
    
    async def check_wallet_participation(self, address: str) -> WalletParticipation:
        """Check if a specific wallet is participating in consensus"""
        # GET /v2/accounts/{address}
        # Check status field and participation key validity
        pass
    
    async def get_decentralization_summary(self) -> dict:
        """Get combined summary for dashboard display"""
        # Returns: network_stats, foundation_stats, estimated_community_stake
        pass
```

3. **API Response Handling**
   - Handle rate limits gracefully (429 errors)
   - Cache results for 5 minutes (don't hammer the API)
   - Return sensible defaults on error

4. **Conversion Notes**
   - Algorand API returns balances in microAlgos (1 ALGO = 1,000,000 microAlgos)
   - Convert to ALGO for display (divide by 1_000_000)

5. **Testing**
   - Include a simple test that fetches real mainnet data
   - Print human-readable output
```

---

## Prompt 2: Create Network Stats API Endpoints

```
Add API endpoints for network statistics to the FastAPI backend.

## File: api/routes.py (add to existing)

### New Endpoints

1. **GET /api/v1/network/stats**
Returns current network participation statistics.

Response:
```json
{
  "network": {
    "total_supply_algo": 10000000000,
    "online_stake_algo": 2500000000,
    "participation_rate": 25.0,
    "current_round": 45000000
  },
  "foundation": {
    "total_balance_algo": 1500000000,
    "online_balance_algo": 500000000,
    "pct_of_total_supply": 15.0,
    "pct_of_online_stake": 20.0
  },
  "community": {
    "estimated_stake_algo": 2000000000,
    "pct_of_online_stake": 80.0
  },
  "decentralization_score": 80,
  "estimated_node_count": 3075,
  "fetched_at": "2024-12-26T12:00:00Z"
}
```

2. **GET /api/v1/network/wallet/{address}**
Check participation status for a specific wallet.

Response:
```json
{
  "address": "ABC123...",
  "is_participating": true,
  "balance_algo": 120000,
  "stake_percentage": 0.0048,
  "participation_key": {
    "first_valid": 44000000,
    "last_valid": 48000000,
    "is_expired": false,
    "rounds_remaining": 3000000
  },
  "contribution_tier": "Active Participant"
}
```

### Schemas (api/schemas.py)

Add Pydantic models:
- NetworkStatsResponse
- WalletParticipationResponse

### Caching
- Cache network stats for 5 minutes (these don't change rapidly)
- Individual wallet lookups can be cached for 1 minute

### Error Handling
- Return 503 if Algorand API is unreachable
- Return partial data if some Foundation addresses fail to fetch
```

---

## Prompt 3: Build Enhanced Network Page UI

```
Enhance the /network page with real decentralization metrics and visualizations.

## File: web/app/network/page.tsx

### Data Fetching
- Fetch from GET /api/v1/network/stats on page load
- Show loading skeleton while fetching
- Auto-refresh every 5 minutes (or manual refresh button)

### Section 1: Network Health Dashboard

Display key metrics in stat cards (similar to analyze page):

Card 1: "Online Stake"
- Value: X.XX Billion ALGO
- Subtext: XX% of total supply participating
- Color: Green if >30%, Yellow if 20-30%, Red if <20%

Card 2: "Participation Rate" 
- Value: XX%
- Subtext: "of all ALGO securing the network"
- Visual: Small progress bar

Card 3: "Estimated Nodes"
- Value: ~3,000+
- Subtext: "Independent validators"
- Note: Link to Nodely.io for live count

Card 4: "Decentralization Score"
- Value: XX/100
- Subtext: Based on stake distribution
- Color coded by health

### Section 2: Stake Distribution Visualization

Donut/Pie chart using Recharts showing:
- Foundation Stake (known addresses) - Red/Orange
- Community Stake (remainder) - Green
- Offline/Non-participating - Gray

Include legend with actual numbers.

Below chart, add context text:
"The Algorand Foundation currently controls approximately XX% of online stake. 
For true decentralization, community stake should exceed 80% of online participation."

### Section 3: Your Contribution (Wallet Connected)

If wallet connected via @txnlab/use-wallet:

Card showing:
- Participation Status: "Online" (green checkmark) or "Offline" (gray X)
- Your Stake: XXX,XXX ALGO
- Network Contribution: "You represent 0.XXX% of online stake"
- Key Status: "Valid until round X,XXX,XXX" or "EXPIRED - Re-register needed"

If participating:
- Celebration message: "🎉 You're helping secure Algorand!"

If NOT participating:
- CTA: "Start Contributing" button → links to /network/run-a-node (or external guide for now)
- Explain benefits: "Running a node earns staking rewards (30k+ ALGO required)"

If no wallet connected:
- "Connect your wallet to see your contribution to decentralization"
- Connect wallet button

### Section 4: The Decentralization Imperative

Educational content block (collapsible or always visible):

Title: "Why Decentralization Matters"

Points:
- Single points of failure create systemic risk
- Regulatory pressure can compromise centralized entities  
- True sovereignty requires distributed control
- Every participation node strengthens the network

CTA: "Learn how to run a node →" (link to guide)

### Section 5: Call to Action

Grid of action cards:

1. "Run a Node" 
   - Icon: Server/Computer
   - "Contribute to decentralization and earn rewards"
   - Link: /network/run-a-node (or https://developer.algorand.org/docs/run-a-node/participate/ for now)

2. "Earn iGA"
   - Icon: Token/Coin
   - "Get rewarded for participation with iGetAlgo"
   - Link: https://twitter.com/iGetAlgo (external)

3. "Stack Hard Money"
   - Icon: Gold bars
   - "Build your sovereignty ratio"
   - Link: /analyze

### Design Notes
- Use existing dark theme with orange accents
- Charts: Recharts library (already available)
- Responsive: Stack sections vertically on mobile
- Loading states: Skeleton components while data fetches
- Error state: Show cached/default data with warning banner
```

---

## Prompt 4: Create Node Runner Guide Page

```
Create a comprehensive guide for running an Algorand participation node.

## File: web/app/network/run-a-node/page.tsx

### Page Structure

**Hero Section**
- Title: "Run Your Own Algorand Node"
- Subtitle: "Contribute to decentralization, earn rewards, achieve sovereignty"
- Stats row: "~$20/month • 2 hours setup • 24/7 passive income potential"

**Table of Contents** (sticky sidebar on desktop)
1. Why Run a Node?
2. Requirements
3. Rewards & Incentives  
4. Setup Options
5. Registration Process
6. Monitoring
7. FAQ

### Section 1: Why Run a Node?

Benefits cards:

1. **Secure the Network**
   - Your node validates transactions and votes on blocks
   - More nodes = more decentralized = more secure

2. **Earn Staking Rewards**
   - 30,000+ ALGO stake earns protocol rewards
   - Rewards paid automatically for valid block proposals

3. **Earn iGA Tokens**
   - iGetAlgo rewards participation node runners
   - 333 total supply - ultra-scarce
   - Link: https://twitter.com/iGetAlgo

4. **True Sovereignty**
   - Verify transactions yourself
   - Don't trust third parties
   - Be part of the solution, not the problem

### Section 2: Requirements

**Hardware Requirements Card**
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16 GB |
| Storage | 100 GB SSD | 256 GB NVMe |
| Network | 10 Mbps | 100 Mbps+ |
| Uptime | 95%+ | 99%+ |

**Cost Estimates Card**
- Cloud VPS: $20-50/month (DigitalOcean, Vultr, Hetzner)
- Home Server: $150-300 one-time (Raspberry Pi 5, Mini PC)
- Electricity: ~$5-10/month for home setup

**Stake Requirements Card**
- Minimum to run: 0.1 ALGO (just for account)
- Minimum for rewards: 30,000 ALGO
- No maximum stake limit

Note: "You can run a node with any amount, but staking rewards require 30k+ ALGO. 
Even small participants strengthen decentralization!"

### Section 3: Rewards & Incentives

**Protocol Rewards**
- Block proposers earn transaction fees
- Stakers with 30k+ ALGO receive ongoing rewards
- Rewards distributed automatically - no claiming needed

**iGetAlgo (iGA)**
- Community-run incentive program
- Earn iGA tokens for running nodes
- Only 333 iGA exist - extremely scarce
- Qualifies as "hard money" in our classification

**Governance**
- Node runners can participate in Algorand governance
- Vote on protocol upgrades and fund allocation

### Section 4: Setup Options (Tabs)

**Tab 1: One-Click Options (Easiest)**

Option A: NodeKit
- Terminal-based installer
- Works on Linux, Mac
- Link: https://github.com/algorandfoundation/nodekit

Option B: FUNC
- Cross-platform GUI
- Good for beginners
- Link: (FUNC website)

**Tab 2: Manual Linux Setup**

Prerequisites:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
```

Installation:
```bash
# Add Algorand repository
# Install algod
# Configure node
```

Link to full guide: https://developer.algorand.org/docs/run-a-node/setup/install/

**Tab 3: Windows (WSL)**

Note: "This is how the Sovereignty Analyzer creator runs his node!"

Steps:
1. Enable WSL2 on Windows
2. Install Ubuntu from Microsoft Store
3. Follow Linux installation steps
4. Configure to run at startup

**Tab 4: Cloud Providers**

Recommendations:
- Hetzner (cheapest, Europe-based)
- DigitalOcean (easy setup, good docs)
- Vultr (global locations)
- AWS/GCP (overkill but works)

Approximate costs:
- Hetzner: ~€5-10/month
- DigitalOcean: ~$20-40/month
- Vultr: ~$20-40/month

### Section 5: Key Registration

After your node is synced, you need to register participation keys:

1. Generate participation keys
2. Sign key registration transaction
3. Wait for registration to take effect (~320 rounds)

Tools:
- AlgoTools.org - Web-based transaction composer
- Pera/Defly wallet - Sign transactions
- Goal CLI - Command line registration

Link to detailed guide: https://nodely.io/blog/algorand-key-reg/

### Section 6: Monitoring

**Built-in Monitoring**
```bash
goal node status
goal account listpartkeys
```

**External Tools**
- Nodely Telemetry: Free monitoring service
- Allo Alerts: Participation key expiry notifications

**What to Monitor**
- Node sync status
- Participation key expiry
- Block proposals (you should see occasional proposals)
- Network connectivity

### Section 7: FAQ

Q: "How much ALGO do I need to start?"
A: Any amount works, but 30,000+ ALGO required for protocol rewards.

Q: "Will I lose my ALGO if my node goes offline?"
A: No. Your ALGO is never locked or at risk. You just miss rewards.

Q: "Can I run multiple accounts on one node?"
A: Yes, but limit to 4 accounts. More causes performance issues.

Q: "How long until I see rewards?"
A: Depends on stake size. Larger stake = more frequent proposals.

Q: "Is it worth it for small holders?"
A: Yes! Even without rewards, you're strengthening decentralization.

### Footer CTAs

- "Check your participation status" → Link to /analyze (with wallet)
- "View network statistics" → Link to /network
- "Join the community" → Link to Algorand Discord #node-runners

### Design Notes
- Clean, documentation-style layout
- Code blocks with copy buttons
- Tabs for different setup paths
- Collapsible FAQ sections
- Progress feel - make it seem achievable
- External links open in new tabs
```

---

## Prompt 5: Add iGA to Hard Money Classification

```
Update the asset classification system to include iGetAlgo (iGA) as a hard money asset.

## Task 1: Update data/asset_classification.csv

Add this line:
```csv
2635992378,iGetAlgo,iGA,hard_money,"333 fixed supply, earned through node participation"
```

## Task 2: Verify core/classifier.py

Ensure the classifier:
1. Reads from the CSV file
2. Recognizes ASA 2635992378 as hard money
3. Falls back to pattern matching for "iGetAlgo" or "iGA" names

Add pattern if needed:
```python
# In HARD_MONEY_PATTERNS or equivalent
r"(?i)^igetAlgo$",
r"(?i)^iGA$",
```

## Task 3: Update pricing (core/pricing.py)

Verify iGA can get a price from Vestige or other sources.
- ASA ID: 2635992378
- If no price available, handle gracefully (show quantity, note "price unavailable")
- iGA is traded on Tinyman, so Vestige should have pricing

## Task 4: Test

Run analyzer against a wallet known to hold iGA and verify:
1. iGA appears in hard_money category, not shitcoin
2. USD value is calculated (if price available)
3. Sovereignty ratio includes iGA value

## Context
iGA represents the scarcest asset on Algorand (333 total supply) and is earned by running participation nodes. It's the perfect hard money classification - scarce, earned through contribution, not speculative.
```

---

## Prompt 6: Verify Meld & goBTC Classifications  

```
Verify that all precious metal and Bitcoin assets are properly classified as hard money.

## Assets to Verify

| Asset | ASA ID | Expected Category |
|-------|--------|-------------------|
| Meld Gold (GOLD$) | 246516580 | hard_money |
| Meld Silver (SILVER$) | 246519683 | hard_money |
| goBTC | 386192725 | hard_money |

## Tasks

1. Check data/asset_classification.csv
   - Confirm all three ASAs are present
   - Confirm category is "hard_money"
   - Add if missing

2. Check core/classifier.py
   - Verify pattern matching catches variations:
     - "GOLD$", "Meld Gold", "XAUT", "PAXG"
     - "SILVER$", "Meld Silver"
     - "goBTC", "gobtc", "wrapped bitcoin"

3. Test by analyzing a wallet with these assets
   - All should appear in hard_money category
   - Prices should be fetched (Meld metals trade on DEXs)

## Reference Prices (for sanity check)
- GOLD$ should roughly track gold spot price (~$2,600/oz as of Dec 2024)
- SILVER$ should roughly track silver spot price (~$30/oz)
- goBTC should track Bitcoin price

If prices seem wrong, check Vestige API configuration.
```

---

## Summary: Implementation Order

1. **Prompt 1**: Create `core/network.py` - Backend module for fetching network stats
2. **Prompt 2**: Add API endpoints `/api/v1/network/stats` and `/api/v1/network/wallet/{address}`
3. **Prompt 5 & 6**: Update asset classifications (quick wins, do alongside backend work)
4. **Prompt 3**: Build enhanced Network page UI (after API is ready)
5. **Prompt 4**: Create Node Runner Guide page (can be done in parallel with UI)

## External Resources Referenced

- AlgoNode API: https://mainnet-api.algonode.cloud
- Nodely API: https://nodely.io
- Algorand Developer Docs: https://developer.algorand.org/docs/run-a-node/participate/
- Foundation Addresses: https://algorand.foundation/updated-wallet-addresses
- Node Setup Guide: https://nodely.io/blog/algorand-key-reg/
- iGetAlgo: https://twitter.com/iGetAlgo

## Notes

- Free AlgoNode API has 50ms artificial latency - acceptable for our dashboard
- Node count (~3,075) is an estimate from Nodely - exact counting is complex
- Foundation addresses are published but may not be complete
- Participation key expiry needs to be checked against current round
- Staking rewards require 30,000 ALGO minimum (changed from older docs)
