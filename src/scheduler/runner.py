"""
Scheduled runner module.
Handles lock file management and scheduled execution.
"""

import json
import os
import sys
import fcntl
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class LockFile:
    """Manages a lock file to prevent duplicate runs."""

    def __init__(self, lock_path: str = "./data/.lock"):
        self.lock_path = Path(lock_path)
        self.lock_file = None
        self.locked = False

    def acquire(self) -> bool:
        """
        Try to acquire the lock.

        Returns:
            True if lock acquired, False if already locked
        """
        try:
            # Ensure directory exists
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)

            # Open lock file
            self.lock_file = open(self.lock_path, 'w')

            # Try to acquire exclusive lock (non-blocking)
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.locked = True
            return True

        except (IOError, OSError):
            # Lock already held by another process
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            return False

    def release(self) -> None:
        """Release the lock."""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
            except Exception:
                pass
            finally:
                self.lock_file = None
                self.locked = False

            # Remove lock file
            try:
                self.lock_path.unlink()
            except Exception:
                pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class RunHistory:
    """Tracks run history to avoid duplicate processing."""

    def __init__(self, history_path: str = "./data/run_history.json"):
        self.history_path = Path(history_path)
        self.data: Dict[str, Any] = {
            "runs": [],
            "last_successful_run": None,
            "last_run": None
        }
        self._load()

    def _load(self) -> None:
        """Load history from file."""
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r') as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def _save(self) -> None:
        """Save history to file."""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save run history: {e}")

    def record_run(self, success: bool, location: str, videos_processed: int) -> None:
        """Record a run in history."""
        run_record = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "location": location,
            "videos_processed": videos_processed
        }

        self.data["runs"].append(run_record)
        self.data["last_run"] = run_record["timestamp"]

        if success:
            self.data["last_successful_run"] = run_record["timestamp"]

        # Keep only last 100 runs
        if len(self.data["runs"]) > 100:
            self.data["runs"] = self.data["runs"][-100:]

        self._save()

    def was_run_today(self) -> bool:
        """Check if a successful run happened today."""
        last_run = self.data.get("last_successful_run")
        if not last_run:
            return False

        try:
            last_run_date = datetime.fromisoformat(last_run).date()
            return last_run_date == datetime.now().date()
        except Exception:
            return False

    def get_last_run(self) -> Optional[str]:
        """Get timestamp of last run."""
        return self.data.get("last_run")

    def get_stats(self) -> Dict[str, Any]:
        """Get run statistics."""
        runs = self.data.get("runs", [])
        successful = sum(1 for r in runs if r.get("success"))
        failed = len(runs) - successful

        return {
            "total_runs": len(runs),
            "successful_runs": successful,
            "failed_runs": failed,
            "last_run": self.data.get("last_run"),
            "last_successful_run": self.data.get("last_successful_run")
        }


class ScheduledRunner:
    """Handles scheduled execution with lock management."""

    def __init__(
        self,
        lock_path: str = "./data/.lock",
        history_path: str = "./data/run_history.json",
        log_dir: str = "./logs"
    ):
        self.lock = LockFile(lock_path)
        self.history = RunHistory(history_path)
        self.log_dir = Path(log_dir)
        self.logger = None

    def setup_logging(self) -> logging.Logger:
        """Set up logging for this run."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

        log_file = self.log_dir / f"scheduled_{datetime.now().strftime('%Y-%m-%d')}.log"

        # Create logger
        logger = logging.getLogger("home_search_scheduler")
        logger.setLevel(logging.INFO)

        # Clear existing handlers
        logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(file_formatter)
        logger.addHandler(console_handler)

        self.logger = logger
        return logger

    def should_run(self, force: bool = False) -> tuple[bool, str]:
        """
        Check if we should run.

        Returns:
            (should_run, reason)
        """
        if force:
            return True, "Forced run requested"

        # Check if already run today
        if self.history.was_run_today():
            return False, "Already ran successfully today"

        return True, "No run today, proceeding"

    def run(
        self,
        location: str = "LB Nagar",
        max_videos: int = 10,
        force: bool = False
    ) -> bool:
        """
        Execute a scheduled run.

        Args:
            location: Search location
            max_videos: Maximum videos to process
            force: Force run even if already ran today

        Returns:
            True if successful
        """
        logger = self.setup_logging()

        logger.info("=" * 50)
        logger.info("Home Search - Scheduled Run")
        logger.info(f"Location: {location}")
        logger.info(f"Max videos: {max_videos}")
        logger.info("=" * 50)

        # Check if we should run
        should_run, reason = self.should_run(force)
        logger.info(f"Run check: {reason}")

        if not should_run:
            logger.info("Skipping run")
            return True

        # Try to acquire lock
        logger.info("Acquiring lock...")
        if not self.lock.acquire():
            logger.warning("Could not acquire lock - another instance is running")
            return False

        logger.info("Lock acquired")

        try:
            # Import here to avoid circular imports
            from src.youtube.search import search_by_location
            from src.storage.dedup import get_tracker
            from src.parser.ollama_parser import check_ollama_available

            # Check Ollama
            if not check_ollama_available():
                logger.error("Ollama not available")
                self.history.record_run(False, location, 0)
                return False

            # Load config
            config_path = Path("./config.json")
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
            else:
                config = {
                    "query_templates": [
                        "independent house for sale {location}",
                        "individual house {location}",
                        "house for sale {location} Hyderabad"
                    ]
                }

            # Search for videos
            logger.info("Searching YouTube...")
            query_templates = config.get("query_templates", config.get("search", {}).get("query_templates", []))
            videos = search_by_location(
                location=location,
                query_templates=query_templates,
                max_results_per_query=max_videos
            )

            logger.info(f"Found {len(videos)} videos")

            if not videos:
                logger.info("No videos found")
                self.history.record_run(True, location, 0)
                return True

            # Filter to unprocessed
            tracker = get_tracker()
            unprocessed = [v for v in videos if not tracker.is_processed(v.video_id)]
            logger.info(f"Unprocessed: {len(unprocessed)} videos")

            if not unprocessed:
                logger.info("All videos already processed")
                self.history.record_run(True, location, 0)
                return True

            # Process videos
            from main import process_single_video

            videos_to_process = unprocessed[:max_videos]
            success_count = 0
            fail_count = 0

            for i, video in enumerate(videos_to_process, 1):
                logger.info(f"Processing video {i}/{len(videos_to_process)}: {video.title}")

                try:
                    success = process_single_video(
                        video.url,
                        location=location,
                        config=config
                    )
                    if success:
                        success_count += 1
                        logger.info(f"Video {i}: SUCCESS")
                    else:
                        fail_count += 1
                        logger.warning(f"Video {i}: FAILED")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Video {i}: ERROR - {e}")

            # Rebuild indexes
            if success_count > 0:
                from src.storage.index_builder import rebuild_all_indexes
                logger.info("Rebuilding indexes...")
                rebuild_all_indexes()

            # Record run
            total_processed = success_count + fail_count
            self.history.record_run(
                success=fail_count == 0,
                location=location,
                videos_processed=success_count
            )

            logger.info("=" * 50)
            logger.info(f"Run complete: {success_count} success, {fail_count} failed")
            logger.info("=" * 50)

            return fail_count == 0

        except Exception as e:
            logger.error(f"Run failed with error: {e}")
            self.history.record_run(False, location, 0)
            return False

        finally:
            logger.info("Releasing lock...")
            self.lock.release()


def run_scheduled_job(
    location: str = "LB Nagar",
    max_videos: int = 10,
    force: bool = False
) -> bool:
    """
    Convenience function to run a scheduled job.

    Args:
        location: Search location
        max_videos: Maximum videos to process
        force: Force run even if already ran today

    Returns:
        True if successful
    """
    runner = ScheduledRunner()
    return runner.run(location=location, max_videos=max_videos, force=force)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run scheduled home search job")
    parser.add_argument("--location", "-l", default="LB Nagar", help="Search location")
    parser.add_argument("--max-videos", "-m", type=int, default=10, help="Max videos")
    parser.add_argument("--force", "-f", action="store_true", help="Force run")

    args = parser.parse_args()

    success = run_scheduled_job(
        location=args.location,
        max_videos=args.max_videos,
        force=args.force
    )

    sys.exit(0 if success else 1)
