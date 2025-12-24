#!/usr/bin/env python3
"""
Finish contract setup for already-deployed NFT sale contract.
Opts into ASAs and transfers NFTs.
"""

import os
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import ApplicationNoOpTxn, AssetTransferTxn, wait_for_confirmation

load_dotenv()

# Configuration
APP_ID = 3381223080
ALGOD_ADDRESS = "https://mainnet-api.algonode.cloud"
ALGOD_TOKEN = ""

# Pickaxe ASA IDs
PICKAXE_ASAS = {
    "gold": 3381152020,
    "silver": 3381152697,
    "bitcoin": 3381152867
}

# How many of each to transfer to contract
NFT_AMOUNTS = {
    "gold": 10,
    "silver": 10,
    "bitcoin": 10
}

def get_app_address(app_id: int) -> str:
    """Get the address for an application."""
    from algosdk.logic import get_application_address
    return get_application_address(app_id)

def main():
    # Load mnemonic
    mnemonic_phrase = os.getenv("ALGO_MNEMONIC")
    if not mnemonic_phrase:
        print("❌ ALGO_MNEMONIC not set in .env")
        return
    
    private_key = mnemonic.to_private_key(mnemonic_phrase)
    deployer_address = account.address_from_private_key(private_key)
    
    # Initialize client
    client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
    
    app_address = get_app_address(APP_ID)
    
    print(f"""
==========================================
  FINISH CONTRACT SETUP
==========================================
App ID: {APP_ID}
App Address: {app_address}
Deployer: {deployer_address}
""")
    
    # Check deployer balance
    account_info = client.account_info(deployer_address)
    balance = account_info.get("amount", 0) / 1_000_000
    print(f"Deployer balance: {balance:.6f} ALGO")
    
    # Step 1: Opt contract into each ASA
    print("\n--- Opting contract into ASAs ---")
    
    for name, asa_id in PICKAXE_ASAS.items():
        print(f"\nOpting into {name} pickaxe (ASA {asa_id})...")
        
        try:
            params = client.suggested_params()
            params.fee = 2000  # Cover outer + inner tx
            params.flat_fee = True
            
            txn = ApplicationNoOpTxn(
                sender=deployer_address,
                sp=params,
                index=APP_ID,
                app_args=[b"opt_in_asa"],
                foreign_assets=[asa_id]
            )
            
            signed_txn = txn.sign(private_key)
            txid = client.send_transaction(signed_txn)
            print(f"  Transaction: {txid}")
            
            wait_for_confirmation(client, txid, 4)
            print(f"  ✅ Opted into {name} pickaxe!")
            
        except Exception as e:
            if "already opted in" in str(e).lower():
                print(f"  ⚠️ Already opted in to {name}")
            else:
                print(f"  ❌ Error: {e}")
    
    # Step 2: Transfer NFTs to contract
    print("\n--- Transferring NFTs to contract ---")
    
    for name, asa_id in PICKAXE_ASAS.items():
        amount = NFT_AMOUNTS[name]
        print(f"\nTransferring {amount} {name} pickaxes...")
        
        try:
            params = client.suggested_params()
            
            txn = AssetTransferTxn(
                sender=deployer_address,
                sp=params,
                receiver=app_address,
                amt=amount,
                index=asa_id
            )
            
            signed_txn = txn.sign(private_key)
            txid = client.send_transaction(signed_txn)
            print(f"  Transaction: {txid}")
            
            wait_for_confirmation(client, txid, 4)
            print(f"  ✅ Transferred {amount} {name} pickaxes!")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Verify final state
    print("\n--- Verification ---")
    app_info = client.account_info(app_address)
    
    print(f"\nContract holdings:")
    for asset in app_info.get("assets", []):
        asa_id = asset["asset-id"]
        amount = asset["amount"]
        name = next((n for n, i in PICKAXE_ASAS.items() if i == asa_id), "unknown")
        print(f"  {name}: {amount} NFTs")
    
    print(f"\n✅ Contract setup complete!")
    print(f"Explorer: https://explorer.perawallet.app/application/{APP_ID}")

if __name__ == "__main__":
    main()
