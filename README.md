# Obsidian LLM Wiki

Personal local LLM Wiki workspace for verified development knowledge.

## Workflow

```text
raw/ -> ingest/compile -> review -> wiki/
```

- `raw/`: original observations captured during work.
- `review/`: corrections, failed assumptions, and items that need human review.
- `wiki/`: verified reusable knowledge.

Use this repository as a personal Obsidian vault or as the target directory for `obsidian-llm-wiki-local`.

## Local Audio Analysis

`tools/analyze_audio.py` provides lightweight local SFX analysis using `numpy` and `miniaudio`.

Example:

```powershell
python tools\analyze_audio.py "D:\mmo_program_framework\3001001.WAV" `
  --segment 0:0.5 --segment 0.25:0.5 --segment 0.5:1.0
```

Useful fields:

- `active_gt_-40dbfs`: rough audible duration.
- `top_peaks`: transient or motion peaks.
- `side_to_mid_db`: stereo width; higher values such as `-8 dB` are wider than `-30 dB`.
- `centroid` and `roll85`: brightness and upper energy range.
- `bands`: low/mid/high energy distribution for prompt iteration.
