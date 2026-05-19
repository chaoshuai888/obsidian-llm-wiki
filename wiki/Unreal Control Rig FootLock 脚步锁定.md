---
title: Unreal Control Rig FootLock 脚步锁定
tags:
- unreal-engine
- control-rig
- animation
- ik
- foot-lock
sources:
- raw/Unreal/2026-05-14-unreal-control-rig-footlock.md
- E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootLock_full.json
- E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootLock_summary.md
- E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootIKLibrary_full.json
- E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootIKLibrary_summary.md
- E:/NDSVN_UE_ARPG_Battle/Source/Runtime/GameComponent/MeshRotationSmoothCpt.cpp:33
- E:/NDSVN_UE_ARPG_Battle/Source/Runtime/GameComponent/MeshRotationSmoothCpt.cpp:113
- E:/NDSVN_UE_ARPG_Battle/Source/Runtime/GameComponent/MeshRotationSmoothCpt.h:13
- E:/NDSVN_UE_ARPG_Battle/Source/Runtime/GameBase/MyAnimInstanceBase.h:10
- E:/NDSVN_UE_ARPG_Battle/Source/Runtime/GameSystem/SkillSystem.cpp:299
- E:/NDSVN_UE_ARPG_Battle/Source/Runtime/GameSystem/GameSkillUtility.cpp:355
- E:/NDSVN_UE_ARPG_Battle/Source/Runtime/GameComponent/FRigUnit_ActorFollow.cpp:9
confidence: confirmed
status: published
created: 2026-05-14
updated: 2026-05-14
---

# Unreal Control Rig FootLock 脚步锁定

## Summary

`CRFL_FootLock` 的作用是：技能强制角色转向时，让作为转向轴的左脚或右脚临时保持在世界空间原地，避免 `UMeshRotationSmoothCpt` 平滑旋转 Mesh 的过程中出现脚底滑动。

完整闭环是：

```text
AttackRotation Notify
-> USkillSystem::GetRotationSmoothTime 读取 RoatationAxis
-> UGameSkillUtility::FaceTarget 先旋转 Actor
-> UMeshRotationSmoothCpt::StartMeshSmooth 将 Mesh 退回旧朝向，并写 FootLockData
-> CRFL_FootLock 根据 EnableLFootLock / EnableRFootLock 锁左脚或右脚
-> ExcuteFootIK 应用锁定后的脚目标
-> ActorFollow 把骨盆世界位置回传给 UMeshRotationSmoothCpt
-> UMeshRotationSmoothCpt::UpdateMeshRotation 平滑 Mesh，并在本地控制端补偿 Actor XY
```

## Data Contract

C++ 暴露给 AnimBP / Control Rig 的数据结构是 `FFootLockData`：

- `bEnableLFootLock`: 是否锁左脚。
- `bEnableRFootLock`: 是否锁右脚。
- `FootLockPos`: 被锁脚在开始平滑转身时的世界坐标。
- `IkBeavior`: 传给 Control Rig 的 IK root behavior 参数。
- `ShouldBeOnGround`: 锁点是否必须投到地面。

`CRFL_FootLock` 中对应的成员变量是：

- `EnableLFootLock`
- `EnableRFootLock`
- `FootLockPos`
- `LFootLockLocation`
- `RFootLockLocation`
- `LFootBoneName`
- `RFootBoneName`
- `PelvisBoneName`
- `IsOnGround`
- `FootHeight`
- `IKBehavior`
- `SholudBeOnGround`

注意资产里变量名是 `SholudBeOnGround`，拼写如此；C++ 结构里是 `ShouldBeOnGround`。

## Who Chooses Left Or Right

左右脚不是 Control Rig 自己推断的，而是动画/技能链路决定的。

`UAnimNotify_AttackRotation` 上配置 `ERoatationAxis`：

- `RightFoot`: 右脚作为转向轴，适用于右脚原地不动、左脚向前踏的动画。
- `LeftFoot`: 左脚作为转向轴，适用于左脚原地不动、右脚向前踏的动画。
- `None`: 不启用轴脚锁定。

`USkillSystem::GetRotationSmoothTime` 遍历蒙太奇 Notify，找到名为 `AttackRotation` 的 Notify 后，读取触发时间作为 Mesh 平滑时间，并把 Notify 里的 `RoatationAxis` 带出来。

`UGameSkillUtility::FaceTarget` 会先记录当前 Mesh 旋转，再立刻设置 Actor 到目标朝向，然后调用 `UMeshRotationSmoothCpt::StartMeshSmooth(SourceRotator, SmoothTime, RotationAxis)`。也就是说逻辑朝向先完成，视觉 Mesh 再从旧朝向平滑追过去。

## Lock Point Sampling

`UMeshRotationSmoothCpt::StartMeshSmooth` 做三件关键事：

1. 保存目标旋转，把 Mesh 先设置回旧旋转。
2. 判断转向角度是否超过 `AngleThreshold = 5` 度，小角度不锁脚。
3. 如果 `RoatationAxis` 不是 `None`，从对应脚骨骼 socket 取世界坐标，并向下 `HeightThreshold = 30` 做一次 trace；脚离地太高或 trace 不到地面时不锁。

满足条件时写入：

```text
RoatationAxis == LeftFoot  -> bEnableLFootLock = true
RoatationAxis == RightFoot -> bEnableRFootLock = true
FootLockPos = 当前轴脚 socket 世界坐标
```

这一步的 `FootLockPos` 是锁脚的核心：它是转身开始那一帧的世界空间锚点。后续 Mesh 视觉上继续旋转，但 Control Rig 会不断把被锁的那只脚拉回这个锚点附近。

## Lock Point Math

脚锁的数学可以分成两层：`CRFL_FootLock` 生成“目标点”，`CRFL_FootIKLibrary.ExcuteFootIK` 用 PBIK 把骨骼反解到这个目标点。

锁定开启的第一帧，C++ 采样轴脚世界坐标：

```text
AnchorWS = SkeletalMeshComponent->GetSocketLocation(AxisFootBone)
FootLockPos = AnchorWS
```

后续每一帧，只要 `EnableLFootLock` 或 `EnableRFootLock` 仍为 true，Control Rig 不再跟随动画里那只脚的新位置，而是继续使用这个锚点：

```text
TargetFootWS = FootLockPos
```

如果 `SholudBeOnGround` 为 true，会先做地面修正：

```text
TargetFootWS = FootTrace(FootLockPos, FootHeight)
```

所以锁定阶段的核心不是显式保存上一帧脚位置再计算 `Current - Previous`，而是保存一个世界空间锚点 `AnchorWS`，每帧让 IK 目标保持等于这个锚点。动画、Actor 或 Mesh 旋转导致当前脚骨骼位置发生变化时，差值可以理解为：

```text
DeltaWS = TargetFootWS - AnimatedFootWS
```

这个 `DeltaWS` 没有作为一个独立变量写在图里，但它隐含在 IK 求解里：`AnimatedFootWS` 来自当前帧骨骼姿态，`TargetFootWS` 来自锁点。PBIK 求解器会把脚 effector 拉到 `TargetFootWS`，相当于把当前帧动画脚位置产生的位移逆向补偿回去。

主图里这个过程是：

```text
LFootLockLocation / RFootLockLocation
-> From World / From World_1
-> ExcuteFootIK.FootIkInfo.0.BoneTransform.Translation
```

`From World` 节点把世界空间锁点转到 Rig 所需空间，再作为脚 effector 的目标 Translation 输入。

## Control Rig Main Graph

`CRFL_FootLock` 主图有两条对称分支：

```text
左脚:
EnableLFootLock
  true:
    SholudBeOnGround true  -> FootTrace(FootLockPos, FootHeight) -> LFootLockLocation
    SholudBeOnGround false -> FootLockPos -> LFootLockLocation
  false:
    LerpFootPos(LFootBoneName, LFootLockLocation, IsOnGround) -> LFootLockLocation

右脚:
EnableRFootLock
  true:
    SholudBeOnGround true  -> FootTrace(FootLockPos, FootHeight) -> RFootLockLocation
    SholudBeOnGround false -> FootLockPos -> RFootLockLocation
  false:
    LerpFootPos(RFootBoneName, RFootLockLocation, IsOnGround) -> RFootLockLocation
```

`FootTrace` 的意义是把锁点投到地面：当外部要求 `ShouldBeOnGround` 时，Control Rig 不直接使用 C++ 采样的 `FootLockPos`，而是基于脚高 `FootHeight` 修正出 `GroundPos`，再写入对应的 `LFootLockLocation` 或 `RFootLockLocation`。

`LerpFootPos` 的意义是解锁时平滑释放：当对应 `Enable*FootLock` 关闭后，它不会立刻把锁点清零，而是把锁定位置逐步插值回当前脚位置，避免脚目标突然跳变。

## FootTrace And Foot Height

`FootTrace` 的输入 `FootLoc` 是锁点或插值后的脚目标。函数内部先把 `FootLoc` 转到 Rig 空间，然后从该点向下做 `SphereTraceByTraceChannel`：

```text
TraceStart = FootLoc
TraceEnd   = FootLoc + (0, 0, -90)
Radius     = 5
```

如果 trace 命中地面：

```text
GroundPos = HitLocation + (0, 0, FootHeight)
```

如果没有命中：

```text
GroundPos = FootLoc
```

`FootHeight` 由 `InitFootHeight` 计算。它取脚骨骼自身 Z，再遍历脚骨骼子项找到最低 Z，用两者差值作为脚底高度：

```text
FootHeight = FootBoneZ - MinChildZ
```

因此锁点投地时不是把骨骼目标直接放到地面 hit 点，而是把 hit 点抬高一个脚底偏移，让脚骨骼保持在正确高度，减少穿地。

## Release Interpolation

真正涉及“上一帧锁点和当前帧脚位置差”的地方，是解锁释放阶段的 `LerpFootPos`。

`LerpFootPos` 每次执行都会先取当前脚骨骼位置并转为世界坐标：

```text
AnimatedFootWS = ToWorld(GetTransform(FootBoneName).Translation)
```

然后用传入的旧锁点 `FootLockPos` 向当前动画脚位置插值：

```text
NextLockWS = Lerp(FootLockPos, AnimatedFootWS, 0.5)
```

图里还用 `IsNearlyEqual` 比较 `NextLockWS.XY` 和 `AnimatedFootWS.XY`，容差是 `3`。当插值后的锁点已经接近当前动画脚位置时，结果直接归到当前动画脚位置；否则继续保留插值结果。

如果 `SholudBeOnGround` 为 true，插值结果还会再过一次 `FootTrace`：

```text
NextLockWS = FootTrace(NextLockWS, FootHeight)
```

所以释放阶段的逻辑更接近：

```text
OldTargetWS = LFootLockLocation 或 RFootLockLocation
AnimatedFootWS = 当前帧动画脚世界位置
DeltaWS = AnimatedFootWS - OldTargetWS
NextTargetWS = OldTargetWS + DeltaWS * 0.5
```

这个写法和图中的 `Lerp(OldTargetWS, AnimatedFootWS, 0.5)` 等价。它不是继续把脚钉死，而是让锁点逐帧追向动画脚，直到二者足够接近后完全交还给动画。

## Applying IK

锁点最终通过 `ExcuteFootIK` 应用到骨骼。

左、右两侧都会取当前脚骨骼 transform，并把锁定位置转换到需要的空间：

- 当前脚骨骼名来自 `LFootBoneName` / `RFootBoneName`。
- 骨盆名来自 `PelvisBoneName`。
- 锁定位置来自 `LFootLockLocation` / `RFootLockLocation`。
- `GetIKRootBeavior` 把外部 `IKBehavior` 整数转换成 IK root behavior，传给 `ExcuteFootIK.IKBeavior`。

因此，`CRFL_FootLock` 本身负责决定“目标脚应该去哪里”；实际腿部链条如何弯曲、骨盆如何参与，则交给 `ExcuteFootIK` 函数引用处理。

`ExcuteFootIK` 定义在 `CRFL_FootIKLibrary`。它会遍历传入的 `FootIkInfo` 数组，把每个脚目标转成 `FPBIKEffector`：

```text
FPBIKEffector.Bone      = FootIkInfo.Element.FootBoneName
FPBIKEffector.Transform = FootIkInfo.Element.BoneTransform
```

然后把 effector 数组输入 `RigUnit_PBIK`：

```text
PBIK.Root                  = PelvisBoneName
PBIK.Effectors             = Effectors
PBIK.Settings.RootBehavior = IKBeavior
```

`FPBIKEffector` 默认 `PositionAlpha = 1`、`RotationAlpha = 1`、`StrengthAlpha = 1`，所以目标 Transform 对脚骨骼是满权重约束。PBIK 在当前骨骼姿态基础上求解，使脚骨骼尽量到达锁点目标。换成调试视角，就是每帧根据：

```text
ErrorWS = TargetFootWS - CurrentSolvedOrAnimatedFootWS
```

把腿链和骨盆做反向修正，直到脚 effector 接近目标点。

## Actor Follow Compensation

只锁脚做 IK 还不够。因为 Actor 已经先转到目标朝向，而 Mesh 正在补间，脚锁住后 Mesh 和 Actor 胶囊体可能产生位置偏移。

`CRFL_FootLock` 在对应脚锁定开启时执行 `ActorFollow` / `ActorFollow_1`，把骨盆位置转成世界坐标后传给自定义 Rig Unit `FRigUnit_ActorFollow`。

`FRigUnit_ActorFollow` 会找到角色上的 `UMeshRotationSmoothCpt`，调用 `FollowMesh(NewLocation)`。`UMeshRotationSmoothCpt::UpdateMeshRotation` 下一帧在本地控制角色上把 Actor 的 XY 移到这个 Mesh 位置，高度 Z 保持 Actor 原值。

这一步让锁脚后的视觉 Mesh 和逻辑 Actor 重新贴合，减少胶囊体和骨骼之间的脱节。

## Unlock

平滑时间结束或 Mesh 已经追上目标旋转时，`UMeshRotationSmoothCpt::UpdateMeshRotation` 清理：

```text
bEnableLFootLock = false
bEnableRFootLock = false
FootLockPos = Zero
SourceRotation.Reset()
NewMeshLoc.Reset()
```

Control Rig 下一帧进入 `LerpFootPos` 分支，把 `LFootLockLocation` / `RFootLockLocation` 平滑释放回当前脚位置。

## How To Debug

排查脚锁功能时按这个顺序看：

1. 蒙太奇里是否有 `AttackRotation` Notify，且 `RoatationAxis` 选了正确轴脚。
2. `USkillSystem::GetRotationSmoothTime` 是否读到了该 Notify，并带出了 `RotationAxis`。
3. `StartMeshSmooth` 是否因为角度小于 `AngleThreshold` 或脚下 trace 失败而没有开启 `bEnable*FootLock`。
4. AnimBP 是否把 `FootLockData` 正确传给 `CRFL_FootLock` 的外部变量。
5. `CRFL_FootLock` 中对应侧是否把 `FootLockPos` 或 `FootTrace.GroundPos` 写入了 `LFootLockLocation` / `RFootLockLocation`。
6. `ExcuteFootIK` 是否收到正确脚骨骼名、骨盆名、锁点 translation 和 IK behavior。
7. `ActorFollow` 是否在锁脚期间执行，`FollowMesh` 是否只在本地控制端补偿 Actor XY。

## Verification

本条目基于 UE 5.5.2 commandlet 导出的 `CRFL_FootLock_full.json` 和 C++ 源码确认。导出统计：

- `CRFL_FootLock` 资产类型：`/Script/ControlRigDeveloper.ControlRigBlueprint`
- 主图：74 nodes、81 links、422 recursive pins
- 函数库：`LerpFootPos`、`InitFootHeight`、`FootTrace`、`GetIKRootBeavior`
- 导出错误：0

## Related

- [[Unreal Control Rig 资产解析]]
