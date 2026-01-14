# YouTube Real Estate Video Scraper & Analyzer

## Project Overview

Build an automated tool that searches YouTube for real estate videos in configurable locations, extracts transcripts, and uses AI to parse property details into structured JSON data for easy analysis.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Configuration Layer                          │
│  (locations, search queries, filters, output preferences)           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      YouTube Search Module                          │
│  - Search for videos by location/query                              │
│  - Paginate through results                                         │
│  - Extract video metadata (URL, title, channel, date)               │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Transcript Extraction Module                     │
│  - Fetch YouTube auto-captions (preferred)                          │
│  - Fallback: Audio download + Speech-to-Text                        │
│  - Handle multiple languages (Telugu, Hindi, English)               │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AI Parsing Module                              │
│  - Send transcript to Claude API                                    │
│  - Extract structured property data                                 │
│  - Validate and normalize data                                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Storage Module                            │
│  - JSON output with all properties                                  │
│  - Deduplication logic                                              │
│  - Search/filter capabilities                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Specifications

### 1. Configuration System

**File: `config.json`**

```json
{
  "search": {
    "locations": ["LB Nagar"],
    "active_location": "LB Nagar",
    "query_templates": [
      "independent house for sale {location}",
      "individual house {location}",
      "house for sale {location} Hyderabad"
    ],
    "max_videos_per_search": 50,
    "sort_by": "relevance",
    "upload_date_filter": "this_year"
  },
  "extraction": {
    "primary_language": "te",
    "languages": ["te", "hi", "en"],
    "whisper_model": "medium"
  },
  "llm": {
    "provider": "ollama",
    "model": "qwen2.5:7b",
    "base_url": "http://localhost:11434"
  },
  "output": {
    "properties_dir": "./data/properties",
    "index_file": "./data/index.json",
    "csv_file": "./data/index.csv"
  },
  "scheduling": {
    "enabled": true,
    "cron_time": "0 0 * * *",
    "lock_file": "./data/.lock",
    "skip_if_ran_today": true
  },
  "rate_limits": {
    "delay_between_videos_ms": 2000,
    "max_retries": 3
  }
}
```

**No API keys required** - all tools run locally.

**Configurable Parameters:**
- `locations`: Array of locations to search (easily add/remove)
- `active_location`: Currently active search location
- `query_templates`: Customizable search query patterns
- `max_videos_per_search`: Limit videos processed per search
- `upload_date_filter`: Filter by recency (today, this_week, this_month, this_year)

---

### 2. YouTube Search Module

**Chosen Technology: yt-dlp (no API key needed)**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| YouTube Data API v3 | Official, structured | Quota limits, needs API key | ❌ Skip |
| **yt-dlp library** | No API key, feature-rich | May break (actively maintained) | ✅ Use |
| Selenium/Playwright | Full browser control | Slow, resource-heavy | ❌ Skip |

**yt-dlp capabilities we'll use:**
- `ytsearch50:query` - Search YouTube, get up to 50 results
- Extract metadata (title, channel, duration, upload date)
- Download audio only (for Whisper transcription)
- Use browser cookies if needed: `--cookies-from-browser chrome`

**Search Module Functions:**
```
search_videos(location: str, query: str) -> List[VideoMetadata]
get_video_list(search_results) -> List[str]  # video IDs
filter_videos(videos, criteria) -> List[VideoMetadata]
```

**Video Metadata Structure:**
```json
{
  "video_id": "abc123xyz",
  "url": "https://youtube.com/watch?v=abc123xyz",
  "title": "3BHK Independent House for Sale in LB Nagar | 150 Sq Yards",
  "channel": "Hyderabad Properties",
  "channel_url": "https://youtube.com/channel/...",
  "upload_date": "2024-01-15",
  "duration_seconds": 425,
  "view_count": 12500,
  "description": "...",
  "thumbnail_url": "..."
}
```

---

### 3. Transcript Extraction Module

**Primary Method: Whisper Audio Transcription (for Telugu)**
- Download audio using `yt-dlp`
- Transcribe using OpenAI Whisper locally
- `large-v3` model recommended for best Telugu accuracy
- Handles Telugu, Hindi, English, and code-switching

**Secondary Method: YouTube Captions API**
- Use `youtube-transcript-api` Python library
- Only reliable for English-language videos
- Telugu auto-captions on YouTube are typically poor quality

**Transcript Extraction Flow (Telugu-First):**
```
1. Download audio from video (yt-dlp, audio-only m4a/mp3)
   └── ~5MB per 10-minute video

2. Transcribe with Whisper (language hint: Telugu)
   ├── GPU: large-v3 model (~30 seconds per 10-min video)
   └── CPU: medium model (~3-5 minutes per 10-min video)

3. Post-process transcript:
   ├── Normalize Telugu numerals → Arabic numerals
   ├── Standardize unit terms (గజాలు → sq_yards)
   └── Clean up repetitions/filler words

4. Return transcript with timestamps
```

**Transcript Output Structure:**
```json
{
  "video_id": "abc123xyz",
  "language": "te",
  "source": "whisper_transcription",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": "ఈ అందమైన ప్రాపర్టీకి స్వాగతం..."},
    {"start": 5.2, "end": 12.1, "text": "ఇది 3BHK ఇండిపెండెంట్ హౌస్..."}
  ],
  "full_text": "ఈ అందమైన ప్రాపర్టీకి స్వాగతం... ఇది 3BHK ఇండిపెండెంట్ హౌస్..."
}
```

---

### 3.1 Telugu Language Handling (Critical)

**Primary Challenge:** Most Hyderabad real estate videos are in Telugu. YouTube auto-captions for Telugu are often poor or missing.

**Recommended Approach: Whisper large-v3**
- OpenAI's Whisper `large-v3` model has strong Telugu support
- Runs locally (requires ~10GB VRAM for large-v3, or use CPU with slower processing)
- Alternative: Use `medium` model for faster processing with acceptable accuracy

**Telugu-Specific Real Estate Terminology:**

| Telugu Term | English Equivalent | Notes |
|-------------|-------------------|-------|
| గజాలు (gajalu) | Square yards | Most common unit in Hyderabad |
| అడుగులు (adugulu) | Square feet | Built-up area measurement |
| లక్షలు (lakshalu) | Lakhs (100,000) | Price unit |
| కోట్లు (kotlu) | Crores (10,000,000) | Price unit |
| తూర్పు ముఖం (toorpu mukham) | East facing | Direction |
| పడమర ముఖం (padamara mukham) | West facing | Direction |
| ఉత్తరం ముఖం (uttaram mukham) | North facing | Direction |
| దక్షిణం ముఖం (dakshinam mukham) | South facing | Direction |
| బోర్ వెల్ (bore well) | Bore well | Water source |
| సంప్ (sump) | Underground water tank | Storage |
| ఓవర్ హెడ్ ట్యాంక్ | Overhead tank | Storage |
| పూజ గది (pooja gadi) | Prayer room | Common amenity |
| కార్ పార్కింగ్ | Car parking | Parking |
| టెర్రస్ | Terrace | Outdoor space |
| సెల్లార్ | Cellar/Basement | Storage |
| G+1, G+2 | Ground + floors | Building height |
| GHMC అప్రూవ్డ్ | GHMC Approved | Municipal approval |
| HMDA అప్రూవ్డ్ | HMDA Approved | Development authority approval |
| రిజిస్ట్రేషన్ రెడీ | Registration ready | Legal status |
| బ్యాంక్ లోన్ ఎలిజిబుల్ | Bank loan eligible | Financing |

**Code-Switching Handling:**
- Telugu real estate videos frequently mix Telugu with English terms
- Example: "ఈ property లో 3 bedrooms ఉన్నాయి, total area 150 square yards"
- Whisper handles this well; Claude can parse mixed-language transcripts

**Transcript Processing Flow (Telugu-First):**
```
1. Download audio from YouTube video (yt-dlp)

2. Run Whisper transcription with Telugu language hint
   whisper audio.mp3 --model large-v3 --language te

3. If confidence is low, retry with language=auto
   (handles Hindi/English mixed content)

4. Post-process transcript:
   - Normalize Telugu numerals to Arabic numerals
   - Standardize unit spellings (గజాలు → sq_yards)

5. Send to local LLM for structured extraction
```

**Whisper Configuration for Telugu (CPU):**
```python
# CPU-optimized settings (no GPU required)
whisper_config = {
    "model": "medium",          # Good balance for CPU
    "language": "te",           # Telugu language code
    "task": "transcribe",       # Keep in original language
    "device": "cpu",            # CPU processing
    "temperature": 0.0,         # Deterministic output
    "condition_on_previous_text": True,  # Better context
}
# Processing time: ~5-10 min per 10-minute video on CPU
```

---

### 4. AI Parsing Module (Local LLM via Ollama)

**Purpose:** Extract structured property data from unstructured video transcripts.

**Local LLM: Qwen 2.5 7B via Ollama**
- Best multilingual support among open models
- Reliable JSON output
- Runs on CPU (~2-3 min per transcript)

**Setup:**
```bash
# Install Ollama (one-time)
brew install ollama

# Download model (one-time, ~4.5GB)
ollama pull qwen2.5:7b

# Start Ollama server (runs in background)
ollama serve
```

**Prompt Engineering Strategy (Telugu-Optimized):**

```
SYSTEM PROMPT:
You are a real estate data extraction assistant specializing in Hyderabad/Telangana
properties. You understand Telugu, Hindi, and English. Extract property details from
video transcripts that may be in Telugu or a mix of Telugu and English.

Important Telugu real estate terms:
- గజాలు (gajalu) = square yards
- లక్షలు (lakshalu) = lakhs (100,000 INR)
- కోట్లు (kotlu) = crores (10,000,000 INR)
- తూర్పు/పడమర/ఉత్తరం/దక్షిణం = East/West/North/South facing

Return ONLY valid JSON. If a field cannot be determined, use null.

USER PROMPT:
Extract property details from this Hyderabad real estate video transcript.
The transcript is primarily in Telugu (may include English terms).

<transcript>
{transcript_text}
</transcript>

Extract and NORMALIZE to English the following fields:
- property_type (independent_house, apartment, villa, plot, commercial)
- dimensions (length_ft, width_ft, plot_area_sq_yards, built_up_area_sq_ft)
- price (amount in INR as integer, price_per_sq_yard, negotiable boolean)
- location (area, sub_area, city, landmark, full_address)
- configuration (bedrooms, bathrooms, floors, parking_spaces)
- amenities (list in English: bore_well, sump, overhead_tank, pooja_room, etc.)
- construction (year_built, facing_direction, road_width_ft, approval_status)
- contact (name, phone numbers as array, agency)
- additional_notes (any other relevant details, translated to English)

Convert all Telugu terms to their English equivalents in the output.
Return as JSON.
```

**Extracted Data Schema:**
```json
{
  "property_type": "independent_house",
  "dimensions": {
    "length_ft": 30,
    "width_ft": 45,
    "plot_area_sq_yards": 150,
    "built_up_area_sq_ft": 2400
  },
  "price": {
    "amount": 12500000,
    "currency": "INR",
    "price_per_sq_yard": 83333,
    "negotiable": true
  },
  "location": {
    "area": "LB Nagar",
    "sub_area": "Bairamalguda",
    "city": "Hyderabad",
    "state": "Telangana",
    "landmark": "Near Metro Station",
    "full_address": null
  },
  "configuration": {
    "bedrooms": 3,
    "bathrooms": 3,
    "floors": 2,
    "hall": true,
    "kitchen": true,
    "parking_spaces": 1,
    "car_parking": true,
    "bike_parking": true
  },
  "amenities": [
    "bore_well",
    "overhead_tank",
    "sump",
    "modular_kitchen",
    "pooja_room",
    "terrace"
  ],
  "construction": {
    "year_built": 2022,
    "age_years": 2,
    "facing_direction": "east",
    "road_width_ft": 30,
    "construction_type": "RCC",
    "floors_allowed": "G+2"
  },
  "legal": {
    "ownership_type": "freehold",
    "approval_status": "GHMC_approved",
    "bank_loan_eligible": true
  },
  "contact": {
    "name": "Ramesh Kumar",
    "phone": ["+91 9876543210"],
    "agency": "Hyderabad Properties",
    "role": "agent"
  },
  "additional_notes": [
    "Corner plot",
    "Ready to move",
    "All documents clear"
  ],
  "confidence_score": 0.85
}
```

---

### 5. Data Storage & Output Module

**Hybrid Storage Approach:**
- Individual JSON file per property (easy to add/update)
- Auto-generated `index.json` (combined array for dashboard)
- Auto-generated `index.csv` (for Excel/analysis)

**Directory Structure:**
```
data/
├── properties/
│   ├── 2026-01-14_abc123xyz.json    # Individual property files
│   ├── 2026-01-14_def456uvw.json    # Format: {date}_{video_id}.json
│   └── ...
├── index.json                        # Combined array (auto-regenerated)
├── index.csv                         # Flattened CSV (auto-regenerated)
├── processed_videos.json             # Tracking already-processed videos
└── .lock                             # Lock file for scheduling
```

**Individual Property File: `data/properties/2026-01-14_abc123xyz.json`**
```json
{
  "video_info": {
    "video_id": "abc123xyz",
    "url": "https://youtube.com/watch?v=abc123xyz",
    "title": "3BHK House for Sale in LB Nagar",
    "channel": "Hyderabad Properties",
    "upload_date": "2026-01-10",
    "duration_seconds": 425
  },
  "extracted_data": {
    "property_type": "independent_house",
    "dimensions": { "plot_area_sq_yards": 150, "built_up_area_sq_ft": 2400 },
    "price": { "amount": 12500000, "price_per_sq_yard": 83333 },
    "location": { "area": "LB Nagar", "sub_area": "Bairamalguda" },
    "configuration": { "bedrooms": 3, "bathrooms": 3, "floors": 2 },
    "amenities": ["bore_well", "sump", "pooja_room"],
    "construction": { "facing_direction": "east", "road_width_ft": 30 },
    "contact": { "phone": ["+91 9876543210"] }
  },
  "processing_info": {
    "processed_at": "2026-01-14T14:25:00Z",
    "transcript_source": "whisper_medium",
    "llm_model": "qwen2.5:7b",
    "search_location": "LB Nagar"
  }
}
```

**Combined Index File: `data/index.json`**
```json
{
  "metadata": {
    "last_updated": "2026-01-14T14:30:00Z",
    "total_properties": 42,
    "locations": ["LB Nagar"]
  },
  "properties": [
    { /* property 1 */ },
    { /* property 2 */ },
    ...
  ],
  "statistics": {
    "avg_price": 11500000,
    "price_range": {"min": 5500000, "max": 25000000},
    "common_configurations": {"3BHK": 25, "2BHK": 12, "4BHK": 5},
    "avg_price_per_sq_yard": 75000
  }
}
```

**Deduplication Logic:**
- Track processed video IDs in `processed_videos.json`
- Skip already-processed videos on subsequent runs
- Option to force re-process

---

### 6. CLI Interface

**On-Demand Commands:**

```bash
# Search and process videos for active location (on-demand)
python main.py search

# Search specific location
python main.py search --location "Dilsukhnagar"

# Process a single video URL
python main.py process-video "https://youtube.com/watch?v=..."

# Change active location
python main.py set-location "Uppal"

# Rebuild index.json and index.csv from individual files
python main.py rebuild-index

# View statistics
python main.py stats

# List all processed properties
python main.py list
```

**Scheduled Processing (12 AM daily):**

```bash
# Setup cron job (one-time)
python main.py setup-cron

# This adds to crontab:
# 0 0 * * * /path/to/home-search/run_scheduled.sh >> /path/to/logs/cron.log 2>&1
```

**Scheduling Logic:**
- Uses lock file (`data/.lock`) to prevent duplicate runs
- If manually triggered during the day → skips 12 AM run
- Stores `last_run_timestamp` in `processed_videos.json`
- Only processes new videos (not already in `processed_videos.json`)

**run_scheduled.sh:**
```bash
#!/bin/bash
cd /path/to/home-search

# Check if already running
if [ -f "data/.lock" ]; then
    echo "Already running, skipping..."
    exit 0
fi

# Check if ran today already
python main.py should-run-today || exit 0

# Run the search
python main.py search
```

---

## Project Structure

```
home-search/
├── config.json                 # Main configuration
├── main.py                     # CLI entry point
├── requirements.txt            # Python dependencies
├── run_scheduled.sh            # Script for cron job
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration loader
│   ├── youtube/
│   │   ├── __init__.py
│   │   ├── search.py          # YouTube search via yt-dlp
│   │   └── downloader.py      # Audio download for Whisper
│   ├── transcript/
│   │   ├── __init__.py
│   │   ├── whisper_transcribe.py  # Primary Telugu transcription
│   │   └── telugu_normalize.py    # Telugu term normalization
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── ollama_parser.py   # Qwen 2.5 7B via Ollama
│   │   └── prompts.py         # Prompt templates
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── property_store.py  # Individual JSON file operations
│   │   ├── index_builder.py   # Rebuild index.json and index.csv
│   │   └── dedup.py           # Deduplication logic
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging configuration
│       └── scheduler.py       # Cron/scheduling utilities
├── data/                       # Output directory
│   ├── properties/            # Individual property JSON files
│   │   ├── 2026-01-14_abc123.json
│   │   └── ...
│   ├── index.json             # Combined array (auto-generated)
│   ├── index.csv              # Flattened CSV (auto-generated)
│   ├── processed_videos.json  # Tracking file
│   └── .lock                  # Lock file for scheduling
├── logs/                      # Log files
│   └── cron.log
└── tests/
    ├── test_search.py
    ├── test_transcript.py
    └── test_parser.py
```

---

## Dependencies

**requirements.txt:**
```
# YouTube
yt-dlp>=2024.1.0

# Speech-to-Text (Telugu)
openai-whisper>=20231117

# Local LLM
ollama>=0.4.0           # Python client for Ollama

# CLI
click>=8.1.0
rich>=13.0.0            # Pretty console output

# Utilities
pydantic>=2.0.0         # Data validation
httpx>=0.25.0           # HTTP client for Ollama API

# Audio processing
ffmpeg-python>=0.2.0    # Required by Whisper
```

**System Dependencies (install separately):**
```bash
# macOS
brew install ffmpeg     # Required for Whisper
brew install ollama     # Local LLM server

# Then download the model
ollama pull qwen2.5:7b
```

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Set up project structure
- [ ] Create configuration system
- [ ] Implement YouTube search module using yt-dlp
- [ ] Basic video metadata extraction
- [ ] Unit tests for search module

### Phase 2: Transcript Extraction (Telugu-First)
- [ ] Implement audio download via yt-dlp
- [ ] Implement Whisper transcription (primary method for Telugu)
- [ ] Build Telugu term normalization/post-processing
- [ ] Add YouTube captions as optional secondary method
- [ ] Handle code-switching (Telugu + English mix)
- [ ] Unit tests for transcript module

### Phase 3: AI Parsing (Local LLM)
- [ ] Set up Ollama with Qwen 2.5 7B
- [ ] Design and test extraction prompts for Telugu
- [ ] Implement data validation and normalization
- [ ] Handle edge cases (incomplete data, non-property videos)
- [ ] Unit tests for parser module

### Phase 4: Storage & CLI
- [ ] Implement hybrid storage (individual JSON + index files)
- [ ] Build CLI interface with on-demand commands
- [ ] Add progress indicators and logging
- [ ] Statistics generation and index rebuilding

### Phase 5: Scheduling & Polish
- [ ] Implement 12 AM cron job with lock file
- [ ] Error handling and retry logic
- [ ] Rate limiting implementation
- [ ] Resume capability for interrupted searches
- [ ] CSV export in index rebuilding

---

## Potential Challenges & Mitigations

| Challenge | Risk | Mitigation |
|-----------|------|------------|
| YouTube blocking/rate limiting | Medium | Implement delays, use cookies if needed |
| Telugu transcription accuracy | **High** | Whisper medium on CPU, Telugu post-processing |
| Code-switching (Telugu + English mix) | Medium | Whisper handles well; test Qwen prompts extensively |
| Telugu numeral/unit normalization | Medium | Post-processing step to convert గజాలు→sq_yards, లక్షలు→lakhs |
| Local LLM parsing Telugu | Medium | Detailed prompts with Telugu terminology reference |
| CPU processing time | Medium | Batch overnight, ~10-15 min per video acceptable |
| Non-property videos in results | Low | Pre-filter by title keywords, LLM classification |
| Ollama server not running | Low | Auto-start check in CLI |

---

## Cost Analysis

**Total Cost: $0 (All Local)**

| Component | Cost | Notes |
|-----------|------|-------|
| YouTube search/download | $0 | yt-dlp, no API key |
| Whisper transcription | $0 | Local model, CPU |
| LLM parsing | $0 | Qwen 2.5 7B via Ollama |
| Storage | $0 | Local JSON files |

**Only "cost" is CPU time:**
- ~5-10 min per video for Whisper (CPU)
- ~2-3 min per transcript for LLM
- Total: ~10-15 min per video
- 50 videos = ~8-12 hours (run overnight)

---

## Future Enhancements (Out of Scope for v1)

1. **Web Dashboard**: Visual interface to browse properties
2. **Alerts**: Notifications for new properties matching criteria
3. **Price Tracking**: Monitor price changes over time
4. **Image Extraction**: Capture screenshots from videos
5. **Map Integration**: Plot properties on Google Maps
6. **Comparison Tool**: Side-by-side property comparison
7. **Database Backend**: SQLite/PostgreSQL for larger datasets

---

## Resolved Questions

| Question | Answer | Decision |
|----------|--------|----------|
| YouTube API Key | Not needed | Use yt-dlp only |
| Cloud LLM API | Not needed | Use Qwen 2.5 7B via Ollama (local) |
| GPU Availability | No GPU | Use Whisper medium on CPU |
| Initial Location | LB Nagar | Start here, expand later |
| Budget | Zero cost | All local tools |
| Output Format | JSON + CSV | Hybrid: individual JSON + auto-generated index |
| Processing Mode | Both | On-demand + 12 AM cron job |
| RAM | 16GB confirmed | Sufficient for all models |

---

## Next Steps

1. ✅ Plan reviewed and approved
2. Begin Phase 1 implementation:
   - Set up project structure
   - Install dependencies (ffmpeg, ollama, python packages)
   - Download models (whisper medium, qwen2.5:7b)
   - Implement YouTube search with yt-dlp
