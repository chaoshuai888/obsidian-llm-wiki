# 2026-05-08 Feedback

Status: review
Related: raw/AI/工程技术：在智能体优先的世界中利用_Codex.md
Trigger: failed_build

What was wrong:
`olw ingest` could not process the raw note because the configured local Ollama provider was unavailable.

Correction:
Preferred path: start/install Ollama and make sure the configured models are available: `gemma4:e4b`, `qwen2.5:14b`, and `nomic-embed-text`.

Fallback path: when the local machine does not have the required `olw` models, use the current Codex or Claude Code session to perform an equivalent Markdown ingest, then write the result as a human-reviewable draft under `wiki/.drafts/` rather than publishing directly.

Evidence:
- Command: `olw ingest D:\obsidian-llm-wiki\raw\AI\工程技术：在智能体优先的世界中利用_Codex.md --force`
- Error: `Ollama not running. Start it with: ollama serve`
- Command: `where.exe ollama`
- Error: `INFO: Could not find files for the given pattern(s).`
- User correction on 2026-05-08: when local `olw` models are unavailable, use the current Codex or Claude Code session.
