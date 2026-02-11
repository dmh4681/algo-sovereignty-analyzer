"""
Historical sovereignty tracking module.

Manages snapshots of sovereignty metrics over time, storing data in JSON files
for each wallet address.
"""

import json
import os
import shutil
import tempfile
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

    def _validate_snapshot(self, snapshot: dict) -> bool:
        """Validate a snapshot has required fields before writing."""
        required = ('address', 'timestamp', 'sovereignty_ratio')
        return all(snapshot.get(field) is not None for field in required)

    def _save_raw_data(self, address: str, data: List[dict]) -> None:
        """Save raw snapshot data to file atomically.

        Writes to a temp file first, fsyncs, then renames to avoid
        data corruption if a crash occurs mid-write.
        """
        file_path = self._get_file_path(address)

        # Back up existing file before overwriting
        if file_path.exists():
            try:
                shutil.copy2(file_path, file_path.with_suffix('.json.bak'))
            except OSError:
                pass  # Backup is best-effort

        # Atomic write: temp file -> fsync -> rename
        tmp_fd = None
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=self.history_dir, suffix='.tmp'
            )
            with os.fdopen(tmp_fd, 'w') as f:
                tmp_fd = None  # os.fdopen takes ownership of fd
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            Path(tmp_path).replace(file_path)
        except Exception:
            # Clean up temp file on failure; original file is untouched
            if tmp_fd is not None:
                os.close(tmp_fd)
            if tmp_path and Path(tmp_path).exists():
                try:
                    Path(tmp_path).unlink()
                except OSError:
                    pass
            raise

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
            # Validate before persisting
            snap_dict = snapshot.model_dump()
            if not self._validate_snapshot(snap_dict):
                print(f"Snapshot validation failed for {snapshot.address}")
                return False

            # Load existing data
            snapshots = self._load_raw_data(snapshot.address)

            # Add new snapshot
            snapshots.append(snap_dict)

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

    def get_progress(self, address: str, days: int = 30) -> Optional[dict]:
        """
        Calculate sovereignty ratio change and trend over a period.

        Returns dict with current_ratio, previous_ratio, change, trend.
        """
        snapshots = self.get_history(address, days)
        if not snapshots:
            return None

        current = snapshots[-1]
        if len(snapshots) < 2:
            return {
                "current_ratio": current.sovereignty_ratio,
                "previous_ratio": None,
                "change_absolute": None,
                "change_pct": None,
                "trend": "new",
                "days_tracked": 0,
                "snapshots_count": len(snapshots),
            }

        previous = snapshots[0]
        change = current.sovereignty_ratio - previous.sovereignty_ratio
        change_pct = (change / previous.sovereignty_ratio * 100) if previous.sovereignty_ratio else None

        if abs(change) < 0.01:
            trend = "stable"
        elif change > 0:
            trend = "improving"
        else:
            trend = "declining"

        return {
            "current_ratio": current.sovereignty_ratio,
            "previous_ratio": previous.sovereignty_ratio,
            "change_absolute": round(change, 4),
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "trend": trend,
            "days_tracked": days,
            "snapshots_count": len(snapshots),
        }

    def get_all_time_stats(self, address: str) -> Optional[dict]:
        """
        Get all-time high, low, and average sovereignty ratio from all snapshots.
        """
        raw_data = self._load_raw_data(address)
        if not raw_data:
            return None

        ratios = []
        first_ts = None
        for snap in raw_data:
            ratio = snap.get("sovereignty_ratio")
            if ratio is not None:
                ratios.append(ratio)
                ts = snap.get("timestamp")
                if first_ts is None or (ts and ts < first_ts):
                    first_ts = ts

        if not ratios:
            return None

        return {
            "high": round(max(ratios), 4),
            "low": round(min(ratios), 4),
            "average": round(sum(ratios) / len(ratios), 4),
            "first_tracked": first_ts or "unknown",
        }

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
