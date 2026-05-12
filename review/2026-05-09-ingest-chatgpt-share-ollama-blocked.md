# 2026-05-09 ChatGPT 分享 ingest 被 Ollama 阻塞

Status: review
Related:
- raw/AI/2026-05-09-ai-game-audio-tools-chatgpt-share.md
- wiki/.drafts/AI 游戏音频生产工具链.md
Trigger: failed_build

What was wrong:
执行 `olw ingest raw/AI/2026-05-09-ai-game-audio-tools-chatgpt-share.md` 时失败。原因不是 raw 文档格式错误，而是本机本地 Ollama 未运行，且 `wiki.toml` 中配置的模型不可用。

Correction:
保留解析出的 ChatGPT share raw 笔记，并在 `wiki/.drafts/` 下创建人工可审阅草稿，不直接发布到正式 `wiki/`。只有在 Ollama 正常运行且所需模型安装完成后，才重新执行 `olw ingest`。

Evidence:
- Command: `olw doctor`
- Result: `Ollama not running`
- `olw` 提示需要执行：`ollama serve`
- `olw` 提示需要安装模型：`ollama pull gemma4:e4b`、`ollama pull qwen2.5:14b`、`ollama pull nomic-embed-text`
- Command: `olw ingest raw\AI\2026-05-09-ai-game-audio-tools-chatgpt-share.md`
- Result: `Ollama not running`
