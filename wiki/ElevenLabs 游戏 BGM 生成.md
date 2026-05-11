---
confidence: confirmed
created: 2026-05-11
sources:
- raw/AI/2026-05-11-elevenlabs-game-bgm-docs.md
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
status: published
tags:
- elevenlabs
- bgm
- game-audio
- ai-music
- unreal-engine
- dynamic-music
title: ElevenLabs 游戏 BGM 生成
updated: '2026-05-11'
---

# ElevenLabs 游戏 BGM 生成

## 摘要

生成游戏 BGM 应优先使用 Eleven Music，而不是 Sound Effects。Sound Effects 适合 30 秒内的短音效、循环环境声和 stinger；Eleven Music 可生成完整音乐轨、纯器乐、带结构的段落、游戏配乐、预告片音乐和场景氛围。

推荐定位：

```text
Eleven Music = BGM / 配乐 / 音乐 stem 草稿
ElevenLabs Sound Effects = UI / 技能 / Foley / stinger / ambience layer
DAW = 剪辑、响度、循环点、stem 清理
Unreal MetaSounds / Quartz / FMOD / Wwise = 游戏内动态音乐系统
```

核心结论：Eleven Music 可以生成游戏中可用的 BGM 素材，但不能直接替代游戏动态音乐系统。真正能在游戏里稳定使用，还需要循环点校正、响度统一、分层、状态切换、节拍同步和引擎内混音。

## 使用方式

ElevenCreative 网页适合人工创作。创建 Music 项目，输入自然语言 prompt，选择 Finetune、Variants 和 Duration。官方产品向导建议复杂歌曲可以先生成 30 秒短段，再逐步添加 section。生成后可在编辑器里修改歌词、添加/删除段落、调整段落时长和风格关键词，再导出音频。

Music API 适合批量生产和工具链集成。核心端点：

```text
POST https://api.elevenlabs.io/v1/music
```

相关端点：

```text
POST /v1/music/plan             # 从 prompt 创建 composition plan
POST /v1/music/detailed         # 返回 composition plan、metadata 和音频
POST /v1/music/stream           # 流式生成音乐
POST /v1/music/video-to-music   # 从一个或多个视频生成背景音乐
POST /v1/music/upload           # 上传音乐供 inpainting 使用，企业功能
POST /v1/music/stem-separation  # 把音频分离成 stems
```

API access 当前面向付费订阅用户。API key 必须放在服务端环境变量或密钥管理系统里，不要写进前端、游戏客户端、仓库或 wiki。

## API 参数

`prompt` 是简单生成入口。描述音乐的用途、场景、风格、情绪、乐器、速度、调性、结构和禁止项。API reference 限制 prompt 长度不超过 4100 字符。`prompt` 和 `composition_plan` 不能同时使用。

`composition_plan` 是结构化生成入口。它包含全局正向/负向风格、sections、每段 local styles、duration 和 lyrics lines。适合菜单、探索、战斗、Boss、结算、过场这类需要固定段落结构的 BGM。

`music_length_ms` 只和 `prompt` 一起使用，用毫秒指定生成长度。API reference 当前写作 3000 到 600000ms；但 overview/product guide 仍有 3 秒到 5 分钟的描述。项目里应以实际端点和账号权限为准。

`model_id` 当前为 `music_v1`。

`force_instrumental` 只和 `prompt` 一起使用。生成游戏 BGM 时通常设为 `true`，避免模型自动加入人声或歌词。若使用 `composition_plan`，应通过空 lyrics、`instrumental only`、负向风格和 section 描述约束无 vocals。

`respect_sections_durations` 只和 `composition_plan` 一起使用。为 true 时更严格遵守每段 `duration_ms`；为 false 时模型可微调段落长度，通常质量和延迟可能更好，但总时长仍保持。游戏循环和拍点对齐更重视稳定段落长度，优先 true；概念草稿可尝试 false。

`seed` 用于让同参数生成更一致，但官方明确不保证完全可复现，并说明系统更新后输出可能变化。API reference 当前还标注 seed 不能和 prompt 同用，使用前要按 SDK 和端点实测。

`output_format` 是 query parameter，格式类似 `mp3_44100_192` 或 PCM/Opus 等枚举。高码率 MP3、PCM 和高质量下载受套餐限制。给游戏引擎导入时，优先导出高质量源文件，再由引擎或构建管线压缩到平台格式。

`sign_with_c2pa` 可为 MP3 签 C2PA。适合需要内容来源标记或外部分发的素材；游戏内部运行时通常不是第一优先级。

## Python 最小示例

```python
import os
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
if api_key is None:
    raise RuntimeError("ELEVENLABS_API_KEY is not set")

elevenlabs = ElevenLabs(api_key=api_key)

track = elevenlabs.music.compose(
    prompt=(
        "Instrumental only. Seamless-feeling dark fantasy dungeon exploration BGM, "
        "90 BPM in D minor, low strings, soft frame drums, distant choir pads, "
        "subtle tension, no vocals, no lyrics, no hard ending, suitable for looping in a roguelike game."
    ),
    music_length_ms=60_000,
    model_id="music_v1",
    force_instrumental=True,
)

out = Path("bgm_dungeon_exploration.mp3")
with out.open("wb") as f:
    for chunk in track:
        f.write(chunk)
```

生成结果不应直接进项目。先在 DAW 里检查开头、结尾、响度、循环点、动态范围和是否混入不想要的人声或标志性旋律。

## cURL 示例

```bash
curl -X POST "https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Instrumental only. Fast cyberpunk combat loop for a twin-stick shooter, 140 BPM, aggressive synth bass, tight electronic drums, glitch percussion, short risers, no vocals, no lyrics, no fade out.",
    "music_length_ms": 90000,
    "model_id": "music_v1",
    "force_instrumental": true
  }' \
  --output combat_cyberpunk.mp3
```

## Composition Plan 用法

简单 prompt 适合探索方向；composition plan 适合游戏音乐生产。原因是游戏 BGM 往往不只是“一首歌”，而是 intro、loop、layer、stinger、transition 和 outro 的组合。

先让 API 创建 plan：

```python
composition_plan = elevenlabs.music.composition_plan.create(
    prompt=(
        "Instrumental only. 120 seconds of heroic fantasy battle music for a tactical RPG. "
        "Orchestral percussion, low brass, strings ostinato, no vocals. "
        "Structure: short intro, main loop, higher intensity loop, clean ending."
    ),
    music_length_ms=120_000,
    model_id="music_v1",
)
```

然后人工检查并修改 plan。游戏 BGM 常见 section：

```text
Intro: 4 到 8 秒，进入战斗或场景时播放一次
Loop A: 30 到 60 秒，普通探索或普通战斗
Loop B: 30 到 60 秒，高危、低血量、Boss phase
Stinger: 3 到 8 秒，胜利、失败、发现、转场
Outro: 4 到 10 秒，退出场景或结算
```

生成时传入 plan：

```python
track = elevenlabs.music.compose(
    composition_plan=composition_plan,
    model_id="music_v1",
    respect_sections_durations=True,
)
```

对严格循环音乐，composition plan 只能帮助段落结构，不等于自动无缝 loop。仍需在 DAW 中手动找零交叉点、裁掉尾部混响、做 crossfade，必要时导出 Loop Start/Loop End metadata 或在引擎中用 Quartz/FMOD/Wwise 对齐。

## Prompt 模板

基础模板：

```text
Instrumental only. <游戏场景> BGM for <玩法/镜头/状态>,
<genre/style>, <tempo BPM>, <key>,
<instrumentation>, <mood>,
structure: <intro/loop/stinger/outro>,
avoid: vocals, lyrics, fade out, copyrighted artist references.
```

菜单：

```text
Instrumental only. Main menu BGM for a cozy fantasy strategy game,
80 BPM in G major, warm strings, soft harp, gentle woodwinds, subtle magical shimmer,
calm and hopeful, no vocals, no lyrics, no dramatic climax.
```

探索循环：

```text
Instrumental only. Seamless-feeling exploration loop for an underground ruins level,
95 BPM in E minor, muted percussion, low drones, sparse plucked strings,
mysterious but not too dark, no vocals, no lyrics, avoid strong melody hooks, no fade out.
```

战斗：

```text
Instrumental only. High-energy combat BGM for an action roguelike,
150 BPM in C minor, driving drums, distorted synth bass, aggressive strings,
loop-friendly structure, rising tension but no final cadence, no vocals.
```

Boss：

```text
Instrumental only. Two-phase boss battle music, dark orchestral electronic hybrid,
Phase A: ominous low brass and taiko pulse, Phase B: faster strings and choir-like synth pads,
140 BPM, no vocals, no lyrics, no existing artist references.
```

胜利 stinger：

```text
Instrumental only. Short 5-second victory stinger for a fantasy tactics game,
bright brass flourish, cymbal swell, uplifting final chord, no vocals.
```

## 游戏 BGM 生产流程

先写音乐需求表：

```text
asset_id
scene/state
duration
BPM/key
loop or one-shot
required sections
instrumentation
forbidden elements
target engine integration
license/account note
```

第一轮用短时长快速探索风格。网页端可用多个 variants；API 端可重复生成多个候选并保存 prompt、参数、song-id 和文件名。不要只保存 MP3，必须保留 prompt、plan、账号计划和日期。

第二轮用 composition plan 固定结构。把可用候选拆成 intro、loop、stinger、outro 的目标长度，再生成更接近生产结构的版本。

第三轮做 DAW 处理。检查循环点、尾部混响、响度、动态范围、频段占用、转场边界。游戏 BGM 通常要给对白、UI 和战斗音效留空间，不要让音乐一直占满 1 到 5 kHz。

第四轮进引擎或中间件。Unreal 可用 Sound Wave、MetaSound、Quartz、Sound Class、Submix 和 Audio Modulation；FMOD/Wwise 可做 segment、transition、vertical remixing 和 state switch。Eleven Music 产物只是素材层，动态逻辑仍在引擎或中间件里。

## 动态音乐与 stem

Eleven Music v1 prompt guide 说明，模型不直接从一条完整生成中输出真正可控 stems；想获得更强控制，可以用更定向的 prompt 生成 solo instrument 或 a cappella 片段。

Music API 当前提供 `POST /v1/music/stem-separation`，可上传音频并返回 ZIP stems。`stem_variation_id` 支持 `two_stems_v1` 和 `six_stems_v1`。这对游戏动态音乐有用，但它是分离结果，不等于作曲阶段原生 stem。导入游戏前必须逐轨听：鼓、bass、instrument、vocal 分离可能有串音、相位和瞬态损伤。

适合用 stem 的场景：

- 战斗强度上升时逐步加 percussion、bass、high strings。
- 潜行暴露时加入 high tension layer。
- Boss phase 切换时加 choir pad 或 distorted synth layer。
- 对话播放时 duck melody 或 high-frequency layer。

不适合把 stem separation 当作万能方案。若项目真的需要高质量 adaptive music，最好从一开始就用 composition plan 或多次 prompt 生成各层，并在 DAW 中按同 BPM/key 对齐。

## Video To Music

`POST /v1/music/video-to-music` 可从一个或多个视频生成背景音乐。官方 API reference 说明视频会按顺序合并，可选 `description` 和最多 10 个 style tags，最多 10 个视频，总大小 200MB，总时长 600 秒。

适用场景：

- 给 gameplay capture 快速生成 trailer BGM。
- 根据关卡 walkthrough 生成氛围草稿。
- 为广告、商店页、宣传片做配乐方向。

不建议直接把 video-to-music 作为游戏运行时 BGM 生产主路径。它更适合“看画面配音乐”，而不是生产可循环、可分层、可互动的游戏内音乐。

## 版权与商业使用

不要在 prompt 中写真实艺术家名、乐队名、歌曲名、专辑名、音乐厂牌名、音乐出版公司名，或大段已有歌词。Music quickstart 说明这类 prompt 可能返回 `bad_prompt`；Music Terms 也明确列出 prohibited inputs。

独立游戏可行性较高。Eleven Music v1 Terms 当前把 independent interactive media，例如 indie games，列为 self-serve 与 Enterprise Music Lite permitted commercial use 示例。

大型商业发行要谨慎。Music API 产品页和 v1 Terms 当前说明 film、TV、radio 和 large studio games 不包含在 self-serve media rights 中；large studio game rights 需要 Enterprise Music。正式商业项目应在立项或发布前复核最新 Music Terms，并保留账号计划、生成日期、song-id、prompt、plan、下载文件和条款版本。

Free plan 不能当作商业游戏素材来源。Help Center 说明 free plan 不包含商业 license；付费计划的商用也要受 Music Terms、Prohibited Use Policy 和 plan 限制约束。

## 导入 Unreal 的建议

Unreal 中的后续集成参考 [[Unreal 音频系统与 MetaSounds]]。

普通 BGM：

```text
Sound Wave -> Music Sound Class -> Music Submix
```

循环 BGM：

```text
DAW 修循环点
-> Sound Wave
-> MetaSound 或 Audio Component
-> Allow Play when Silent / Virtualization 按需配置
```

动态 BGM：

```text
Intro / Loop A / Loop B / Stinger / Outro
-> Quartz 按小节触发
-> Audio Modulation 或 Sound Class 控制状态混音
-> Submix 做 ducking、EQ、limiter
```

如果音乐要和玩法节拍同步，用 Quartz 或 FMOD/Wwise 的音乐时间线，不要靠 Blueprint Delay 猜时间。

## 常见失败与处理

生成了人声：设置 `force_instrumental: true`，prompt 第一行写 `Instrumental only`，并加入 `no vocals, no lyrics`。

不像循环：prompt 写 `loop-friendly`、`no fade out`、`no final cadence`，但最终仍要在 DAW 修循环点。

旋律太抢对白：prompt 降低 melody density，减少高频 lead，DAW 中让 1 到 5 kHz 给对白和 UI 留空间。

战斗音乐太满：把鼓、bass、lead、pad 分层生成或做 stem separation，在引擎里按状态混音。

BPM/key 不稳：prompt 明确 BPM/key，并在 DAW 中校正；需要严密同步时不要只依赖模型。

结构不可控：先用 `/v1/music/plan` 生成 plan，再人工调整 section duration 和 local styles。

素材授权不确定：不要发布；先查 Music Terms、账号计划、项目规模和发行方式。

## Codex 使用提示

当用户要“用 ElevenLabs 做游戏 BGM”时，先区分三类需求：

- 只要一条菜单/关卡背景音乐：用 prompt + `force_instrumental`。
- 需要战斗/探索状态切换：用 composition plan，后续进 Unreal/FMOD/Wwise。
- 需要动态 stem：优先规划同 BPM/key 的多层生成，stem separation 作为辅助，不当作唯一方案。

回答或写脚本时不要把 Sound Effects API 当作 BGM 主工具；它只适合短循环、stinger 和音效层。

## 验证

- Eleven Music capabilities 和 Help Center 确认 Eleven Music 是从自然语言 prompt 生成高保真音乐的模型，支持完整音乐、纯器乐、结构控制和游戏/媒体配乐用途。
- Music quickstart 确认 Python SDK 可用 `elevenlabs.music.compose(...)` 生成音乐，Music API 仅面向 paid users。
- Compose music API reference 确认 `POST /v1/music`，支持 `prompt` 或 `composition_plan`、`music_length_ms`、`model_id=music_v1`、`force_instrumental`、`respect_sections_durations`、`output_format`。
- Create composition plan API reference 确认 `POST /v1/music/plan` 可从 prompt 创建 plan，且不消耗 credits 但受 rate limiting。
- Video To Music API reference 确认 `POST /v1/music/video-to-music` 可从一个或多个视频生成背景音乐。
- Stem Separation API reference 确认 `POST /v1/music/stem-separation` 返回包含分离 stems 的 ZIP。
- Music Terms 和 Eleven Music v1 Terms 确认 Music 输入、商业使用、plan 权限和 large studio games 边界需要按当前条款复核。
