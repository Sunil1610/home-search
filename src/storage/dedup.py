"""
Deduplication module.
Tracks processed videos to avoid reprocessing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Set, Optional, Dict, Any


class ProcessedVideosTracker:
    """Tracks which videos have been processed."""

    def __init__(self, filepath: str = "./data/processed_videos.json"):
        self.filepath = filepath
        self.data: Dict[str, Any] = {
            "processed_videos": {},
            "last_updated": None,
            "stats": {
                "total_processed": 0,
                "total_failed": 0
            }
        }
        self._load()

    def _load(self) -> None:
        """Load processed videos from file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error loading processed videos: {e}")

    def _save(self) -> None:
        """Save processed videos to file."""
        try:
            # Ensure directory exists
            Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)

            self.data["last_updated"] = datetime.now().isoformat()

            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving processed videos: {e}")

    def is_processed(self, video_id: str) -> bool:
        """Check if a video has been processed."""
        return video_id in self.data["processed_videos"]

    def mark_processed(
        self,
        video_id: str,
        success: bool = True,
        location: str = "",
        notes: str = ""
    ) -> None:
        """
        Mark a video as processed.

        Args:
            video_id: YouTube video ID
            success: Whether processing succeeded
            location: Search location used
            notes: Optional notes
        """
        self.data["processed_videos"][video_id] = {
            "processed_at": datetime.now().isoformat(),
            "success": success,
            "location": location,
            "notes": notes
        }

        if success:
            self.data["stats"]["total_processed"] += 1
        else:
            self.data["stats"]["total_failed"] += 1

        self._save()

    def get_processed_ids(self) -> Set[str]:
        """Get set of all processed video IDs."""
        return set(self.data["processed_videos"].keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "total_processed": self.data["stats"]["total_processed"],
            "total_failed": self.data["stats"]["total_failed"],
            "last_updated": self.data.get("last_updated"),
            "unique_videos": len(self.data["processed_videos"])
        }

    def filter_unprocessed(self, video_ids: list) -> list:
        """
        Filter list to only unprocessed video IDs.

        Args:
            video_ids: List of video IDs to filter

        Returns:
            List of unprocessed video IDs
        """
        processed = self.get_processed_ids()
        return [vid for vid in video_ids if vid not in processed]

    def clear(self) -> None:
        """Clear all processed videos (use with caution)."""
        self.data = {
            "processed_videos": {},
            "last_updated": None,
            "stats": {
                "total_processed": 0,
                "total_failed": 0
            }
        }
        self._save()


# Global tracker instance
_tracker: Optional[ProcessedVideosTracker] = None


def get_tracker(filepath: str = "./data/processed_videos.json") -> ProcessedVideosTracker:
    """Get or create the global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ProcessedVideosTracker(filepath)
    return _tracker


def is_video_processed(video_id: str) -> bool:
    """Check if a video has been processed."""
    return get_tracker().is_processed(video_id)


def mark_video_processed(video_id: str, success: bool = True, location: str = "") -> None:
    """Mark a video as processed."""
    get_tracker().mark_processed(video_id, success, location)


def get_unprocessed_videos(video_ids: list) -> list:
    """Filter to only unprocessed videos."""
    return get_tracker().filter_unprocessed(video_ids)


if __name__ == "__main__":
    print("=== Testing Deduplication ===\n")

    tracker = ProcessedVideosTracker("./data/test_processed.json")

    # Test marking
    tracker.mark_processed("video1", success=True, location="LB Nagar")
    tracker.mark_processed("video2", success=True, location="LB Nagar")
    tracker.mark_processed("video3", success=False, location="LB Nagar", notes="403 error")

    # Test checking
    print(f"video1 processed: {tracker.is_processed('video1')}")
    print(f"video4 processed: {tracker.is_processed('video4')}")

    # Test filtering
    all_videos = ["video1", "video2", "video3", "video4", "video5"]
    unprocessed = tracker.filter_unprocessed(all_videos)
    print(f"Unprocessed: {unprocessed}")

    # Stats
    print(f"Stats: {tracker.get_stats()}")

    # Cleanup test file
    os.remove("./data/test_processed.json")
