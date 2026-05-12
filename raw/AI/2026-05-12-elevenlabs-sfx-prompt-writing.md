# 2026-05-12 ElevenLabs 音效提示词写法改进

Status: raw
Confidence: confirmed
Task: 将如何更好的写音效提示词沉淀到 wiki
Sources:
- https://elevenlabs.io/docs/eleven-agents/best-practices/prompting-guide
- https://help.elevenlabs.io/hc/en-us/articles/25735604945041-How-do-I-prompt-for-sound-effects
- https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert
- wiki/ElevenLabs 音效生成.md

Observation:
ElevenLabs Sound Effects 的最终 prompt 应描述可听见的声音事件，而不是长篇剧情或视觉设定。更稳定的写法是把 prompt 拆成声源、动作/包络、材质/质感、运动、空间/混音、用途/风格、时长和排除项；复杂技能音效应拆成 charge、cast、travel、impact、tail、ambience 等阶段分别生成。

Conversational AI Prompting Guide 对直接生成音效不是主文档，但它的结构化提示、简洁指令、Guardrails、示例和测试迭代原则适合迁移到“音效 prompt 生成器”的 system prompt：让生成器稳定输出固定字段、禁止音乐/人声/歌词等元素，并按试听失败原因做 targeted refinements。

Verification:
ElevenLabs Agents prompting guide 确认清晰分区、简洁指令、Guardrails、工具参数说明和测试迭代能提升 prompt 可靠性。ElevenLabs Sound Effects Help Center 确认简单 prompt、细节 prompt 和复杂 prompt 都可用，但复杂多事件通常应拆分为单独音效后在音频编辑器中组合。Sound Effects API reference 确认可用 `duration_seconds`、`loop`、`prompt_influence` 等参数配合 prompt 控制结果。

Boundary:
这是 prompt 设计和生产流程知识，不保证 ElevenLabs 单次生成即可得到可上线音频。最终仍需人工试听、候选对比、DAW 后期、循环点检查、响度统一，以及在 Unreal、Unity、FMOD 或 Wwise 中验证播放效果。
