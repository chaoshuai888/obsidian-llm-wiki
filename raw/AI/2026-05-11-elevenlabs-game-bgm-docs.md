# 2026-05-11 ElevenLabs 游戏 BGM 生成官方文档调研

Status: raw
Confidence: confirmed
Task: 看如何使用 ElevenLabs 生成游戏中使用的 BGM，并沉淀为文档
Sources:
- https://elevenlabs.io/docs/overview/capabilities/music
- https://elevenlabs.io/docs/eleven-creative/products/music
- https://elevenlabs.io/docs/eleven-api/guides/cookbooks/music
- https://elevenlabs.io/docs/api-reference/music/compose
- https://elevenlabs.io/docs/api-reference/music/stream
- https://elevenlabs.io/docs/api-reference/music/compose-detailed
- https://elevenlabs.io/docs/api-reference/music/create-composition-plan
- https://elevenlabs.io/docs/api-reference/music/video-to-music
- https://elevenlabs.io/docs/api-reference/music/upload
- https://elevenlabs.io/docs/api-reference/music/separate-stems
- https://elevenlabs.io/docs/best-practices/prompting/eleven-music/
- https://help.elevenlabs.io/hc/en-us/articles/37780368848785-What-is-Eleven-Music
- https://elevenlabs.io/music-api
- https://elevenlabs.io/music-terms
- https://elevenlabs.io/eleven-music-v1-terms

Observation:
ElevenLabs 已有专门的 Eleven Music / Music API，可从自然语言 prompt 或 composition plan 生成音乐，适合游戏 BGM、预告片配乐、菜单音乐、战斗音乐和场景氛围音乐。API 的核心端点包括 `POST /v1/music`、`POST /v1/music/plan`、`POST /v1/music/detailed`、`POST /v1/music/stream`、`POST /v1/music/video-to-music` 和 `POST /v1/music/stem-separation`。

Verification:
已核对 Eleven Music capabilities、ElevenCreative Music 产品向导、Music quickstart、Compose/Stream/Detailed/Plan/Video-to-Music/Upload/Stem Separation API reference、Prompting Eleven Music、Help Center、Music API 产品页、Music Terms 和 Eleven Music v1 Terms。官方文档确认 Music API 面向付费订阅者，支持 `music_v1`、`music_length_ms`、`force_instrumental`、composition plan、流式生成、视频转音乐和 stem separation。

Boundary:
Eleven Music 生成的是音乐素材，不是完整游戏动态音乐系统。循环点、stem 质量、横向重编排、纵向分层、节拍同步、状态切换和游戏内混音仍需 DAW、Unreal MetaSounds/Quartz、FMOD 或 Wwise 处理。官方页面对最大生成时长存在差异：overview/product guide 提到 5 分钟，API reference 和 Music API FAQ 当前显示 `music_length_ms` 最高 600000ms。落地时应以实际使用端点、账号权限、返回错误和最新条款为准。商业发行还需核对 Music Terms：独立互动媒体示例被列为 permitted self-serve use，但 large studio games 需要 Enterprise Music 权限。
