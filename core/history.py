"""
Historical sovereignty tracking module.

Manages snapshots of sovereignty metrics over time, storing data in JSON files
for each wallet address.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


def get_data_directory() -> Path:
    """
    Get the data directory path.

    Uses DATA_DIR environment variable if set (for Railway/production),
    otherwise defaults to 'data' in project root.
    """
    env_data_dir = os.environ.get('DATA_DIR')
    if env_data_dir:
        return Path(env_data_dir)

    # Default: project root's data directory
    project_root = Path(__file__).parent.parent
    return project_root / "data"


class SovereigntySnapshot(BaseModel):
    """A point-in-time snapshot of sovereignty metrics."""
    address: str
    timestamp: str  # ISO format datetime string
    sovereignty_ratio: float
    hard_money_usd: float
    total_portfolio_usd: float
    algo_price: float
    participation_status: bool


class HistoryManager:
    """
    Manages historical sovereignty snapshots.

    Stores data in JSON files under data/history/{address}.json
    Keeps up to 365 days of history per address.
    """

    MAX_DAYS = 365

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the history manager.

        Args:
            data_dir: Base data directory. Defaults to DATA_DIR env var or 'data' in project root.
        """
        if data_dir is None:
            data_dir = get_data_directory()
        else:
            data_dir = Path(data_dir)

        self.history_dir = data_dir / "history"
        self._ensure_directory()
        print(f"[HistoryManager] Using history directory: {self.history_dir}")

    def _ensure_directory(self) -> None:
        """Create history directory if it doesn't exist."""
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, address: str) -> Path:
        """Get the JSON file path for a given address."""
        # Sanitize address for filename (should already be safe, but be careful)
        safe_address = "".join(c for c in address if c.isalnum())
        return self.history_dir / f"{safe_address}.json"

    def _load_raw_data(self, address: str) -> List[dict]:
        """Load raw snapshot data from file."""
        file_path = self._get_file_path(address)

        if not file_path.exists():
            return []

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError):
            return []

    def _save_raw_data(self, address: str, data: List[dict]) -> None:
        """Save raw snapshot data to file."""
        file_path = self._get_file_path(address)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _prune_old_snapshots(self, snapshots: List[dict]) -> List[dict]:
        """Remove snapshots older than MAX_DAYS."""
        if not snapshots:
            return []

        cutoff_date = datetime.utcnow() - timedelta(days=self.MAX_DAYS)

        pruned = []
        for snapshot in snapshots:
            try:
                ts = datetime.fromisoformat(snapshot.get('timestamp', ''))
                if ts >= cutoff_date:
                    pruned.append(snapshot)
            except (ValueError, TypeError):
                # Skip invalid timestamps
                continue

        return pruned

    def save_snapshot(self, snapshot: SovereigntySnapshot) -> bool:
        """
        Save a new sovereignty snapshot.

        Args:
            snapshot: The snapshot to save.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # Load existing data
            snapshots = self._load_raw_data(snapshot.address)

            # Add new snapshot
            snapshots.append(snapshot.model_dump())

            # Prune old data
            snapshots = self._prune_old_snapshots(snapshots)

            # Sort by timestamp (oldest first)
            snapshots.sort(key=lambda x: x.get('timestamp', ''))

            # Save
            self._save_raw_data(snapshot.address, snapshots)

            return True
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return False

    def get_history(
        self,
        address: str,
        days: int = 90
    ) -> List[SovereigntySnapshot]:
        """
        Get historical snapshots for an address.

        Args:
            address: The wallet address.
            days: Number of days to retrieve (30, 90, or 365).

        Returns:
            List of snapshots within the time period, sorted by timestamp.
        """
        # Validate days parameter
        if days not in (30, 90, 365):
            days = 90

        # Load data
        raw_data = self._load_raw_data(address)

        if not raw_data:
            return []

        # Filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        filtered_snapshots = []
        for data in raw_data:
            try:
                ts = datetime.fromisoformat(data.get('timestamp', ''))
                if ts >= cutoff_date:
                    filtered_snapshots.append(SovereigntySnapshot(**data))
            except (ValueError, TypeError):
                continue

        # Sort by timestamp
        filtered_snapshots.sort(key=lambda x: x.timestamp)

        return filtered_snapshots

    def get_latest_snapshot(self, address: str) -> Optional[SovereigntySnapshot]:
        """
        Get the most recent snapshot for an address.

        Args:
            address: The wallet address.

        Returns:
            The latest snapshot, or None if no history exists.
        """
        raw_data = self._load_raw_data(address)

        if not raw_data:
            return None

        # Sort by timestamp descending and get first
        try:
            sorted_data = sorted(
                raw_data,
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )
            return SovereigntySnapshot(**sorted_data[0])
        except (IndexError, ValueError):
            return None

    def clear_history(self, address: str) -> bool:
        """
        Clear all history for an address.

        Args:
            address: The wallet address.

        Returns:
            True if cleared successfully, False otherwise.
        """
        try:
            file_path = self._get_file_path(address)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception:
            return False


# Singleton instance for convenience
_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """Get the singleton HistoryManager instance."""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager
