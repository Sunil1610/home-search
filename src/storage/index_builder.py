"""
Index builder module.
Builds index.json and index.csv from individual property files.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


def build_index_json(
    properties_dir: str = "./data/properties",
    output_path: str = "./data/index.json"
) -> Optional[str]:
    """
    Build index.json from all property files.

    Args:
        properties_dir: Directory containing property JSON files
        output_path: Path for output index.json

    Returns:
        Path to created file, or None if failed
    """
    try:
        props_path = Path(properties_dir)
        if not props_path.exists():
            print(f"Properties directory not found: {properties_dir}")
            return None

        # Load all properties
        properties = []
        for filepath in sorted(props_path.glob("*.json")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    prop = json.load(f)
                    prop["_source_file"] = filepath.name
                    properties.append(prop)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")

        # Build index document
        index_doc = {
            "generated_at": datetime.now().isoformat(),
            "total_properties": len(properties),
            "properties": properties
        }

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write index
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index_doc, f, ensure_ascii=False, indent=2)

        print(f"Built index.json with {len(properties)} properties")
        return str(output_file)

    except Exception as e:
        print(f"Error building index.json: {e}")
        return None


def flatten_property(prop: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten a property document for CSV export.

    Args:
        prop: Property document with nested structure

    Returns:
        Flat dictionary suitable for CSV
    """
    video_info = prop.get("video_info", {})
    extracted = prop.get("extracted_data", {})
    processing = prop.get("processing_info", {})

    # Extract nested fields
    dimensions = extracted.get("dimensions", {}) or {}
    price = extracted.get("price", {}) or {}
    location = extracted.get("location", {}) or {}
    config = extracted.get("configuration", {}) or {}
    construction = extracted.get("construction", {}) or {}
    contact = extracted.get("contact", {}) or {}

    return {
        # Video info
        "video_id": video_info.get("video_id", ""),
        "video_url": video_info.get("url", ""),
        "video_title": video_info.get("title", ""),
        "channel": video_info.get("channel", ""),
        "upload_date": video_info.get("upload_date", ""),
        "duration_seconds": video_info.get("duration_seconds", ""),
        "view_count": video_info.get("view_count", ""),

        # Property type
        "property_type": extracted.get("property_type", ""),

        # Dimensions
        "plot_area_sq_yards": dimensions.get("plot_area_sq_yards", ""),
        "plot_area_sq_ft": dimensions.get("plot_area_sq_ft", ""),
        "built_up_area_sq_ft": dimensions.get("built_up_area_sq_ft", ""),
        "dimensions_raw": dimensions.get("dimensions_raw", ""),

        # Price
        "price_amount": price.get("amount", ""),
        "price_currency": price.get("currency", "INR"),
        "price_per_sq_yard": price.get("per_sq_yard", ""),
        "price_negotiable": price.get("negotiable", ""),
        "price_raw": price.get("price_raw", ""),

        # Location
        "area": location.get("area", ""),
        "city": location.get("city", ""),
        "landmark": location.get("landmark", ""),
        "full_address": location.get("full_address", ""),

        # Configuration
        "bedrooms": config.get("bedrooms", ""),
        "bathrooms": config.get("bathrooms", ""),
        "floors": config.get("floors", ""),
        "facing": config.get("facing", ""),
        "age_years": config.get("age_years", ""),

        # Construction
        "construction_status": construction.get("status", ""),
        "structure_type": construction.get("structure_type", ""),
        "roof_type": construction.get("roof_type", ""),

        # Contact
        "contact_name": contact.get("name", ""),
        "contact_phone": contact.get("phone", ""),

        # Amenities (joined)
        "amenities": ", ".join(extracted.get("amenities", []) or []),

        # Metadata
        "confidence_score": extracted.get("confidence_score", ""),
        "search_location": processing.get("search_location", ""),
        "processed_at": processing.get("processed_at", ""),
        "source_file": prop.get("_source_file", "")
    }


def build_index_csv(
    properties_dir: str = "./data/properties",
    output_path: str = "./data/index.csv"
) -> Optional[str]:
    """
    Build index.csv from all property files.

    Args:
        properties_dir: Directory containing property JSON files
        output_path: Path for output index.csv

    Returns:
        Path to created file, or None if failed
    """
    try:
        props_path = Path(properties_dir)
        if not props_path.exists():
            print(f"Properties directory not found: {properties_dir}")
            return None

        # Load and flatten all properties
        rows = []
        for filepath in sorted(props_path.glob("*.json")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    prop = json.load(f)
                    prop["_source_file"] = filepath.name
                    rows.append(flatten_property(prop))
            except Exception as e:
                print(f"Error loading {filepath}: {e}")

        if not rows:
            print("No properties found to export")
            return None

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV
        fieldnames = list(rows[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Built index.csv with {len(rows)} properties")
        return str(output_file)

    except Exception as e:
        print(f"Error building index.csv: {e}")
        return None


def rebuild_all_indexes(
    properties_dir: str = "./data/properties",
    data_dir: str = "./data"
) -> Dict[str, Optional[str]]:
    """
    Rebuild both index.json and index.csv.

    Args:
        properties_dir: Directory containing property JSON files
        data_dir: Directory for output index files

    Returns:
        Dictionary with paths to created files
    """
    json_path = build_index_json(
        properties_dir=properties_dir,
        output_path=f"{data_dir}/index.json"
    )

    csv_path = build_index_csv(
        properties_dir=properties_dir,
        output_path=f"{data_dir}/index.csv"
    )

    return {
        "index_json": json_path,
        "index_csv": csv_path
    }


def get_index_stats(data_dir: str = "./data") -> Dict[str, Any]:
    """
    Get statistics about the index files.

    Args:
        data_dir: Directory containing index files

    Returns:
        Statistics dictionary
    """
    stats = {
        "index_json_exists": False,
        "index_csv_exists": False,
        "total_properties": 0,
        "last_generated": None
    }

    # Check index.json
    json_path = Path(data_dir) / "index.json"
    if json_path.exists():
        stats["index_json_exists"] = True
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
                stats["total_properties"] = index.get("total_properties", 0)
                stats["last_generated"] = index.get("generated_at")
        except Exception:
            pass

    # Check index.csv
    csv_path = Path(data_dir) / "index.csv"
    if csv_path.exists():
        stats["index_csv_exists"] = True

    return stats


if __name__ == "__main__":
    print("=== Testing Index Builder ===\n")

    # Rebuild indexes
    results = rebuild_all_indexes()

    print(f"\nResults:")
    print(f"  index.json: {results['index_json']}")
    print(f"  index.csv: {results['index_csv']}")

    # Get stats
    stats = get_index_stats()
    print(f"\nStats: {stats}")
