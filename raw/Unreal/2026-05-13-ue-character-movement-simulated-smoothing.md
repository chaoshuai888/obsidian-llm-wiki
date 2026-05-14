# 2026-05-13 UE Character Movement Simulated Smoothing

Status: raw
Confidence: confirmed
Task: 读取 D:/UnrealEngine 中 UE5 CharacterMovement 源码，沉淀模拟端移动插值逻辑，并区分本地修改与官方 5.5.2 基线
Sources:
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
- command: git -C D:/UnrealEngine describe --tags --always --dirty
- command: git -C D:/UnrealEngine diff --stat 5.5.2-release -- Engine/Source/Runtime/Engine/Private/Components/CharacterMovementComponent.cpp Engine/Source/Runtime/Engine/Classes/GameFramework/CharacterMovementComponent.h

Observation:
UE CharacterMovement 的模拟端平滑不是把服务端 Actor 位置慢慢插过去，而是网络更新到达后先把 capsule/UpdatedComponent 校正到新权威位置，同时给 Mesh 留下一个视觉 offset，再在后续 tick 里把这个 offset 插值或衰减回零。主要链路是 `ACharacter::PostNetReceiveLocationAndRotation -> UCharacterMovementComponent::SmoothCorrection -> SimulatedTick/SimulateMovement -> SmoothClientPosition_Interpolate -> SmoothClientPosition_UpdateVisuals`。`ENetworkSmoothingMode` 有 Disabled、Linear、Exponential 三种，其中默认是 Exponential；Linear 使用服务端时间戳算 alpha，Exponential 按平滑时间衰减 offset。

Verification:
本地源码目录当前分支为 `nd-master`，描述为 `5.5.2-release-199-gdc0fe411c845`，读取时 `git status --short` 为空。相对 `5.5.2-release`，`CharacterMovementComponent.cpp/.h` 有本地修改，主要涉及调试绘制、NavWalking floor 判断、忽略 root motion 位移、客户端上传 MaxWalkSpeed、一次性旋转等；核心 `SmoothCorrection`、Linear/Exponential 插值算法本身未见逻辑性改写，仅有一处调试显示位置从 130 改为 300。

Boundary:
本观察针对 UE 5.5.2 附近的本地源码快照。由于 `D:/UnrealEngine` 有本地改动，涉及 NavWalking、root motion、速度上发或瞬转时，应回到本地 diff 和项目需求复核，不能把这些改动当作 Epic 原版行为。
