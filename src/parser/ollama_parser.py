"""
Ollama parser module for property data extraction.
Uses Qwen 2.5 7B to extract structured data from transcripts.
"""

import json
import re
from typing import Optional

import ollama

from .models import PropertyData, ExtractionResult
from .prompts import get_extraction_prompt, SAMPLE_TRANSCRIPT


def check_ollama_available(model: str = "qwen2.5:7b") -> bool:
    """
    Check if Ollama is running and model is available.

    Args:
        model: Model name to check

    Returns:
        True if Ollama is ready with the model
    """
    try:
        response = ollama.list()
        # Handle both dict and object response formats
        if hasattr(response, 'models'):
            models = response.models
            model_names = [m.model for m in models]
        else:
            models = response.get('models', [])
            model_names = [m.get('name', m.get('model', '')) for m in models]

        return model in model_names or any(model.split(':')[0] in m for m in model_names)
    except Exception as e:
        print(f"Ollama check failed: {e}")
        return False


def extract_json_from_response(text: str) -> Optional[dict]:
    """
    Extract JSON object from LLM response.
    Handles cases where model adds extra text around JSON.

    Args:
        text: Raw LLM response

    Returns:
        Parsed JSON dict or None
    """
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    # Look for content between { and }
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try to find JSON after common prefixes
    prefixes = ['```json', '```', 'JSON:', 'json:']
    for prefix in prefixes:
        if prefix in text:
            after_prefix = text.split(prefix, 1)[1]
            json_match = re.search(r'\{[\s\S]*\}', after_prefix)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    continue

    return None


def extract_property_data(
    transcript: str,
    video_id: str = "",
    model: str = "qwen2.5:7b",
    use_simple_prompt: bool = False,
    temperature: float = 0.1
) -> ExtractionResult:
    """
    Extract property data from a transcript using Ollama/Qwen.

    Args:
        transcript: The transcript text to extract from
        video_id: Video ID for tracking
        model: Ollama model to use
        use_simple_prompt: Use simplified prompt for faster extraction
        temperature: LLM temperature (lower = more deterministic)

    Returns:
        ExtractionResult with extracted property data
    """
    # Check Ollama is available
    if not check_ollama_available(model):
        return ExtractionResult(
            success=False,
            video_id=video_id,
            error=f"Ollama not available or model {model} not found"
        )

    # Truncate very long transcripts
    max_chars = 8000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "..."

    # Get prompts
    system_prompt, user_prompt = get_extraction_prompt(
        transcript,
        use_simple=use_simple_prompt
    )

    try:
        print(f"Extracting property data (model: {model})...")

        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            options={
                'temperature': temperature,
                'num_predict': 2000,  # Max tokens to generate
            }
        )

        raw_response = response['message']['content']

        # Parse JSON from response
        json_data = extract_json_from_response(raw_response)

        if json_data is None:
            return ExtractionResult(
                success=False,
                video_id=video_id,
                raw_response=raw_response,
                error="Failed to parse JSON from response"
            )

        # Validate with Pydantic model
        try:
            property_data = PropertyData(**json_data)
        except Exception as e:
            # Try to salvage partial data
            property_data = PropertyData()
            for key, value in json_data.items():
                if hasattr(property_data, key) and value is not None:
                    try:
                        setattr(property_data, key, value)
                    except:
                        pass

        return ExtractionResult(
            success=True,
            video_id=video_id,
            property_data=property_data,
            raw_response=raw_response
        )

    except Exception as e:
        return ExtractionResult(
            success=False,
            video_id=video_id,
            error=str(e)
        )


def extract_from_file(
    transcript_path: str,
    video_id: str = "",
    model: str = "qwen2.5:7b"
) -> ExtractionResult:
    """
    Extract property data from a transcript file.

    Args:
        transcript_path: Path to transcript JSON or text file
        video_id: Video ID for tracking
        model: Ollama model to use

    Returns:
        ExtractionResult with extracted property data
    """
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if it's JSON (transcript result) or plain text
        try:
            data = json.loads(content)
            transcript = data.get('full_text', content)
        except json.JSONDecodeError:
            transcript = content

        return extract_property_data(transcript, video_id=video_id, model=model)

    except Exception as e:
        return ExtractionResult(
            success=False,
            video_id=video_id,
            error=f"Failed to read file: {e}"
        )


if __name__ == "__main__":
    print("=== Testing Ollama Parser ===\n")

    # Check Ollama
    print("1. Checking Ollama availability...")
    if check_ollama_available():
        print("   Ollama is available with qwen2.5:7b\n")
    else:
        print("   ERROR: Ollama not available!")
        exit(1)

    # Test extraction with sample transcript
    print("2. Testing extraction with sample transcript...")
    print(f"   Transcript length: {len(SAMPLE_TRANSCRIPT)} chars\n")

    result = extract_property_data(
        SAMPLE_TRANSCRIPT,
        video_id="test_video",
        use_simple_prompt=False
    )

    if result.success:
        print("3. Extraction successful!\n")
        print("=== Extracted Property Data ===")
        if result.property_data:
            print(json.dumps(result.property_data.to_dict(), indent=2))
    else:
        print(f"3. Extraction failed: {result.error}")
        if result.raw_response:
            print(f"\nRaw response:\n{result.raw_response[:500]}")
