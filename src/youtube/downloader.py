"""
Audio downloader module using yt-dlp.
Downloads audio from YouTube videos for Whisper transcription.
"""

import os
import subprocess
import time
import random
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class DownloadResult:
    """Result of an audio download."""
    success: bool
    audio_path: Optional[str]
    video_id: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "audio_path": self.audio_path,
            "video_id": self.video_id,
            "error": self.error
        }


def download_audio(
    video_url: str,
    output_dir: str = "./data/temp_audio",
    video_id: Optional[str] = None,
    retry_count: int = 3,
    use_cookies: bool = True
) -> DownloadResult:
    """
    Download audio from a YouTube video for transcription.

    Args:
        video_url: YouTube video URL or video ID
        output_dir: Directory to save the audio file
        video_id: Optional video ID (extracted from URL if not provided)
        retry_count: Number of retries on failure
        use_cookies: Whether to use browser cookies

    Returns:
        DownloadResult with success status and audio file path
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Handle both URL and video ID input
    if not video_url.startswith("http"):
        video_url = f"https://www.youtube.com/watch?v={video_url}"

    # Extract video ID if not provided
    if not video_id:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = "unknown"

    # Check if already downloaded
    for ext in [".mp3", ".m4a", ".webm", ".opus"]:
        existing_file = output_path / f"{video_id}{ext}"
        if existing_file.exists():
            return DownloadResult(
                success=True,
                audio_path=str(existing_file),
                video_id=video_id
            )

    # Output file path
    output_template = str(output_path / f"{video_id}.%(ext)s")

    # Try different strategies
    strategies = [
        # Strategy 1: Use iOS client (often bypasses restrictions)
        {
            "name": "iOS client",
            "args": [
                "--extractor-args", "youtube:player_client=ios",
                "--format", "bestaudio[ext=m4a]/bestaudio/best",
            ]
        },
        # Strategy 2: Use web client with cookies
        {
            "name": "Web client with cookies",
            "args": [
                "--cookies-from-browser", "chrome",
                "--format", "bestaudio/best",
            ]
        },
        # Strategy 3: Use android client
        {
            "name": "Android client",
            "args": [
                "--extractor-args", "youtube:player_client=android",
                "--format", "bestaudio/best",
            ]
        },
    ]

    last_error = None

    for strategy in strategies:
        for attempt in range(retry_count):
            # Add random delay between attempts (5-15 seconds)
            if attempt > 0:
                delay = random.uniform(5, 15)
                print(f"  Retry {attempt + 1}/{retry_count} after {delay:.1f}s delay...")
                time.sleep(delay)

            cmd = [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format", "mp3",
                "--audio-quality", "5",  # Medium quality (faster)
                "-o", output_template,
                "--no-playlist",
                "--no-warnings",
                "--extractor-retries", "3",
                "--socket-timeout", "30",
                "--retries", "3",
                "--fragment-retries", "3",
            ] + strategy["args"] + [video_url]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    # Find the downloaded file
                    audio_file = None
                    for ext in [".mp3", ".m4a", ".webm", ".opus"]:
                        potential_file = output_path / f"{video_id}{ext}"
                        if potential_file.exists():
                            audio_file = str(potential_file)
                            break

                    if not audio_file:
                        for file in output_path.iterdir():
                            if file.stem == video_id:
                                audio_file = str(file)
                                break

                    if audio_file:
                        return DownloadResult(
                            success=True,
                            audio_path=audio_file,
                            video_id=video_id
                        )

                last_error = result.stderr

                # If 403 error, try next strategy
                if "403" in result.stderr:
                    print(f"  {strategy['name']}: 403 error, trying next strategy...")
                    break  # Try next strategy

            except subprocess.TimeoutExpired:
                last_error = "Download timed out"
            except Exception as e:
                last_error = str(e)

    return DownloadResult(
        success=False,
        audio_path=None,
        video_id=video_id,
        error=f"All strategies failed. Last error: {last_error}"
    )


def cleanup_audio(audio_path: str) -> bool:
    """
    Delete an audio file after processing.

    Args:
        audio_path: Path to the audio file

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        path = Path(audio_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error cleaning up audio file: {e}")
        return False


def get_audio_duration(audio_path: str) -> Optional[float]:
    """
    Get the duration of an audio file in seconds using ffprobe.

    Args:
        audio_path: Path to the audio file

    Returns:
        Duration in seconds or None if failed
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
        return None

    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return None


# Global delay tracker
_last_download_time = 0


def wait_before_download(min_delay: float = 10, max_delay: float = 30):
    """Wait a random amount of time before downloading to avoid rate limits."""
    global _last_download_time

    current_time = time.time()
    elapsed = current_time - _last_download_time

    if elapsed < min_delay:
        delay = random.uniform(min_delay, max_delay)
        print(f"  Waiting {delay:.1f}s to avoid rate limiting...")
        time.sleep(delay)

    _last_download_time = time.time()


if __name__ == "__main__":
    # Test download
    print("Testing audio download...")

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    print(f"Downloading audio from: {test_url}")
    result = download_audio(test_url, output_dir="./data/temp_audio")

    if result.success:
        print(f"Success! Audio saved to: {result.audio_path}")

        duration = get_audio_duration(result.audio_path)
        if duration:
            print(f"Duration: {duration:.2f} seconds")

        cleanup_audio(result.audio_path)
        print("Cleaned up audio file")
    else:
        print(f"Failed: {result.error}")
