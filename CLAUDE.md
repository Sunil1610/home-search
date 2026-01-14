# Claude Code Instructions for home-search Project

## Overview
This file contains instructions for Claude to follow automatically throughout this project. These rules apply to every interaction.

---

## Permissions Granted

Claude has full permission to:
- **Download files from the internet** (models, dependencies, data)
- **Install packages** via pip, brew, npm, etc.
- **Run shell commands** without asking for confirmation
- **Create, modify, delete files** as needed
- **Run long-running processes** (Whisper, Ollama, etc.)
- **Set up cron jobs** and system scheduling
- **Access YouTube** via yt-dlp for video/audio download

**No need to ask permission for any of the above in this project.**

---

## 1. Discussion Tracking

**File:** `discussions.md`

- Log ALL significant discussions, decisions, and Q&A in `discussions.md`
- Format each session with a header: `## Session N - Topic (YYYY-MM-DD)`
- Include:
  - Questions asked and answers given
  - Decisions made with reasoning
  - Any changes to the plan
- Update the Decision Log table at the bottom of the file
- This serves as the project's memory and audit trail

---

## 2. Code Organization

**IMPORTANT: Code lives in standard folders, NOT in phases/**

```
home-search/
├── CLAUDE.md              # This file (instructions)
├── pln.md                 # Master plan
├── discussions.md         # Discussion history
├── config.json            # Configuration
├── main.py                # CLI entry point
├── requirements.txt       # Dependencies
├── run_scheduled.sh       # Cron script
│
├── src/                   # ALL SOURCE CODE GOES HERE
│   ├── __init__.py
│   ├── config.py
│   ├── youtube/           # YouTube search & download
│   ├── transcript/        # Whisper transcription
│   ├── parser/            # LLM parsing
│   ├── storage/           # JSON/CSV storage
│   └── utils/             # Utilities
│
├── data/                  # Output data
│   ├── properties/        # Individual JSON files
│   ├── index.json
│   └── index.csv
│
├── logs/                  # Log files
│
├── tests/                 # Test files
│
└── phases/                # TRACKING ONLY (no code here)
    ├── phase1_foundation/
    │   └── TODO.md
    ├── phase2_transcription/
    │   └── TODO.md
    └── ...
```

**Key Rule:**
- `phases/` folder is ONLY for TODO.md tracking files and context notes
- ALL code goes in `src/`, `main.py`, `tests/`, etc.

---

## 3. Task Management (Per Phase)

**Structure:**
```
phases/
├── phase1_foundation/
│   └── TODO.md           # Task tracking ONLY
├── phase2_transcription/
│   └── TODO.md
├── phase3_parsing/
│   └── TODO.md
├── phase4_storage_cli/
│   └── TODO.md
└── phase5_scheduling/
    └── TODO.md
```

**TODO.md Format:**
```markdown
# Phase N: [Phase Name]

## Status: [Not Started | In Progress | Completed]

## Tasks

- [x] Task 1 - completed and tested
- [x] Task 2 - completed and tested
- [ ] Task 3 - in progress
- [ ] Task 4 - pending

## Files Created/Modified
- `src/youtube/search.py` - YouTube search module
- `src/youtube/downloader.py` - Audio downloader

## Notes
- Any relevant notes or blockers
```

**Rules:**
- Create TODO.md at the start of each phase
- Mark tasks with `[x]` ONLY when code is developed AND tested
- List files created/modified in that phase
- Update TODO.md after completing each task
- Use Claude's TodoWrite tool to track current session progress

---

## 4. Phase Verification Process (REQUIRED)

**Before marking a phase complete, create `VERIFICATION.md` with evidence.**

**Structure:**
```
phases/
├── phase1_foundation/
│   ├── TODO.md           # Task tracking
│   └── VERIFICATION.md   # Test evidence (REQUIRED)
├── phase2_transcription/
│   ├── TODO.md
│   └── VERIFICATION.md
└── ...
```

**VERIFICATION.md Format:**
```markdown
# Phase N: [Phase Name] - Verification Report

**Date:** YYYY-MM-DD
**Status:** [X/Y CHECKS PASSED]

---

## Summary

| Check | Component | Status |
|-------|-----------|--------|
| 1 | Component A | PASS/FAIL |
| 2 | Component B | PASS/FAIL |

---

## Detailed Evidence

### 1. [Check Name]
```
[Actual command output or test results]
```
**Status:** PASS/FAIL

---

## Known Issues (Non-Blocking)
- List any warnings or minor issues that don't affect functionality

---

## Conclusion
[Summary and readiness for next phase]
```

**Verification Rules:**
1. Run ALL functionality checks before completing a phase
2. Capture actual command output as evidence
3. Document both PASS and FAIL results
4. List any non-blocking issues/warnings
5. Phase is NOT complete until VERIFICATION.md exists with all checks passing

**What to Verify Per Phase:**

| Phase | Required Checks |
|-------|-----------------|
| Phase 1: Foundation | ffmpeg, ollama, packages, YouTube search, audio download, LLM test, config |
| Phase 2: Transcription | Whisper model loads, Telugu audio transcribes, output format correct |
| Phase 3: Parsing | LLM extracts data, JSON output valid, Telugu terms normalized |
| Phase 4: Storage & CLI | Files save correctly, CLI commands work, index rebuilds |
| Phase 5: Scheduling | Cron runs, lock file works, scheduled processing completes |

---

## 5. Development Workflow

For each task:
1. Update TODO.md to mark task as in-progress
2. Write the code in appropriate `src/` folder
3. Test the code (manually or with unit tests)
4. Mark task as complete in TODO.md with `[x]`
5. Log any significant decisions in discussions.md

**At phase completion:**
6. Run all functionality checks
7. Create VERIFICATION.md with evidence
8. Only then mark phase as complete

---

## 6. Key Project Files Reference

| File | Purpose |
|------|---------|
| `pln.md` | Master implementation plan |
| `discussions.md` | All discussions and decisions |
| `phases/phaseN/TODO.md` | Task tracking per phase (no code) |
| `phases/phaseN/VERIFICATION.md` | Test evidence per phase (REQUIRED) |
| `config.json` | Runtime configuration |
| `src/` | All source code |

---

## 7. Reminders

- Always check `discussions.md` for context on past decisions
- Always update `phases/phaseN/TODO.md` when completing tasks
- Code goes in `src/`, tracking goes in `phases/`
- Test before marking complete
- Log important decisions immediately
- Download and install whatever is needed without asking
