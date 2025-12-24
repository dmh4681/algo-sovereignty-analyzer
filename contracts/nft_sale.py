"""
NFT Sale Smart Contract for Pickaxe Mining NFTs

This PyTeal contract handles the sale of pickaxe NFTs:
- Users pay 100 ALGO to receive 1 pickaxe NFT
- Owner can withdraw proceeds and unsold NFTs
- Owner can update the price

Pickaxe ASA IDs (mainnet):
- Gold Pickaxe: 3381152020
- Silver Pickaxe: 3381152697
- Bitcoin Pickaxe: 3381152867
"""

from pyteal import *

# Constants
PRICE_MICROALGOS = Int(100_000_000)  # 100 ALGO in microALGOs

# Valid pickaxe ASA IDs
GOLD_PICKAXE_ASA = Int(3381152020)
SILVER_PICKAXE_ASA = Int(3381152697)
BITCOIN_PICKAXE_ASA = Int(3381152867)

# Global state keys
KEY_OWNER = Bytes("owner")
KEY_PRICE = Bytes("price")

# App methods
METHOD_BUY = Bytes("buy")
METHOD_WITHDRAW_ALGO = Bytes("withdraw_algo")
METHOD_WITHDRAW_NFT = Bytes("withdraw_nft")
METHOD_UPDATE_PRICE = Bytes("update_price")
METHOD_OPT_IN_ASA = Bytes("opt_in_asa")


def approval_program():
    """Main approval program for the NFT sale contract."""

    # Initialize global state on creation
    on_create = Seq(
        App.globalPut(KEY_OWNER, Txn.sender()),
        App.globalPut(KEY_PRICE, PRICE_MICROALGOS),
        Approve(),
    )

    # Check if caller is the owner
    is_owner = Txn.sender() == App.globalGet(KEY_OWNER)

    # Check if an ASA ID is a valid pickaxe
    @Subroutine(TealType.uint64)
    def is_valid_pickaxe(asa_id):
        return Or(
            asa_id == GOLD_PICKAXE_ASA,
            asa_id == SILVER_PICKAXE_ASA,
            asa_id == BITCOIN_PICKAXE_ASA,
        )

    # Get contract's ASA balance
    @Subroutine(TealType.uint64)
    def get_asa_balance(asa_id):
        balance = AssetHolding.balance(Global.current_application_address(), asa_id)
        return Seq(balance, If(balance.hasValue(), balance.value(), Int(0)))

    # Check if buyer has opted into the ASA
    @Subroutine(TealType.uint64)
    def buyer_opted_in(buyer_addr, asa_id):
        balance = AssetHolding.balance(buyer_addr, asa_id)
        return Seq(balance, balance.hasValue())

    # Buy NFT: Atomic group with payment + app call
    # Group[0]: Payment to contract (100 ALGO)
    # Group[1]: App call with "buy" method and asset ID
    on_buy = Seq(
        # Must be a group of 2 transactions
        Assert(Global.group_size() == Int(2)),
        # First txn must be a payment
        Assert(Gtxn[0].type_enum() == TxnType.Payment),
        # Payment must be to this contract
        Assert(Gtxn[0].receiver() == Global.current_application_address()),
        # Payment amount must match price EXACTLY (no overpayment)
        Assert(Gtxn[0].amount() == App.globalGet(KEY_PRICE)),
        # No close remainder (don't close account)
        Assert(Gtxn[0].close_remainder_to() == Global.zero_address()),
        # This app call must be second in group
        Assert(Txn.group_index() == Int(1)),
        # Must have exactly 1 foreign asset (the NFT to buy)
        Assert(Txn.assets.length() == Int(1)),
        # Asset must be a valid pickaxe
        Assert(is_valid_pickaxe(Txn.assets[0])),
        # Contract must have at least 1 of this NFT
        Assert(get_asa_balance(Txn.assets[0]) >= Int(1)),
        # Buyer must have opted into the ASA before purchasing
        Assert(buyer_opted_in(Gtxn[0].sender(), Txn.assets[0])),
        # Send 1 NFT to the buyer
        InnerTransaction.Begin(),
        InnerTransaction.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: Txn.assets[0],
                TxnField.asset_amount: Int(1),
                TxnField.asset_receiver: Gtxn[0].sender(),  # Send to payer
                TxnField.fee: Int(0),  # Use pooled fee
            }
        ),
        InnerTransaction.Submit(),
        Approve(),
    )

    # Owner: Withdraw ALGO proceeds
    # Protects against withdrawing below minimum balance (would brick contract)
    on_withdraw_algo = Seq(
        Assert(is_owner),
        # Must specify amount in app args[1]
        Assert(Txn.application_args.length() >= Int(2)),
        # Ensure withdrawal won't drop below minimum balance
        Assert(
            Balance(Global.current_application_address()) - Btoi(Txn.application_args[1])
            >= MinBalance(Global.current_application_address())
        ),
        InnerTransaction.Begin(),
        InnerTransaction.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: Btoi(Txn.application_args[1]),
                TxnField.receiver: Txn.sender(),
                TxnField.fee: Int(0),
            }
        ),
        InnerTransaction.Submit(),
        Approve(),
    )

    # Owner: Withdraw unsold NFTs
    on_withdraw_nft = Seq(
        Assert(is_owner),
        # Must have asset in foreign assets
        Assert(Txn.assets.length() >= Int(1)),
        # Must specify amount in app args[1]
        Assert(Txn.application_args.length() >= Int(2)),
        InnerTransaction.Begin(),
        InnerTransaction.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: Txn.assets[0],
                TxnField.asset_amount: Btoi(Txn.application_args[1]),
                TxnField.asset_receiver: Txn.sender(),
                TxnField.fee: Int(0),
            }
        ),
        InnerTransaction.Submit(),
        Approve(),
    )

    # Owner: Update price
    # Minimum price of 1 ALGO to prevent accidental free giveaways
    on_update_price = Seq(
        Assert(is_owner),
        Assert(Txn.application_args.length() >= Int(2)),
        # Minimum price: 1 ALGO (1,000,000 microALGOs)
        Assert(Btoi(Txn.application_args[1]) >= Int(1_000_000)),
        App.globalPut(KEY_PRICE, Btoi(Txn.application_args[1])),
        Approve(),
    )

    # Owner: Opt contract into an ASA (needed before receiving NFTs)
    on_opt_in_asa = Seq(
        Assert(is_owner),
        Assert(Txn.assets.length() >= Int(1)),
        InnerTransaction.Begin(),
        InnerTransaction.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: Txn.assets[0],
                TxnField.asset_amount: Int(0),
                TxnField.asset_receiver: Global.current_application_address(),
                TxnField.fee: Int(0),
            }
        ),
        InnerTransaction.Submit(),
        Approve(),
    )

    # Route based on method
    on_call = Cond(
        [Txn.application_args[0] == METHOD_BUY, on_buy],
        [Txn.application_args[0] == METHOD_WITHDRAW_ALGO, on_withdraw_algo],
        [Txn.application_args[0] == METHOD_WITHDRAW_NFT, on_withdraw_nft],
        [Txn.application_args[0] == METHOD_UPDATE_PRICE, on_update_price],
        [Txn.application_args[0] == METHOD_OPT_IN_ASA, on_opt_in_asa],
    )

    # Main router
    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, on_call],
        [Txn.on_completion() == OnComplete.DeleteApplication, And(is_owner, Approve())],
        [Txn.on_completion() == OnComplete.UpdateApplication, And(is_owner, Approve())],
        [Txn.on_completion() == OnComplete.OptIn, Approve()],
        [Txn.on_completion() == OnComplete.CloseOut, Approve()],
    )

    return program


def clear_program():
    """Clear state program - always approve."""
    return Approve()


if __name__ == "__main__":
    import os
    from pathlib import Path

    # Compile and save TEAL
    approval_teal = compileTeal(approval_program(), mode=Mode.Application, version=8)
    clear_teal = compileTeal(clear_program(), mode=Mode.Application, version=8)

    # Save to files
    contracts_dir = Path(__file__).parent

    approval_path = contracts_dir / "nft_sale_approval.teal"
    clear_path = contracts_dir / "nft_sale_clear.teal"

    with open(approval_path, "w") as f:
        f.write(approval_teal)
    print(f"Approval program saved to: {approval_path}")

    with open(clear_path, "w") as f:
        f.write(clear_teal)
    print(f"Clear program saved to: {clear_path}")

    print(f"\nApproval program size: {len(approval_teal)} bytes")
    print(f"Clear program size: {len(clear_teal)} bytes")
