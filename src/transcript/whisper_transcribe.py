"""
Whisper transcription module for Telugu audio.
Uses OpenAI Whisper for speech-to-text with Telugu language support.
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class TranscriptSegment:
    """A single segment of transcribed text with timestamps."""
    start: float
    end: float
    text: str

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text
        }


@dataclass
class TranscriptResult:
    """Result of audio transcription."""
    success: bool
    video_id: str
    language: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    full_text: str = ""
    duration_seconds: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "video_id": self.video_id,
            "language": self.language,
            "segments": [s.to_dict() for s in self.segments],
            "full_text": self.full_text,
            "duration_seconds": self.duration_seconds,
            "error": self.error
        }


# Global model cache
_model_cache = {}


def load_whisper_model(model_name: str = "medium"):
    """
    Load Whisper model (cached for reuse).

    Args:
        model_name: Whisper model size (tiny, base, small, medium, large)

    Returns:
        Loaded Whisper model
    """
    global _model_cache

    if model_name not in _model_cache:
        import whisper
        print(f"Loading Whisper {model_name} model (this may take a moment)...")
        _model_cache[model_name] = whisper.load_model(model_name)
        print(f"Whisper {model_name} model loaded.")

    return _model_cache[model_name]


def transcribe_audio(
    audio_path: str,
    video_id: str = "",
    language: str = "te",
    model_name: str = "medium"
) -> TranscriptResult:
    """
    Transcribe audio file using Whisper.

    Args:
        audio_path: Path to audio file
        video_id: Video ID for tracking
        language: Language code (te=Telugu, hi=Hindi, en=English)
        model_name: Whisper model size

    Returns:
        TranscriptResult with transcription
    """
    if not os.path.exists(audio_path):
        return TranscriptResult(
            success=False,
            video_id=video_id,
            language=language,
            error=f"Audio file not found: {audio_path}"
        )

    try:
        # Load model
        model = load_whisper_model(model_name)

        print(f"Transcribing {audio_path} (language: {language})...")

        # Transcribe with language hint
        result = model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            verbose=False,
            temperature=0.0,
            condition_on_previous_text=True
        )

        # Extract segments
        segments = []
        for seg in result.get("segments", []):
            segments.append(TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip()
            ))

        # Get full text
        full_text = result.get("text", "").strip()

        # Calculate duration from last segment
        duration = segments[-1].end if segments else 0.0

        # Detected language (Whisper may auto-detect)
        detected_lang = result.get("language", language)

        print(f"Transcription complete. Duration: {duration:.1f}s, Segments: {len(segments)}")

        return TranscriptResult(
            success=True,
            video_id=video_id,
            language=detected_lang,
            segments=segments,
            full_text=full_text,
            duration_seconds=duration
        )

    except Exception as e:
        return TranscriptResult(
            success=False,
            video_id=video_id,
            language=language,
            error=str(e)
        )


def transcribe_with_auto_language(
    audio_path: str,
    video_id: str = "",
    model_name: str = "medium"
) -> TranscriptResult:
    """
    Transcribe audio with automatic language detection.
    Useful for videos that mix Telugu, Hindi, and English.

    Args:
        audio_path: Path to audio file
        video_id: Video ID for tracking
        model_name: Whisper model size

    Returns:
        TranscriptResult with transcription
    """
    if not os.path.exists(audio_path):
        return TranscriptResult(
            success=False,
            video_id=video_id,
            language="unknown",
            error=f"Audio file not found: {audio_path}"
        )

    try:
        model = load_whisper_model(model_name)

        print(f"Transcribing {audio_path} (auto language detection)...")

        # Transcribe without language hint
        result = model.transcribe(
            audio_path,
            task="transcribe",
            verbose=False,
            temperature=0.0,
            condition_on_previous_text=True
        )

        segments = []
        for seg in result.get("segments", []):
            segments.append(TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip()
            ))

        full_text = result.get("text", "").strip()
        duration = segments[-1].end if segments else 0.0
        detected_lang = result.get("language", "unknown")

        print(f"Transcription complete. Language: {detected_lang}, Duration: {duration:.1f}s")

        return TranscriptResult(
            success=True,
            video_id=video_id,
            language=detected_lang,
            segments=segments,
            full_text=full_text,
            duration_seconds=duration
        )

    except Exception as e:
        return TranscriptResult(
            success=False,
            video_id=video_id,
            language="unknown",
            error=str(e)
        )


def save_transcript(
    result: TranscriptResult,
    output_path: str
) -> bool:
    """
    Save transcript result to JSON file.

    Args:
        result: TranscriptResult to save
        output_path: Path for output JSON file

    Returns:
        True if saved successfully
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False


if __name__ == "__main__":
    # Test with downloaded audio
    test_audio = "./data/temp_audio/HRPUzE9UfJA.mp3"

    if os.path.exists(test_audio):
        print("Testing Whisper transcription with Telugu audio...")
        print(f"Audio file: {test_audio}")
        print()

        result = transcribe_audio(
            test_audio,
            video_id="HRPUzE9UfJA",
            language="te",
            model_name="medium"
        )

        if result.success:
            print(f"\n=== Transcription Result ===")
            print(f"Language: {result.language}")
            print(f"Duration: {result.duration_seconds:.1f}s")
            print(f"Segments: {len(result.segments)}")
            print(f"\n=== First 500 chars of transcript ===")
            print(result.full_text[:500])
            print("...")
        else:
            print(f"Transcription failed: {result.error}")
    else:
        print(f"Test audio not found: {test_audio}")
        print("Run audio download first to create test file.")
