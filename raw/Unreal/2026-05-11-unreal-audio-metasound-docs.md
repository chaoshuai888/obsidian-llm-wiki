# 2026-05-11 Unreal Audio 与 MetaSound 官方文档调研

Status: raw
Confidence: confirmed
Task: 搜集整理 Unreal MetaSound 和 Unreal 音频系统信息，并详细介绍配置用途
Sources:
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

Observation:
Unreal 音频系统以 Sound Wave/MetaSound/Sound Cue 作为声音源，以 Audio Component 触发播放，以 Sound Attenuation、Sound Concurrency、Sound Class、Sound Mix、Audio Modulation 和 Submix 控制空间、并发、分组、动态混音和 DSP 路由。MetaSound 是 UE5 的高性能 DSP 图系统，适合做程序化音效、样本精确触发、参数化音效模板和游戏状态驱动的声音变体。

Verification:
已核对 Epic 官方 Working with Audio、Audio in UE5、Audio Engine Overview、MetaSounds overview/reference、MetaSound Pages、Project Audio Settings、Sound Classes、Sound Attenuation、Submixes、Audio Modulation、Quartz、Audio Insights 和 Stream Caching 文档。配置项说明以官方文档为事实来源，实践建议为对这些系统在游戏音频流水线中的归纳。

Boundary:
Sound Attenuation 和 Audio Stream Caching 的部分长文档当前官方搜索结果仍指向 4.27 页面，但对应 API 与 UE5 文档中仍有相关结构和设置。项目落地时应以目标 UE 版本编辑器里的实际 Project Settings、平台 Audio Settings、插件状态和打包平台为准。MetaSound Pages 文档标注为 Experimental，发布项目中使用前需要单独验证平台 cook、回退和运行时切换行为。
