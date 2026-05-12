# 2026-05-11 ElevenLabs 复杂游戏技能音效 Prompt

Status: raw
Confidence: confirmed
Task: 参考 ElevenLabs Help Center，整理复杂游戏技能音效的提示词写法并整合到 wiki
Sources:
- https://help.elevenlabs.io/hc/en-us/articles/25735604945041-How-do-I-prompt-for-sound-effects
- wiki/ElevenLabs 音效生成.md
- wiki/Unreal 音频系统与 MetaSounds.md

Observation:
ElevenLabs Help Center 说明复杂 prompt 可以描述多个事件，但通常最佳做法是把复杂音效拆成单个音效分别生成，再在音频编辑器里组合。复杂游戏技能音效应按 charge、cast、travel、impact、tail、ambience 等阶段拆分，每个 prompt 聚焦一个阶段和一个声学目标，再在 DAW、MetaSound、FMOD 或 Wwise 中分层和随机化。

Verification:
已核对 Help Center 对 simple prompt、detailed prompt、complex prompt 和拆分组合的建议，并把结论整合进 `wiki/ElevenLabs 音效生成.md` 的 Prompt 写法部分。

Boundary:
这是 prompt 设计与生产流程建议，不代表 ElevenLabs 一次生成就能得到可直接上线的完整技能音效。复杂技能的节奏、动画同步、循环层、距离衰减、响度、分层比例和随机化仍需在 DAW 或游戏引擎音频系统中验证。
