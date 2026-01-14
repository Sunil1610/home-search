"""
Audio downloader module using yt-dlp.
Downloads audio from YouTube videos for Whisper transcription.
"""

import os
import subprocess
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
    video_id: Optional[str] = None
) -> DownloadResult:
    """
    Download audio from a YouTube video for transcription.

    Args:
        video_url: YouTube video URL or video ID
        output_dir: Directory to save the audio file
        video_id: Optional video ID (extracted from URL if not provided)

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

    # Output file path (will be .m4a or .mp3 depending on source)
    output_template = str(output_path / f"{video_id}.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",  # Extract audio
        "--audio-format", "mp3",  # Convert to mp3 for compatibility
        "--audio-quality", "0",  # Best quality
        "-o", output_template,
        "--no-playlist",  # Don't download playlist if URL is part of one
        "--no-warnings",
        "--cookies-from-browser", "chrome",  # Use Chrome cookies for auth
        "--extractor-retries", "3",  # Retry on failure
        video_url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for download
        )

        if result.returncode != 0:
            return DownloadResult(
                success=False,
                audio_path=None,
                video_id=video_id,
                error=result.stderr
            )

        # Find the downloaded file
        audio_file = None
        for ext in [".mp3", ".m4a", ".webm", ".opus"]:
            potential_file = output_path / f"{video_id}{ext}"
            if potential_file.exists():
                audio_file = str(potential_file)
                break

        if not audio_file:
            # Try to find any file with the video_id prefix
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
        else:
            return DownloadResult(
                success=False,
                audio_path=None,
                video_id=video_id,
                error="Audio file not found after download"
            )

    except subprocess.TimeoutExpired:
        return DownloadResult(
            success=False,
            audio_path=None,
            video_id=video_id,
            error="Download timed out after 5 minutes"
        )
    except Exception as e:
        return DownloadResult(
            success=False,
            audio_path=None,
            video_id=video_id,
            error=str(e)
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


if __name__ == "__main__":
    # Test download
    print("Testing audio download...")

    # Test with a short video (replace with actual test video)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Example

    print(f"Downloading audio from: {test_url}")
    result = download_audio(test_url, output_dir="./data/temp_audio")

    if result.success:
        print(f"Success! Audio saved to: {result.audio_path}")

        duration = get_audio_duration(result.audio_path)
        if duration:
            print(f"Duration: {duration:.2f} seconds")

        # Cleanup
        cleanup_audio(result.audio_path)
        print("Cleaned up audio file")
    else:
        print(f"Failed: {result.error}")
