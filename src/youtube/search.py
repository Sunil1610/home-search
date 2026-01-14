"""
YouTube search module using yt-dlp.
Searches for real estate videos based on location and query templates.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from pathlib import Path


@dataclass
class VideoMetadata:
    """Metadata for a YouTube video."""
    video_id: str
    url: str
    title: str
    channel: str
    channel_url: Optional[str]
    upload_date: Optional[str]
    duration_seconds: int
    view_count: Optional[int]
    description: Optional[str]
    thumbnail_url: Optional[str]

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "url": self.url,
            "title": self.title,
            "channel": self.channel,
            "channel_url": self.channel_url,
            "upload_date": self.upload_date,
            "duration_seconds": self.duration_seconds,
            "view_count": self.view_count,
            "description": self.description,
            "thumbnail_url": self.thumbnail_url
        }


def search_videos(
    query: str,
    max_results: int = 50,
    upload_date_filter: Optional[str] = None
) -> List[VideoMetadata]:
    """
    Search YouTube for videos matching the query.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default 50)
        upload_date_filter: Filter by upload date (today, week, month, year)

    Returns:
        List of VideoMetadata objects
    """
    # Build yt-dlp command
    search_query = f"ytsearch{max_results}:{query}"

    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--no-download",
        search_query
    ]

    # Add date filter if specified
    if upload_date_filter:
        date_filters = {
            "today": "--dateafter today",
            "week": "--dateafter now-1week",
            "month": "--dateafter now-1month",
            "year": "--dateafter now-1year",
            "this_year": "--dateafter now-1year"
        }
        if upload_date_filter in date_filters:
            filter_arg = date_filters[upload_date_filter]
            cmd.extend(filter_arg.split())

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}")
            return []

        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                video = VideoMetadata(
                    video_id=data.get("id", ""),
                    url=data.get("url", f"https://youtube.com/watch?v={data.get('id', '')}"),
                    title=data.get("title", ""),
                    channel=data.get("channel", data.get("uploader", "")),
                    channel_url=data.get("channel_url", data.get("uploader_url")),
                    upload_date=data.get("upload_date"),
                    duration_seconds=data.get("duration", 0) or 0,
                    view_count=data.get("view_count"),
                    description=data.get("description"),
                    thumbnail_url=data.get("thumbnail")
                )
                videos.append(video)
            except json.JSONDecodeError:
                continue

        return videos

    except subprocess.TimeoutExpired:
        print("Search timed out after 120 seconds")
        return []
    except Exception as e:
        print(f"Error during search: {e}")
        return []


def search_by_location(
    location: str,
    query_templates: List[str],
    max_results_per_query: int = 20
) -> List[VideoMetadata]:
    """
    Search for real estate videos in a specific location using multiple query templates.

    Args:
        location: Location name (e.g., "LB Nagar")
        query_templates: List of query templates with {location} placeholder
        max_results_per_query: Max results per query template

    Returns:
        Deduplicated list of VideoMetadata objects
    """
    all_videos = {}  # Use dict to deduplicate by video_id

    for template in query_templates:
        query = template.format(location=location)
        print(f"Searching: {query}")

        videos = search_videos(query, max_results=max_results_per_query)

        for video in videos:
            if video.video_id and video.video_id not in all_videos:
                all_videos[video.video_id] = video

    return list(all_videos.values())


def get_video_details(video_url: str) -> Optional[VideoMetadata]:
    """
    Get detailed metadata for a single video.

    Args:
        video_url: YouTube video URL

    Returns:
        VideoMetadata object or None if failed
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        video_url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}")
            return None

        data = json.loads(result.stdout)

        return VideoMetadata(
            video_id=data.get("id", ""),
            url=data.get("webpage_url", video_url),
            title=data.get("title", ""),
            channel=data.get("channel", data.get("uploader", "")),
            channel_url=data.get("channel_url", data.get("uploader_url")),
            upload_date=data.get("upload_date"),
            duration_seconds=data.get("duration", 0) or 0,
            view_count=data.get("view_count"),
            description=data.get("description"),
            thumbnail_url=data.get("thumbnail")
        )

    except Exception as e:
        print(f"Error getting video details: {e}")
        return None


if __name__ == "__main__":
    # Test search
    print("Testing YouTube search for 'independent house for sale LB Nagar'...")
    videos = search_videos("independent house for sale LB Nagar", max_results=5)

    print(f"\nFound {len(videos)} videos:")
    for i, video in enumerate(videos, 1):
        print(f"\n{i}. {video.title}")
        print(f"   Channel: {video.channel}")
        print(f"   Duration: {video.duration_seconds}s")
        print(f"   URL: {video.url}")
