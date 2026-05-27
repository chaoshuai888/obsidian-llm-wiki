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
- raw/AI/2026-05-12-elevenlabs-sfx-prompt-writing.md
- https://elevenlabs.io/docs/eleven-agents/best-practices/prompting-guide
- raw/AI/2026-05-12-whirlwind-slash-sfx-prompt.md
status: published
tags:
- elevenlabs
- sound-effects
- ai-audio
- game-audio
- audio-generation
title: ElevenLabs 音效生成
updated: '2026-05-12'
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

`output_format` 是 query parameter，SDK 也可作为参数传入，格式形如 `pcm_44100` 或 `mp3_44100_128`。API reference 说明高码率 MP3、PCM 等格式会受套餐限制；官方 skill 列出了常用 MP3、PCM、Opus、u-law、a-law 形式。不要把格式能力写死，批量导出前用目标账号实际请求验证。使用 `pcm_44100` 时，API 返回的是 raw PCM，不是 WAV；最终要导入游戏或音频工具时，应再封装成带 `RIFF/WAVE` 头的 WAV。

## Python 最小示例

```python
import os
import wave
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
    output_format="pcm_44100",
    loop=False,
    model_id="eleven_text_to_sound_v2",
)

pcm_bytes = b"".join(audio)

out = Path("ui_confirm.wav")
with wave.open(str(out), "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(44100)
    wav.writeframes(pcm_bytes)
```

官方 quickstart 还演示了直接 `play(audio)` 播放结果。实际项目里更建议先落盘，记录 prompt 和参数，再进入人工试听与后期处理。

## cURL 示例

```bash
curl -X POST "https://api.elevenlabs.io/v1/sound-generation?output_format=pcm_44100" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Deep cinematic braam for a horror trailer impact, sub bass swell, metallic tail",
    "duration_seconds": 3,
    "prompt_influence": 0.5,
    "loop": false,
    "model_id": "eleven_text_to_sound_v2"
  }' \
  --output horror_braam.pcm
```

cURL 示例直接保存的是 raw PCM；如果最终需要 WAV，要用 Python `wave`、ffmpeg、sox 或项目音频管线封装为 44.1 kHz、16-bit、mono WAV。

## Prompt 写法

基础公式：

```text
声源 + 动作 + 材质/空间 + 风格 + 用途 + 约束
```

更可控的制作公式：

```text
声源/发声物 + 动作/包络 + 材质/质感 + 运动 + 空间/混音 + 用途/风格 + 时长 + 排除项
```

写音效 prompt 时，优先描述“能被听见的东西”，不要把篇幅花在剧情、镜头和世界观。`red dragon fireball` 不如 `large fiery whoosh into a short explosive impact, crackling ember tail, no music` 稳定；前者主要是概念，后者给了模型可生成的声学线索。

每个槽位的作用：

```text
声源/发声物：fire, glass, metal, leather, electricity, wind
动作/包络：click, crack, whoosh, swell, burst, impact, decay
材质/质感：brittle, wet, dusty, metallic, crystalline, smoky
运动：rising, falling, fast pass-by, spinning, pulsing, scattered
空间/混音：close microphone, dry studio, wide stereo, distant cave, short reverb
用途/风格：game UI, fantasy RPG spell, cinematic transition, realistic foley
时长：short one-shot, 1 second, 3 second tail, seamless loop
排除项：no music, no vocals, no melody, no intelligible speech
```

### 从游戏概念提炼为声音

写游戏技能音效时，需求表里可以保留 `旋风斩`、`火球术`、`冰锥` 这类游戏概念；但最终喂给 ElevenLabs 的 prompt 应优先写“能听见的声音”。如果模型容易生成得太音乐化、太剧情化或太泛，最终 prompt 可以去掉 `game`、`RPG`、`skill`、`character` 等概念词，只保留声音事件和约束。

转换步骤：

```text
1. 先写内部概念：旋风斩
2. 拆出声音主体：巨剑 / 重型刀刃 / 空气
3. 拆出动作：高速旋转 / 划过空气 / 重复呼啸
4. 拆出质感：低频空气压力 / 金属刃口微光 / 密集旋涡
5. 拆出空间：宽立体声旋转 / 环绕运动
6. 明确不要什么：no impact, no tail ending, no music
7. 再写最终 prompt
```

概念到声音的例子：

```text
旋风斩 -> oversized heavy sword rotating fast through air,
repeating deep blade whooshes, dense circular wind vortex

火球飞行 -> fast fiery whoosh, hot air pressure, crackling ember texture

冰锥发射 -> sharp icy whoosh, crystalline shimmer, cutting air movement

雷电链 -> rapid electric arcs, crackling zaps, bright transient jumps
```

如果只做循环层，不要写完整技能。循环层 prompt 要排除命中、爆发和结束尾音：

```text
Seamless loop sound effect, oversized heavy sword rotating fast through air,
repeating deep blade whooshes, dense circular wind vortex,
subtle metallic edge shimmer, strong low-frequency air movement,
wide stereo rotation, no impact, no tail ending, no music, no vocals, no melody
```

循环层参数建议：

```text
duration_seconds: 4 到 8
prompt_influence: 0.55 到 0.75
loop: true
```

Conversational AI Prompting Guide 对 Sound Effects 的帮助是间接的：它不负责告诉模型“火球应该怎么响”，但可以用来设计一个稳定的音效 prompt 生成器。把生成器的 system prompt 分成 `Goal`、`Output format`、`Rules`、`Examples`、`Failure fixes`，要求它输出固定字段和最终 prompt；把 `no music, no vocals, no melody`、每条 prompt 只描述一个事件、复杂技能必须拆阶段这类规则放进 Guardrails。这样比让模型自由发挥一大段描述更稳定。

音效 prompt 生成器的输出格式可以固定为：

```text
Asset: <asset_id>
Purpose: <where this sound is used>
Phase: <one-shot | loop | charge | cast | travel | impact | tail>
Duration: <seconds or auto>
Loop: <true | false>
Prompt influence: <0.0-1.0>
Final prompt: <one concise ElevenLabs prompt>
Notes: <what to check by ear>
```

好 prompt 通常有三层信息：先说声音事件，再说质感/空间，最后说禁用项。例如：

```text
Short sci-fi UI confirm click, bright glassy digital blip,
close and dry, one-shot, no music, no vocals
```

不稳定 prompt 的常见问题：

- 只写视觉或剧情：`an epic dragon attack in a burning castle`。
- 一条里塞太多事件：`charge, fly, hit, explode, burn the ground, enemies scream`。
- 形容词互相打架：`tiny massive soft explosive thunder click`。
- 忘记排除项，导致结果带旋律、人声或像音乐 stinger。
- 用抽象评价代替声音线索：`make it awesome, premium, powerful`。

把失败反馈转成 prompt 修改：

```text
太像音乐：加 sound effect, one-shot, no music, no melody；缩短时长。
太散：提高 prompt_influence，删掉次要设定，只保留一个声音事件。
太单薄：加入材质、低频/高频、尾音和空间描述。
太长或拖尾：指定 short transient, short decay, 0.8 seconds。
循环有跳点：写 seamless loop，开启 loop，并在 DAW/引擎里复听。
有可辨识人声：加 no vocals, non-verbal, no intelligible speech。
```

简单音效用短句，先让模型聚焦单一事件。例如：`glass shattering on concrete`、`heavy wooden door creaking open`、`thunder rumbling in the distance`。

更稳定的制作 prompt 可以补充录音质量、材质、距离、空间和用途。例如：

```text
High-quality professionally recorded leather boot footsteps on wet concrete,
close microphone, foley sound effect, no music
```

复杂序列可以描述事件顺序，但官方 Help Center 建议最佳实践是拆成单独音效再在音频编辑器里组合。比如“走廊脚步、开门、摔下楼梯”不要一次生成一个长 prompt；更可控的做法是分别生成脚步、门轴、跌落冲击和滚落碎响。

## 复杂游戏技能音效 Prompt

复杂技能音效不要只写一个超长 prompt。更稳定的做法是把技能拆成阶段和层，每个阶段单独生成 one-shot 或 loop，再在 DAW、MetaSound、FMOD 或 Wwise 中组合。

常见阶段：

```text
charge   蓄力、预警、能量聚集
cast     释放瞬间、手势、法阵触发
travel   飞行、挥砍、轨迹、弹道
impact   命中、爆炸、破碎、打击
tail     尾音、余烬、回响、消散
ambience 持续 aura、地面效果、环境层
```

通用模板：

```text
High-quality game sound effect, <element> <skill action>,
<phase>, <materials and texture>, <energy or movement>,
<camera distance or mix style>, one-shot, no music, no vocals, no melody
```

持续层模板：

```text
Seamless loop, high-quality game sound effect, <element> aura or ambience,
<texture>, <motion>, subtle variation, no music, no vocals, no melody
```

复杂技能的拆分示例：

```text
Fireball charge:
High-quality fantasy game sound effect, magical fireball charging in the caster's hands,
rising flame energy, soft crackling embers, low magical hum, close perspective,
one-shot, no music, no vocals, no melody

Fireball cast:
High-quality fantasy game sound effect, fireball spell released forward,
fast fiery whoosh, air pressure burst, bright ignition transient,
one-shot, no music, no vocals, no melody

Fireball impact:
High-quality fantasy game sound effect, fireball impact explosion on stone,
deep impact, burst of flames, debris, short sub bass punch, cinematic but game-ready,
one-shot, no music, no vocals, no melody

Fireball tail:
High-quality fantasy game sound effect, burning embers fading after a magic explosion,
small crackles, smoky fire tail, short decay, no music, no vocals, no melody
```

冰系技能：

```text
Ice charge:
High-quality fantasy game sound effect, ice magic charging,
crystalline shimmer, cold wind swirl, fragile glassy tension, close perspective,
one-shot, no music, no vocals, no melody

Ice travel:
High-quality fantasy game sound effect, sharp ice shards launching forward,
fast icy whoosh, glittering crystal particles, cutting air movement,
one-shot, no music, no vocals, no melody

Ice impact:
High-quality fantasy game sound effect, ice projectile impact and shatter,
crystal explosion, frozen debris, sharp transient, short low impact,
one-shot, no music, no vocals, no melody
```

闪电链：

```text
Lightning charge:
High-quality action RPG sound effect, electric spell charge,
rising voltage, buzzing plasma, small sparks, tense high-frequency energy,
one-shot, no music, no vocals, no melody

Lightning chain:
High-quality action RPG sound effect, chain lightning jumping between enemies,
rapid electric arcs, crackling zaps, sharp stereo movement, bright transient hits,
one-shot, no music, no vocals, no melody
```

暗影诅咒：

```text
Shadow cast:
High-quality dark fantasy game sound effect, shadow curse being cast,
low ghostly whoosh, whisper-like texture without human words, dark magical pulse,
one-shot, no music, no vocals, no melody, no intelligible speech

Shadow impact:
High-quality dark fantasy game sound effect, cursed shadow impact on enemy,
soft void burst, low thump, smoky magical decay, ominous tail,
one-shot, no music, no vocals, no melody
```

治疗技能：

```text
Heal cast:
High-quality fantasy game sound effect, healing spell activation,
warm magical shimmer, soft bell-like sparkle, gentle upward energy,
clean and comforting, one-shot, no music, no vocals, no melody

Heal aura loop:
Seamless loop, high-quality fantasy game sound effect, gentle healing aura,
soft magical shimmer, warm light particles, subtle pulsing energy,
no music, no vocals, no melody
```

参数建议：

```text
普通技能 one-shot:
duration_seconds: 1 到 5
prompt_influence: 0.5 到 0.75
loop: false

蓄力或持续 aura:
duration_seconds: 6 到 20
prompt_influence: 0.35 到 0.6
loop: true

短促技能反馈:
duration_seconds: 0.5 到 1.2
prompt_influence: 0.7 到 0.9
loop: false
```

生产建议：

- 每个 prompt 只负责一个阶段，不要同时要求蓄力、飞行、命中、燃烧和环境变化。
- 用 `whoosh`、`impact`、`tail`、`drone`、`glitch`、`one-shot`、`seamless loop` 这类声音设计词汇。
- 加 `no music, no vocals, no melody`，避免模型把技能音效生成成音乐片段。
- 需要怪物声、吟唱或低语时，用 `non-verbal` 或 `no intelligible speech` 控制，不要让模型生成可辨识台词。
- 在 Unreal 中用 MetaSound 分层、随机 pitch/volume、按技能等级混合，相关配置见 [[Unreal 音频系统与 MetaSounds]]。

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

Unreal 项目中的后续集成可参考 [[Unreal 音频系统与 MetaSounds]]，尤其是 Sound Wave 导入、MetaSound 随机化、Attenuation、Concurrency、Sound Class 和 Submix 路由。Unity 项目中的后续集成可参考 [[Unity 音频系统]]，重点是 Audio Clip 导入、Audio Random Container 变体、Audio Source 3D 设置和 Audio Mixer 分类混音。

## 验证

- Sound Effects quickstart 确认 Python SDK 可调用 `text_to_sound_effects.convert(...)` 并生成音频。
- API reference 确认端点为 `POST /v1/sound-generation`，请求字段包括 `text`、`loop`、`duration_seconds`、`prompt_influence`、`model_id`，响应是生成音频。
- API reference 确认 `loop` 仅适用于 `eleven_text_to_sound_v2`，`prompt_influence` 范围为 0 到 1，默认 0.3。
- Capabilities overview 确认最大时长 30 秒、可生成电影音效、游戏音效、Foley、环境声和短音乐元素，并提示完整音乐应使用 Music API。
- Product guide 确认 Playground 每次生成 4 个候选，并可从 History 下载。
- Help Center 确认复杂多事件 prompt 虽可理解，但最佳结果通常来自拆分单个音效后在音频编辑器中组合。
