#!/usr/bin/env python3
"""
Home Search CLI
Search YouTube for real estate videos, transcribe, extract property data.
"""

import json
import os
import sys
import time
import random
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.youtube.search import search_videos, search_by_location, get_video_details
from src.youtube.downloader import download_audio, cleanup_audio
from src.transcript.whisper_transcribe import transcribe_audio
from src.parser.ollama_parser import extract_property_data, check_ollama_available
from src.storage.property_store import save_property, list_properties, load_property
from src.storage.dedup import get_tracker, is_video_processed, mark_video_processed
from src.storage.index_builder import rebuild_all_indexes, get_index_stats

console = Console()

# Default configuration
DEFAULT_CONFIG = {
    "locations": ["LB Nagar"],
    "query_templates": [
        "independent house for sale {location}",
        "individual house {location}",
        "house for sale {location} Hyderabad"
    ],
    "whisper_model": "medium",
    "llm_model": "qwen2.5:7b",
    "language": "te"
}


def load_config() -> dict:
    """Load configuration from config.json or use defaults."""
    config_path = Path("./config.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG


def is_garbage_transcript(text: str) -> bool:
    """
    Detect if a transcript is garbage (Whisper hallucination).
    Returns True if the transcript appears to be repetitive nonsense.
    """
    if not text or len(text) < 50:
        return True

    # Check for repetitive patterns
    words = text.split()
    if len(words) < 10:
        return True

    # Count unique words vs total words
    unique_words = set(words)
    uniqueness_ratio = len(unique_words) / len(words)

    # If less than 20% unique words, it's probably garbage
    if uniqueness_ratio < 0.2:
        return True

    # Check for specific hallucination patterns
    hallucination_patterns = [
        "పాపరిటి", "మాలికి", "కికికి", "టిటిటి",
        "ististist", "alalal", "inging"
    ]
    for pattern in hallucination_patterns:
        if pattern in text.lower():
            return True

    return False


def process_single_video(
    video_url: str,
    location: str = "",
    config: dict = None,
    force: bool = False
) -> bool:
    """
    Process a single video: download → transcribe → extract → save.

    Returns True if successful, False otherwise.
    """
    config = config or DEFAULT_CONFIG

    # Get video details
    console.print(f"\n[cyan]Getting video details...[/cyan]")
    video_info = get_video_details(video_url)

    if not video_info:
        console.print(f"[red]Failed to get video details[/red]")
        return False

    video_id = video_info.video_id
    console.print(f"[green]Video:[/green] {video_info.title}")
    console.print(f"[green]Channel:[/green] {video_info.channel}")
    console.print(f"[green]Duration:[/green] {video_info.duration_seconds}s")

    # Check if already processed
    if not force and is_video_processed(video_id):
        console.print(f"[yellow]Video already processed. Use --force to reprocess.[/yellow]")
        return True

    # Skip very short videos (likely just music/intro)
    if video_info.duration_seconds < 30:
        console.print(f"[yellow]Skipping very short video (<30s)[/yellow]")
        mark_video_processed(video_id, success=False, location=location)
        return False

    # Download audio
    console.print(f"\n[cyan]Downloading audio...[/cyan]")
    download_result = download_audio(video_url, video_id=video_id)

    if not download_result.success:
        console.print(f"[red]Download failed:[/red] {download_result.error}")
        mark_video_processed(video_id, success=False, location=location)
        return False

    audio_path = download_result.audio_path
    console.print(f"[green]Audio saved:[/green] {audio_path}")

    try:
        # Transcribe
        console.print(f"\n[cyan]Transcribing (this may take a few minutes)...[/cyan]")
        transcript_result = transcribe_audio(
            audio_path,
            video_id=video_id,
            language=config.get("language", "te"),
            model_name=config.get("whisper_model", "medium")
        )

        transcript_text = ""
        if transcript_result.success:
            transcript_text = transcript_result.full_text
            console.print(f"[green]Transcription complete:[/green] {len(transcript_text)} chars")

            # Check if transcript is garbage
            if is_garbage_transcript(transcript_text):
                console.print(f"[yellow]Transcript appears to be low quality (Whisper hallucination)[/yellow]")
                transcript_text = ""  # Don't use garbage transcript

        # Build combined text from description + title + transcript
        # Video description often has more reliable info than audio
        combined_text = f"""
VIDEO TITLE: {video_info.title}

VIDEO DESCRIPTION:
{video_info.description or 'No description'}

TRANSCRIPT:
{transcript_text if transcript_text else 'No usable transcript available'}
"""

        console.print(f"[cyan]Using description + title + transcript for extraction[/cyan]")

        # Extract property data
        console.print(f"\n[cyan]Extracting property data...[/cyan]")
        extraction_result = extract_property_data(
            combined_text,
            video_id=video_id,
            model=config.get("llm_model", "qwen2.5:7b")
        )

        if not extraction_result.success:
            console.print(f"[red]Extraction failed:[/red] {extraction_result.error}")
            mark_video_processed(video_id, success=False, location=location)
            return False

        # Save property
        console.print(f"\n[cyan]Saving property data...[/cyan]")
        # Use combined text for summary (prefer description if transcript is garbage)
        summary_text = video_info.description or transcript_text or video_info.title
        filepath = save_property(
            video_info=video_info,
            property_data=extraction_result.property_data,
            transcript_summary=summary_text[:500] if summary_text else "",
            search_location=location
        )

        if filepath:
            console.print(f"[green]Saved:[/green] {filepath}")
            mark_video_processed(video_id, success=True, location=location)
            return True
        else:
            console.print(f"[red]Failed to save property[/red]")
            mark_video_processed(video_id, success=False, location=location)
            return False

    finally:
        # Cleanup audio file
        if audio_path and os.path.exists(audio_path):
            cleanup_audio(audio_path)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Home Search - YouTube Real Estate Video Analyzer"""
    pass


@cli.command()
@click.option("--location", "-l", default="LB Nagar", help="Location to search")
@click.option("--max-videos", "-m", default=10, help="Maximum videos to process")
@click.option("--skip-processed", is_flag=True, default=True, help="Skip already processed videos")
def search(location: str, max_videos: int, skip_processed: bool):
    """Search YouTube and process real estate videos."""
    config = load_config()

    console.print(f"\n[bold cyan]Home Search - Real Estate Video Analyzer[/bold cyan]")
    console.print(f"Location: [green]{location}[/green]")
    console.print(f"Max videos: [green]{max_videos}[/green]")

    # Check Ollama
    if not check_ollama_available():
        console.print("[red]Error: Ollama not running or qwen2.5:7b not available[/red]")
        console.print("Run: ollama pull qwen2.5:7b")
        return

    # Search for videos
    console.print(f"\n[cyan]Searching YouTube...[/cyan]")

    query_templates = config.get("query_templates", DEFAULT_CONFIG["query_templates"])
    videos = search_by_location(
        location=location,
        query_templates=query_templates,
        max_results_per_query=max_videos
    )

    console.print(f"[green]Found {len(videos)} videos[/green]")

    if not videos:
        console.print("[yellow]No videos found for this location[/yellow]")
        return

    # Filter to unprocessed
    if skip_processed:
        tracker = get_tracker()
        unprocessed = [v for v in videos if not tracker.is_processed(v.video_id)]
        console.print(f"[green]Unprocessed: {len(unprocessed)} videos[/green]")
        videos = unprocessed[:max_videos]
    else:
        videos = videos[:max_videos]

    if not videos:
        console.print("[yellow]All videos already processed![/yellow]")
        return

    # Process each video
    success_count = 0
    fail_count = 0

    for i, video in enumerate(videos, 1):
        # Add delay between videos to avoid rate limiting (except for first video)
        if i > 1:
            delay = random.uniform(15, 30)
            console.print(f"\n[dim]Waiting {delay:.0f}s before next video to avoid rate limiting...[/dim]")
            time.sleep(delay)

        console.print(f"\n[bold]━━━ Video {i}/{len(videos)} ━━━[/bold]")
        console.print(f"[blue]{video.title}[/blue]")

        try:
            success = process_single_video(
                video.url,
                location=location,
                config=config
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            console.print(f"[red]Error processing video: {e}[/red]")
            fail_count += 1

    # Summary
    console.print(f"\n[bold cyan]━━━ Processing Complete ━━━[/bold cyan]")
    console.print(f"[green]Success: {success_count}[/green]")
    console.print(f"[red]Failed: {fail_count}[/red]")

    # Rebuild indexes
    if success_count > 0:
        console.print(f"\n[cyan]Rebuilding indexes...[/cyan]")
        rebuild_all_indexes()
        console.print(f"[green]Indexes updated[/green]")


@cli.command("process-video")
@click.argument("video_url")
@click.option("--location", "-l", default="", help="Search location (for metadata)")
@click.option("--force", "-f", is_flag=True, help="Force reprocess even if already done")
def process_video(video_url: str, location: str, force: bool):
    """Process a single YouTube video by URL."""
    config = load_config()

    console.print(f"\n[bold cyan]Processing Single Video[/bold cyan]")

    # Check Ollama
    if not check_ollama_available():
        console.print("[red]Error: Ollama not running or qwen2.5:7b not available[/red]")
        return

    success = process_single_video(video_url, location=location, config=config, force=force)

    if success:
        console.print(f"\n[green]✓ Video processed successfully[/green]")
        rebuild_all_indexes()
    else:
        console.print(f"\n[red]✗ Video processing failed[/red]")


@cli.command("rebuild-index")
def rebuild_index():
    """Rebuild index.json and index.csv from property files."""
    console.print(f"\n[cyan]Rebuilding indexes...[/cyan]")

    results = rebuild_all_indexes()

    if results["index_json"]:
        console.print(f"[green]Created:[/green] {results['index_json']}")
    if results["index_csv"]:
        console.print(f"[green]Created:[/green] {results['index_csv']}")

    stats = get_index_stats()
    console.print(f"\n[green]Total properties:[/green] {stats['total_properties']}")


@cli.command()
def stats():
    """Show processing statistics."""
    console.print(f"\n[bold cyan]Processing Statistics[/bold cyan]")

    # Get tracker stats
    tracker = get_tracker()
    tracker_stats = tracker.get_stats()

    table = Table(title="Video Processing")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Processed", str(tracker_stats["total_processed"]))
    table.add_row("Total Failed", str(tracker_stats["total_failed"]))
    table.add_row("Unique Videos", str(tracker_stats["unique_videos"]))
    table.add_row("Last Updated", tracker_stats.get("last_updated", "Never") or "Never")

    console.print(table)

    # Index stats
    index_stats = get_index_stats()

    table2 = Table(title="Index Files")
    table2.add_column("File", style="cyan")
    table2.add_column("Status", style="green")

    table2.add_row("index.json", "✓" if index_stats["index_json_exists"] else "✗")
    table2.add_row("index.csv", "✓" if index_stats["index_csv_exists"] else "✗")
    table2.add_row("Properties in Index", str(index_stats["total_properties"]))

    console.print(table2)


@cli.command("list")
@click.option("--limit", "-n", default=20, help="Number of properties to show")
def list_props(limit: int):
    """List processed properties."""
    console.print(f"\n[bold cyan]Processed Properties[/bold cyan]")

    files = list_properties()

    if not files:
        console.print("[yellow]No properties found[/yellow]")
        return

    table = Table()
    table.add_column("#", style="dim")
    table.add_column("Video ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Price", style="yellow")
    table.add_column("Area", style="magenta")
    table.add_column("Location")

    for i, filepath in enumerate(files[:limit], 1):
        prop = load_property(filepath)
        if not prop:
            continue

        video_id = prop.get("video_info", {}).get("video_id", "?")
        extracted = prop.get("extracted_data", {})

        prop_type = extracted.get("property_type", "-")

        price_data = extracted.get("price", {}) or {}
        price = price_data.get("amount", "-")
        if price and price != "-":
            price = f"₹{int(price):,}"

        dims = extracted.get("dimensions", {}) or {}
        area = dims.get("plot_area_sq_yards", "-")
        if area and area != "-":
            area = f"{area} sq.yd"

        loc = extracted.get("location", {}) or {}
        location = loc.get("area", "-")

        table.add_row(str(i), video_id, str(prop_type), str(price), str(area), str(location))

    console.print(table)
    console.print(f"\nShowing {min(limit, len(files))} of {len(files)} properties")


@cli.command()
def check():
    """Check if all dependencies are available."""
    console.print(f"\n[bold cyan]Dependency Check[/bold cyan]")

    checks = []

    # Check yt-dlp
    import subprocess
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=10)
        checks.append(("yt-dlp", True, result.stdout.decode().strip()))
    except Exception as e:
        checks.append(("yt-dlp", False, str(e)))

    # Check ffmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
        version = result.stdout.decode().split('\n')[0]
        checks.append(("ffmpeg", True, version[:50]))
    except Exception as e:
        checks.append(("ffmpeg", False, str(e)))

    # Check Ollama
    try:
        available = check_ollama_available()
        checks.append(("Ollama (qwen2.5:7b)", available, "Ready" if available else "Not available"))
    except Exception as e:
        checks.append(("Ollama", False, str(e)))

    # Check Whisper
    try:
        import whisper
        checks.append(("Whisper", True, f"Installed"))
    except ImportError:
        checks.append(("Whisper", False, "Not installed"))

    # Display results
    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    table.add_column("Details", style="dim")

    for name, ok, details in checks:
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, status, details[:60])

    console.print(table)

    all_ok = all(c[1] for c in checks)
    if all_ok:
        console.print(f"\n[green]All dependencies ready![/green]")
    else:
        console.print(f"\n[red]Some dependencies missing. Please install them first.[/red]")


@cli.group()
def schedule():
    """Manage scheduled runs."""
    pass


@schedule.command("install")
def schedule_install():
    """Install the launchd job for daily runs at midnight."""
    import shutil

    console.print(f"\n[bold cyan]Installing Scheduled Job[/bold cyan]")

    source_plist = Path("./scripts/com.homesearch.daily.plist")
    target_dir = Path.home() / "Library" / "LaunchAgents"
    target_plist = target_dir / "com.homesearch.daily.plist"

    if not source_plist.exists():
        console.print(f"[red]Error: Plist file not found at {source_plist}[/red]")
        return

    # Create LaunchAgents directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy plist file
    shutil.copy(source_plist, target_plist)
    console.print(f"[green]Copied plist to:[/green] {target_plist}")

    # Load the job
    import subprocess
    result = subprocess.run(
        ["launchctl", "load", str(target_plist)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        console.print(f"[green]✓ Scheduled job installed![/green]")
        console.print(f"  Will run daily at 12:00 AM")
    else:
        console.print(f"[yellow]Warning: {result.stderr}[/yellow]")
        console.print(f"[green]Plist copied. Load manually with:[/green]")
        console.print(f"  launchctl load {target_plist}")


@schedule.command("uninstall")
def schedule_uninstall():
    """Uninstall the launchd job."""
    import subprocess

    console.print(f"\n[bold cyan]Uninstalling Scheduled Job[/bold cyan]")

    target_plist = Path.home() / "Library" / "LaunchAgents" / "com.homesearch.daily.plist"

    if not target_plist.exists():
        console.print(f"[yellow]Job not installed[/yellow]")
        return

    # Unload the job
    subprocess.run(
        ["launchctl", "unload", str(target_plist)],
        capture_output=True,
        text=True
    )

    # Remove the plist
    target_plist.unlink()
    console.print(f"[green]✓ Scheduled job uninstalled[/green]")


@schedule.command("status")
def schedule_status():
    """Show status of scheduled job."""
    import subprocess

    console.print(f"\n[bold cyan]Scheduled Job Status[/bold cyan]")

    # Check if plist exists
    target_plist = Path.home() / "Library" / "LaunchAgents" / "com.homesearch.daily.plist"
    installed = target_plist.exists()

    # Check if job is loaded
    result = subprocess.run(
        ["launchctl", "list", "com.homesearch.daily"],
        capture_output=True,
        text=True
    )
    loaded = result.returncode == 0

    table = Table()
    table.add_column("Check", style="cyan")
    table.add_column("Status")

    table.add_row("Plist installed", "[green]✓[/green]" if installed else "[red]✗[/red]")
    table.add_row("Job loaded", "[green]✓[/green]" if loaded else "[red]✗[/red]")
    table.add_row("Schedule", "Daily at 12:00 AM" if loaded else "-")

    console.print(table)

    # Show run history
    try:
        from src.scheduler.runner import RunHistory
        history = RunHistory()
        stats = history.get_stats()

        table2 = Table(title="Run History")
        table2.add_column("Metric", style="cyan")
        table2.add_column("Value", style="green")

        table2.add_row("Total runs", str(stats["total_runs"]))
        table2.add_row("Successful", str(stats["successful_runs"]))
        table2.add_row("Failed", str(stats["failed_runs"]))
        table2.add_row("Last run", stats.get("last_run", "Never") or "Never")

        console.print(table2)
    except Exception:
        pass

    if not installed:
        console.print(f"\n[yellow]Run 'python3 main.py schedule install' to set up daily runs[/yellow]")


@schedule.command("run")
@click.option("--location", "-l", default="LB Nagar", help="Search location")
@click.option("--max-videos", "-m", default=10, help="Max videos to process")
@click.option("--force", "-f", is_flag=True, help="Force run even if already ran today")
def schedule_run(location: str, max_videos: int, force: bool):
    """Run the scheduled job manually."""
    from src.scheduler.runner import run_scheduled_job

    console.print(f"\n[bold cyan]Running Scheduled Job[/bold cyan]")
    console.print(f"Location: {location}")
    console.print(f"Max videos: {max_videos}")

    success = run_scheduled_job(
        location=location,
        max_videos=max_videos,
        force=force
    )

    if success:
        console.print(f"\n[green]✓ Scheduled job completed successfully[/green]")
    else:
        console.print(f"\n[red]✗ Scheduled job failed[/red]")


@cli.command()
def dashboard():
    """Launch the Streamlit dashboard."""
    import subprocess

    console.print(f"\n[bold cyan]Launching Dashboard...[/bold cyan]")
    console.print(f"Opening in browser at http://localhost:8501")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")

    subprocess.run(["streamlit", "run", "dashboard.py"])


if __name__ == "__main__":
    cli()
