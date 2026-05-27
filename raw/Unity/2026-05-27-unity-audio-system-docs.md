# 2026-05-27 Unity 音频系统官方资料观察

Status: raw
Confidence: confirmed
Task: 搜集 Unity 音频系统的使用、配置、支持格式等资料并沉淀为 wiki
Sources:
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

Observation:
Unity 6.4 的音频系统可以按 Audio Clip / Audio Random Container、Audio Source、Audio Listener、Audio Mixer、Project Audio Settings、effects / reverb / spatializer、Profiler 几层理解。Unity 6.4 官方格式兼容页列出可导入 `.mp3`、`.aiff/.aif`、`.wav`、`.ogg`、`.flac`，并支持 tracker module：`.mod`、`.xm`、`.it`、`.s3m`。导入后 Unity 会把非 tracker 音频转码为适合目标平台和声音类型的运行时格式，主要配置点是 Load Type、Compression Format、Sample Rate Setting、Load In Background、Preload Audio Data 和平台 override。

Verification:
2026-05-27 读取 Unity 官方 Manual / Scripting API 当前在线文档；页面显示版本为 Unity 6.4 (6000.4)，Built on: 2026-05-22。未在本机 Unity 项目中创建场景或打包验证。

Boundary:
Unity 音频 UI 和功能会随版本变化。旧 LTS 版本可能没有 Audio Random Container、Scriptable Audio Pipeline，格式兼容表也可能不含 FLAC。落到具体项目时，应以目标 Unity 版本、目标平台、Project Settings、Audio Profiler 和真机试听为准。
