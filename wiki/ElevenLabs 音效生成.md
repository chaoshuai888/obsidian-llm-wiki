---
confidence: confirmed
created: 2026-05-11
sources:
- raw/AI/2026-05-11-elevenlabs-sound-effects-docs.md
- https://elevenlabs.io/docs/eleven-api/guides/cookbooks/sound-effects
- https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert
- https://elevenlabs.io/docs/overview/capabilities/sound-effects
- https://elevenlabs.io/docs/eleven-creative/playground/sound-effects
- https://help.elevenlabs.io/hc/en-us/articles/25735604945041-How-do-I-prompt-for-sound-effects
- https://elevenlabs.io/docs/api-reference/authentication
- https://elevenlabs.io/docs/eleven-api/resources/libraries
- https://elevenlabs.io/docs/overview/models
- https://github.com/elevenlabs/skills/blob/main/sound-effects/SKILL.md
status: published
tags:
- elevenlabs
- sound-effects
- ai-audio
- game-audio
- audio-generation
title: ElevenLabs 音效生成
updated: '2026-05-11'
---

# ElevenLabs 音效生成

## 摘要

ElevenLabs Sound Effects 用文本描述生成短音效，适合 UI 声、Foley、环境声、电影冲击声、转场声、游戏技能声和短音乐元素。它不是游戏自适应音乐系统，也不是完整 DAW；复杂序列、长 BGM、分层音乐和互动音乐仍需要在 Reaper、Audacity、FMOD、Wwise、Unreal MetaSounds 或 Unity Audio Mixer 中整理和集成。

推荐把它当作“音频素材生成器”：

```text
音效需求表
-> ElevenLabs 生成多个候选
-> 人耳筛选
-> DAW 清理、裁剪、响度统一、循环点处理
-> 引擎或音频中间件中随机化、分层、空间化
```

## 两条使用路径

Playground 适合探索和人工挑选。进入 ElevenLabs 的 Sound Effects 页面，输入音效描述，设置时长或 auto，打开 Looping 可生成可循环素材，调节 Prompt influence 控制贴合 prompt 的程度。产品向导说明每次生成会给 4 个音效候选，生成后可在 History 中下载，常见下载格式包括 MP3 44.1 kHz 和 WAV 48 kHz。

API 适合批量生产和集成工具链。核心端点是：

```text
POST https://api.elevenlabs.io/v1/sound-generation
```

认证使用 `xi-api-key` header。API key 必须放在服务端、`.env`、CI secret 或托管密钥系统中，不要写入浏览器前端、仓库或可下载客户端。ElevenLabs 认证文档还支持给 API key 设置 endpoint scope 和 credit quota，生产环境建议使用受限 key。

## API 参数

`text` 是必填项，描述要生成的音效。

`model_id` 默认是 `eleven_text_to_sound_v2`。模型总览页把 `eleven_text_to_sound_v2` 描述为从文本 prompt 生成 sound effects 的模型。

`duration_seconds` 可为空。为空时由模型按 prompt 自动判断；指定时用于固定音效长度。官方页面均确认单次最大 30 秒，但下限描述不一致：capabilities overview 写 0.1 秒，API reference 和官方 sound-effects skill 写 0.5 秒。落地实现时按 API reference 的 0.5 到 30 秒处理，遇到 `422` 参数错误时回退修正。

`prompt_influence` 默认 `0.3`，范围 0 到 1。数值越高越贴合 prompt，同时变化更少；数值越低越容易出现创造性变体。UI 点击、短技能声、严格品牌声建议偏高；环境声、氛围、灵感探索可用中低值。

`loop` 默认 `false`，只适用于 `eleven_text_to_sound_v2`。适合雨声、风声、机器底噪、魔法能量层、空间 ambience、drone 等需要无缝循环的素材。对一次性点击、冲击、爆炸、脚步单响不要打开。

`output_format` 是 query parameter，格式形如 `mp3_44100_128`。API reference 说明高码率 MP3、PCM 等格式会受套餐限制；官方 skill 列出了常用 MP3、PCM、Opus、u-law、a-law 形式。不要把格式能力写死，批量导出前用目标账号实际请求验证。

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

client = ElevenLabs(api_key=api_key)

audio = client.text_to_sound_effects.convert(
    text="Short crisp sci-fi UI confirm click, bright digital blip, one-shot, no reverb",
    duration_seconds=1.0,
    prompt_influence=0.7,
    loop=False,
    model_id="eleven_text_to_sound_v2",
)

out = Path("ui_confirm.mp3")
with out.open("wb") as f:
    for chunk in audio:
        f.write(chunk)
```

官方 quickstart 还演示了直接 `play(audio)` 播放结果。实际项目里更建议先落盘，记录 prompt 和参数，再进入人工试听与后期处理。

## cURL 示例

```bash
curl -X POST "https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Deep cinematic braam for a horror trailer impact, sub bass swell, metallic tail",
    "duration_seconds": 3,
    "prompt_influence": 0.5,
    "loop": false,
    "model_id": "eleven_text_to_sound_v2"
  }' \
  --output horror_braam.mp3
```

## Prompt 写法

基础公式：

```text
声源 + 动作 + 材质/空间 + 风格 + 用途 + 约束
```

简单音效用短句，先让模型聚焦单一事件。例如：`glass shattering on concrete`、`heavy wooden door creaking open`、`thunder rumbling in the distance`。

更稳定的制作 prompt 可以补充录音质量、材质、距离、空间和用途。例如：

```text
High-quality professionally recorded leather boot footsteps on wet concrete,
close microphone, foley sound effect, no music
```

复杂序列可以描述事件顺序，但官方 Help Center 建议最佳实践是拆成单独音效再在音频编辑器里组合。比如“走廊脚步、开门、摔下楼梯”不要一次生成一个长 prompt；更可控的做法是分别生成脚步、门轴、跌落冲击和滚落碎响。

常用术语：

- `impact`：撞击、命中、落地、爆裂。
- `whoosh`：挥动、飞行、转场、技能释放前摇。
- `ambience`：场景底噪和环境气氛。
- `one-shot`：单次触发音效。
- `loop`：可重复播放的循环片段。
- `stem`：可分层使用的孤立音频组件。
- `braam`：预告片式低频铜管冲击。
- `glitch`：故障、卡顿、数字破碎。
- `drone`：持续音色，用于悬疑、空间感或能量层。

## 参数配方

UI 点击和菜单反馈：

```text
duration_seconds: 0.5 到 1.2
prompt_influence: 0.6 到 0.9
loop: false
prompt: Short crisp 8-bit menu select click, bright, one-shot, no music
```

脚步、布料、道具 Foley：

```text
duration_seconds: auto 或 1 到 4
prompt_influence: 0.5 到 0.8
loop: false
prompt: Professional foley, leather gloves tightening, close microphone, dry studio
```

技能、魔法、武器：

```text
duration_seconds: 1 到 5
prompt_influence: 0.4 到 0.7
loop: false
prompt: Arcane ice projectile charging then sharp crystal impact, fantasy game spell, no music
```

环境循环：

```text
duration_seconds: 10 到 30
prompt_influence: 0.3 到 0.6
loop: true
prompt: Seamless forest night ambience loop, soft wind through leaves, distant insects, no birdsong
```

电影冲击和转场：

```text
duration_seconds: 2 到 6
prompt_influence: 0.4 到 0.7
loop: false
prompt: Dark cinematic riser into deep braam impact, horror trailer transition, sub bass tail
```

## 批量生产流程

先建音效需求表，至少包含 `asset_id`、用途、prompt、时长、是否循环、输出格式、目标响度、备注。不要只存最终音频文件，prompt 和参数是复现、再生成和风格统一的关键。

每个音效先生成 4 到 12 个候选。Playground 自带每次 4 个候选；API 批量时可重复请求同一 prompt 并保存不同编号。对同类 UI 声、脚步、命中声，保留多个可用变体比追求单个“完美音效”更适合游戏。

筛选后进入 DAW 做基础处理：裁剪静音、淡入淡出、响度统一、必要 EQ、瞬态修正、去掉不需要的音乐性尾巴。循环素材必须单独检查循环点；即使开启 `loop`，也建议在目标引擎中实际循环播放 1 到 2 分钟确认没有明显跳变。

导入引擎时再做运行时变化：随机 pitch、随机 volume、分层播放、距离衰减、混响发送、材质切换、MetaSounds/FMDO/Wwise 参数驱动。ElevenLabs 负责生成基础素材，引擎和中间件负责让素材在玩法中不机械重复。

## 适用边界

适合：

- 游戏 UI、技能、武器、道具、环境声、怪物声和过场转场。
- 视频、播客、有声书、广告和短片中的 Foley 或氛围素材。
- 原型期快速补齐音效，或为声音设计师提供候选方向。

不适合单独承担：

- 长篇完整 BGM 或复杂歌曲结构。
- 需要 stem、拍点同步、phase sync、adaptive music 的互动音乐系统。
- 严格拟真、必须和画面逐帧同步的复杂 Foley 场景。
- 未经人工审核的商用批量发布。

如果目标是完整音乐，官方 capabilities 页面也提示应使用 Music API。若目标是游戏内动态音乐，通常要把 Music API、DAW stem、FMOD/Wwise/MetaSounds 组合起来，而不是只依赖 Sound Effects。

完整游戏 BGM 的 ElevenLabs 路线见 [[ElevenLabs 游戏 BGM 生成]]。Sound Effects 只适合短循环、stinger、氛围层和非音乐音效，不应作为 BGM 主工具。

## 常见失败与处理

结果太散：提高 `prompt_influence`，缩短 prompt，移除互相冲突的形容词。

结果太死板：降低 `prompt_influence`，多生成候选，加入风格或空间描述。

复杂序列不准确：拆成多个 one-shot，在 DAW 或引擎时间轴中组合。

循环有跳点：使用 `loop: true`，把 prompt 写成 seamless loop，并在 DAW 或引擎中实测循环；必要时手工交叉淡化。

音效像音乐或带旋律：明确加入 `sound effect`、`one-shot`、`no music`、`foley`、`dry` 等约束。

参数报 422：检查 `duration_seconds`、`prompt_influence`、`loop` 与 `model_id`，尤其按 API reference 使用 0.5 到 30 秒。

输出格式不符合预期：确认 `output_format` 写在 query parameter 中，并核对当前套餐是否支持目标码率或 PCM。

## Codex 使用提示

当用户要求生成游戏或应用音效时，先把需求整理成表格，而不是直接写一串 prompt。每条音效至少确认用途、长度、是否循环、风格、禁用元素和目标平台。

写工具集成时优先把 API key 从环境变量读取；不要把 key、内网地址或生成音频的临时目录写进 wiki 或提交到仓库。

如果要把 ElevenLabs 生成的音效接入 Unreal 或 Unity，下游验证比 API 调通更重要：要在实际音量、混音总线、空间化和重复播放条件下听。短 UI 声和脚步声尤其需要多变体和随机化。

Unreal 项目中的后续集成可参考 [[Unreal 音频系统与 MetaSounds]]，尤其是 Sound Wave 导入、MetaSound 随机化、Attenuation、Concurrency、Sound Class 和 Submix 路由。

## 验证

- Sound Effects quickstart 确认 Python SDK 可调用 `text_to_sound_effects.convert(...)` 并生成音频。
- API reference 确认端点为 `POST /v1/sound-generation`，请求字段包括 `text`、`loop`、`duration_seconds`、`prompt_influence`、`model_id`，响应是生成音频。
- API reference 确认 `loop` 仅适用于 `eleven_text_to_sound_v2`，`prompt_influence` 范围为 0 到 1，默认 0.3。
- Capabilities overview 确认最大时长 30 秒、可生成电影音效、游戏音效、Foley、环境声和短音乐元素，并提示完整音乐应使用 Music API。
- Product guide 确认 Playground 每次生成 4 个候选，并可从 History 下载。
- Help Center 确认复杂多事件 prompt 虽可理解，但最佳结果通常来自拆分单个音效后在音频编辑器中组合。
