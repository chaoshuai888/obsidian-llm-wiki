# 2026-05-12 旋风斩循环层音效提示词写法

Status: raw
Confidence: likely
Task: 讨论生成游戏角色旋风斩技能音效时，是否应去掉游戏概念并提炼为声音描述
Sources:
- 本轮用户反馈：提示词中去掉游戏概念；只做巨剑快速旋转划过空气的循环旋转层；不要尾音消散
- wiki/ElevenLabs 音效生成.md
- raw/AI/2026-05-12-elevenlabs-sfx-prompt-writing.md

Observation:
为 ElevenLabs Sound Effects 写技能音效 prompt 时，最终喂给模型的文本可以去掉 `game`、`RPG`、`skill`、`character` 等概念词，改为直接描述可听见的声学事件。以旋风斩为例，循环层应聚焦“巨剑高速旋转划过空气”：oversized heavy sword、rotating fast through air、repeating deep blade whooshes、dense circular wind vortex、wide stereo rotation；如果只做循环旋转层，应显式排除 impact、tail ending、music、vocals 和 melody。

Verification:
已根据现有 wiki 的 prompt 写法原则进行人工推导：先从游戏概念拆出声音主体、动作、运动方式、空气/金属质感、空间运动和排除项，再形成一个单一循环层 prompt。该 prompt 尚未调用 ElevenLabs 生成并试听，因此效果需通过实际生成候选和循环播放验证。

Boundary:
这是针对技能音效“循环层”的提示词写法，不适用于完整技能一条生成。完整旋风斩仍应拆成 wind-up、loop、hit、tail 等层；本条只记录 loop 层如何避免命中声、结束声和游戏概念干扰。
