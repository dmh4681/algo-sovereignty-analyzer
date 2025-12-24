#!/usr/bin/env python3
"""
Deploy NFT Sale Smart Contract

Deploys the PyTeal NFT sale contract to Algorand and optionally:
- Opts the contract into the pickaxe ASAs
- Transfers NFTs to the contract for sale

Usage:
  python scripts/deploy_nft_sale.py --testnet              # Deploy to testnet
  python scripts/deploy_nft_sale.py                        # Deploy to mainnet
  python scripts/deploy_nft_sale.py --opt-in               # Deploy and opt into ASAs
  python scripts/deploy_nft_sale.py --fund-nfts            # Deploy, opt-in, and transfer NFTs

Environment:
  ALGO_MNEMONIC: 25-word mnemonic phrase for the deployer account
"""

import argparse
import base64
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

# Add contracts to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "contracts"))

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

# Pickaxe ASA IDs (mainnet)
PICKAXE_ASAS = {
    "gold": 3381152020,
    "silver": 3381152697,
    "bitcoin": 3381152867,
}

# Output file path
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "nfts" / "deployed_contract.json"


def get_algod_client(network: str) -> algod.AlgodClient:
    """Create an Algod client for the specified network."""
    config = NETWORKS[network]
    return algod.AlgodClient(config["algod_token"], config["algod_url"])


def get_deployer_account() -> tuple[str, str]:
    """Load deployer account from environment variable."""
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


def compile_contract() -> tuple[str, str]:
    """Compile the PyTeal contract and return approval/clear TEAL."""
    try:
        from nft_sale import approval_program, clear_program
        from pyteal import Mode, compileTeal

        approval_teal = compileTeal(approval_program(), mode=Mode.Application, version=8)
        clear_teal = compileTeal(clear_program(), mode=Mode.Application, version=8)

        return approval_teal, clear_teal
    except ImportError as e:
        print(f"Error: Could not import contract - {e}")
        print("Make sure pyteal is installed: pip install pyteal")
        sys.exit(1)


def compile_teal(client: algod.AlgodClient, teal_source: str) -> bytes:
    """Compile TEAL source to bytecode."""
    response = client.compile(teal_source)
    return base64.b64decode(response["result"])


def deploy_contract(
    client: algod.AlgodClient,
    private_key: str,
    deployer_address: str,
    network: str,
) -> dict:
    """Deploy the NFT sale contract."""
    print("\n" + "=" * 50)
    print("  DEPLOYING NFT SALE CONTRACT")
    print("=" * 50)
    print(f"Network: {network.upper()}")
    print(f"Deployer: {deployer_address}")

    # Compile contract
    print("\nCompiling PyTeal contract...")
    approval_teal, clear_teal = compile_contract()
    print(f"Approval program: {len(approval_teal)} bytes")
    print(f"Clear program: {len(clear_teal)} bytes")

    # Compile to bytecode
    print("Compiling to bytecode...")
    approval_program = compile_teal(client, approval_teal)
    clear_program = compile_teal(client, clear_teal)

    # Get suggested params
    params = client.suggested_params()

    # Create application
    print("Creating application...")
    txn = transaction.ApplicationCreateTxn(
        sender=deployer_address,
        sp=params,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=transaction.StateSchema(num_uints=1, num_byte_slices=1),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
    )

    # Sign and submit
    signed_txn = txn.sign(private_key)

    try:
        txid = client.send_transaction(signed_txn)
        print(f"Transaction ID: {txid}")
        print("Waiting for confirmation...")

        confirmed_txn = transaction.wait_for_confirmation(client, txid, 4)
        app_id = confirmed_txn.get("application-index")
        app_address = transaction.logic.get_application_address(app_id)

        print(f"\n✅ CONTRACT DEPLOYED!")
        print(f"App ID: {app_id}")
        print(f"App Address: {app_address}")

        # Build explorer URL
        explorer_base = (
            "https://explorer.perawallet.app"
            if network == "mainnet"
            else "https://testnet.explorer.perawallet.app"
        )
        explorer_url = f"{explorer_base}/application/{app_id}"
        print(f"Explorer: {explorer_url}")

        return {
            "app_id": app_id,
            "app_address": app_address,
            "txid": txid,
            "network": network,
            "explorer_url": explorer_url,
            "deployer": deployer_address,
            "deployed_at": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        print(f"❌ DEPLOYMENT FAILED: {e}")
        sys.exit(1)


def fund_contract(
    client: algod.AlgodClient,
    private_key: str,
    sender_address: str,
    app_address: str,
    amount_algo: float = 1.0,
) -> str:
    """Fund the contract with ALGO for minimum balance and fees."""
    print(f"\nFunding contract with {amount_algo} ALGO...")

    params = client.suggested_params()
    txn = transaction.PaymentTxn(
        sender=sender_address,
        sp=params,
        receiver=app_address,
        amt=int(amount_algo * 1_000_000),
    )

    signed_txn = txn.sign(private_key)
    txid = client.send_transaction(signed_txn)
    transaction.wait_for_confirmation(client, txid, 4)

    print(f"✅ Funded contract: {txid}")
    return txid


def opt_contract_into_asa(
    client: algod.AlgodClient,
    private_key: str,
    sender_address: str,
    app_id: int,
    asa_id: int,
) -> str:
    """Call the contract to opt into an ASA."""
    print(f"Opting contract into ASA {asa_id}...")

    params = client.suggested_params()
    # Cover fee for outer tx + inner tx (contract opt-in)
    params.fee = 2000
    params.flat_fee = True
    txn = transaction.ApplicationNoOpTxn(
        sender=sender_address,
        sp=params,
        index=app_id,
        app_args=[b"opt_in_asa"],
        foreign_assets=[asa_id],
    )

    signed_txn = txn.sign(private_key)
    txid = client.send_transaction(signed_txn)
    transaction.wait_for_confirmation(client, txid, 4)

    print(f"✅ Opted into ASA {asa_id}: {txid}")
    return txid


def transfer_nfts_to_contract(
    client: algod.AlgodClient,
    private_key: str,
    sender_address: str,
    app_address: str,
    asa_id: int,
    amount: int,
) -> str:
    """Transfer NFTs to the contract for sale."""
    print(f"Transferring {amount} NFTs (ASA {asa_id}) to contract...")

    params = client.suggested_params()
    txn = transaction.AssetTransferTxn(
        sender=sender_address,
        sp=params,
        receiver=app_address,
        amt=amount,
        index=asa_id,
    )

    signed_txn = txn.sign(private_key)
    txid = client.send_transaction(signed_txn)
    transaction.wait_for_confirmation(client, txid, 4)

    print(f"✅ Transferred {amount} NFTs: {txid}")
    return txid


def save_deployment_info(info: dict) -> None:
    """Save deployment info to JSON file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(info, f, indent=2)
    print(f"\n📁 Deployment info saved to: {OUTPUT_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy NFT Sale Smart Contract",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/deploy_nft_sale.py --testnet              # Deploy to testnet only
  python scripts/deploy_nft_sale.py                        # Deploy to mainnet only
  python scripts/deploy_nft_sale.py --opt-in               # Deploy and opt into ASAs
  python scripts/deploy_nft_sale.py --fund-nfts            # Full setup with NFT transfer

Environment Variables:
  ALGO_MNEMONIC    Your 25-word Algorand mnemonic (required)
        """,
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Deploy to testnet instead of mainnet",
    )
    parser.add_argument(
        "--opt-in",
        action="store_true",
        help="After deployment, opt the contract into pickaxe ASAs",
    )
    parser.add_argument(
        "--fund-nfts",
        action="store_true",
        help="Full setup: deploy, opt-in, and transfer NFTs to contract",
    )
    parser.add_argument(
        "--nft-amounts",
        type=str,
        default="100,100,100",
        help="NFTs to transfer (gold,silver,bitcoin). Default: 100,100,100",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without deploying",
    )

    args = parser.parse_args()
    network = "testnet" if args.testnet else "mainnet"

    print("\n" + "=" * 60)
    print("  NFT SALE CONTRACT DEPLOYMENT")
    print("  Algo Sovereignty Analyzer")
    print("=" * 60)

    # Get deployer account
    private_key, deployer_address = get_deployer_account()
    print(f"\nDeployer: {deployer_address}")
    print(f"Network: {network.upper()}")

    # Parse NFT amounts
    nft_amounts = [int(x) for x in args.nft_amounts.split(",")]
    if len(nft_amounts) != 3:
        print("Error: --nft-amounts must have 3 values (gold,silver,bitcoin)")
        sys.exit(1)

    if args.dry_run:
        print("\n🔍 DRY RUN - No transactions will be sent")
        print(f"\nWould deploy contract to {network}")
        if args.opt_in or args.fund_nfts:
            print("Would opt contract into ASAs:", list(PICKAXE_ASAS.values()))
        if args.fund_nfts:
            print(f"Would transfer NFTs: Gold={nft_amounts[0]}, Silver={nft_amounts[1]}, Bitcoin={nft_amounts[2]}")
        return

    # Confirm before mainnet
    if network == "mainnet":
        print("\n⚠️  WARNING: You are about to deploy on MAINNET!")
        print("This will use real ALGO and create a permanent application.")
        confirm = input("Type 'DEPLOY' to confirm: ")
        if confirm != "DEPLOY":
            print("Aborted.")
            return

    # Connect to network
    client = get_algod_client(network)

    # Check balance
    account_info = client.account_info(deployer_address)
    balance = account_info.get("amount", 0) / 1_000_000
    print(f"Balance: {balance:.6f} ALGO")

    # Deploy contract
    deployment_info = deploy_contract(client, private_key, deployer_address, network)

    # Fund contract (needed for minimum balance when holding ASAs)
    if args.opt_in or args.fund_nfts:
        # Need ~0.5 ALGO for 3 ASA opt-ins + some extra for fees
        fund_contract(client, private_key, deployer_address, deployment_info["app_address"], 1.0)

    # Opt into ASAs
    if args.opt_in or args.fund_nfts:
        print("\n" + "-" * 40)
        print("Opting contract into pickaxe ASAs...")
        for name, asa_id in PICKAXE_ASAS.items():
            opt_contract_into_asa(
                client, private_key, deployer_address, deployment_info["app_id"], asa_id
            )
        deployment_info["opted_into_asas"] = list(PICKAXE_ASAS.values())

    # Transfer NFTs
    if args.fund_nfts:
        print("\n" + "-" * 40)
        print("Transferring NFTs to contract...")
        transfers = {}
        for (name, asa_id), amount in zip(PICKAXE_ASAS.items(), nft_amounts):
            if amount > 0:
                txid = transfer_nfts_to_contract(
                    client,
                    private_key,
                    deployer_address,
                    deployment_info["app_address"],
                    asa_id,
                    amount,
                )
                transfers[name] = {"asa_id": asa_id, "amount": amount, "txid": txid}
        deployment_info["nft_transfers"] = transfers

    # Save deployment info
    save_deployment_info(deployment_info)

    # Summary
    print("\n" + "=" * 60)
    print("  DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\nApp ID: {deployment_info['app_id']}")
    print(f"App Address: {deployment_info['app_address']}")
    print(f"Explorer: {deployment_info['explorer_url']}")

    if args.fund_nfts:
        print("\nNFTs in contract:")
        for name, data in deployment_info.get("nft_transfers", {}).items():
            print(f"  • {name.capitalize()} Pickaxe: {data['amount']}")


if __name__ == "__main__":
    main()
