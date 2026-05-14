---
title: Unreal Sound Attenuation 配置项
tags:
- unreal-engine
- audio
- sound-attenuation
- spatial-audio
- game-audio
sources:
- raw/Unreal/2026-05-12-unreal-sound-attenuation-docs.md
- https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-attenuation?application_version=4.27
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Sound/FSoundAttenuationSettings
- https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SoundAttenuationSettings.html?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Components/UAudioComponent/AdjustAttenuation
confidence: confirmed
status: published
created: '2026-05-12'
updated: '2026-05-12'
---

# Unreal Sound Attenuation 配置项

## 摘要

Sound Attenuation 是 UE 中把声音从“播放一个音频文件”变成“场景中的 3D 声源”的核心配置。它通常挂在 Sound Wave、Sound Cue、MetaSound Source、Audio Component 或 Ambient Sound 上，用来控制：

```text
距离音量衰减 -> 空间方位 -> 空气吸收滤波 -> 听者焦点 -> 播放优先级 -> 混响/Submix 发送 -> 遮挡 -> 第三方插件
```

最常用的 3D 物件音效配置是：开启 Volume Attenuation、开启 Spatialization、形状用 Sphere、设置 Inner Radius/Shape Extents 和 Falloff Distance，并按需要开启 Occlusion。

## 编辑器中使用位置

- Content Browser 中创建 `Sounds > Sound Attenuation` 资产。
- 在 Audio Component 的 Attenuation Settings 上引用该资产。
- 也可以在 Audio Component 上启用 Override Attenuation，直接内联覆写设置。
- 运行时调用 `UAudioComponent::AdjustAttenuation` 时，设置应在播放前应用，因为 Attenuation 会在声音开始播放时传给新的 Active Sound。

## 距离音量衰减

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Volume Attenuation | `enable_volume_attenuation` / C++ `bAttenuate` | 是否根据声源到 Listener 的距离降低音量。关闭后，声音可仍然空间化，但不会随距离变小。 |
| Attenuation Function | `distance_algorithm` / attenuation function | 决定从内圈边界到最大距离之间音量下降的曲线。 |
| Linear | Linear | 线性下降，距离和音量变化直观，适合机器声、提示声等可控衰减。 |
| Logarithmic | Logarithmic | 近处下降较快、远处尾部较长，比较接近常见环境声感受。 |
| Inverse | Inverse | 按反比形式下降，近距离变化明显，远距离衰减较缓。 |
| Log Reverse | Log Reverse | Logarithmic 的反向风格，近处保持更久，接近边缘时更快下降。 |
| Natural Sound | Natural Sound | 模拟自然声压随距离下降的曲线，适合追求较自然空间感的点声源。 |
| Custom | Custom | 使用自定义曲线控制距离到音量的映射。 |
| Custom Attenuation Curve | `custom_attenuation_curve` | 自定义衰减曲线，仅在 Attenuation Function 为 Custom 时生效。 |
| Falloff Distance | `falloff_distance` | 从 Attenuation Shape 外边界继续向外的衰减距离；超过形状范围 + Falloff 后通常听不到或接近 0。 |

## Attenuation Shape

Attenuation Shape 定义“内圈”或“满音量区域”的几何形状。Listener 在形状内部时通常保持最大音量；离开形状后，在 Falloff Distance 范围内按衰减函数降低音量。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Attenuation Shape | `attenuation_shape` | 选择距离计算的基础形状：Sphere、Capsule、Box、Cone。 |
| Attenuation Shape Extents | `attenuation_shape_extents` | 形状参数向量，含义取决于 Shape 类型。 |
| Sphere | Sphere | 球形范围；通常 X 表示半径。适合火把、机器、传送门、怪物 idle 等点声源。 |
| Capsule | Capsule | 胶囊范围；通常 X 表示半径，Y 表示半高/长度参数。适合长条声源，如管道、水流、能量柱。 |
| Box | Box | 盒状范围；X/Y/Z 表示盒体半尺寸或范围。适合房间、区域型环境声。 |
| Cone | Cone | 锥形范围；用于有方向性的声源，如喇叭、喷口、朝向性的机器。 |
| Cone Offset | `cone_offset` | 将锥体原点沿反方向偏移，避免声音只从几何尖端开始，常用于让锥形声场覆盖发声物体前方。 |

## Spatialization 空间化

Spatialization 控制“听起来从哪个方向来”，而 Volume Attenuation 控制“离远后有多小”。两者可以独立开关。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Spatialization | `enable_spatialization` / C++ `bSpatialize` | 是否把声音作为 3D 声源进行方位渲染。关闭后更像 2D 声音。 |
| Spatialization Method | `spatialization_method` / `SpatializationAlgorithm` | 空间化算法。常见为 Panning 或 Binaural。 |
| Panning | Panning | 基于左右声道/扬声器声像定位，性能低、兼容性好。 |
| Binaural | Binaural | 基于 HRTF/双耳算法，耳机下方向感更强，通常依赖启用的空间音频插件。 |
| 3D Stereo Spread | `stereo_spread` / `StereoSpread` | 立体声资源空间化时，虚拟左右声道之间的世界距离。值越大，声源听起来越宽。普通点声源通常更推荐 mono。 |
| Normalize 3D Stereo Sounds | `normalize_3d_stereo_sounds` / `bApplyNormalizationToStereoSounds` | 对 3D 立体声源进行归一化，避免多声道叠加导致音量过大。 |
| Binaural Radius | `binaural_radius` | Listener 到声源距离小于该半径时，可能从双耳空间化切换或混合到普通声像，以避免近距离 HRTF 过度变化。 |
| Spatialization Plugin Settings | plugin settings | 第三方或平台空间化插件的专属配置数组。 |

## Air Absorption 空气吸收

Air Absorption 用距离驱动低通/高通滤波，模拟声音在空气中传播时高频逐渐损失，或制造远距离闷、近距离清晰的效果。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Air Absorption | `enable_air_absorption` / C++ `bAttenuateWithLPF` | 是否启用随距离变化的空气吸收滤波。 |
| Absorption Method | `absorption_method` | 空气吸收曲线来源，通常为 Linear 或 Custom。 |
| Enable Log Frequency Scaling | `enable_log_frequency_scaling` | 对频率插值使用对数尺度，使滤波频率变化更符合听感。 |
| Min Distance Range | `min_distance_range` | 空气吸收开始插值的距离。小于该距离通常使用 Min 侧滤波频率。 |
| Max Distance Range | `max_distance_range` | 空气吸收结束插值的距离。大于该距离通常使用 Max 侧滤波频率。 |
| Low Pass Cutoff Frequency Min | `air_absorption_lowpass_cutoff_frequency_min` / `LPFFrequencyAtMin` | 在近距离端使用的低通截止频率。值越高，高频保留越多。 |
| Low Pass Cutoff Frequency Max | `air_absorption_lowpass_cutoff_frequency_max` / `LPFFrequencyAtMax` | 在远距离端使用的低通截止频率。值越低，远处越闷。 |
| High Pass Cutoff Frequency Min | `air_absorption_highpass_cutoff_frequency_min` / `HPFFrequencyAtMin` | 在近距离端使用的高通截止频率。 |
| High Pass Cutoff Frequency Max | `air_absorption_highpass_cutoff_frequency_max` / `HPFFrequencyAtMax` | 在远距离端使用的高通截止频率。可用于距离越远低频越少等特殊效果。 |
| Custom Lowpass Air Absorption Curve | `custom_lowpass_air_absorption_curve` | 自定义距离到低通频率的曲线。 |
| Custom Highpass Air Absorption Curve | `custom_highpass_air_absorption_curve` | 自定义距离到高通频率的曲线。 |

## Listener Focus 听者焦点

Listener Focus 根据声源相对玩家视线/听者朝向的位置，改变音量、距离缩放和优先级。它常用于让镜头前方的声音更突出、镜头后方的声音更弱。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Listener Focus | `enable_listener_focus` / `bEnableListenerFocus` | 是否启用基于 Listener 朝向的焦点处理。 |
| Focus Azimuth | `focus_azimuth` | 正前方焦点角度范围。声源落在该角度内时被视为 in-focus。 |
| Non Focus Azimuth | `non_focus_azimuth` | 非焦点角度范围。通常大于 Focus Azimuth；两者之间会插值过渡。 |
| Focus Distance Scale | `focus_distance_scale` | 焦点内声源的距离缩放。小于 1 会让声音“听起来更近”。 |
| Non Focus Distance Scale | `non_focus_distance_scale` | 非焦点声源的距离缩放。大于 1 会让声音“听起来更远”。 |
| Focus Priority Scale | `focus_priority_scale` | 焦点内声源播放优先级缩放。用于并发裁剪时保留前方重要声音。 |
| Non Focus Priority Scale | `non_focus_priority_scale` | 非焦点声源播放优先级缩放。 |
| Focus Volume Attenuation | `focus_volume_attenuation` | 焦点内声源音量倍率。 |
| Non Focus Volume Attenuation | `non_focus_volume_attenuation` | 非焦点声源音量倍率。常用于降低背后或侧后方声音。 |
| Focus Attack Interp Speed | `focus_attack_interp_speed` | 声源进入焦点时参数变化的插值速度。 |
| Focus Release Interp Speed | `focus_release_interp_speed` | 声源离开焦点时参数恢复的插值速度。 |
| Enable Focus Interpolation | `enable_focus_interpolation` | 是否对焦点变化进行平滑插值，避免音量或滤波突变。 |

## Priority Attenuation 优先级衰减

Priority Attenuation 不直接改变音量，而是让距离影响 Active Sound 的优先级。它主要服务于声音并发和性能预算：当同时播放声音太多时，远处或不重要的声音更容易被裁掉。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Priority Attenuation | `enable_priority_attenuation` / `bEnablePriorityAttenuation` | 是否启用距离驱动的优先级缩放。 |
| Priority Attenuation Method | `priority_attenuation_method` | 优先级缩放方式，常见为 Linear、Custom 或 Manual。 |
| Priority Attenuation Min Distance | `priority_attenuation_distance_min` | 开始改变优先级的距离。 |
| Priority Attenuation Max Distance | `priority_attenuation_distance_max` | 优先级改变到远距离端的距离。 |
| Priority Attenuation Min | `priority_attenuation_min` | 远距离或最小端的优先级倍率。 |
| Priority Attenuation Max | `priority_attenuation_max` | 近距离或最大端的优先级倍率。 |
| Manual Priority Attenuation | `manual_priority_attenuation` | 手动指定固定优先级倍率。 |
| Custom Priority Attenuation Curve | `custom_priority_attenuation_curve` | 自定义距离到优先级倍率曲线。 |

## Reverb Send 混响发送

Reverb Send 控制声源向混响系统发送多少湿声。常见用法是近处干声更多、远处或空间深处混响更多。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Reverb Send | `enable_reverb_send` / `bEnableReverbSend` | 是否允许 Attenuation 控制混响发送量。 |
| Reverb Send Method | `reverb_send_method` | 混响发送量控制方式，常见为 Linear、Custom 或 Manual。 |
| Reverb Wet Level Min | `reverb_wet_level_min` | 最小混响发送量。 |
| Reverb Wet Level Max | `reverb_wet_level_max` | 最大混响发送量。 |
| Reverb Distance Min | `reverb_distance_min` | 开始按距离改变混响发送量的距离。 |
| Reverb Distance Max | `reverb_distance_max` | 达到最大/最终混响发送量的距离。 |
| Manual Reverb Send Level | `manual_reverb_send_level` | 手动固定混响发送量。 |
| Custom Reverb Send Curve | `custom_reverb_send_curve` | 自定义距离到混响发送量曲线。 |
| Reverb Plugin Settings | plugin settings | 第三方或平台混响插件的专属配置。 |

## Occlusion 遮挡

Occlusion 通过从 Listener 到声源做碰撞检测，判断声音是否被墙体或物体遮挡。遮挡后通常降低音量并降低低通截止频率，让声音变闷。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Occlusion | `enable_occlusion` / `bEnableOcclusion` | 是否启用声音遮挡检测。 |
| Occlusion Trace Channel | `occlusion_trace_channel` | 用于遮挡射线检测的碰撞通道。需要与项目碰撞设置匹配。 |
| Use Complex Collision for Occlusion | `use_complex_collision_for_occlusion` | 是否使用复杂碰撞。更精确但更贵；大多数项目优先使用简单碰撞。 |
| Occlusion Low Pass Filter Frequency | `occlusion_low_pass_filter_frequency` | 被遮挡时应用的低通截止频率。值越低，声音越闷。 |
| Occlusion Volume Attenuation | `occlusion_volume_attenuation` | 被遮挡时的音量倍率。小于 1 会降低音量。 |
| Occlusion Interpolation Time | `occlusion_interpolation_time` | 遮挡状态变化时的插值时间，避免开门、穿墙、移动时音色突变。 |
| Occlusion Plugin Settings | plugin settings | 第三方或平台遮挡插件的专属配置。 |

## Submix Sends

Submix Send 让 Attenuation 按距离控制声源送往一个或多个 Sound Submix 的发送量。它适合做距离相关的效果总线，例如远距离滤波、洞穴反射、无线电处理或特殊环境声处理。

| 编辑器项 | UE5/Python 常见名 | 作用 |
|---|---|---|
| Enable Submix Sends | `enable_submix_sends` / `bEnableSubmixSends` | 是否启用 Attenuation 驱动的 Submix 发送。 |
| Submix Send Settings | `submix_send_settings` | Submix 发送配置数组，可配置多个目标 Submix。 |
| Sound Submix | `sound_submix` | 目标 Sound Submix。 |
| Send Level Control Method | `send_level_control_method` | 发送量控制方式，常见为 Linear、Custom 或 Manual。 |
| Send Level | `send_level` | 手动发送量或基础发送量。 |
| Disable Manual Send Clamp | `disable_manual_send_clamp` | 手动发送量是否绕过 Min/Max 夹取。 |
| Min Send Level | `min_send_level` | 最小发送量。 |
| Max Send Level | `max_send_level` | 最大发送量。 |
| Min Send Distance | `min_send_distance` | 开始插值发送量的距离。 |
| Max Send Distance | `max_send_distance` | 达到最终发送量的距离。 |
| Custom Send Level Curve | `custom_send_level_curve` | 自定义距离到 Submix 发送量曲线。 |

## Plugin Settings

UE 的 Attenuation 可把设置传给平台或第三方音频插件。常见分组包括：

| 配置项 | 作用 |
|---|---|
| Spatialization Plugin Settings Array | 空间化插件配置，例如 HRTF、平台 3D 音频或第三方声学插件。 |
| Occlusion Plugin Settings Array | 遮挡插件配置，用于替代引擎默认射线遮挡或增加声学传播模型。 |
| Reverb Plugin Settings Array | 混响插件配置，用于平台/第三方混响发送和环境声学。 |

这些设置是否显示、字段是什么，取决于项目启用的 Audio Plugin。

## 实用建议

- 普通 3D 点声源优先使用 mono 资源 + Spatialization；stereo 资源空间化时要额外检查 Stereo Spread 和归一化。
- 小物件循环声可从 Sphere + Inner Radius 200~500 + Falloff 1000~3000 起步。
- 门后、墙后、洞穴内声源再开启 Occlusion；大量短促音效不应无脑开启复杂遮挡。
- 远距离音色需要更自然时启用 Air Absorption，而不是只靠音量衰减。
- 并发很多的场景启用 Priority Attenuation，可减少远处低价值声音抢占声道。
- Reverb Send 和 Submix Sends 适合做空间混音，不建议把所有距离音色变化都塞进单个 Sound Cue。

## 与 [[Unreal 音频系统与 MetaSounds]] 的关系

Sound Attenuation 负责播放实例的空间和距离语义；MetaSound 负责声音内容本身的程序化生成和参数化。需要按距离或方位改变 MetaSound 内部音色时，可以使用 MetaSound 的 Attenuation/Spatialization 相关接口读取距离和方向，而不是在蓝图里每帧手动推参数。
