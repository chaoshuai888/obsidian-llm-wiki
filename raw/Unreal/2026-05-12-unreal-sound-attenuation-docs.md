# 2026-05-12 Unreal Sound Attenuation 官方文档观察

Status: raw
Confidence: confirmed
Task: 搜索 UE 官方文档，详细介绍 Attenuation 每个配置项，并沉淀为 wiki
Sources:
- https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-attenuation?application_version=4.27
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Sound/FSoundAttenuationSettings
- https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SoundAttenuationSettings.html?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Components/UAudioComponent/AdjustAttenuation
- WebSearch result snippets on 2026-05-12; WebFetch to dev.epicgames.com was blocked by network safety verification.

Observation:
UE 的 Sound Attenuation 资产/结构用于统一控制 3D 声音的距离音量衰减、空间化、空气吸收、听者焦点、优先级、混响发送、遮挡、Submix 发送和插件扩展。编辑器标签、C++ `FSoundAttenuationSettings` 字段和 Python `unreal.SoundAttenuationSettings` 属性名称存在大小写/命名差异，但概念一一对应。

Verification:
通过 UE 官方 Sound Attenuation 文档、UE5.6 C++ API 页面、UE5.6 Python API 页面和搜索结果摘要交叉确认。由于当前环境无法直接 WebFetch dev.epicgames.com 页面正文，细项说明按官方页面可检索摘要、API 字段名和 UE 常用编辑器命名整理。

Boundary:
不同 UE 版本、音频插件和项目设置可能显示不同字段；第三方 Spatialization/Occlusion/Reverb 插件会扩展插件配置数组。遇到项目内具体版本时，应以当前引擎编辑器 Details 面板和对应版本 API 为准。
