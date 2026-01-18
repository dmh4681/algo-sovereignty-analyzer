"""
AI Asset Classification Training - User Corrections System

This module handles storage and retrieval of user-submitted classification corrections.
When users disagree with an auto-classification, they can submit a correction which:
1. Gets stored in a JSON file for persistence
2. Is prioritized over auto-classification (but lower than CSV overrides)
3. Can be reviewed and promoted to the CSV for permanent inclusion

The learning hierarchy is:
1. CSV manual overrides (highest priority)
2. User-submitted corrections (medium priority)
3. Auto-classification regex (lowest priority)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum


class CorrectionStatus(str, Enum):
    """Status of a user correction."""
    PENDING = "pending"      # Awaiting review
    APPROVED = "approved"    # Promoted to CSV
    REJECTED = "rejected"    # Determined incorrect
    ACTIVE = "active"        # In use but not promoted


class ClassificationCorrection(BaseModel):
    """A user-submitted classification correction."""
    asset_id: str
    asset_name: str
    ticker: str
    original_category: str
    corrected_category: str
    reason: Optional[str] = None
    submitted_at: str
    submitted_by: Optional[str] = None  # Wallet address if available
    status: CorrectionStatus = CorrectionStatus.ACTIVE
    reviewed_at: Optional[str] = None
    reviewer_notes: Optional[str] = None


class CorrectionStats(BaseModel):
    """Statistics about the corrections system."""
    total_corrections: int
    active_corrections: int
    pending_corrections: int
    approved_corrections: int
    rejected_corrections: int
    most_corrected_category: Optional[str] = None
    recent_corrections: List[Dict[str, Any]]


class CorrectionsManager:
    """Manages user-submitted classification corrections."""

    def __init__(self, corrections_file: str = 'data/user_corrections.json'):
        self.corrections_file = corrections_file
        self.corrections: Dict[str, ClassificationCorrection] = {}
        self._load_corrections()

    def _load_corrections(self) -> None:
        """Load corrections from JSON file."""
        if os.path.exists(self.corrections_file):
            try:
                with open(self.corrections_file, 'r') as f:
                    data = json.load(f)
                    for asset_id, correction_data in data.items():
                        self.corrections[asset_id] = ClassificationCorrection(**correction_data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load corrections file: {e}")
                self.corrections = {}
        else:
            # Create empty corrections file
            self._save_corrections()

    def _save_corrections(self) -> None:
        """Save corrections to JSON file."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.corrections_file) or '.', exist_ok=True)

        with open(self.corrections_file, 'w') as f:
            data = {
                asset_id: correction.model_dump()
                for asset_id, correction in self.corrections.items()
            }
            json.dump(data, f, indent=2)

    def submit_correction(
        self,
        asset_id: str,
        asset_name: str,
        ticker: str,
        original_category: str,
        corrected_category: str,
        reason: Optional[str] = None,
        submitted_by: Optional[str] = None
    ) -> ClassificationCorrection:
        """
        Submit a new classification correction.

        Args:
            asset_id: The ASA ID
            asset_name: Human-readable asset name
            ticker: Asset ticker symbol
            original_category: The auto-classified category
            corrected_category: The user's suggested category
            reason: Optional explanation for the correction
            submitted_by: Optional wallet address of submitter

        Returns:
            The created correction object
        """
        # Validate category
        valid_categories = ['hard_money', 'algo', 'dollars', 'shitcoin']
        if corrected_category not in valid_categories:
            raise ValueError(f"Invalid category '{corrected_category}'. Must be one of: {valid_categories}")

        correction = ClassificationCorrection(
            asset_id=str(asset_id),
            asset_name=asset_name,
            ticker=ticker,
            original_category=original_category,
            corrected_category=corrected_category,
            reason=reason,
            submitted_at=datetime.utcnow().isoformat(),
            submitted_by=submitted_by,
            status=CorrectionStatus.ACTIVE
        )

        self.corrections[str(asset_id)] = correction
        self._save_corrections()

        return correction

    def get_correction(self, asset_id: str) -> Optional[str]:
        """
        Get the corrected category for an asset, if one exists.

        Only returns corrections that are ACTIVE or APPROVED.

        Args:
            asset_id: The ASA ID to look up

        Returns:
            The corrected category, or None if no active correction exists
        """
        correction = self.corrections.get(str(asset_id))
        if correction and correction.status in [CorrectionStatus.ACTIVE, CorrectionStatus.APPROVED]:
            return correction.corrected_category
        return None

    def get_all_corrections(self, status: Optional[CorrectionStatus] = None) -> List[ClassificationCorrection]:
        """
        Get all corrections, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of corrections
        """
        corrections = list(self.corrections.values())
        if status:
            corrections = [c for c in corrections if c.status == status]
        return sorted(corrections, key=lambda c: c.submitted_at, reverse=True)

    def update_correction_status(
        self,
        asset_id: str,
        new_status: CorrectionStatus,
        reviewer_notes: Optional[str] = None
    ) -> Optional[ClassificationCorrection]:
        """
        Update the status of a correction.

        Args:
            asset_id: The ASA ID
            new_status: New status to set
            reviewer_notes: Optional notes from reviewer

        Returns:
            Updated correction or None if not found
        """
        correction = self.corrections.get(str(asset_id))
        if not correction:
            return None

        correction.status = new_status
        correction.reviewed_at = datetime.utcnow().isoformat()
        if reviewer_notes:
            correction.reviewer_notes = reviewer_notes

        self._save_corrections()
        return correction

    def delete_correction(self, asset_id: str) -> bool:
        """
        Delete a correction.

        Args:
            asset_id: The ASA ID

        Returns:
            True if deleted, False if not found
        """
        if str(asset_id) in self.corrections:
            del self.corrections[str(asset_id)]
            self._save_corrections()
            return True
        return False

    def get_stats(self) -> CorrectionStats:
        """Get statistics about the corrections system."""
        corrections = list(self.corrections.values())

        # Count by status
        status_counts = {status: 0 for status in CorrectionStatus}
        category_counts: Dict[str, int] = {}

        for c in corrections:
            status_counts[c.status] += 1
            # Count corrected-to categories
            category_counts[c.corrected_category] = category_counts.get(c.corrected_category, 0) + 1

        # Find most corrected-to category
        most_corrected = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None

        # Get recent corrections (last 5)
        recent = sorted(corrections, key=lambda c: c.submitted_at, reverse=True)[:5]

        return CorrectionStats(
            total_corrections=len(corrections),
            active_corrections=status_counts[CorrectionStatus.ACTIVE],
            pending_corrections=status_counts[CorrectionStatus.PENDING],
            approved_corrections=status_counts[CorrectionStatus.APPROVED],
            rejected_corrections=status_counts[CorrectionStatus.REJECTED],
            most_corrected_category=most_corrected,
            recent_corrections=[c.model_dump() for c in recent]
        )

    def export_to_csv_format(self) -> str:
        """
        Export approved corrections in CSV format for manual review.

        Returns:
            CSV-formatted string of approved corrections
        """
        approved = self.get_all_corrections(CorrectionStatus.APPROVED)
        lines = ["asset_id,name,ticker,category,notes"]

        for c in approved:
            notes = f"User correction: {c.reason}" if c.reason else "User correction"
            lines.append(f"{c.asset_id},{c.asset_name},{c.ticker},{c.corrected_category},{notes}")

        return "\n".join(lines)


# Global instance
_corrections_manager: Optional[CorrectionsManager] = None


def get_corrections_manager() -> CorrectionsManager:
    """Get the global corrections manager instance."""
    global _corrections_manager
    if _corrections_manager is None:
        _corrections_manager = CorrectionsManager()
    return _corrections_manager
