---
confidence: confirmed
created: 2026-05-13
sources:
- raw/Unreal/2026-05-13-ue-character-movement-simulated-smoothing.md
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h:952
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Character.cpp:1541
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Character.cpp:1633
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:683
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:1662
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:1817
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:2119
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:7990
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:8187
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:8211
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:8362
- D:/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp:12098
status: published
tags:
- unreal-engine
- character-movement
- networking
- interpolation
- source-code
title: "Unreal 模拟端移动插值"
updated: '2026-05-14'
---

# Unreal 模拟端移动插值

## 结论

UE CharacterMovement 的模拟端移动平滑并不是“Actor 位置慢慢插到服务端位置”。网络更新到达后，组件先把 `UpdatedComponent`，通常是 capsule，校正到权威位置；为了避免视觉跳变，`CharacterOwner->GetMesh()` 会保留一个相对 offset，然后后续 tick 里把 mesh offset 插值或衰减回正常相对位置。

核心链路是：

```text
ACharacter::PostNetReceiveLocationAndRotation
-> UCharacterMovementComponent::SmoothCorrection
-> UCharacterMovementComponent::SimulatedTick / SimulateMovement
-> UCharacterMovementComponent::SmoothClientPosition
-> SmoothClientPosition_Interpolate
-> SmoothClientPosition_UpdateVisuals
```

这里的“模拟端”主要指非拥有客户端上的 `ROLE_SimulatedProxy`。监听服务器上看到远端自主代理时，也可能通过 listen server smoothing 走同一套 `SmoothClientPosition` 视觉平滑。

## 版本边界

本条目基于本机 `D:/UnrealEngine`，读取时分支为 `nd-master`，描述为 `5.5.2-release-199-gdc0fe411c845`。相对 `5.5.2-release`，`CharacterMovementComponent.cpp/.h` 有本地改动：调试绘制、NavWalking floor 判断、忽略 root motion 位移、客户端上传 `MaxWalkSpeed`、一次性旋转等。

核心平滑算法 `SmoothCorrection`、`SmoothClientPosition_Interpolate` 和 `SmoothClientPosition_UpdateVisuals` 未见逻辑性本地改写；只有一处模拟修正调试文本位置从 130 调到 300。涉及 NavWalking、root motion、速度上发或瞬转时，应按本地源码理解，不要直接当 Epic 原版行为。

## 关键数据

`ENetworkSmoothingMode` 有三种模式：

- `Disabled`：不平滑，网络位置到达就更新。
- `Linear`：从源到目标线性插值。
- `Exponential`：指数式衰减，离目标越远视觉修正越快。

`UCharacterMovementComponent` 默认 `NetworkSmoothingMode = Exponential`。默认平滑参数包括：

- `NetworkSimulatedSmoothLocationTime = 0.100f`
- `NetworkSimulatedSmoothRotationTime = 0.050f`
- `ListenServerNetworkSimulatedSmoothLocationTime = 0.040f`
- `ListenServerNetworkSimulatedSmoothRotationTime = 0.033f`
- `NetworkMaxSmoothUpdateDistance = 256.f`
- `NetworkNoSmoothUpdateDistance = 384.f`

运行时状态主要存在 `FNetworkPredictionData_Client_Character`：

- `OriginalMeshTranslationOffset`：一次修正开始时的 mesh 平移 offset。
- `MeshTranslationOffset`：当前仍需视觉平滑掉的平移 offset。
- `OriginalMeshRotationOffset`：Linear 模式下旋转插值起点。
- `MeshRotationOffset`：当前视觉旋转 offset 或 Linear 插值旋转。
- `MeshRotationTarget`：旋转目标。
- `SmoothingServerTimeStamp` / `SmoothingClientTimeStamp`：Linear 模式计算插值进度。
- `LastCorrectionDelta`：上次修正需要平滑的服务端时间跨度。

`bNetworkSmoothingComplete` 是一个跳过开关。新修正到达时 `SmoothCorrection` 把它设为 false；插值完成后 `SmoothClientPosition_Interpolate` 把它设为 true，后续 tick 不再调用平滑。

## 网络更新入口

`ACharacter::PostNetReceiveLocationAndRotation` 在模拟代理收到复制位置时触发。如果不是基于 movement base 的相对位置，它会：

1. 记录旧位置和旧旋转。
2. 从 `ReplicatedMovement.Location` 计算新位置。
3. 把 `bNetworkSmoothingComplete` 置 false。
4. 调用 `CharacterMovement->SmoothCorrection(OldLocation, OldRotation, NewLocation, RepRotation)`。
5. 调用 `OnUpdateSimulatedPosition`，并设置 `bNetworkUpdateReceived`。

Linear 平滑依赖服务端 transform 更新时间。`ACharacter::PreReplication` 只在 `NetworkSmoothingMode == Linear` 或强制复制时间戳时复制 `ReplicatedServerLastTransformUpdateTimeStamp`，用于客户端按服务端更新间隔计算插值 alpha。

## SmoothCorrection 做什么

`SmoothCorrection` 的重点是“修正 capsule，保留 mesh 视觉连续性”。

通用步骤：

1. 确认只在模拟代理或 listen server 远端自主代理上运行。
2. 计算 `NewToOldVector = OldLocation - NewLocation`。
3. NavWalking 且 Z 误差很小时，忽略重力方向上的小误差。
4. 根据 `MaxSmoothNetUpdateDist` 和 `NoSmoothNetUpdateDist` 限制或取消平移平滑。
5. 更新平滑时间戳，限制客户端平滑时间不要落后太多或跑到服务端时间之后。

`Disabled` 模式直接 `SetWorldLocationAndRotation(NewLocation, NewRotation, TeleportPhysics)`，然后标记平滑完成。

`Linear` 模式保存平移和旋转插值起点：`OriginalMeshTranslationOffset`、`OriginalMeshRotationOffset`、`MeshRotationOffset`、`MeshRotationTarget`。随后只移动 capsule 到 `NewLocation`，暂不直接把旋转设成目标旋转，注释也明确说旋转会在 `SmoothClientPosition` 中插过去。

`Exponential` 模式立即把 capsule 的位置和旋转设为新网络值，同时把 mesh 的旋转 offset 改成“新 capsule 旋转到旧视觉旋转”的差值。之后 mesh offset 会衰减回零和 identity。

## SimulatedTick 和代理预测

`TickComponent` 遇到 `ROLE_SimulatedProxy` 会调用 `SimulatedTick`。非 root motion 的常规路径里，如果角色复制 movement：

1. 如果平滑未完成，用 `FScopedPreventAttachedComponentMove` 暂时阻止 mesh 跟着 capsule 模拟移动。
2. 没有特殊 root motion 时调用 `SimulateMovement`。
3. `SimulateMovement` 根据网络更新标志刷新重力方向和 movement mode，处理 pending launch、base movement、proxy acceleration。
4. 代理用当前速度 `MoveSmooth(Velocity, DeltaSeconds)` 做前向模拟。
5. 之后做 floor 检查，必要时切到 falling。
6. 最后如果平滑未完成，调用 `SmoothClientPosition` 更新视觉。

本地分支在 `SimulateMovement` 的 floor 检查里改过 NavWalking 逻辑：`MOVE_NavWalking` 时会用 `FindNavFloor` 判断导航地面，并影响是否切 falling。这会影响代理模拟结果，但不是平滑算法本身。

## Linear 插值

Linear 模式可以理解成“按网络更新的时间轴，把上一次修正平摊播放完”。它特别在意服务端 transform 更新的时间戳，而不是简单用一个固定的 `SmoothNetUpdateTime` 去倒计时。

网络包到达时，`SmoothCorrection` 已经知道两件事：

- 客户端刚才本地模拟出来的位置和旋转：`OldLocation`、`OldRotation`。
- 服务端新复制过来的权威位置和旋转：`NewLocation`、`NewRotation`。

Linear 的处理方式是：位置上先把 capsule 移到 `NewLocation`，但让 mesh 留在视觉上接近旧位置；旋转上记住 `OldRotation` 和 `NewRotation`，后续逐帧把视觉旋转插过去。这样碰撞和网络状态尽快贴近服务端，而玩家眼睛看到的骨骼网格不会瞬间跳一格。

更直观地说，如果服务端告诉客户端：“你现在其实应该在前方 30 cm”，Linear 不会让角色 mesh 立刻弹到前方 30 cm；它会先让 capsule 到正确位置，再让 mesh 相对 capsule 暂时落后 30 cm，随后用一段时间把这个相对偏移拉回 0。

`SmoothCorrection` 在 Linear 模式下会准备这些起点和终点：

- `OriginalMeshTranslationOffset`：这次修正开始时 mesh 相对权威位置的平移误差。
- `MeshTranslationOffset`：当前帧仍然保留的平移误差。
- `OriginalMeshRotationOffset`：旋转插值起点，通常是修正前的旋转。
- `MeshRotationTarget`：旋转插值终点，也就是服务端复制过来的新旋转。
- `LastCorrectionDelta`：这次修正对应的服务端更新时间跨度。

后续每帧 `SmoothClientPosition_Interpolate` 会先推进客户端平滑时间：

```text
SmoothingClientTimeStamp += DeltaSeconds
RemainingTime = SmoothingServerTimeStamp - SmoothingClientTimeStamp
CurrentSmoothTime = LastCorrectionDelta - RemainingTime
LerpPercent = CurrentSmoothTime / LastCorrectionDelta
```

这里的意思是：客户端不问“我想用 0.1 秒完成吗”，而是问“按服务端两次更新之间的真实间隔，我现在应该播放到百分之多少”。如果上一段服务端更新时间跨度是 0.05 秒，那么平滑就倾向于用这 0.05 秒完成；如果网络更新间隔变大，平滑窗口也会跟着变大。

UE 还会做两个保护：

- 如果客户端平滑时间跑到服务端时间戳前面太多，会把它限制住。
- `LerpLimit = 1.15`，允许移动中的角色最多插到 115%，也就是一点点前推。

这个 1.15 很关键。移动角色如果严格停在 100%，在下一次网络更新还没来时容易显得微微落后；允许一点前推，可以让连续移动看起来更顺。但它不是无限预测，超过这个范围就会认为平滑完成。

当 `LerpPercent < 1`：

- `MeshTranslationOffset` 从 `OriginalMeshTranslationOffset` 线性插到 `ZeroVector`。
- `MeshRotationOffset` 从 `OriginalMeshRotationOffset` 通过 `FastLerp` 插到 `MeshRotationTarget`。

当 `LerpPercent` 接近或超过 1：

- 如果速度接近 0，直接清零 translation offset，并把 client timestamp 对齐 server timestamp。
- 如果仍在移动，允许插值继续到 `1.15`，提供一点前推缓冲。
- rotation offset 直接设为目标。

可以用一个小例子理解。假设这次网络修正发现 mesh 视觉上比权威位置落后 40 cm，`LastCorrectionDelta` 是 0.1 秒：

- 刚收到修正时，`MeshTranslationOffset` 约等于 40 cm。
- 过了 0.05 秒，`LerpPercent` 约等于 0.5，mesh 还保留约 20 cm offset。
- 过了 0.1 秒，`LerpPercent` 约等于 1，offset 回到 0。
- 如果角色仍在移动，可能继续允许到 1.15，用很小的前推减少视觉落后。

`SmoothClientPosition_UpdateVisuals` 负责把这些插值结果真正应用到组件上。平移上，它会把 `MeshTranslationOffset` 转成 mesh 的相对位置；旋转上，如果当前 capsule 旋转和插值中的 `MeshRotationOffset` 不一致，会设置 `UpdatedComponent` 的世界旋转，并配合直接写 mesh 相对位置来减少 transform 链的重复更新。

因此 Linear 模式的核心直觉是：把“上一次服务端修正造成的误差”当成一段动画，按服务端时间轴线性播放完。它的好处是时间语义清晰，特别适合 replay 或需要按服务端更新间隔还原移动的场景；代价是它依赖服务端更新时间戳，普通 listen server 场景下 UE 默认会把 Linear 改回 Exponential。

## Exponential 衰减

Exponential 模式可以理解成“每帧消掉剩余误差的一部分”。它不按服务端时间戳算 `LerpPercent`，也不试图保证某个 correction interval 内刚好从 0 走到 1；它只关心当前还剩多少视觉 offset，然后按 `SmoothNetUpdateTime` 和 `DeltaSeconds` 把 offset 往 0 衰减。

网络包到达时，`SmoothCorrection` 在 Exponential 模式下会更果断：

- capsule 的位置和旋转直接设成服务端新值。
- `MeshTranslationOffset` 记录旧位置到新位置之间的视觉误差。
- `MeshRotationOffset` 记录一个旋转差，让 mesh 在视觉上先保持接近旧朝向。
- `MeshRotationTarget` 通常是 identity，表示最终 mesh 不再额外抵消 capsule 旋转。

换句话说，真实移动组件已经贴到权威状态；平滑只发生在 mesh 的相对平移和相对旋转上。看到的角色慢慢归位，但碰撞胶囊已经在服务端认可的位置。

每帧的位置衰减逻辑是：

- 如果速度为零，位置平滑时间使用 `0.5 * SmoothNetUpdateTime`，停止时更快归位。
- 如果 `DeltaSeconds < SmoothLocationTime`，`MeshTranslationOffset *= (1 - DeltaSeconds / SmoothLocationTime)`。
- 否则 translation offset 直接清零。
- rotation offset 通过 `FastLerp(MeshRotationOffset, MeshRotationTarget, DeltaSeconds / SmoothNetUpdateRotationTime)` 靠近目标。

这里的乘法是 Exponential 模式的关键。假设 `SmoothLocationTime = 0.1`，当前帧 `DeltaSeconds = 0.016`，那么本帧会保留约 `1 - 0.016 / 0.1 = 84%` 的剩余 offset，消掉约 16%。下一帧不是再消掉原始误差的 16%，而是消掉“剩余误差”的 16%。

所以如果初始 offset 是 40 cm，大致会像这样靠近 0：

```text
40.0 -> 33.6 -> 28.2 -> 23.7 -> 19.9 -> ...
```

它一开始收得快，越接近目标越慢。这就是“指数衰减”的体感：大误差能快速压下去，小误差会柔和地贴近目标。UE 最后会用阈值收尾，避免无限接近但永远不完成。

当 translation offset 足够接近 0，并且 rotation offset 等于目标时，`bNetworkSmoothingComplete = true`，并把 translation offset 精确清零。

视觉应用时，Exponential 模式不会再改 capsule 的权威位置；它只把 mesh 的相对平移设置为 `UpdatedComponent` 逆变换下的 offset，并把 mesh 相对旋转设置为 `MeshRotationOffset * BaseRotationOffset`。

Exponential 的直觉比 Linear 更像弹簧阻尼，但源码里不是物理弹簧，没有速度状态，也没有二阶振荡；它只是按比例减少误差。它的优点是实现简单、对不稳定网络更新间隔比较宽容、默认效果通常不突兀；缺点是它没有 Linear 那种“按服务端时间轴严格走到目标”的语义，平滑尾巴更多由阈值和时间常量决定。

对比一下两种模式：

- Linear：我知道上一段服务端时间跨度，按这个跨度把误差从起点插到终点。
- Exponential：我不关心上一段服务端时间跨度，每帧按比例砍掉当前剩余误差。
- Linear 的速度更像匀速播放一段修正动画。
- Exponential 的速度更像先快后慢地贴近目标。
- 两者都不是改变服务器权威位置，本质都是让 mesh 的视觉表现别突然跳变。

## 应用场景与案例

`NetworkSmoothingMode` 不建议只按“哪个更平滑”来选，而要看你更在意什么：时间还原、视觉稳定、调试真相，还是完全交给自定义系统。

### Exponential

Exponential 是普通网络对战角色最常用、也最稳妥的默认选择。UE 构造函数里默认就是 `ENetworkSmoothingMode::Exponential`，listen server 上如果配置成 Linear，也会在注册时改回 Exponential。

适合：

- 常规联机角色，尤其是第三人称动作、ARPG、射击游戏里看到的其他玩家。
- 网络更新间隔不完全稳定的场景。
- 更重视“看起来别抖、别停顿”，而不是严格按服务端时间轴还原。
- 服务器更新频率较高、误差通常不大，只需要把小修正柔和消掉。

直观案例：一个远端玩家持续跑步，网络包有时 50 ms 来一包，有时 80 ms 来一包。Exponential 不会强依赖每两包之间的精确时间跨度，而是每帧消掉当前 offset 的一部分；包间隔抖动时，视觉上通常更柔和。

容易踩坑：

- 它是“按比例衰减”，不是严格定时抵达目标；尾巴什么时候结束主要看阈值和 smooth time。
- 如果修正很频繁且 offset 一直没消完，mesh 可能长期带着一点视觉滞后。
- 误差很大时，虽然会被快速压下去，但仍可能看到明显拉回；这时要先查为什么 capsule 一直偏离服务端。

### Linear

Linear 更适合需要“按服务端更新节奏播放 correction”的场景。它用 `SmoothingServerTimeStamp`、`SmoothingClientTimeStamp` 和 `LastCorrectionDelta` 来算 alpha，所以它的平滑过程更像把服务端两次更新之间的时间切成一段播放轨道。

适合：

- replay、回放、观战录制等需要按时间轴还原的场景。UE 源码里 replay 会强制使用 Linear。
- 你想让模拟代理的视觉位置更严格地跟随服务端 transform 更新时间。
- 调试网络平滑时间戳、观察 correction alpha、比较服务端更新间隔对视觉的影响。
- 网络更新比较规律，且你希望误差用接近匀速的方式被吃掉。

直观案例：录制回放时，角色在第 10.00 秒和第 10.05 秒有两次服务端 transform 更新。Linear 会倾向于把这 0.05 秒当作修正播放窗口，这样回放里的移动更像沿着服务器时间轴重建出来，而不是用一个固定衰减时间自由贴近。

容易踩坑：

- 移动中会允许 `LerpPercent` 超过 100%，最多到 `1.15`，这是为了下一包没来时别显得卡在目标点。
- 如果服务端时间戳不稳定、复制更新时间异常，Linear 的视觉节奏也会被牵动。
- 普通 listen server 视角下，Linear 通常不是最佳默认值，因为本机渲染 tick 和远端客户端更新节奏很容易不一致。

### Disabled

Disabled 是“不要视觉平滑”。收到网络修正后，`SmoothCorrection` 直接把 `UpdatedComponent` 设置到新位置和新旋转，并把 `bNetworkSmoothingComplete` 标成 true。mesh 不再保留 offset 慢慢回正，所以你看到的就是原始网络修正。

适合：

- 调试 raw correction：想确认服务端到底多久修一次、每次修多大，不想被 mesh smoothing 掩盖。
- 非角色展示对象，视觉跳变可以接受，或者对象本身没有需要平滑的角色 mesh。
- 你自己实现了另一套插值、预测或表现层，不希望 CMC 再做一层 mesh offset。
- 需要瞬时对齐的特殊状态，例如某些传送、重生、强制同步、调试校验流程。

直观案例：排查“到底是网络修正抖，还是平滑算法造成拖尾”时，可以临时设成 Disabled。如果 Disabled 下角色位置一跳一跳，说明服务端修正本身就很频繁或很大；如果 Disabled 下反而更符合预期，而开启平滑后出现拖影，就该重点看 `MeshTranslationOffset`、smooth time 和更新频率。

容易踩坑：

- 普通联机角色不建议长期开 Disabled，远端角色会直接 pop 到新位置。
- 它不能解决网络误差，只是把误差赤裸裸显示出来。
- 如果你关掉 CMC 平滑但没有自己的表现层，低更新率或丢包下视觉质量会明显下降。

简单选择规则：

- 默认联机玩法：先用 Exponential。
- replay 或强时间轴还原：考虑 Linear。
- 查原始网络修正或完全自定义表现：用 Disabled。
- 不确定时，先看 `p.NetVisualizeSimulatedCorrections` 和 `MeshTranslationOffset`，不要只凭肉眼判断模式好坏。

## 调试要点

排查模拟端抖动时，先分清三件事：

1. capsule 是否被频繁校正：看网络复制、服务端权威位置、`SmoothCorrection` 进入频率。
2. mesh offset 是否过大或被取消：看 `NetworkMaxSmoothUpdateDistance`、`NetworkNoSmoothUpdateDistance` 和 `MeshTranslationOffset`。
3. 代理前向模拟是否和服务端偏离：看 `SimulateMovement`、movement mode、floor、base movement、root motion 和速度。

`p.NetVisualizeSimulatedCorrections` 可以画出修正和平滑位置；本地源码把部分调试文字位置上移过，因此调试显示的高度不完全等同 Epic 原版。

## 下次如何使用

需要解释 UE 模拟代理移动平滑时，优先按“capsule 立即校正，mesh 视觉 offset 插值回零”来理解。Linear 适合关注服务端时间戳和插值 alpha；Exponential 适合关注 offset 衰减时间；Disabled 适合看清未平滑的原始 correction。遇到本地项目的 NavWalking、root motion 或瞬转问题时，不要只套官方 CMC 逻辑，要先看本地 `CharacterMovementComponent` diff。

相关动画选姿和轨迹匹配逻辑见 [[Unreal Motion Matching 核心原理]]。
