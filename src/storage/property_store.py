"""
Property storage module.
Saves and loads individual property JSON files.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..parser.models import PropertyData, ExtractionResult
from ..youtube.search import VideoMetadata


def get_property_filename(video_id: str, date: Optional[str] = None) -> str:
    """
    Generate filename for a property JSON file.

    Args:
        video_id: YouTube video ID
        date: Optional date string (defaults to today)

    Returns:
        Filename in format: {date}_{video_id}.json
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return f"{date}_{video_id}.json"


def save_property(
    video_info: VideoMetadata,
    property_data: PropertyData,
    transcript_summary: str = "",
    output_dir: str = "./data/properties",
    search_location: str = ""
) -> Optional[str]:
    """
    Save a property to a JSON file.

    Args:
        video_info: Video metadata from YouTube
        property_data: Extracted property data
        transcript_summary: Optional transcript summary
        output_dir: Directory to save to
        search_location: Search location used

    Returns:
        Path to saved file, or None if failed
    """
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = get_property_filename(video_info.video_id)
        filepath = output_path / filename

        # Build property document
        document = {
            "video_info": video_info.to_dict(),
            "extracted_data": property_data.to_dict() if property_data else {},
            "transcript_summary": transcript_summary[:500] if transcript_summary else "",
            "processing_info": {
                "processed_at": datetime.now().isoformat(),
                "search_location": search_location,
                "transcript_source": "whisper_medium",
                "llm_model": "qwen2.5:7b"
            }
        }

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)

        return str(filepath)

    except Exception as e:
        print(f"Error saving property: {e}")
        return None


def load_property(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load a property from a JSON file.

    Args:
        filepath: Path to property JSON file

    Returns:
        Property document dict, or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading property {filepath}: {e}")
        return None


def list_properties(properties_dir: str = "./data/properties") -> List[str]:
    """
    List all property JSON files in the directory.

    Args:
        properties_dir: Directory containing property files

    Returns:
        List of file paths
    """
    path = Path(properties_dir)
    if not path.exists():
        return []

    return sorted([str(f) for f in path.glob("*.json")])


def load_all_properties(properties_dir: str = "./data/properties") -> List[Dict[str, Any]]:
    """
    Load all properties from directory.

    Args:
        properties_dir: Directory containing property files

    Returns:
        List of property documents
    """
    properties = []
    for filepath in list_properties(properties_dir):
        prop = load_property(filepath)
        if prop:
            properties.append(prop)
    return properties


def delete_property(video_id: str, properties_dir: str = "./data/properties") -> bool:
    """
    Delete a property file by video ID.

    Args:
        video_id: YouTube video ID
        properties_dir: Directory containing property files

    Returns:
        True if deleted, False otherwise
    """
    path = Path(properties_dir)
    for filepath in path.glob(f"*_{video_id}.json"):
        try:
            filepath.unlink()
            return True
        except Exception as e:
            print(f"Error deleting {filepath}: {e}")
            return False
    return False


if __name__ == "__main__":
    # Test storage
    from ..youtube.search import VideoMetadata
    from ..parser.models import PropertyData, Dimensions, Price, Location

    print("=== Testing Property Storage ===\n")

    # Create test data
    video = VideoMetadata(
        video_id="test123",
        url="https://youtube.com/watch?v=test123",
        title="Test Property Video",
        channel="Test Channel",
        channel_url=None,
        upload_date="2026-01-14",
        duration_seconds=300,
        view_count=1000,
        description="Test description",
        thumbnail_url=None
    )

    property_data = PropertyData(
        property_type="independent_house",
        dimensions=Dimensions(plot_area_sq_yards=150),
        price=Price(amount=10000000),
        location=Location(area="LB Nagar", city="Hyderabad")
    )

    # Save
    filepath = save_property(
        video,
        property_data,
        transcript_summary="Test transcript...",
        search_location="LB Nagar"
    )

    if filepath:
        print(f"Saved to: {filepath}")

        # Load
        loaded = load_property(filepath)
        if loaded:
            print(f"Loaded: {loaded['video_info']['title']}")
            print(f"Price: {loaded['extracted_data'].get('price', {}).get('amount')}")
