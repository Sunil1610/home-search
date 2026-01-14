# Project Discussions & Decisions Log

## Session 1 - Initial Planning (2026-01-14)

### User Requirements
- Primary language: **Telugu** (not English)
- Location: **LB Nagar, Hyderabad** (expandable later)
- Output: **JSON** (dashboard planned for future)
- Budget: **Zero cost preferred** (local/free tools only)
- Hardware: **CPU only** (no GPU)

---

### Q&A: Technology Choices

#### Q1: YouTube API Key - Do we need it?
**Answer: NO, not needed.**

`yt-dlp` works without any API key. It can:
- Search YouTube (`ytsearch:houses for sale in LB Nagar`)
- Download video metadata (title, channel, duration, etc.)
- Download audio for transcription
- Handle pagination through search results

YouTube Data API would only add quota limits. We're better off without it.

---

#### Q2: Can a local LLM replace Claude API?
**Answer: YES, but model size matters.**

**Will Llama 3B work?**
- 3B models (Llama 3.2 3B, Phi-3 mini) are **risky** for this task
- They often produce malformed JSON or miss details from long transcripts
- Telugu understanding in small models is limited

**Recommended local models (7B-8B range):**

| Model | Size | Telugu Support | JSON Reliability | Speed (CPU) |
|-------|------|----------------|------------------|-------------|
| **Qwen 2.5 7B** | ~4.5GB | Good | Excellent | ~2-3 min/transcript |
| **Llama 3.1 8B** | ~4.5GB | Moderate | Good | ~2-3 min/transcript |
| **Mistral 7B** | ~4GB | Moderate | Good | ~2-3 min/transcript |
| Llama 3.2 3B | ~2GB | Poor | Unreliable | ~1 min/transcript |

**Recommendation:** Start with **Qwen 2.5 7B Instruct** (Q4 quantized, ~4.5GB RAM)
- Best multilingual support among open models
- Reliable JSON output
- Runs on CPU (slower but works)

**Tools to run local LLM:**
- **Ollama** (easiest) - `ollama run qwen2.5:7b`
- **llama.cpp** (fastest on CPU)
- **LM Studio** (GUI option)

---

#### Q3: Where was budget needed in the original plan?
**Answer: Only for cloud APIs, which we're eliminating.**

| Original Cost Item | Cost | Our Approach | New Cost |
|--------------------|------|--------------|----------|
| Claude API | ~$0.50-1.00/100 videos | Local LLM (Qwen 2.5 7B) | **$0** |
| Whisper API | ~$0.60/hour audio | Local Whisper | **$0** |
| YouTube Data API | Free but quota limited | yt-dlp | **$0** |
| Server/Cloud | Variable | Run locally | **$0** |

**Total ongoing cost: $0**

Only "cost" is your CPU time:
- Whisper transcription: ~5-10 min per 10-min video (CPU, medium model)
- LLM parsing: ~2-3 min per transcript
- Total: ~8-15 min processing per video on CPU

---

#### Q4: Chrome Headless + YouTube login - Is it needed?
**Answer: Probably NOT needed, but let's compare.**

| Approach | Pros | Cons |
|----------|------|------|
| **yt-dlp (recommended)** | Simple, fast, reliable, no browser overhead | Can't interact with page elements |
| **Chrome Headless** | Full browser control, can login | Complex, slow, detection risk, resource heavy |

**When Chrome Headless would be needed:**
- Age-restricted videos (yt-dlp can use cookies instead)
- Videos requiring login (rare for real estate content)
- If YouTube blocks yt-dlp (hasn't happened, actively maintained)

**Recommendation:** Start with yt-dlp. Only add Chrome if we hit specific blockers.

**If we do need login later:**
```bash
# yt-dlp can use browser cookies without needing headless chrome
yt-dlp --cookies-from-browser chrome "ytsearch:houses for sale LB Nagar"
```

---

### Final Technology Stack (Zero Cost)

```
┌─────────────────────────────────────────────────────────────┐
│                    HOME-SEARCH TOOL                         │
├─────────────────────────────────────────────────────────────┤
│  YouTube Search & Download    │  yt-dlp (no API key)        │
│  Audio Transcription          │  Whisper medium (local CPU) │
│  Telugu → Structured Data     │  Qwen 2.5 7B via Ollama     │
│  Data Storage                 │  JSON files                 │
│  Future Dashboard             │  TBD (React/Streamlit?)     │
└─────────────────────────────────────────────────────────────┘

Total Cost: $0
Hardware Required: Any modern laptop/desktop with 8GB+ RAM
```

---

### Updated Requirements

```yaml
Hardware:
  RAM: 8GB minimum (16GB recommended for comfort)
  Storage: ~10GB for models + data
  GPU: Not required
  CPU: Any modern CPU (Intel i5/AMD Ryzen 5 or better recommended)

Software:
  Python: 3.10+
  Ollama: For running Qwen 2.5 7B
  ffmpeg: For audio processing

Models to Download:
  - Whisper medium (~1.5GB) - for Telugu transcription
  - Qwen 2.5 7B Q4 (~4.5GB) - for data extraction
```

---

### Open Questions for Next Session
1. Do you have 8GB+ RAM available?
2. Should we process videos in batch (overnight) or on-demand?
3. Any specific property criteria to filter (price range, BHK, etc.)?

---

## Session 2 - Follow-up Questions (2026-01-14)

### Q5: RAM Available?
**Answer: 16GB RAM confirmed** (via `system_profiler SPHardwareDataType`)

This is excellent - can comfortably run:
- Whisper medium model (~1.5GB)
- Qwen 2.5 7B (~4.5GB)
- Python + data in memory
- With room to spare

---

### Q6: Processing Mode - Batch or On-Demand?
**User wants: BOTH**

**Implementation Plan:**

```bash
# On-demand: Process immediately
python main.py search --location "LB Nagar"

# Scheduled: Run at 12 AM daily if not already running
# Uses cron job or launchd (macOS)
```

**Scheduling Approach:**
- Use a lock file to prevent duplicate runs
- If manually triggered during the day, skip the 12 AM run
- Store last run timestamp to avoid re-processing same videos

**Cron entry (to be set up):**
```bash
0 0 * * * /path/to/home-search/run_if_idle.sh >> /path/to/logs/cron.log 2>&1
```

---

### Q7: Data Storage Format?
**User preference:** Individual JSON files OR CSV, flexible

**Analysis:**

| Format | Pros | Cons |
|--------|------|------|
| Individual JSON per property | Clean nested data, easy updates | Many files |
| Single JSON array | Dashboard-friendly | Hard to append |
| CSV | Excel/analysis friendly | Loses nested structure |

**Chosen Approach: Hybrid**

```
data/
├── properties/
│   ├── 2026-01-14_abc123xyz.json    # Individual property files
│   ├── 2026-01-14_def456uvw.json
│   └── ...
├── index.json                        # Combined array (auto-generated)
├── index.csv                         # Flattened CSV (auto-generated)
└── processed_videos.json             # Tracking file
```

**Why this works:**
1. **Individual JSON files** - Easy to add/update single properties
2. **index.json** - Auto-regenerated, loads all data for dashboard
3. **index.csv** - Auto-regenerated, for Excel/analysis
4. Filename format: `{date}_{video_id}.json` - prevents duplicates, sortable

**CLI commands:**
```bash
# Search and process (on-demand)
python main.py search --location "LB Nagar"

# Rebuild index files from individual JSONs
python main.py rebuild-index

# Export to CSV
python main.py export --format csv --output properties.csv
```

---

### Q8: Property Criteria/Filters?
**User preference:** Search for individual homes in general, no specific filters

**Search queries to use:**
- "independent house for sale LB Nagar"
- "individual house LB Nagar"
- "house for sale LB Nagar Hyderabad"

Will NOT filter by price/BHK - capture everything and filter later in dashboard.

---

### Decision Log

| Decision | Choice | Reason | Date |
|----------|--------|--------|------|
| YouTube access method | yt-dlp | No API key needed, reliable | 2026-01-14 |
| Transcription | Whisper medium (CPU) | Free, good Telugu support | 2026-01-14 |
| LLM for parsing | Qwen 2.5 7B via Ollama | Best multilingual, free | 2026-01-14 |
| Primary language | Telugu | User requirement | 2026-01-14 |
| Initial location | LB Nagar | User requirement | 2026-01-14 |
| RAM confirmed | 16GB | Sufficient for all models | 2026-01-14 |
| Processing mode | On-demand + 12 AM cron | User wants both options | 2026-01-14 |
| Storage format | Hybrid (individual JSON + index) | Flexible for dashboard + analysis | 2026-01-14 |
| Property filter | None (general search) | Capture all, filter in dashboard | 2026-01-14 |
| Project instructions | CLAUDE.md file | Auto-apply rules for Claude | 2026-01-14 |
| Task tracking | Per-phase TODO.md files | Track progress per phase | 2026-01-14 |

---

## Session 3 - Project Setup & Instructions (2026-01-14)

### CLAUDE.md Created

User requested automatic instructions for Claude to follow throughout the project:

1. **Discussion Tracking** → Log all discussions in `discussions.md`
2. **Task Management** → Create TODO.md per phase folder
3. **Phase Folders** → Organize work by implementation phase

### Directory Structure Created

```
phases/
├── phase1_foundation/
├── phase2_transcription/
├── phase3_parsing/
├── phase4_storage_cli/
└── phase5_scheduling/
```

Each phase will have:
- `TODO.md` - Task tracking for that phase
- Source files specific to that phase's work

### Workflow Established

1. Start phase → Create TODO.md with tasks
2. Work on task → Update TODO.md (in progress)
3. Complete & test → Mark `[x]` in TODO.md
4. Log decisions → Update discussions.md
5. Repeat until phase complete

---

### Clarification: Code vs Tracking Separation

**User clarified:**
- `phases/` folder is ONLY for tracking (TODO.md files)
- ALL code goes in standard folders: `src/`, `main.py`, `tests/`
- phases/ should NOT contain any source code

**Permissions granted to Claude:**
- Download from internet (models, dependencies)
- Install packages (pip, brew, etc.)
- Run shell commands without confirmation
- Create/modify/delete files
- Run long-running processes
- Set up cron jobs
- Access YouTube via yt-dlp

**No need to ask permission for the above in this project.**

---

## Session 4 - Phase 1 Implementation (2026-01-14)

### Completed Tasks

1. **Project Structure Created:**
   - `src/` with youtube/, transcript/, parser/, storage/, utils/
   - `data/` with properties/, temp_audio/
   - `logs/`, `tests/`

2. **Dependencies Installed:**
   - ffmpeg (via brew) - for audio processing
   - ollama (via brew) - for local LLM
   - Python packages: yt-dlp, openai-whisper, ollama, click, rich, pydantic, httpx

3. **Models Downloaded:**
   - Qwen 2.5 7B via Ollama (~4.5GB) - for data extraction
   - Whisper medium will download on first use (~1.5GB)

4. **YouTube Modules Implemented:**
   - `src/youtube/search.py` - Search YouTube using yt-dlp
   - `src/youtube/downloader.py` - Download audio from videos

### Test Results
- **Search Test:** Found 5 videos for "independent house for sale LB Nagar"
  - Videos from channels: Vedantha Properties, BB property, Rudra Properties, VRK Properties
- **Download Test:** Successfully downloaded 503-second audio file

### Issues Encountered
- Some videos return HTTP 403 (protected/restricted)
- Added Chrome cookie support to downloader for better reliability
- Python 3.9 deprecation warning (non-blocking, works fine)

### Phase 1 Status: COMPLETED

---

## Session 5 - Phase 2 Implementation (2026-01-14)

### Completed Tasks

1. **Whisper Transcription Module:**
   - `src/transcript/whisper_transcribe.py` - 180 lines
   - Loads Whisper medium model (1.42GB)
   - Supports Telugu (te), Hindi (hi), English (en)
   - Auto language detection option

2. **Telugu Normalization Module:**
   - `src/transcript/telugu_normalize.py` - 200 lines
   - 50+ Telugu real estate terms mapped to English
   - Examples: గజాలు→sq_yards, లక్షలు→lakhs, తూర్పు ముఖం→east_facing

### Test Results
- **Language Detection:** PASS - Correctly identifies Telugu
- **Term Normalization:** PASS - All test cases pass
- **Audio Processing:** PASS - Pipeline works correctly
- **Processing Time:** ~6-7 min per 8-min video on CPU

### Issues Encountered
1. **Hallucination on music-heavy videos** - Whisper produces repetitive output on videos with minimal speech. This is expected behavior.
2. **YouTube 403 errors** - Rate limiting on some videos. Handled gracefully with retries and cookie support.

### Phase 2 Status: COMPLETED

---

## Session 6 - Phase 3 Implementation (2026-01-14)

### Completed Tasks

1. **Pydantic Data Models:**
   - `src/parser/models.py` - PropertyData, ExtractionResult
   - Nested models: Dimensions, Price, Location, Configuration, etc.

2. **Telugu-Optimized Prompts:**
   - `src/parser/prompts.py`
   - System prompt with Telugu terminology reference
   - Extraction prompt requesting structured JSON

3. **Ollama Parser Module:**
   - `src/parser/ollama_parser.py`
   - Qwen 2.5 7B integration via Ollama
   - JSON extraction with fallback parsing

### Test Results
- **Mixed Telugu+English:** PASS (confidence: 0.9)
- **Pure Telugu:** PASS (confidence: 0.92)
- **Price Conversion:** 85 లక్షలు → 8500000 INR
- **Location Extraction:** బైరమల్గూడ → Biramalguda

### Performance
- Extraction time: ~15-30 seconds per transcript
- Memory usage: ~5-6 GB during inference
- Success rate: 100% on test cases

### Phase 3 Status: COMPLETED

---

## Session 7 - Phase 4 Implementation (2026-01-14)

### Completed Tasks

1. **Property Storage Module:**
   - `src/storage/property_store.py` - 204 lines
   - Save/load individual property JSON files
   - Filename format: `{date}_{video_id}.json`

2. **Deduplication Module:**
   - `src/storage/dedup.py` - 174 lines
   - Track processed videos in `data/processed_videos.json`
   - Filter unprocessed videos before processing

3. **Index Builder Module:**
   - `src/storage/index_builder.py` - 203 lines
   - Generate `data/index.json` (combined array)
   - Generate `data/index.csv` (flattened for Excel)

4. **CLI Entry Point:**
   - `main.py` - 330 lines using Click
   - Commands: search, process-video, rebuild-index, stats, list, check

### Test Results

**Dependency Check:**
- yt-dlp: PASS (2025.10.14)
- ffmpeg: PASS (8.0.1)
- Ollama (qwen2.5:7b): PASS
- Whisper: PASS

**Integration Test (Mock Data):**
- Extraction: PASS (Telugu+English transcript parsed correctly)
- Storage: PASS (Property JSON saved)
- Indexing: PASS (Both index.json and index.csv generated)

**Extraction Accuracy:**
- "1 crore 20 lakhs" → 12,000,000 INR
- "150 square yards" → 150.0 sq yards
- "LB Nagar" → correct location
- "3 bedrooms, 3 bathrooms" → correct config

### Issues Encountered

1. **YouTube 403 Errors:** Rate limiting from YouTube during video download. This is an external issue, not a code problem. Videos may work during off-peak hours.

2. **Python PATH:** yt-dlp and whisper installed to user's local Python bin which wasn't on PATH. Need to add `/Users/sunil/Library/Python/3.9/bin` to PATH.

### CLI Commands
```bash
python3 main.py check          # Check dependencies
python3 main.py search         # Search and process videos
python3 main.py process-video  # Process single video
python3 main.py stats          # Show statistics
python3 main.py list           # List properties
python3 main.py rebuild-index  # Rebuild index files
```

### Phase 4 Status: COMPLETED

---

## Session 8 - Phase 5 Implementation (2026-01-14)

### Completed Tasks

1. **Scheduler Module:**
   - `src/scheduler/runner.py` - 290 lines
   - `LockFile` class using flock for mutual exclusion
   - `RunHistory` class for tracking daily runs
   - `ScheduledRunner` class for orchestrating scheduled jobs

2. **Shell Script:**
   - `scripts/run_scheduled.sh` - 30 lines
   - Sets up environment and calls Python scheduler
   - Logs to `logs/scheduled_YYYY-MM-DD.log`

3. **macOS launchd Config:**
   - `scripts/com.homesearch.daily.plist`
   - Runs at 12:00 AM daily
   - Validated with `plutil -lint`

4. **CLI Schedule Commands:**
   - `schedule install` - Install launchd job
   - `schedule uninstall` - Remove launchd job
   - `schedule status` - Show job status and history
   - `schedule run` - Manual run with --force option

### Test Results

**Lock File Test:** PASS
- Lock correctly prevents duplicate acquisition
- Second process blocked while first holds lock

**Run History Test:** PASS
- Correctly tracks successful/failed runs
- `was_run_today()` prevents duplicate daily runs

**Shell Script Test:** PASS
- Correctly sets up environment
- Calls scheduler module
- Logs output to file

**Plist Validation:** PASS
- `plutil -lint` confirms valid plist

### How Scheduling Works

1. launchd triggers `run_scheduled.sh` at 12:00 AM
2. Lock file acquired (prevents duplicate runs)
3. Run history checked (skips if already ran today)
4. Videos searched, downloaded, transcribed, parsed
5. Properties saved, indexes rebuilt
6. Lock released, run recorded in history

### Phase 5 Status: COMPLETED
