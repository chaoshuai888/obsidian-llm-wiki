# 2026-05-11 ElevenLabs Sound Effects 官方文档调研

Status: raw
Confidence: confirmed
Task: 阅读 ElevenLabs Sound Effects quickstart，并搜索类似官方文档，沉淀一份使用 ElevenLabs 生成音效的文档
Sources:
- https://elevenlabs.io/docs/eleven-api/guides/cookbooks/sound-effects
- https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert
- https://elevenlabs.io/docs/overview/capabilities/sound-effects
- https://elevenlabs.io/docs/eleven-creative/playground/sound-effects
- https://help.elevenlabs.io/hc/en-us/articles/25735604945041-How-do-I-prompt-for-sound-effects
- https://elevenlabs.io/docs/api-reference/authentication
- https://elevenlabs.io/docs/eleven-api/resources/libraries
- https://elevenlabs.io/docs/overview/models
- https://github.com/elevenlabs/skills/blob/main/sound-effects/SKILL.md

Observation:
ElevenLabs Sound Effects 可通过 Playground 或 `POST /v1/sound-generation` 从文本生成音效，常用参数是 `text`、`duration_seconds`、`prompt_influence`、`loop` 和 `model_id`。官方文档把它定位为电影/预告片音效、游戏与交互媒体音效、Foley、环境声和短音乐元素生成；完整歌曲或复杂音乐制作应转向 Music API 或后期音频工作流。

Verification:
已读取 quickstart、API reference、capabilities overview、Playground 产品向导、Help Center prompt 说明、认证说明、SDK 列表、模型列表和官方 GitHub sound-effects skill。API reference 确认端点为 `https://api.elevenlabs.io/v1/sound-generation`，默认模型为 `eleven_text_to_sound_v2`，`loop` 仅适用于该 v2 模型。

Boundary:
ElevenLabs 文档当前对 `duration_seconds` 下限存在不一致：capabilities overview 写作 0.1 到 30 秒，API reference 与官方 skill 写作 0.5 到 30 秒。实现时优先以 API reference 和实际 API 校验为准，并把 422 参数错误作为需要回退或修正的信号。价格、套餐、输出格式限制和授权条款可能随时间变化，商用或大批量生产前需要重新验证官方最新说明。
