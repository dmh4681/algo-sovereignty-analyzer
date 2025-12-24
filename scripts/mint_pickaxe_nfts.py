#!/usr/bin/env python3
"""
Mint Pickaxe NFT Collections on Algorand

Creates ASAs for Gold, Silver, and Bitcoin pickaxe NFTs following ARC3 standard.

Usage:
  python scripts/mint_pickaxe_nfts.py --testnet --type gold   # Test with one on testnet
  python scripts/mint_pickaxe_nfts.py --testnet --type all    # Test all on testnet
  python scripts/mint_pickaxe_nfts.py --type all              # Mint all on mainnet

Environment:
  ALGO_MNEMONIC: 25-word mnemonic phrase for the creator account
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from algosdk import account, mnemonic, transaction
    from algosdk.v2client import algod
except ImportError:
    print("Error: py-algorand-sdk not installed. Run: pip install py-algorand-sdk")
    sys.exit(1)


# Network configurations
NETWORKS = {
    "mainnet": {
        "algod_url": "https://mainnet-api.algonode.cloud",
        "algod_token": "",
    },
    "testnet": {
        "algod_url": "https://testnet-api.algonode.cloud",
        "algod_token": "",
    },
}

# Pickaxe NFT definitions
PICKAXE_NFTS = {
    "gold": {
        "unit_name": "GOLDPICK",
        "asset_name": "Gold Pickaxe",
        "total": 1000,
        "url": "https://algosovereignty.com/nfts/metadata/gold_pickaxe.json#arc3",
        "description": "Auto-mine GOLD$ with every deposit",
    },
    "silver": {
        "unit_name": "SLVRPICK",
        "asset_name": "Silver Pickaxe",
        "total": 2000,
        "url": "https://algosovereignty.com/nfts/metadata/silver_pickaxe.json#arc3",
        "description": "Auto-mine SILVER$ with every deposit",
    },
    "bitcoin": {
        "unit_name": "BTCPICK",
        "asset_name": "Bitcoin Pickaxe",
        "total": 1500,
        "url": "https://algosovereignty.com/nfts/metadata/bitcoin_pickaxe.json#arc3",
        "description": "Auto-mine goBTC with every deposit",
    },
}

# Output file path
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "nfts" / "minted_pickaxes.json"


def get_algod_client(network: str) -> algod.AlgodClient:
    """Create an Algod client for the specified network."""
    config = NETWORKS[network]
    return algod.AlgodClient(config["algod_token"], config["algod_url"])


def get_creator_account() -> tuple[str, str]:
    """Load creator account from environment variable."""
    mnemonic_phrase = os.environ.get("ALGO_MNEMONIC")
    if not mnemonic_phrase:
        print("Error: ALGO_MNEMONIC environment variable not set")
        print("Set it with: export ALGO_MNEMONIC='your 25 word mnemonic phrase'")
        sys.exit(1)

    try:
        private_key = mnemonic.to_private_key(mnemonic_phrase)
        address = account.address_from_private_key(private_key)
        return private_key, address
    except Exception as e:
        print(f"Error: Invalid mnemonic - {e}")
        sys.exit(1)


def check_balance(client: algod.AlgodClient, address: str) -> int:
    """Check account balance and return available microALGOs."""
    try:
        account_info = client.account_info(address)
        balance = account_info.get("amount", 0)
        min_balance = account_info.get("min-balance", 100000)
        available = balance - min_balance
        return balance, available
    except Exception as e:
        print(f"Error checking balance: {e}")
        sys.exit(1)


def mint_pickaxe_nft(
    client: algod.AlgodClient,
    private_key: str,
    creator_address: str,
    pickaxe_type: str,
    network: str,
) -> dict:
    """Mint a single pickaxe NFT and return the result."""
    nft = PICKAXE_NFTS[pickaxe_type]

    print(f"\n{'='*50}")
    print(f"Minting: {nft['asset_name']}")
    print(f"Network: {network.upper()}")
    print(f"Supply: {nft['total']}")
    print(f"Unit: {nft['unit_name']}")
    print(f"{'='*50}")

    # Get suggested parameters
    params = client.suggested_params()

    # Create the asset creation transaction
    txn = transaction.AssetConfigTxn(
        sender=creator_address,
        sp=params,
        total=nft["total"],
        decimals=0,  # NFTs are whole units
        default_frozen=False,
        unit_name=nft["unit_name"],
        asset_name=nft["asset_name"],
        url=nft["url"],
        manager=creator_address,
        reserve=creator_address,
        freeze=creator_address,
        clawback=creator_address,
    )

    # Sign and submit
    signed_txn = txn.sign(private_key)

    try:
        txid = client.send_transaction(signed_txn)
        print(f"Transaction ID: {txid}")
        print("Waiting for confirmation...")

        # Wait for confirmation
        confirmed_txn = transaction.wait_for_confirmation(client, txid, 4)
        asset_id = confirmed_txn.get("asset-index")

        print(f"✅ SUCCESS! Asset ID: {asset_id}")

        # Build explorer URL
        explorer_base = "https://explorer.perawallet.app" if network == "mainnet" else "https://testnet.explorer.perawallet.app"
        explorer_url = f"{explorer_base}/asset/{asset_id}"
        print(f"Explorer: {explorer_url}")

        return {
            "type": pickaxe_type,
            "asset_name": nft["asset_name"],
            "unit_name": nft["unit_name"],
            "asset_id": asset_id,
            "total": nft["total"],
            "txid": txid,
            "network": network,
            "explorer_url": explorer_url,
            "metadata_url": nft["url"],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return {
            "type": pickaxe_type,
            "asset_name": nft["asset_name"],
            "error": str(e),
            "network": network,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }


def load_existing_results() -> dict:
    """Load existing minted pickaxes results if file exists."""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"mainnet": {}, "testnet": {}}


def save_results(results: dict) -> None:
    """Save minting results to JSON file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Results saved to: {OUTPUT_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Mint Pickaxe NFT Collections on Algorand",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/mint_pickaxe_nfts.py --testnet --type gold   # Test with gold on testnet
  python scripts/mint_pickaxe_nfts.py --testnet --type all    # Test all on testnet
  python scripts/mint_pickaxe_nfts.py --type gold             # Mint gold on mainnet
  python scripts/mint_pickaxe_nfts.py --type all              # Mint all on mainnet

Environment Variables:
  ALGO_MNEMONIC    Your 25-word Algorand mnemonic (required)
        """,
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Use testnet instead of mainnet",
    )
    parser.add_argument(
        "--type",
        choices=["gold", "silver", "bitcoin", "all"],
        required=True,
        help="Which pickaxe NFT(s) to mint",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be minted without actually minting",
    )

    args = parser.parse_args()
    network = "testnet" if args.testnet else "mainnet"

    # Determine which NFTs to mint
    if args.type == "all":
        types_to_mint = ["gold", "silver", "bitcoin"]
    else:
        types_to_mint = [args.type]

    print("\n" + "=" * 60)
    print("  PICKAXE NFT MINTING SCRIPT")
    print("  Algo Sovereignty Analyzer")
    print("=" * 60)
    print(f"\nNetwork: {network.upper()}")
    print(f"NFTs to mint: {', '.join(types_to_mint)}")

    # Get creator account
    private_key, creator_address = get_creator_account()
    print(f"Creator: {creator_address}")

    # Connect to network
    client = get_algod_client(network)

    # Check balance
    balance, available = check_balance(client, creator_address)
    print(f"Balance: {balance / 1_000_000:.6f} ALGO")
    print(f"Available: {available / 1_000_000:.6f} ALGO")

    # Each ASA creation costs 0.1 ALGO (100,000 microALGO) min balance + txn fee
    required = len(types_to_mint) * 101_000  # 0.1 ALGO + 0.001 fee per NFT
    if available < required:
        print(f"\n⚠️  Warning: May need more ALGO. Required ~{required / 1_000_000:.3f} ALGO")

    if args.dry_run:
        print("\n🔍 DRY RUN - No transactions will be sent")
        for pickaxe_type in types_to_mint:
            nft = PICKAXE_NFTS[pickaxe_type]
            print(f"\nWould mint: {nft['asset_name']}")
            print(f"  Unit: {nft['unit_name']}")
            print(f"  Supply: {nft['total']}")
            print(f"  URL: {nft['url']}")
        print("\nRun without --dry-run to actually mint.")
        return

    # Confirm before mainnet
    if network == "mainnet":
        print("\n⚠️  WARNING: You are about to mint on MAINNET!")
        print("This will use real ALGO and create permanent assets.")
        confirm = input("Type 'MINT' to confirm: ")
        if confirm != "MINT":
            print("Aborted.")
            return

    # Load existing results and mint
    all_results = load_existing_results()

    for pickaxe_type in types_to_mint:
        result = mint_pickaxe_nft(
            client, private_key, creator_address, pickaxe_type, network
        )
        all_results[network][pickaxe_type] = result

    # Save results
    save_results(all_results)

    # Summary
    print("\n" + "=" * 60)
    print("  MINTING COMPLETE")
    print("=" * 60)

    successful = [r for r in all_results[network].values() if "asset_id" in r]
    failed = [r for r in all_results[network].values() if "error" in r]

    if successful:
        print(f"\n✅ Successfully minted {len(successful)} NFT(s):")
        for r in successful:
            print(f"  • {r['asset_name']}: ASA ID {r['asset_id']}")

    if failed:
        print(f"\n❌ Failed to mint {len(failed)} NFT(s):")
        for r in failed:
            print(f"  • {r['asset_name']}: {r['error']}")


if __name__ == "__main__":
    main()
