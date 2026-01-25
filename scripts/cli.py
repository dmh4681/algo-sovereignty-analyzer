#!/usr/bin/env python3
"""
Algorand Sovereignty Analyzer - Command Line Interface
======================================================

A command-line tool for analyzing Algorand wallet sovereignty based on
hard money maximalist principles.

This CLI provides a quick way to analyze any Algorand wallet without
needing to run the web interface or API server.

Usage:
    python -m scripts.cli <ALGORAND_ADDRESS>

Examples:
    # Basic analysis
    python -m scripts.cli I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4

    # Analysis with sovereignty ratio calculation (interactive prompt)
    python -m scripts.cli YOUR_ADDRESS_HERE
    # When prompted, enter your monthly fixed expenses

Output:
    The CLI produces a detailed breakdown of wallet holdings:

    1. HARD MONEY (Bitcoin, Gold, Silver)
       - Lists all hard money assets with amounts and USD values
       - Shows total hard money value

    2. ALGORAND
       - Native ALGO balance with participation status
       - Liquid staking derivatives (xALGO, fALGO, etc.)

    3. DOLLARS (Stablecoins)
       - USDC, USDT, DAI, and Folks Finance wrapped versions

    4. SHITCOINS (Everything Else)
       - LP tokens, governance tokens, meme coins, NFTs
       - Sorted by USD value (highest first)

    5. SOVEREIGNTY SUMMARY
       - Participation status (online/offline)
       - Asset counts per category
       - If expenses provided: sovereignty ratio and status

JSON Export:
    Results are automatically exported to:
    sovereignty_analysis_{ADDRESS_PREFIX}.json

Node Configuration:
    The CLI automatically tries to connect to a local Algorand node first.
    If unavailable, it falls back to the public AlgoNode API.

    To configure a local node, set environment variables:
        ALGORAND_NODE_URL=http://127.0.0.1:8080
        ALGORAND_NODE_TOKEN=your-token

Dependencies:
    - requests: HTTP client for API calls
    - core.analyzer: Main analysis engine

See Also:
    - core/analyzer.py: AlgorandSovereigntyAnalyzer class
    - docs/SETUP-GUIDE.md: Full setup instructions
"""

import sys
import requests
# Note: Duplicate imports removed from original

# When running as a module from project root with `python -m scripts.cli`,
# Python adds the root directory to sys.path, allowing this import to work.
from core.analyzer import AlgorandSovereigntyAnalyzer


def print_usage():
    """Print CLI usage information and examples."""
    print("""
Algorand Sovereignty Analyzer CLI
=================================

Analyze any Algorand wallet for financial sovereignty metrics.

Usage:
    python -m scripts.cli <ALGORAND_ADDRESS>

Arguments:
    ALGORAND_ADDRESS    58-character Algorand wallet address

Examples:
    # Analyze a specific wallet
    python -m scripts.cli I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4

    # After analysis, you'll be prompted to enter monthly expenses
    # for sovereignty ratio calculation

Output:
    - Categorized asset breakdown (hard money, algo, dollars, shitcoin)
    - USD values for each asset
    - Sovereignty ratio and status (if expenses provided)
    - JSON export to sovereignty_analysis_*.json

Environment Variables:
    ALGORAND_NODE_URL    Local node URL (optional, faster)
    ALGORAND_NODE_TOKEN  Local node auth token (if required)

For more information, see docs/SETUP-GUIDE.md
""")


def validate_address(address: str) -> bool:
    """
    Validate Algorand address format.

    Algorand addresses are 58 characters using base32 encoding (A-Z, 2-7).

    Args:
        address: The address string to validate

    Returns:
        True if valid format, False otherwise
    """
    if len(address) != 58:
        return False

    # Check for valid base32 characters (A-Z, 2-7)
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')
    return all(c in valid_chars for c in address.upper())


def check_node_connectivity(analyzer: AlgorandSovereigntyAnalyzer) -> bool:
    """
    Test if the configured Algorand node is accessible.

    Attempts to reach the node's /health endpoint with a 2-second timeout.

    Args:
        analyzer: Analyzer instance with node configuration

    Returns:
        True if node responded with 200 OK, False otherwise
    """
    try:
        response = requests.get(
            f"{analyzer.algod_address}/health",
            headers=analyzer.headers,
            timeout=2
        )
        return response.status_code == 200
    except (requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException):
        return False


def main():
    """
    Main entry point for the CLI.

    Flow:
    1. Parse command line arguments
    2. Validate Algorand address format
    3. Attempt local node connection, fallback to AlgoNode
    4. Run wallet analysis
    5. Optionally calculate sovereignty ratio (interactive prompt)
    6. Export results to JSON
    """
    # =========================================================================
    # Argument Parsing
    # =========================================================================
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    address = sys.argv[1]

    # Handle help flag
    if address in ['-h', '--help', 'help']:
        print_usage()
        sys.exit(0)

    # =========================================================================
    # Address Validation
    # =========================================================================
    if not validate_address(address):
        print(f"\n❌ Invalid Algorand address format: {address[:20]}...")
        print("\nAlgorand addresses must be:")
        print("  - Exactly 58 characters long")
        print("  - Use base32 encoding (A-Z, 2-7)")
        print("\nExample: I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4")
        sys.exit(1)

    # =========================================================================
    # Node Connection
    # =========================================================================
    # Try local node first for better performance, fallback to public API
    print("Attempting to connect to local Algorand node...")
    analyzer = AlgorandSovereigntyAnalyzer(use_local_node=True)

    if check_node_connectivity(analyzer):
        print("✅ Connected to local node\n")
    else:
        print("⚠️  Local node not accessible, using public AlgoNode API\n")
        analyzer = AlgorandSovereigntyAnalyzer(use_local_node=False)

    # =========================================================================
    # Wallet Analysis
    # =========================================================================
    # Run the full analysis - this will:
    # 1. Fetch all assets from blockchain
    # 2. Classify each asset (hard_money, algo, dollars, shitcoin)
    # 3. Decompose LP tokens into underlying assets
    # 4. Calculate USD values
    # 5. Print results to console
    # 6. Export to JSON file

    categories = analyzer.analyze_wallet(address)

    if categories is None:
        print(f"\n❌ Wallet not found or error fetching data: {address[:8]}...")
        sys.exit(1)

    # =========================================================================
    # Sovereignty Ratio Calculation (Interactive)
    # =========================================================================
    # After analysis, prompt user for monthly expenses to calculate
    # sovereignty ratio. This is optional - user can skip by entering 0.
    #
    # The ratio = Total Portfolio USD / Annual Fixed Expenses
    # This tells you how many years of expenses your portfolio covers.

    analyzer.calculate_sovereignty_ratio(analyzer.last_hard_money_algo)


if __name__ == "__main__":
    main()
