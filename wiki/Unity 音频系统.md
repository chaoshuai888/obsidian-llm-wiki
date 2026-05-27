---
confidence: confirmed
created: 2026-05-27
sources:
- raw/Unity/2026-05-27-unity-audio-system-docs.md
- https://docs.unity3d.com/Manual/Audio.html
- https://docs.unity3d.com/Manual/AudioOverview.html
- https://docs.unity3d.com/Manual/AudioFiles-compatibility.html
- https://docs.unity3d.com/Manual/AudioFiles-compression.html
- https://docs.unity3d.com/Manual/class-AudioClip.html
- https://docs.unity3d.com/Manual/class-AudioSource.html
- https://docs.unity3d.com/Manual/AudioSource-reference.html
- https://docs.unity3d.com/Manual/AudioSource-create.html
- https://docs.unity3d.com/Manual/class-AudioListener.html
- https://docs.unity3d.com/Manual/AudioMixerOverview.html
- https://docs.unity3d.com/Manual/AudioMixer.html
- https://docs.unity3d.com/Manual/class-AudioManager.html
- https://docs.unity3d.com/Manual/class-AudioEffect.html
- https://docs.unity3d.com/Manual/class-AudioReverbZone.html
- https://docs.unity3d.com/Manual/AudioRandomContainer.html
- https://docs.unity3d.com/Manual/audio-scriptable-processors.html
- https://docs.unity3d.com/Manual/AudioSpatializerSDK.html
- https://docs.unity3d.com/Manual/AudioMixerNativeAudioPlugin.html
- https://docs.unity3d.com/Manual/ProfilerAudio.html
- https://docs.unity3d.com/ScriptReference/AudioSource.html
- https://docs.unity3d.com/ScriptReference/AudioSettings.html
- https://docs.unity3d.com/ScriptReference/Microphone.html
status: published
tags:
- unity
- audio
- game-audio
- audio-mixer
- audio-configuration
title: Unity 音频系统
updated: '2026-05-27'
---

# Unity 音频系统

## 摘要

Unity 音频系统可以按“素材、播放、监听、空间、混音、全局配置、调试”七层理解：

```text
Audio file
-> Audio Clip / Audio Random Container
-> Audio Source
-> Audio Listener
-> Audio Mixer / Audio Mixer Group
-> Audio filters / Reverb Zone / Spatializer / Ambisonic decoder
-> Project Settings > Audio
-> Audio Profiler
```

最小播放链路是：把音频文件导入为 Audio Clip，把 Audio Clip 分配给场景中某个 Audio Source，场景里保留一个 Audio Listener，运行时通过 `AudioSource.Play()`、`PlayOneShot()`、`PlayScheduled()` 或 `PlayClipAtPoint()` 播放。复杂项目应把 Audio Source 输出路由到 Audio Mixer Group，再用 Mixer 管理 Music、SFX、UI、Dialogue、Ambience 等分类音量、效果、快照和 ducking。

本文基于 Unity 6.4 (6000.4) 官方文档整理。旧版本 UI 和能力可能不同，例如某些 LTS 版本没有 Audio Random Container、Scriptable Audio Pipeline，格式兼容表也可能和 Unity 6.4 不完全一致。

## 支持的音频格式

Unity 6.4 官方格式兼容页确认，Unity 支持 mono、stereo 和最多 8 声道的 multichannel audio assets。

普通音频文件：

| 格式 | 扩展名 |
|---|---|
| MPEG layer 3 | `.mp3` |
| Audio Interchange File Format | `.aiff` / `.aif` |
| Microsoft Wave | `.wav` |
| Ogg Vorbis | `.ogg` |
| Free Lossless Audio Codec | `.flac` |

Tracker module：

| 格式 | 扩展名 |
|---|---|
| Ultimate Soundtracker module | `.mod` |
| FastTracker 2 module | `.xm` |
| Impulse Tracker module | `.it` |
| Scream Tracker module | `.s3m` |

Tracker module 在 Unity 里也作为音频资源使用，但 Asset Import Inspector 不显示 waveform preview。

注意：Unity 支持“导入源文件格式”和“运行时编码格式”是两回事。官方压缩文档说明，导入非 tracker 音频后 Unity 会重新编码为适合目标 build target 和声音类型的格式。默认运行时压缩通常是 Vorbis 或 MP3，也可以按平台 override 为 PCM、ADPCM、MP3 等。

## 导入和 Audio Clip

导入方式：

- 菜单：`Assets -> Import New Asset`，选择音频文件。
- 拖拽：把系统文件管理器里的音频文件拖到 Unity Project 窗口。
- 快速创建源：把音频文件从 Project 窗口拖进 Scene，Unity 会创建带 Audio Source 的 GameObject 并绑定该音频。

导入后得到 Audio Clip。Audio Clip 保存音频数据和导入阶段提取的元信息，例如长度、声道数和采样率。脚本和音频系统可以在实际加载音频数据前使用这些元信息，这对对白、音乐调度和内存控制有用。

### Import Settings

`Force To Mono`：把多声道音频 downmix 为 mono。普通 3D 点声源、脚步、武器、碰撞声通常应优先 mono，因为空间化本身会负责方向和距离。UI、音乐、环境床和明确需要宽度的素材可以保留 stereo 或 multichannel。

`Normalize`：在 Force To Mono 过程后做峰值归一化。用于避免 downmix 后过低，但最终响度仍应在 DAW、音频表或项目响度规范里控制。

`Load In Background`：让 Audio Clip 异步加载，减少主线程 stall。适合大音频、关卡中动态加载的对白或音乐。Unity 会延迟仍在加载中的 Clip 的播放请求，脚本可用 `AudioClip.loadState` 查询状态。

`Ambisonic`：当音频文件是 Ambisonic 编码时启用，常用于 360 视频、XR 和全景环境声。项目还需要配置 Ambisonic Decoder Plugin。

`Preload Audio Data`：默认启用，场景加载后预载音频数据。关闭后，音频会在首次 `AudioSource.Play`、`PlayOneShot`、`AudioClip.LoadAudioData` 时加载，并可用 `AudioClip.UnloadAudioData` 卸载。

### Load Type

`Decompress On Load`：加载时解压。适合短小、频繁、低延迟的声音，例如 UI click、脚步、近战 hit、枪声。官方提醒：Vorbis 解压到内存大约会比压缩数据多 10 倍内存，ADPCM 约 3.5 倍，因此不要用于大文件。

`Compressed In Memory`：内存里保持压缩，播放时在 mixer thread 解压。适合内存压力较高、但不能或不想 streaming 的中等长度声音。代价是 DSP CPU 增加，尤其是 Ogg/Vorbis。

`Streaming`：连续解码，压缩数据从磁盘逐步读取，在独立 streaming thread 解码。适合长 BGM、长对白、长 ambience。官方说明 streaming clip 即使没有加载音频数据也有大约 200 KB 开销，因此不适合大量极短 one-shot。

### Compression Format

`PCM`：不压缩，CPU 成本低，内存和包体大。适合很短、极频繁、必须低延迟或需要高质量瞬态的音效。

`ADPCM`：压缩比约为 PCM 的 3.5 倍，CPU 远低于 MP3/Vorbis，适合噪声多、数量大的声音，例如脚步、碰撞、武器。它会带来可听 artefacts，不适合平滑音乐或环境床。

`Vorbis/MP3`：更省空间，质量由 Quality slider 控制。适合中等长度音效、音乐、对白和环境声。应从较高质量开始，逐步降低到刚好听不出明显损失的位置，再稍微回调。

`Sample Rate Setting`：控制采样率和体积/质量平衡。`Preserve Sample Rate` 保持原采样率；`Optimize Sample Rate` 按最高频内容自动优化；`Override Sample Rate` 手动降采样。PCM 和 ADPCM 支持自动优化或手动调整采样率。

## Audio Source

Audio Source 是播放控制组件。Unity 6.4 的 Audio Source 可以播放 Audio Clip，也可以把 Audio Random Container 作为 Audio Generator 分配给 Audio Source。

创建方式：

- 把音频文件拖到 Scene，Unity 自动创建带 Audio Source 的 GameObject。
- 在已有 GameObject 上 `Add Component -> Audio -> Audio Source`。
- 在 Hierarchy 的 Add 菜单选择 `Audio -> Audio Source`。

常用配置：

| 配置 | 用途 |
|---|---|
| Audio Generator | 指向要播放的 Audio Clip 或 Audio Random Container。旧文档和旧版本 UI 常称为 Audio Clip。 |
| Output | 指定输出到 Audio Listener，或路由到 Audio Mixer Group。生产项目建议显式路由到 Mixer。 |
| Mute | 静音但仍播放。调试“有播放无声音”时要检查。 |
| Bypass Effects | 绕过挂在 Audio Source 上的 filter effects。 |
| Bypass Listener Effects | 绕过 Listener 上的全局效果。 |
| Bypass Reverb Zones | 不受 Reverb Zone 影响。UI、音乐、全局提示声通常应绕过。 |
| Play On Awake | 组件或 GameObject 激活时自动播放。原型方便，生产逻辑通常用脚本明确触发。 |
| Loop | 播放到末尾后循环。BGM、环境声、机器底噪常用。 |
| Priority | 0 最重要，256 最不重要。音乐和关键对白可用更高优先级，避免 voice 被抢占。 |
| Volume | 源音量，范围通常 0 到 1。最终响度还会受距离、Mixer、Listener 等影响。 |
| Pitch | 播放速度和音高倍率，1 为正常。可做轻微随机化。 |
| Stereo Pan | 2D mono/stereo 声音的左右声像。 |
| Spatial Blend | 0 是完整 2D，1 是完整 3D，中间值混合 2D/3D。 |
| Reverb Zone Mix | 送入 Reverb Zone 的信号量。 |

3D 声音配置：

| 配置 | 用途 |
|---|---|
| Doppler Level | 当前源的 Doppler 效果强度，不需要时设 0。 |
| Spread | 3D stereo 或 multichannel 声音在 speaker space 中的扩散角度。 |
| Min Distance | 距离小于该值时保持最大音量。想让 3D 声音“更大”，通常增大 Min Distance。 |
| Max Distance | Linear 模式下音量到 0 的距离；Custom 曲线下停止继续衰减的距离；Logarithmic Rolloff 会忽略此设置。 |
| Volume Rolloff | 距离衰减模式：Logarithmic、Linear、Custom。 |

距离曲线编辑器可以按距离控制 Volume、Spatial Blend、Spread、Low-Pass cutoff 和 Reverb Zone Mix。Low-Pass 曲线只有在同一 GameObject 上挂 LowPassFilter 时出现。

## Audio Listener

Audio Listener 像场景里的麦克风：接收 Audio Source 输出并把声音输出到扬声器。它没有可调属性，添加即可工作。默认 Main Camera 会带一个 Audio Listener。

关键规则：

- 一个场景中应只有一个 Audio Listener。
- 通常挂在 Main Camera 或代表玩家的 GameObject 上，具体取决于镜头和听点是否一致。
- 2D 声音忽略 3D 处理；3D 声音会按 listener 与 source 的相对位置、速度和朝向计算方向、距离和 Doppler。
- Listener 进入 Reverb Zone 时，会让可听声音受到对应混响影响。Listener 上也可以挂 Audio Effects，这些效果会作用到所有可听声音。

## Audio Mixer

Audio Mixer 是音频路由、分类混音和动态 mastering 资产。Audio Source 的 Output 可以路由到 Mixer Group；Mixer Group 再构成树状层级并最终输出到 Listener。

典型层级：

```text
Master
├── Music
├── SFX
│   ├── Weapon
│   ├── Foley
│   └── Ambience
├── UI
└── Dialogue
```

Audio Mixer 适合做：

- 用户音量滑杆：Master、Music、SFX、UI、Dialogue。
- 分类效果：水下低通、洞穴混响、无线电 EQ、暂停菜单 muffling。
- Snapshot：保存 Mixer 参数状态，并在 gameplay 中平滑切换。例如 Normal、Combat、Pause、Underwater、Cutscene。
- Exposed Parameters：把 Mixer 参数暴露给脚本，通过字符串名控制。
- Ducking：让 Dialogue 或 UI 发生时自动压低 Ambience、Music 或 SFX。
- Send / Return：把一组声音送到共享效果链，例如统一 reverb 或延迟。

Audio Mixer 的路由和分类不依赖场景层级。场景里 Actor 的父子关系不应该决定声音混音分类；声音应按业务类别进入对应 Mixer Group。

注意：Unity 官方 Audio Mixer window 文档说明 Web platform 只部分支持 Audio Mixer。面向 Web 发布时，需要单独验证 Mixer、效果和压缩格式行为。

## Project Settings > Audio

位置：

```text
Edit -> Project Settings -> Audio
```

主要设置：

| 配置 | 用途 |
|---|---|
| Global Volume | 全局音量。通常不作为用户音量系统的主控制，用户滑杆更适合走 Audio Mixer。 |
| Volume Rolloff Scale | 对 Logarithmic rolloff 源的全局距离衰减系数。1 近似现实世界。值越大衰减越快。 |
| Doppler Factor | 全局 Doppler 可听程度。0 关闭，1 让高速物体明显可听。多数游戏应谨慎使用，避免 pitch 漂移过强。 |
| Default Speaker Mode | 默认扬声器模式，默认 2 对应 stereo。运行时可通过 AudioSettings 配置，但要检查平台支持。 |
| System Sample Rate | 输出采样率。0 表示使用系统采样率。部分平台才允许改变。 |
| DSP Buffer Size | 在延迟和性能之间取舍。Best Latency 响应更快但更吃资源；Best Performance 更稳但延迟更高。 |
| Max Virtual Voices | 音频系统管理的虚拟 voice 数，应大于游戏可能播放的 voice 数，否则会有 warning。 |
| Max Real Voices | 同时真实播放的 voice 数。每帧选择最响或优先级更高的 voice。 |
| Spatializer Plugin | 选择用于 3D source 空间滤波的 native audio plugin。 |
| Ambisonic Decoder Plugin | 选择 Ambisonic 到 binaural 的解码插件。 |
| Disable Unity Audio | Standalone build 中停用音频系统。Editor 仍能预览 clip，但模拟 build 行为时不会处理 `AudioSource.Play` 和 `playOnAwake`。 |
| Enable Output Suspension | Editor 中长时间静音后自动暂停音频输出。 |
| Virtualize Effect | 对被剔除的 AudioSource 动态关闭 effects 和 spatializers，以节省 CPU。 |

运行时脚本可以通过 `AudioSettings.GetConfiguration()`、修改配置并 `AudioSettings.Reset()` 来改变 speaker mode、sample rate、DSP buffer size 和 real/virtual voice counts。但官方 API 提醒，`AudioSettings.Reset()` 在异步加载对象时可能造成主线程 stall；除非有明确需求，不要频繁动态重置。

## Effects、Reverb 和空间化

Audio filters 可以挂到 Audio Source 或 Audio Listener 上，用于低通、高通、echo、chorus、distortion、reverb 等处理。组件顺序就是效果应用顺序，必要时可在 Inspector 中 Move Up / Move Down。部分 filter 虽然优化过，仍可能吃 CPU，应在 Audio Profiler 里看 DSP CPU。

Reverb Zone 用于按 Listener 位置逐渐改变环境混响，例如进入山洞、隧道、室内空间。核心参数是 Min Distance、Max Distance 和 Reverb Preset。多个 Reverb Zone 可以叠加混合。

Audio Spatializer SDK 允许用 native plugin 替换 Unity 标准 panner，实现更高级空间化。使用步骤是：在 `Project Settings -> Audio` 选择 Spatializer Plugin，然后在需要的 Audio Source 上启用 Spatialize。空间化效果直接作用在 Audio Source 解码之后，每个 source 都有自己的 spatializer 实例；大量声音同时开启会增加 mixer thread 成本。实战中应只对近处、重要、需要耳机或 XR 空间定位的声音启用，远处或普通 3D 声源继续用内置 panning。

Ambisonic 音频用于表示可包围 listener 的 soundfield，常见于 360 视频和 XR。导入时 Audio Clip 勾选 Ambisonic，并在项目音频设置里选择 Ambisonic Decoder Plugin。

## Audio Random Container

Audio Random Container 是 Unity 6.x 的播放列表随机化资产，可分配给 Audio Source 的 Audio Generator。它适合脚步、碰撞、武器、道具、背景音乐等需要“同类多变体”的声音。

它能处理：

- 随机选择 clip。
- 循环。
- 定时播放。
- Manual / Automatic 播放模式。
- 用 AudioSource API 启动、暂停和停止。

脚步、命中、UI hover、材质 Foley 这类高重复声音，优先考虑 Audio Random Container 或自定义变体系统，而不是单个 clip 重复播放。它能降低机械重复感，并把变体选择从玩法脚本中拆出来。

## Scriptable Audio Pipeline

Scriptable Audio Pipeline 是 Unity 6.4 的扩展框架，用 Burst-compatible HPC# 在指定集成点扩展 Unity audio engine。官方文档把它用于 generators、root outputs 等高级音频处理。

使用边界：

- 普通游戏音效、BGM、UI 声不需要它。
- 当项目要做程序化声音生成、特殊输出、低层音频处理或工具链扩展时再评估。
- 官方文档说明它不支持 Web Platform；Web build 中使用会触发 warning。

## 脚本播放常用 API

最小播放：

```csharp
using UnityEngine;

public class PlaySfx : MonoBehaviour
{
    public AudioSource source;
    public AudioClip clip;

    public void Play()
    {
        source.PlayOneShot(clip);
    }
}
```

常用 API：

| API | 用途 |
|---|---|
| `AudioSource.Play()` | 播放当前绑定的 Audio Clip 或 Audio Generator。 |
| `AudioSource.Pause()` / `UnPause()` | 暂停和继续。 |
| `AudioSource.Stop()` | 停止播放。 |
| `AudioSource.PlayOneShot(clip, volumeScale)` | 用同一个 AudioSource 播放一次性 clip，可叠加多个 one-shot。 |
| `AudioSource.PlayClipAtPoint(clip, position)` | 在世界坐标创建临时 3D 播放。适合简单原型，不适合高频生产玩法。 |
| `AudioSource.PlayDelayed(seconds)` | 延迟播放。 |
| `AudioSource.PlayScheduled(AudioSettings.dspTime + delay)` | 按音频 DSP 时间线调度，适合音乐、节奏、精确衔接。 |
| `AudioSource.time` / `timeSamples` | 查询或设置播放位置。 |
| `AudioSettings.dspTime` | 音频系统当前 DSP 时间，适合精确调度。 |
| `Microphone.devices` / `Microphone.Start()` / `End()` | 获取麦克风并录制到 AudioClip。Web 平台使用 Microphone 需要先请求用户授权。 |

## 实战配置建议

这些是基于官方配置含义推导的项目默认建议，最终应以目标平台 Audio Profiler 和真机试听为准。

| 声音类型 | Load Type | Compression Format | Source / Mixer 建议 |
|---|---|---|---|
| UI click / hover | Decompress On Load | PCM 或 ADPCM | 2D，路由到 UI，Preload，低延迟，高优先级。 |
| 脚步 / Foley / 小碰撞 | Decompress On Load 或 Compressed In Memory | ADPCM | 3D mono，Audio Random Container，多变体，按材质路由到 SFX/Foley。 |
| 武器 / 爆炸 / 技能 one-shot | Decompress On Load 或 Compressed In Memory | ADPCM；关键瞬态可 PCM | 3D，设置合理 Min/Max Distance、Priority、Rolloff，避免同时爆太多 voice。 |
| BGM | Streaming | Vorbis/MP3 | 2D 或非定位，Loop，路由到 Music，Priority 设高，必要时 PlayScheduled。 |
| 长对白 | Streaming 或 Compressed In Memory | Vorbis/MP3 | Dialogue Mixer，Load In Background，配合字幕和 ducking。 |
| 短对白 bark | Decompress On Load 或 Compressed In Memory | ADPCM 或 Vorbis/MP3 | Dialogue Mixer，按角色/距离配置 2D/3D。 |
| 环境床 ambience | Streaming | Vorbis/MP3 | Ambience Mixer，长循环，必要时多层按区域淡入淡出。 |
| 近处 XR 空间声 | Decompress 或 Compressed | 视素材而定 | 3D mono，启用 Spatialize，控制同时 spatializer 数量。 |

导入源文件建议：如果团队会让 Unity 再压缩到目标平台格式，源素材优先保留 WAV、AIFF 或 FLAC 这类无损格式，减少二次有损压缩。若源素材已是 MP3/Ogg，Unity 再编码可能继续损失质量；上线前要听目标平台实际构建产物，不只听 Editor preview。

## 调试和性能

Audio Profiler 路径：

```text
Window -> Analysis -> Profiler -> Audio
```

关注指标：

| 指标 | 说明 |
|---|---|
| Playing Audio Sources | 当前帧正在播放的 Audio Source 数。过高说明触发逻辑或并发控制可能有问题。 |
| Audio Voices | 当前使用的 FMOD channel / voice 数。 |
| Total Audio CPU | 音频总 CPU。 |
| DSP CPU | mixing、effects、Compressed In Memory 解压等成本。 |
| Streaming CPU | Streaming clip 的读取和解码成本。 |
| Total Audio Memory | 音频系统内存。 |
| Sample Sound Memory | Decompress On Load 的解压样本内存。 |
| Streaming File / Decode Memory | Streaming clip 的压缩数据短期缓冲和解码缓冲。 |
| Virtual | 详细视图中显示某声音是否因 Max Real Voices 限制被虚拟化。 |

官方 Profiler 文档提醒，Unity 音频系统会池化分配的内存，运行时增长到饱和后复用，不能在运行时 compact。因此看音频内存时要关注稳定峰值，而不是期待停止播放后立刻下降。

## 常见问题排查

“调用了 Play 但没声音”时按顺序查：

1. 场景是否只有一个 Audio Listener，且 Listener 与 3D source 的距离在可听范围内。
2. AudioSource 是否绑定了 Audio Clip 或 Audio Random Container。
3. `Mute`、`Volume`、`AudioListener.volume`、Mixer Group attenuation、Snapshot、Exposed Parameter 是否把音量压到静音。
4. AudioSource Output 是否路由到错误 Mixer Group，或 Mixer / Group 被 mute、solo、bypass 影响。
5. Spatial Blend 是否为 3D，Min/Max Distance、Rolloff 是否导致听不到。
6. Priority、Max Real Voices 是否让该 voice 被虚拟化；Audio Profiler 详细视图看 `Virtual`。
7. Audio Clip 是否还在 background loading，`loadState` 是否完成。
8. Project Settings 是否启用了 Disable Unity Audio。
9. 如果是 Web 麦克风或录音，是否已请求用户授权。
10. 如果是 Reverb、Filter、Spatializer 相关问题，先绕过效果确认干声链路是否正常。

## 与其他音频条目的关系

- AI 生成素材进 Unity 前，仍应先检查容器和编码，尤其是 `.wav` 文件要确认真的是 RIFF/WAVE，可参考 [[WAV 文件格式]]。
- 用 ElevenLabs 生成短音效后，可把候选导入 Unity，再用 Audio Random Container、Audio Mixer 和 3D 设置做游戏内随机化与混音，见 [[ElevenLabs 音效生成]]。
- BGM 和 stem 生成流程可参考 [[ElevenLabs 游戏 BGM 生成]]，Unity 侧负责 loop、streaming、snapshot、ducking、PlayScheduled 和 Mixer 分类。
- Unreal 的对应概念见 [[Unreal 音频系统与 MetaSounds]]：Unity Audio Mixer 大致对应 Unreal Sound Class/Submix/Mix 一部分职责，Unity Audio Source 大致对应 Unreal Audio Component，但两边动态音频图和资源模型不同，不能一一照搬。

## 验证方式

本条目已在 2026-05-27 依据 Unity 6.4 (6000.4) 官方 Manual / Scripting API 整理。官方页面显示 Built on: 2026-05-22。

落到具体项目时，应重新验证：

- 目标 Unity 版本的 Manual 和 Inspector UI。
- 目标平台的格式、压缩、Web / mobile / console 限制。
- Editor Preview、Play Mode、实际构建包、真机设备上的播放一致性。
- Audio Profiler 中 CPU、memory、voice、virtualization、streaming 指标。
- 循环点、响度、空间化、混响和用户音量滑杆的实际听感。
