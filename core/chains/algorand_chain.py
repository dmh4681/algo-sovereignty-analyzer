"""
Algorand chain analyzer implementation.

This module implements the ChainAnalyzer interface for Algorand,
wrapping the existing analyzer functionality.
"""

import re
import requests
from typing import Optional, Dict, Any, List

from .chain_base import (
    ChainAnalyzer,
    ChainConfig,
    ChainType,
    ChainAsset,
    ChainBalance,
    ADDRESS_PATTERNS,
)


class AlgorandChainAnalyzer(ChainAnalyzer):
    """
    Algorand-specific implementation of ChainAnalyzer.

    Connects to Algorand nodes via the Algod REST API.
    """

    MAINNET_ALGONODE = "https://mainnet-api.algonode.cloud"
    TESTNET_ALGONODE = "https://testnet-api.algonode.cloud"

    def __init__(self, config: ChainConfig):
        super().__init__(config)

        # Set node URL based on network if not specified
        if not config.node_url:
            if config.network == "testnet":
                self.node_url = self.TESTNET_ALGONODE
            else:
                self.node_url = self.MAINNET_ALGONODE
        else:
            self.node_url = config.node_url

        # Build headers
        self.headers = {"Content-Type": "application/json"}
        if config.auth_token:
            self.headers["Authorization"] = f"Bearer {config.auth_token}"

    def validate_address(self, address: str) -> bool:
        """
        Validate an Algorand address.

        Algorand addresses are 58 characters, base32 encoded.
        """
        if not address or len(address) != 58:
            return False

        pattern = ADDRESS_PATTERNS[ChainType.ALGORAND]
        charset = set(pattern["charset"])

        return all(c in charset for c in address)

    def get_balance(self, address: str) -> ChainBalance:
        """
        Get balance and assets for an Algorand address.
        """
        if not self.validate_address(address):
            raise ValueError(f"Invalid Algorand address: {address}")

        # Fetch account data
        url = f"{self.node_url}/v2/accounts/{address}"
        response = requests.get(url, headers=self.headers, timeout=self.config.timeout_seconds)
        response.raise_for_status()

        account_data = response.json()

        # Extract native ALGO balance
        raw_algo = account_data.get("amount", 0)
        algo_balance = self.raw_to_decimal(raw_algo)

        # Extract participation status
        participation = account_data.get("participation", {})
        participation_status = None
        if participation:
            vote_first = participation.get("vote-first-valid", 0)
            vote_last = participation.get("vote-last-valid", 0)
            if vote_first and vote_last:
                participation_status = f"voting_rounds_{vote_first}_{vote_last}"

        # Extract assets
        assets = []
        for asset_holding in account_data.get("assets", []):
            asset_id = str(asset_holding.get("asset-id"))
            raw_amount = asset_holding.get("amount", 0)

            # Get asset details
            asset_details = self.get_asset_details(asset_id)
            if asset_details:
                asset_details.raw_amount = raw_amount
                asset_details.amount = self.raw_to_decimal(raw_amount, asset_details.decimals)
                assets.append(asset_details)

        return ChainBalance(
            chain=ChainType.ALGORAND,
            address=address,
            native_balance=algo_balance,
            native_balance_raw=raw_algo,
            assets=assets,
            participation_status=participation_status,
            metadata={
                "min_balance": account_data.get("min-balance", 0),
                "total_apps_opted_in": account_data.get("total-apps-opted-in", 0),
                "total_assets_opted_in": account_data.get("total-assets-opted-in", 0),
                "total_created_apps": account_data.get("total-created-apps", 0),
                "total_created_assets": account_data.get("total-created-assets", 0),
            },
        )

    def get_asset_details(self, asset_id: str) -> Optional[ChainAsset]:
        """
        Get details for an Algorand Standard Asset (ASA).
        """
        try:
            url = f"{self.node_url}/v2/assets/{asset_id}"
            response = requests.get(url, headers=self.headers, timeout=self.config.timeout_seconds)

            if response.status_code == 404:
                return None

            response.raise_for_status()
            asset_data = response.json()
            params = asset_data.get("params", {})

            return ChainAsset(
                chain=ChainType.ALGORAND,
                asset_id=asset_id,
                ticker=params.get("unit-name", f"ASA-{asset_id}"),
                name=params.get("name", f"Asset {asset_id}"),
                amount=0,  # Will be set by caller
                decimals=params.get("decimals", 0),
                metadata={
                    "total": params.get("total", 0),
                    "creator": params.get("creator"),
                    "manager": params.get("manager"),
                    "reserve": params.get("reserve"),
                    "freeze": params.get("freeze"),
                    "clawback": params.get("clawback"),
                    "url": params.get("url"),
                },
            )
        except Exception as e:
            print(f"Error fetching asset {asset_id}: {e}")
            return None

    def get_native_token_ticker(self) -> str:
        """Return ALGO as the native token ticker."""
        return "ALGO"

    def get_native_token_decimals(self) -> int:
        """Return 6 as ALGO uses microalgos (10^6)."""
        return 6

    def is_participating(self, address: str) -> bool:
        """
        Check if an address is actively participating in consensus.

        Args:
            address: Algorand address

        Returns:
            True if participating, False otherwise
        """
        try:
            balance = self.get_balance(address)
            return balance.participation_status is not None
        except Exception:
            return False

    def get_participation_info(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed participation information for an address.

        Args:
            address: Algorand address

        Returns:
            Participation details or None if not participating
        """
        try:
            url = f"{self.node_url}/v2/accounts/{address}"
            response = requests.get(url, headers=self.headers, timeout=self.config.timeout_seconds)
            response.raise_for_status()

            account_data = response.json()
            participation = account_data.get("participation", {})

            if not participation:
                return None

            return {
                "selection_participation_key": participation.get("selection-participation-key"),
                "vote_first_valid": participation.get("vote-first-valid"),
                "vote_last_valid": participation.get("vote-last-valid"),
                "vote_key_dilution": participation.get("vote-key-dilution"),
                "vote_participation_key": participation.get("vote-participation-key"),
                "state_proof_key": participation.get("state-proof-key"),
            }
        except Exception:
            return None


def create_algorand_analyzer(
    node_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    network: str = "mainnet",
) -> AlgorandChainAnalyzer:
    """
    Convenience function to create an Algorand analyzer.

    Args:
        node_url: Custom node URL (uses AlgoNode if not specified)
        auth_token: Auth token for private nodes
        network: "mainnet" or "testnet"

    Returns:
        Configured AlgorandChainAnalyzer
    """
    config = ChainConfig(
        chain_type=ChainType.ALGORAND,
        node_url=node_url or "",
        auth_token=auth_token,
        network=network,
    )
    return AlgorandChainAnalyzer(config)
