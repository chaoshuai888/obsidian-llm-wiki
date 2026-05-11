---
confidence: confirmed
created: 2026-05-11
sources:
- raw/Unreal/2026-05-11-unreal-audio-metasound-docs.md
- https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-audio-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-in-unreal-engine-5?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-engine-overview-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-pages-in-unreal-engine?application_version=5.7
- https://dev.epicgames.com/documentation/ru-ru/unreal-engine/audio-settings-in-the-unreal-engine-project-settings?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-audio-files?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-classes-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-attenuation?application_version=4.27
- https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-submixes-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-modulation-quick-start-guide?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/control-bus
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/overview-of-quartz-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/quartz-quick-start?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/audioinsights
- https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-stream-caching-overview?application_version=4.27
status: published
tags:
- unreal-engine
- audio
- metasounds
- game-audio
- audio-mixer
- audio-configuration
title: Unreal 音频系统与 MetaSounds
updated: '2026-05-11'
---

# Unreal 音频系统与 MetaSounds

## 摘要

Unreal 的音频系统可以按“素材、播放、空间、混音、调度、调试”六层理解：

```text
Sound Wave / MetaSound / Sound Cue
-> Audio Component / Ambient Sound / Blueprint 播放节点
-> Sound Attenuation / Spatialization / Occlusion
-> Sound Class / Sound Mix / Audio Modulation
-> Submix Graph / Source Effects / Submix Effects / Master Output
-> Quartz / Audio Insights / stat 命令
```

MetaSound 是 UE5 的程序化声音源和 DSP 图系统。它适合把一个基础音频素材扩展成可参数化、可随机化、可分层、可由玩法驱动的声音模板。对游戏音效流水线来说，[[ElevenLabs 音效生成]] 可负责生成候选素材，Unreal 的 MetaSound、Attenuation、Concurrency、Sound Class、Submix 和 Quartz 负责把素材变成可交互的游戏声音。

对 BGM 来说，[[ElevenLabs 游戏 BGM 生成]] 可负责产出菜单、探索、战斗、Boss 或 stinger 素材；Unreal 侧仍要用 Quartz、Sound Class、Submix、Audio Modulation 或 MetaSound 处理循环、分层和状态切换。

## 核心对象

Sound Wave 是导入音频文件后得到的基础资产。官方导入文档说明 UE 支持常见音频格式，并会把导入文件在内部转换为 16-bit wav 表示；项目还会按 Project Settings 中的默认音频压缩类型进行压缩。Sound Wave 适合保存实际录音、AI 生成音效、Foley、BGM stem 或 ambience loop。

Sound Cue 是传统音频图。它可以随机、混合、按距离交叉淡化、调音量和 pitch。UE5 仍支持 Sound Cue，但 MetaSound 更适合新项目中的程序化音效、精细时序和复杂参数化。

MetaSound Source 是可独立播放的 MetaSound 资产，地位接近 Sound Wave 或 Sound Cue。它可以挂在 Audio Component 上播放，也可以放进关卡、蓝图或其他音频系统中。

MetaSound Patch 是可复用子图，本身不独立发声。适合封装共享逻辑，例如随机 pitch、包络、滤波器组、脚步材质选择、命中层混合、循环 ambience 组件。

MetaSound Preset 继承父 MetaSound 的只读图，只覆盖输入默认值。它适合把一个通用模板派生成多个变体，例如 `MSS_UI_Click_Base` 派生出 confirm、cancel、hover、error。

Audio Component 是运行时播放和控制声音的组件。它负责开始/停止、音量、pitch、附着到 Actor、设置参数、接收 Attenuation/Concurrency 等播放级配置。MetaSound 的输入参数通常通过 Audio Component 或 Blueprint 设置。

## MetaSound 工作方式

MetaSound 图不是 Blueprint 那种游戏逻辑执行图，而是音频流图。Audio pin 代表音频 buffer，Trigger pin 用来触发音频事件，Float/Bool/Int/Time/String/UObject 等 pin 传递控制数据。

新建 MetaSound Source 默认带 `On Play` 输入和 `On Finished` 输出。`On Finished` 来自 `UE.Source.OneShot` interface；如果一个 MetaSound 是一次性音效，应该在播放结束时触发 `On Finished`，让声音自然停止。如果是 BGM、风声、机器底噪或其他无限循环声音，可以移除 `UE.Source.OneShot` interface，否则图的生命周期会和 one-shot 预期冲突。

MetaSound 的 Output Format 决定输出声道格式，官方参考列出 Mono、Stereo、Quad、5.1、7.1 等。普通 3D 点声源通常用 mono；UI、音乐、环境床和多声道资产可以用 stereo 或多声道，但要注意多声道声音通常更适合 2D 或 ambience bed，而不是普通空间化点声源。

Inputs 是外部可控参数。应该把玩法会改变的值做成 Input，例如技能等级、危险度、材质类型、随机种子、滤波 cutoff、层音量。Variables 更适合图内部状态；官方参考说明播放中的变量变化不会像 Input 那样作为外部运行时控制通道使用。

Constructor Pin 是播放前确定的只读构造参数，用来让图少做运行时动态更新。适合不会在播放中改变的配置，例如固定波表、固定输出模式、固定数组或模板选择。Trigger 和 Audio 类型不能作为 constructor pin。

Interfaces 用来让 MetaSound 接入引擎音频系统。`UE.Attenuation` 提供距离输入，`UE.Spatialization` 提供方位角和仰角输入，`UE.Source.OneShot` 提供一次性声音结束语义。需要按距离或方位改变音色时，优先考虑 interface，而不是在 Blueprint 每帧推参数。

Output Watching 可以让 Blueprint 或 C++ 监听 MetaSound Source 的输出变化。可监听类型包括 Float、Int32、Bool、Time、String 和 Trigger；音频输出也可用 Envelope Follower 监听响度包络。适合用音频能量驱动 UI、灯光、Niagara、镜头震动或玩法反馈。

Builder API 可通过 Blueprint 或 C++ 动态创建、修改、试听 MetaSound Source 和 Patch。它适合工具、生成式音频、运行时音频实验或自动化构建；普通项目音效制作不应一开始就依赖它。

## MetaSound Pages 配置

MetaSound Pages 是实验性功能，用来为不同硬件性能等级准备不同的 MetaSound 图或输入默认值。它不是普通运行时参数切换，因为页面数据在 MetaSound 实例运行前解析；不能用它修改已经在播放的实例。

位置：

```text
Edit -> Project Settings -> Engine -> MetaSounds -> Pages (Experimental)
```

`Page Settings` 用来定义页面列表，例如 Default、Low、Medium、High、Mobile。用途是建立可 cook、可 target、可回退的性能分层。数组顺序重要，因为目标页不可用时会按页面设置顺序寻找 fallback。

`Name` 是页面名。建议用硬件或质量语义命名，例如 `Low`、`High`、`Mobile`，不要用具体设备型号，除非项目只支持少数固定设备。

`Targetable` 决定页面是否可作为平台目标。为 true 时，该页可被目标平台或平台组选择。用途是让 cook 和运行时目标页选择知道哪些页面是有效候选。

`Exclude from Cook` 用来排除某些平台 cook。用途是避免把高成本页面打进移动包，或避免把移动简化页打进不需要的平台包。

`Target Page Name` 是运行时默认目标页面。它可通过项目设置、平台 `.ini`、控制台变量 `au.MetaSound.Pages.SetTarget PAGE_NAME`、Blueprint 或 C++ 设置。用途是按平台或质量档切换 MetaSound 的图复杂度和默认输入。

使用建议：先做最高质量 Default/High 图，再复制出 Low/Mobile 页面并删掉昂贵层，例如卷积、过多 Wave Player、复杂滤波、密集随机层。所有页面应保持同一组外部输入输出接口，避免调用方按页面写分支。

## Project Audio Settings 配置

位置通常是：

```text
Edit -> Project Settings -> Engine -> Audio
```

不同 UE 版本和平台可能会把部分项放到 `Platforms -> <Platform> -> Audio`，以目标项目编辑器为准。

`Default Sound Class`：新建声音默认归属的 Sound Class。用途是强制所有声音进入项目混音树，例如 Master 下分 Music、SFX、UI、Dialogue。建议项目早期就建立，避免后期大量 Sound Wave 没有分类。

`Default Media Sound Class`：媒体播放器资产默认使用的 Sound Class。用途是把视频、过场、流媒体声音放到正确的混音组，避免它们绕过音乐或对白音量滑杆。

`Default Sound Concurrency`：新建声音默认绑定的 Sound Concurrency。用途是防止粒子、脚步、碰撞、枪声等大量重复触发声音把 voice pool 打爆。原型期可宽松，生产期应按声音类型设置更具体的 concurrency。

`Default Base Sound Mix`：没有其他系统指定 Base Sound Mix 时使用的默认 Sound Mix。用途是给传统 Sound Class Mix 提供基础动态混音层。新项目若使用 Audio Modulation 作为主要混音方式，这项可以保持简单。

`VOIP Sound Class`：VOIP 音频组件使用的 Sound Class。用途是把语音聊天放入独立混音组，便于降噪、ducking、音量选项和输出路由。

`VOIP Sample Rate`：VOIP 采样率。低采样率省带宽和 CPU，正常采样率保留更多清晰度。只影响语音链路，不应该拿来调游戏音效质量。

`Maximum Concurrent Streams`：同一时间允许播放的 streaming sounds 数量；超过后按 priority 排序。用途是控制长音乐、对白、环境流式音频的 IO 和解码压力。开放世界或大量长 ambience 要调大并配合 stream cache；移动端要谨慎。

`Global Min Pitch Scale` / `Global Max Pitch Scale`：全局 pitch 缩放钳制。用途是防止蓝图、随机化或调试参数把声音 pitch 拉到不可用范围，也能避免极端重采样开销。

`Master Submix`：所有声音最终路由的根 submix。用途是放 master meter、limiter、最终 EQ、录音或平台输出控制。不要把具体业务分类全堆到 Master 上，应该建立子 submix。

`Reverb Submix`：启用 reverb send 的声音会送入的 reverb submix。用途是统一处理房间混响、环境混响或 master reverb 效果。

`Default Audio Buses`：Audio Engine 初始化时自动启动的 Audio Bus 列表。用途是准备全局分析、侧链、跨系统信号或一直存在的总线。

`Base Default Submix`：Submix Send 没有指定时使用的默认 submix。用途是提供默认 send 目标，减少资产上空配置导致的路由不一致。

`EQ Submix (Legacy)`：传统 EQ 系统使用的 submix。用途是兼容旧 Sound Mix EQ 流程；现代项目更建议用 Submix Effect Chain 或 Audio Modulation。

`Quality Levels`：音频质量档。用途是为不同平台或性能档准备不同的 max channels、采样率、质量等全局音频能力。移动端、VR、主机和 PC 不应共用未经验证的同一档。

`Allow Play when Silent`：允许 0 音量声音继续播放。用途是让被静音的音乐、循环、MetaSound 或参数驱动声音保持时间轴和内部状态；代价是静音时仍可能占用资源。音乐同步和长循环可开，普通 one-shot 不建议依赖。

`Disable Master EQ`：禁用 master EQ DSP。用途是关闭 legacy master EQ 路径，减少不需要的处理或避免旧系统影响现代 submix 混音。

`Allow Center Channel 3DPanning`：空间化计算是否使用中置声道。用途是环绕声系统下更充分使用 center channel；对白和屏幕中心声音可能受益，但要在目标扬声器布局上试听。

`Num Stopping Sources`：为正在停止的声音保留的 source 数量。用途是让被停止的声音用快速 fade 消除点击爆音，而不是硬切。动作游戏中频繁 voice stealing 时尤其有用。

`Panning Method`：非 binaural 或 object-based panning 的方法。Linear 是线性交叉淡化；Equal Power 更容易保持听感响度稳定。普通游戏扬声器 panning 通常优先试 Equal Power。

`Mono Channel Upmix Method`：非空间化 mono 声音上混到 stereo 的方法。用途是决定 UI、mono 音效、中心提示音在 stereo 输出中的能量和宽度。发现 mono UI 声过响、过窄或相位感奇怪时检查这里。

`Debug Sounds`：只在非 shipping build 打包的调试声音。用途是保留测试 beep、计时音、音频 QA 标记，不污染正式包。

平台 `Max Channels`：平台最大同时 voice 数。官方 API 描述它是该平台同时 voices 的上限，0 表示使用当前 Global Audio Quality Settings。用途是定义 voice pool 天花板；Concurrency 和 Priority 决定达到上限后谁被拒绝或抢占。

## Sound Wave 导入与压缩配置

导入前建议优先准备 16-bit 音频。官方文档说明 24-bit 导入会转成 16-bit 且不做 dither，因此最终制作链里最好在 DAW 中自行控制导出位深、响度和抖动。

`Default Audio Compression Type` 决定 Sound Wave 默认压缩格式。Bink Audio 是默认的感知编码，适合大多数平台和常规项目；ADPCM 解码便宜、压缩率较低，适合短音效和低 CPU 需求；PCM 不压缩、内存高但解码极低，适合极短、极频繁、必须低延迟的声音；Platform Specific 交给平台格式，但官方导入页提示它不支持 seeking。

`Loading Behavior Override` 只在 stream caching 启用时有意义。Inherited 表示继承 Sound Class 或 cvar；Load on Demand 首块播放或 prime 时才加载；Prime on Load 加载资产时加载首块但可被逐出；Retain on Load 首块保留在 cache；Force Inline 强制走非 streaming decode path。UI 点击、枪声、脚步首响等低延迟短音效适合 Prime/Retain/Inline；长音乐和环境音更适合 streaming。

`Use Stream Caching` 和 `Max Cache Size` 控制压缩音频块的缓存方式和内存上限。用途是在开放世界或大量长音频项目中用 IO 换内存。cache 太小会导致首次播放延迟或 underrun；cache 太大会吃内存。修改 cache size 后通常需要重启编辑器验证。

`Prime Sound For Playback` 用于提前把即将播放的声音加载进 cache。用途是开门前预载房间 ambience、上车前预载车内电台、战斗前预载技能音效。

`stat audiostreaming` 可查看 stream cache 状态。发现音频首次播放卡顿、长音频断续或 cache 被打爆时先开它。

## Sound Attenuation 配置

Sound Attenuation Settings 控制声音相对 listener 的距离、空间化、遮挡、滤波、reverb send 和插件设置。它可以直接挂在 sound asset 上，也可以在 Sound Cue、Audio Component 或 Blueprint 中覆盖。

`Enable Volume Attenuation`：是否按距离衰减音量。点声源、脚步、武器、机关声通常开启；UI、BGM、全局提示音通常关闭。

`Attenuation Function`：距离衰减曲线。Linear 适合大型背景声交叉淡化；Logarithmic 适合有清晰定位但远处仍可听见的 3D 声；Inverse 近处更强、远处更快变小；Log Reverse 适合需要大范围保持响度、远端才明显变化的声音；Natural Sound 尝试更接近自然声学；Custom 用 Float Curve 解决特殊玩法需求。

`Attenuation Shape`：衰减区域形状。Sphere 适合点声源；Capsule 适合长条物体、河流、管道、走廊；Box 适合房间、区域氛围、建筑内部；Cone 适合扬声器、警报器、定向风口和喇叭。

`Inner Radius` / `Inner Shape Area`：满音量区域。用途是定义离声源多近时不衰减。机器、大门、瀑布这类大声源需要比小物件更大的内区。

`Falloff Distance`：从内区边缘到最远可听边界的距离。用途是控制声音退出世界的速度。不要只靠音量调小解决远距离听感，应该用合适 falloff 让音频系统能剔除不可听声音。

`Enable Spatialization`：是否把声音放到世界空间中进行 panning 或 binaural。点声源开启；UI、音乐、旁白、非定位 ambience 通常关闭。

`Spatialization Method`：Panning 或 Binaural。Panning 适合扬声器和常规 stereo/surround；Binaural 依赖空间化插件，适合耳机、VR、第一人称沉浸，但要在目标耳机和平台上测试。

`Non-Spatialized Radius`：近距离内从 3D 声平滑过渡到 2D 扩散。用途是避免玩家穿过声源时左右声像突变，也能让大型声源贴近时更包围。

`Air Absorption` / 距离滤波：按距离改变 low-pass 或 high-pass。用途是模拟高频随距离衰减、远处声音变闷，或做玩法化远近辨识。

`Enable Occlusion`：启用内置遮挡检测。系统会检查声源和 listener 之间是否有障碍，并应用低通和音量衰减。用途是墙后声音变闷、门后怪物声、房间隔音。大量声源开启会带来 trace 成本，应按重要声音使用。

`Occlusion Trace Channel`：遮挡用的碰撞通道。默认 Visibility 常能工作，但项目最好建立 Audio 专用 trace channel，以免视觉碰撞、交互碰撞和音频遮挡互相污染。

`Occlusion Low Pass Filter Frequency`：遮挡时低通截止频率。值越低越闷。薄木门、厚墙、金属门应使用不同值。

`Occlusion Volume Attenuation`：遮挡时音量缩放。用途是和低通一起表达“被挡住”。不要只用音量，否则玩家难以分辨是远了还是隔墙。

`Occlusion Interpolation Time`：遮挡变化的过渡时间。用途是避免角色在门框、柱子边缘移动时滤波突变。快节奏枪战可短一点，环境声可长一点。

`Listener Focus`：按 listener 朝向调整音量、优先级等。用途是让视野内声音更清楚、视野外声音更弱或更容易被抢占。第三人称、潜行和恐怖游戏很有用。

`Reverb Send`：按距离把声音送到 reverb submix。用途是近处直接声强，远处或空间声有更多混响。和 Audio Volume 的空间 reverb 配合使用。

`Submix Send`：按手动或距离把声音送到额外 submix。用途是做洞穴回声、无线电处理、低通总线、侧链分析或环境区域效果。

`Plugin Settings`：空间化、遮挡、reverb 插件的专用设置。使用 Meta XR Audio、Steam Audio、Resonance 等插件时，项目关键空间声应在这里配置插件资产，而不是只用 UE 内置 panning。

## Sound Class 与 Sound Mix 配置

Sound Class 是声音分组资产，用于让同类声音共享音量、pitch、滤波、加载、路由和部分 legacy 行为。常见树：

```text
Master
├── Music
├── SFX
│   ├── UI
│   ├── Weapon
│   ├── Footstep
│   └── Ambience
└── Dialogue
```

`Volume`：该类所有声音的响度乘数。用途是做用户音量滑杆或 mix 基础平衡。正式项目不要直接在每个 Sound Wave 上调大量随机音量，应先整理 Sound Class。

`Pitch`：该类所有声音的 pitch 乘数。用途较少，适合全局慢动作、梦境、药水状态等风格化效果。

`Low Pass Filter Frequency`：该类全局低通。20,000 Hz 或更高基本无效果。用途是 pause menu muffling、潜水、受伤、墙后全局处理。

`Attenuation Distance Scale`：缩放该类声音用于距离衰减的距离。用途是动态改变一类声音的感知范围。例如潜行状态把敌人脚步听距放大，或低性能模式缩短环境声距离。

`Always Play`：提高该类声音不被 voice pool 踢掉的优先级。用途是对白、关键 UI、重要 gameplay cue。不要滥用，否则会让不重要声音无法被剔除。

`Child Classes`：子类继承父级设置。用途是建立混音层级，让 Master/SFX/UI 等能统一控制，也能局部覆盖。

`Passive Sound Mix Modifiers`：该类声音播放时自动触发 Sound Mix。用途是传统 ducking，例如对白播放时压低音乐或环境声；可设置最小/最大音量阈值，避免远处几乎听不见的声音触发全局 duck。

`LFE Bleed`：送入低频效果通道比例。用途是爆炸、重击、怪兽脚步等环绕系统低频增强。普通 UI 和对白不需要。

`Voice Center Channel Volume` / `Center Channel Only`：控制送到中置声道。用途是影院式对白或屏幕中心内容。需要真实环绕环境验证。

`Apply Ambient Volume`：是否受 Audio Volume 的 Interior/Exterior 音量和低通影响。用途是让室内外过渡影响 ambience、SFX，而不是影响 UI 或音乐。

`Is UISound`：UI 菜单和暂停期间仍可听到。用途是 pause menu、设置菜单、背包和鼠标 hover。游戏世界声音通常不开。

`Is Music`：标记为音乐。用途是平台、系统或项目逻辑区分音乐声音。

`Default Submix`：该类声音默认输出到哪个 submix；为空则使用 Project Settings 的默认。用途是把 Music、Dialogue、SFX、UI 分到不同总线，便于各自加效果、meter、录音或平台路由。

`Send to Master Reverb Send Amount` / `Default 2D Reverb`：该类是否送 master reverb，以及 2D 声音默认 reverb 量。用途是让非空间化声音也有环境混响，但 UI 和音乐通常不应被房间 reverb 污染。

`Modulation Settings`：安装 Audio Modulation 插件后可给 Sound Class 添加调制目标。用途是用 Control Bus 管理音量、滤波、pitch 等参数。

`Loading`：控制该类下 Sound Wave 的压缩数据加载行为。用途是按分类定义延迟和内存策略：UI/Weapon 可 Prime 或 Retain，长 Music/Ambience 可 Load on Demand 或 stream。

Sound Mix 是传统动态混音资产，可在运行时调整 Sound Class 的 volume/pitch/EQ，适合旧项目和简单 ducking。新项目如果要做用户滑杆、状态混音、滤波和跨系统参数控制，更推荐优先评估 Audio Modulation。

## Audio Modulation 配置

Audio Modulation 是插件系统，用 Control Bus 和 Control Bus Mix 控制常见浮点音频参数。官方 quick start 的目标包括创建 Control Bus、Control Bus Mix、把 Control Bus 分配给 MetaSound Source 和 Sound Class、用 Mix Matrix Debugger 查看当前值、从 Blueprint 调整 bus。

`Control Bus` 是可被音频源或效果引用的调制源。用途是定义一个可被多处共享的参数通道，例如 `CB_Music_Volume`、`CB_SFX_Volume`、`CB_LowPass_Global`、`CB_Combat_Intensity`。

`Control Bus Mix` 是一组 bus 值的集合。用途是一次性应用某种混音状态，例如 Pause、Underwater、Combat、DialogueDucking、LowHealth。

`Mix Matrix Debugger` 用来查看 Control Bus 当前值。用途是调试多个 mix 同时激活时的最终参数，避免“设置滑杆没反应”或“状态 mix 互相覆盖”。

使用建议：用户音量滑杆、战斗强度、潜水低通、暂停菜单 muffling 等长期可组合状态用 Audio Modulation；临时 one-shot 的局部随机 pitch/volume 留在 MetaSound 内。

## Sound Concurrency 与 Priority 配置

Sound Concurrency 解决“同类声音太多时怎么办”。它应该按类别配置，不要让所有声音共用一个全局规则。

`Max Count`：该并发组允许的最大 active voices。用途是限制脚步、弹壳、碰撞、环境小物件和 UI hover 的同时播放数量。

`Limit To Owner`：是否按播放声音的 owner Actor 单独限制。用途是每个角色最多 2 个脚步声，而不是全场所有角色共用 2 个脚步声。没有 owner 时会退回全局并发。

`Resolution Rule`：达到 Max Count 时如何处理。用途是决定拒绝新声音、停止旧声音、停止最安静声音或按优先级替换。具体 UI 选项随版本变化，关键是按听感选择：脚步常替换旧/安静声，关键提示常拒绝低优先级声。

`Retrigger Time`：同并发组两次触发之间的最小间隔。用途是防抖，尤其适合 UI hover、碰撞、机关摩擦、粒子触发声。

`Volume Scale` / duck 相关设置：同组多声音同时存在时按规则压低部分声音。用途是保留层次而不是硬切，例如大量火焰、雨滴、昆虫声。

`Duck Time` / `Recover Time`：duck 生效和恢复时间。用途是让并发组音量变化平滑。

`Voice Steal Release Time`：声音被抢占或剔除时淡出时间。用途是避免硬切爆音。

`Priority` 在 Sound Cue、Sound Wave、MetaSound Source 等 SoundBase 类资产上也很重要。达到平台 max channels 时，优先级和最终音量会影响保留谁。关键对白、UI、玩法提示要比装饰 ambience 更高。

`Virtualization Mode` 用于循环声音被剔除或不可听时如何继续。用途是让音乐、ambience、机器循环在恢复可听时保持时间同步。普通 one-shot 不应依赖虚拟化续播。

## Submix 与 DSP 路由配置

Submix 是 Audio Mixer 的混音和 DSP 图。它一直运行，即使暂时没有声音进入。它有两个核心用途：把多个 source 混成一个输出 buffer，以及把同类声音一起送进 DSP 效果链。

典型路由：

```text
SFX_Submix
Dialogue_Submix
Music_Submix
UI_Submix
-> Master_Submix
-> Audio Hardware
```

`Parent Submix` / `Child Submixes`：定义 submix 图结构。声音从子 submix 流向父 submix，最终到 Master。用途是建立清晰的混音总线。

`Submix Effect Chain`：该 submix 的 DSP 效果链。用途是对一组声音统一加 EQ、compressor、limiter、reverb、delay、convolution、分析器等。不要在每个 Sound Wave 上重复同样效果。

`Mute when Backgrounded`：应用后台时该 submix 输出变为 0。用途是让某些声音在后台静音，同时允许其他必要音频继续。例如移动平台可以后台保留语音但静音游戏世界声。

`Ambisonics Plugin Settings`：把 submix 编码为空间声场的插件设置。用途是 VR、360 视频、ambisonic ambience。需要对应插件支持。

`Envelope Follower`：输出平滑后的响度包络。用途是用 submix 音量驱动 UI、灯光、VFX 或 gameplay，比直接逐采样读取更适合游戏帧率。

`Submix Sends`：声音除 base submix 外额外送到其他 submix。用途类似 DAW aux send，例如把脚步和枪声送到 reverb、把武器送到 sidechain 分析、把无线电对白送到 radio FX。

`Set Submix Output Volume`：Blueprint 直接设置 submix 输出音量。官方 submix 文档不建议把它作为主要游戏音量混音方式；它适合临时调试或局部修正。正式用户滑杆应优先用 Sound Class、Sound Mix 或 Audio Modulation。

`Submix Recording`：可把 submix 输出录成 wav 或 Sound Wave asset。用途是调试、导出程序化音频、录制回放或制作音频分析素材。

## Quartz 配置

Quartz 解决音频渲染 buffer、游戏线程和音频线程之间的时序误差，提供 sample-accurate scheduling。它适合动态音乐、节奏玩法、自动武器连发、节拍同步 UI、BGM stem 切换。

`Quartz Clock`：音频渲染线程上负责调度事件的时钟。用途是给一组音乐或节奏事件共享时间基准。

`Clock Name`：时钟名称。用途是让系统复用或查找时钟。建议按系统命名，例如 `CombatMusicClock`、`MetronomeClock`。

`Time Signature`：拍号配置。用途是决定 bar/beat 的音乐含义。4/4、3/4、7/8 等动态音乐项目要明确。

`Tick Rate` / `Beats Per Minute`：时钟速度。用途是和音乐 BPM 或玩法节奏同步。BPM 变化应通过 clock handle 控制，而不是靠延迟节点。

`Quartz Clock Handle`：游戏线程上的时钟代理。用途是在 Blueprint 中 start、stop、pause、subscribe 和 play quantized。

`Play Quantized`：让 Audio Component 在指定 Quantization Boundary 播放。用途是让鼓点、stem、stinger 或连发声精确落在拍点或时间边界。

`Quantization Boundary`：调度边界。包括 bar、beat、1/4、1/8、1/16、1/32、triplet、dotted 等音乐值，也有 multiplier 和 reference point。用途是表达“下一个小节开始播放”或“两个 beat 后触发”。

`Counting Reference Point`：调度相对参考。Bar Relative 适合小节内某拍；Transport Relative 适合歌曲时间线和 stem；Current Time Relative 适合从现在起推迟若干拍。

`Subscribe to Quantization Event`：订阅节拍事件。用途是让 gameplay、VFX、UI 与音频时钟同步，而不是用 Tick 或 Delay 追音乐。

使用建议：只要声音必须和节奏、BGM 或连发间隔稳定同步，就用 Quartz；普通 UI 点击和随机环境声不需要。

## 典型配置方案

UI 音效：

```text
Sound Wave: 短音效，低延迟加载
MetaSound: 随机 pitch/volume，one-shot
Attenuation: 无
Sound Class: UI，Is UISound 开启
Concurrency: hover/click 防抖
Submix: UI_Submix
```

脚步：

```text
Sound Wave: 多材质、多变体
MetaSound: 按材质选择数组，随机 pitch/volume，轻微滤波
Attenuation: Sphere，小半径，开启 spatialization
Concurrency: Limit To Owner，每角色限制
Sound Class: SFX/Footstep
Submix: SFX_Submix，可少量送 reverb
```

技能或武器：

```text
MetaSound: attack/body/tail 多层，玩法参数驱动层音量
Attenuation: Logarithmic 或 Natural，必要时 occlusion
Concurrency: 按技能类型限制，设置 voice steal fade
Sound Class: SFX/Weapon 或 SFX/Ability
Submix: SFX_Submix + Impact/Reverb send
```

环境循环：

```text
Sound Wave: 可循环 ambience 或 stem
MetaSound: 多层随机、距离/时间慢变化
Attenuation: Box/Capsule/大 Sphere，可开启 non-spatialized radius
Sound Class: Ambience，Apply Ambient Volume 开启
Submix: Ambience_Submix，可被 Dialogue/Combat duck
Loading: streaming 或 Prime on Load，按场景预载
```

动态音乐：

```text
Sound Wave: 分层 stem，循环点已在 DAW 校正
MetaSound 或 Audio Component: 负责播放层
Quartz: 小节边界触发切换
Audio Modulation: 战斗强度、菜单、低血量 mix
Sound Class: Music，Is Music 开启
Submix: Music_Submix
```

## 调试与验证

Audio Insights 是官方音频调试插件，默认未启用。启用后可从 Tools 打开 Audio Insights，在 PIE 或 standalone 中查看 sources、audio buses、submixes、pitch、volume 和参数值。standalone 连接 Unreal Insights 时需要 trace channel 包含 `cpu,audio,audiomixer`。

常用控制台命令：

```text
stat soundwave
stat soundcues
Audio3DVisualize
stat audiostreaming
```

`stat soundwave` 看正在发声的 Sound Wave instance；`stat soundcues` 看 Sound Cue；`Audio3DVisualize` 看 3D 声音位置；`stat audiostreaming` 看 stream cache。

调试顺序：

1. 确认声音是否真的在播放：Audio Insights 或 stat 命令。
2. 确认是否被 Concurrency、Max Channels、Priority 或 Virtualization 影响。
3. 确认路由：Sound Class、Base Submix、Submix Sends、Master Submix。
4. 确认空间：Attenuation、Occlusion trace、Spatialization plugin、listener 位置。
5. 确认加载：stream cache、Loading Behavior、是否提前 prime。
6. 确认 MetaSound 生命周期：`On Finished`、one-shot interface、循环是否意外停止或永不停止。

## 生产建议

不要把所有逻辑塞进 MetaSound。MetaSound 负责一个声音源内部的时序、随机、合成和层混合；Sound Class/Audio Modulation 负责全局混音；Submix 负责 DSP 路由；Quartz 负责精确调度；Attenuation 负责世界空间。

每个声音资产至少要明确四个归属：Sound Class、Submix、Attenuation、Concurrency。没有这四项，声音越多越难维护。

短而频繁的声音优先解决低延迟、并发和随机化；长而持续的声音优先解决 streaming、循环点、virtualization 和 ducking。

AI 生成音效导入 Unreal 前要先在 DAW 中做裁剪、响度统一、循环点和尾音处理。Unreal 可以做很多实时处理，但不应替代基础素材清理。

MetaSound Preset 是保持风格统一的关键。项目可以建立 `MSS_UI_Base`、`MSS_Footstep_Base`、`MSS_Impact_Base`、`MSS_Ambience_Layer_Base`，再用 Preset 覆盖输入，而不是复制一堆独立图。

## 相关条目

- [[ElevenLabs 音效生成]]
- [[ElevenLabs 游戏 BGM 生成]]
- [[AI 游戏音频生产工具链]]
- [[Unreal 远程控制]]

## 验证

- Epic Working with Audio 和 Audio in UE5 文档确认 UE 音频系统覆盖导入素材、Audio Mixer、Sound Cue、Sound Class、Sound Mix、MetaSound、Quartz 等能力。
- MetaSounds overview/reference 确认 MetaSound 是高性能 DSP 图系统，支持 Source、Patch、Preset、sample-accurate timing、输入输出、interfaces、output watching 和 Builder API。
- MetaSound Pages 文档确认 Pages 位于 Project Settings 的 Engine > MetaSounds，且用于按平台或运行时目标选择不同图或输入默认值，并标注为 Experimental。
- Project Audio Settings 文档确认 Default Sound Class、Default Sound Concurrency、Master Submix、Reverb Submix、Allow Play when Silent、Panning Method、Mono Channel Upmix Method 等配置项。
- Sound Classes、Sound Attenuation、Submixes、Audio Modulation、Quartz、Audio Insights 和 Stream Caching 官方文档作为配置用途整理来源。
