---
title: Unreal FBIK 配置与核心原理
tags:
- unreal-engine
- animation
- ik
- fbik
- pbik
sources:
- raw/Unreal/2026-05-14-ue-fbik-pbik-source.md
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/RigUnit_PBIK.h:21
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/RigUnit_PBIK.h:54
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/RigUnit_PBIK.h:155
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/PBIK_Shared.h:11
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/PBIK_Shared.h:19
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/Core/PBIKSolver.h:107
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/Core/PBIKSolver.h:115
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/Core/PBIKSolver.h:153
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKSolver.cpp:192
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKSolver.cpp:252
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKSolver.cpp:327
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKSolver.cpp:384
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKSolver.cpp:479
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKConstraint.cpp:26
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKConstraint.cpp:290
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Private/Core/PBIKBody.cpp:73
- D:/UnrealEngine/Engine/Plugins/Animation/IKRig/Source/IKRig/Public/Rig/Solvers/IKRig_FBIKSolver.h:13
- D:/UnrealEngine/Engine/Plugins/Animation/IKRig/Source/IKRig/Public/Rig/Solvers/IKRig_FBIKSolver.h:185
- D:/UnrealEngine/Engine/Plugins/Animation/IKRig/Source/IKRig/Private/Rig/Solvers/IKRig_PBIKSolver.cpp:59
- D:/UnrealEngine/Engine/Plugins/Experimental/FullBodyIK/Source/FullBodyIK/Private/RigUnit_FullbodyIK.h:109
confidence: confirmed
status: published
created: 2026-05-14
updated: 2026-05-14
---

# Unreal FBIK 配置与核心原理

## Summary

UE 5.5 里日常说的 FBIK，主要是 `FullBodyIK` 插件中 `PBIK` 模块提供的 Position Based IK Solver。Control Rig 节点是 `FRigUnit_PBIK`，显示名为 `Full Body IK`；IK Rig 面板里的 FBIK Solver 是 `UIKRigFBIKSolver`，内部同样调用 `FPBIKSolver`。

源码里还有一个旧的 `FRigUnit_FullbodyIK`，它位于 `Source/FullBodyIK` 模块，核心是 Jacobian solver，并且 USTRUCT 上已经标记 `Deprecated = "5.0"`。除非在维护旧 Control Rig 图，否则理解 UE5 FBIK 应优先看 PBIK 这条线。

本地源码目录 `D:/UnrealEngine` 当前为 `nd-master`，`5.5.2-release-199-gdc0fe411c845`。本轮检查的 `FullBodyIK/PBIK` 与 `IKRig_PBIKSolver` 相关文件相对 `5.5.2-release` 没有 diff，可按 UE 5.5.2 官方基线理解。

## Source Map

- Control Rig PBIK 节点：`FRigUnit_PBIK`，配置包括 `Root`、`Effectors`、`BoneSettings`、`ExcludedBones`、`Settings`、`Debug`。
- IK Rig FBIK Solver：`UIKRigFBIKSolver`，把 IK Rig Goal 转成 PBIK effector，再把求解结果写回 `CurrentPoseGlobal`。
- PBIK 核心求解器：`FPBIKSolver`，负责初始化骨骼、刚体、约束，并执行 position-based 迭代。
- 约束实现：`FPinConstraint` 负责把 effector 连接到目标点，`FJointConstraint` 负责保持父子 body 的关节关系和角度限制。
- 旧版 FullbodyIK：`FRigUnit_FullbodyIK`，已废弃，使用 Jacobian solver。

## Core Mental Model

PBIK 不是单链 CCD/FABRIK，也不是一次矩阵求逆直接给出完美姿势。它更像一个简化物理约束求解器：

1. 从输入动画姿势开始。
2. 把 root 到各个 effector 之间的骨骼路径抽象成一组 `FRigidBody`。
3. 给 effector 建 pin 约束，让脚、手、头等目标骨骼尽量贴近目标 transform。
4. 给相邻 body 建 joint 约束，让骨骼层级仍然连在一起，并按 bone setting 处理 stiffness 和旋转限制。
5. 每轮迭代都做一小步修正，多迭代几次后，所有约束逐渐达成一个折中结果。

通俗讲，FBIK 要解的是“多个人同时拉一个骨架”的问题。手目标、脚目标、骨盆/root、关节角度限制都在抢影响力。PBIK 不先假设哪个单链独占身体，而是把身体当作一个整体系统，让每个约束反复小幅纠偏，最后得到一个全身姿势。

## Control Rig Node Config

`FRigUnit_PBIK` 是 Control Rig 侧节点，显示名是 `Full Body IK`。

### Root

`Root` 是参与 FBIK 求解的最高骨骼。Root 以上的骨骼完全忽略；Root 到各个 effector 之间的骨骼会纳入求解。

常见人形角色会设为 `pelvis`、`hips` 或身体主干的第一个蒙皮骨，而不是一定设为 Skeleton 的全局 `root`。如果只想解上半身或单条局部链，就把 Root 放到局部链的起点，并配合 `RootBehavior = PinToInput` 防止整条链被拖走。

### Effectors

`Effectors` 是目标数组，每个 effector 指定一个骨骼和一个目标 transform。

- `Bone`：被目标拉动的骨骼，例如 foot、hand、head。
- `Transform`：目标位置和旋转。PBIK 会尽量让 `Bone` 到达这个 transform。
- `PositionAlpha`：目标位置权重，0 表示保持输入姿势的位置，1 表示使用 effector 目标位置。
- `RotationAlpha`：目标旋转权重，0 表示保持输入姿势旋转，1 表示使用 effector 目标旋转。
- `StrengthAlpha`：effector 拉骨架的强度。0 时不主动拉向目标，但从 effector 到 root 的骨骼仍会轻微抵抗其他 effector 的影响，可当作稳定器。
- `ChainDepth`：显式指定这个 effector 往父级追溯多少根骨骼算作它的“链”。为 0 时，求解器自动向上找，直到遇到分叉点或另一个 effector。
- `PullChainAlpha`：先把这条链整体预旋转、预平移到目标方向的强度。它能让长链或骨骼很密的链更快收敛，但在机械臂这种强限制链上可能导致不自然结果。
- `PinRotation`：最终把 effector 骨骼旋转贴到目标旋转的程度。1 表示尽量使用目标旋转，0 表示保持由父骨骼 FK 推出来的旋转。

IK Rig 的 `UIKRig_FBIKEffector` 没有直接暴露 `Transform`、`PositionAlpha`、`RotationAlpha`。IK Rig 通过 `GoalName` 找到 Goal，把 `Goal->FinalBlendedPosition` 和 `Goal->FinalBlendedRotation` 传给 PBIK，并把 `PositionAlpha`、`RotationAlpha` 固定为 1，因为 Goal 的 blend 已经在 IK Rig 层处理过了。

### BoneSettings

`BoneSettings` 是逐骨骼配置，用来控制哪些骨骼更愿意动、怎么限制旋转、弯曲时优先往哪个方向弯。

- `Bone`：配置应用到哪根骨骼。
- `RotationStiffness`：旋转刚度，0 最自由，1 最抗拒旋转。值越高，这根骨骼越不愿意转，其他骨骼需要承担更多修正。
- `PositionStiffness`：位置刚度，0 最自由，1 最抗拒平移。PBIK 内部 body 会有位置修正，这个值会降低该 body 的平移响应。
- `X/Y/Z`：每个轴的旋转限制模式，取值为 `Free`、`Limited`、`Locked`。
- `MinX/MaxX`、`MinY/MaxY`、`MinZ/MaxZ`：当对应轴是 `Limited` 时，允许的角度范围。角度相对 Skeletal Mesh reference pose。
- `bUsePreferredAngles`：启用偏好角。当链被压缩时，骨骼会优先往 `PreferredAngles` 指定的方向弯。
- `PreferredAngles`：局部欧拉角，单位是度。常用来让膝盖、手肘往正确方向弯。

调角色时，`PreferredAngles` 通常应该先于硬限制尝试。硬限制能防止越界，但更容易让求解需要更多迭代；PreferredAngles 更像“膝盖请往前弯”的提示，尤其适合修正腿/手臂反向弯的问题。

### ExcludedBones

`ExcludedBones` 表示这些骨骼不参与求解、不弯曲、也不贡献约束。源码注释明确建议：如果你想排除一根骨骼，优先用 `ExcludedBones`，而不是把 `RotationStiffness` 调得极高或把旋转限制设成零范围。

这适合排除武器挂点、装饰骨、某些不希望被 IK 影响的小骨骼。

### Settings

`Settings` 是全局求解器配置，对所有 effectors 和 bone settings 生效。

- `Iterations`：主约束迭代次数。复杂约束、多个目标互相竞争、骨骼限制较多时，提高它能更接近目标，但会增加运行成本。
- `SubIterations`：子链迭代次数。子链由 effector 的 `ChainDepth` 定义，会在主迭代前先解。用于让手臂、腿等局部链先收敛，再进入全身折中。
- `MassMultiplier`：全局质量倍率。质量越大，body 越“重”，关节越硬，更不容易被约束推动，但可能需要更多迭代。
- `bAllowStretch`：是否允许关节平移以到达 effector。开启会产生骨骼拉长效果，适合卡通或夸张动画；默认关闭时，迭代后会做 `RemoveStretch`，尽量保持骨骼长度。
- `RootBehavior`：Root 的行为，见下一节。
- `PrePullRootSettings`：只有 `RootBehavior = PrePull` 时生效，用于控制全身整体预移动/预旋转。
- `GlobalPullChainAlpha`：所有 effector `PullChainAlpha` 的全局倍率。IK Rig UI 中名字是 `PullChainAlpha`。
- `MaxAngle`：单次约束迭代中 body 最多能旋转多少度。求解发散或抖动时可以降低；太低会收敛慢。
- `OverRelaxation`：过松弛系数。大于 1 时每次修正多推一点，加快收敛，但过高会降低稳定性。
- `bStartSolveFromInputPose_DEPRECATED`：废弃字段。当前源码每 tick 都会从输入姿势更新 bones/bodies。

### RootBehavior

`RootBehavior` 决定 solver root 在全身 IK 中怎么动。

- `PrePull`：默认模式。根据所有 effector 从原始位置到目标位置的整体变化，先对全身做一次大尺度平移/旋转，再进入约束迭代。适合全身一起被目标牵引，例如双脚/双手共同影响骨盆。
- `PinToInput`：把 root 锁在输入姿势。源码里通过把 root body 的 `InvMass` 设为 0 实现。适合局部 IK 或不希望骨盆/root 跟着脚手目标跑的情况。
- `Free`：root 像普通 body 一样参与约束，可按 root 自己的 bone setting 自由移动或受限移动。

`PrePullRootSettings` 细分为位置和旋转两组 alpha：

- `PositionAlpha`：整体位置预拉的总权重。
- `PositionAlphaX/Y/Z`：组件空间 X/Y/Z 方向分别给多少预拉。
- `RotationAlpha`：整体旋转预拉的总权重。
- `RotationAlphaX/Y/Z`：组件空间 X/Y/Z 轴旋转分别给多少预拉。

直觉上，PrePull 是“先把整个人大概挪到目标附近，再精修关节”。如果目标很远，只靠迭代一点点拉会慢；PrePull 可以给求解器一个更接近答案的初始姿势。

### Debug

`FPBIKDebug` 主要有：

- `DrawScale`：调试绘制比例。
- `bDrawDebug`：是否开启节点调试绘制。

它会通过 solver 的 debug draw 画出 body 等辅助线，适合观察 PBIK 内部实际在解哪些 body，而不是只看最终骨骼结果。

## IK Rig FBIK Config

IK Rig 里的 `UIKRigFBIKSolver` 是 PBIK 的包装层。

- `RootBone` 对应 Control Rig PBIK 的 `Root`。
- `Iterations`、`SubIterations`、`MassMultiplier`、`bAllowStretch`、`RootBehavior`、`PrePullRootSettings`、`PullChainAlpha`、`MaxAngle`、`OverRelaxation` 会被拷贝到 `FPBIKSolverSettings`。
- `Effectors` 绑定 IK Rig Goals。每个 effector 有 `GoalName`、`BoneName`、`ChainDepth`、`StrengthAlpha`、`PullChainAlpha`、`PinRotation`。
- `BoneSettings` 和 PBIK 的 `FPBIKBoneSetting` 基本一致。

运行时流程是：

1. 把 `IKRigSkeleton.CurrentPoseGlobal` 写入 `FPBIKSolver`。
2. 把 IK Rig bone settings 拷贝到 PBIK 内部 bone settings。
3. 根据 `GoalName` 查找 Goal，把 final blended goal transform 写成 effector goal。
4. 调 `Solver.Solve(Settings)`。
5. 再把 solver 输出的 global transform 写回 `CurrentPoseGlobal`。

所以 IK Rig 的 FBIK 并没有另一套求解算法，它只是把 IK Rig 的 Goal 系统接到 PBIK 上。

## Solve Flow

### 初始化

`FPBIKSolver::Initialize` 只在 solver 未 ready 时执行，内部依次初始化 bones、bodies、constraints。

`InitBones` 做几件事：

1. 找到唯一的 solver root。
2. 建好每根骨骼的 parent 指针。
3. 从每个 effector 往上走到 root，把路径上的骨骼标为 `bIsSolved`。
4. 统计 solved children，分叉点或 root 会标成 `bIsSubRoot`。
5. 记录初始局部旋转，PreferredAngles 和限制都要以这个初始姿势作为参考。

这意味着：只有 root 到 effector 路径上的骨骼真正参与求解；旁支骨骼如果不在路径上，最后只是跟随父骨骼做 FK 传播。

`InitBodies` 会在 effector 到 root 的路径上创建 `FRigidBody`。body 不是简单等于骨骼 pivot，它的 `Position` 是骨骼和孩子位置的质心，`Mass` 来自到孩子的距离。这样 solver 解的是一组带尺寸感的刚体，而不是孤立点。

`InitConstraints` 创建两类约束：

- `FPinConstraint`：每个 effector 一个，把 body 上的 pin point 拉向目标。
- `FJointConstraint`：相邻 body 一个，保持父子 body 在关节点处连接，并负责 joint limit。

### 每帧求解

`FPBIKSolver::Solve` 每帧从输入动画姿势重新更新：

1. `Bone.UpdateFromInputs()`：更新局部位置、局部旋转、长度等输入姿势数据。
2. `Body.UpdateFromInputs(Settings)`：用当前骨骼姿势更新 body transform 和 mass，并根据 `MassMultiplier` 计算 `InvMass`。
3. `Constraint.UpdateFromInputs()`：更新约束的局部 pin 位置。
4. 如果 `RootBehavior = PinToInput`，把 root body 的 `InvMass` 设为 0，让它不可被推动。
5. 更新 effector chain depth 和 sub-chain 状态。
6. `Effector.UpdateFromInputs()`：把输入姿势和目标 transform 按 alpha 混合，得到 pin goal。
7. `UpdateBodies(Settings)`：执行预处理和约束迭代。
8. `UpdateBonesFromBodies()`：把 body 求解结果写回骨骼，effector 可按 `PinRotation` 覆盖旋转，未求解骨骼按 FK 从父骨骼传播。

### PrePull

`ApplyRootPrePull` 只在 `RootBehavior = PrePull` 时运行。

它会收集所有 effector 的原始位置和目标位置，计算一个 best-fit 的整体旋转和中心点位移，再按 `PrePullRootSettings` 混合后，整体移动/旋转所有 bodies。

这一步不直接解关节细节，只负责把整个人先摆到更接近目标的位置。比如左右脚目标都整体往前移动，PrePull 会先让骨盆和全身大致前移，然后关节迭代再精修腿部。

### PreferredAngles

`ApplyPreferredAngles` 会遍历 effector 链。只有当当前 effector 到 chain root 的距离小于输入姿势距离，也就是链被压缩时，才会按 squash 百分比应用 PreferredAngles。

这就是为什么 PreferredAngles 常用来处理膝盖和手肘：当脚或手往身体靠近时，链条必须弯曲，PreferredAngles 告诉 solver “优先往这个方向弯”。它不是硬性角度限制，而是弯曲方向提示。

应用 PreferredAngles 可能引入一些长度偏移，所以源码紧接着会对所有 constraints 做一次完整 `RemoveStretch`，避免把第一轮约束迭代带偏。

### PullChainAlpha

`ApplyPullChainAlpha` 是 effector 链的预处理。它会比较链在输入姿势中的方向和当前目标方向，得到一个 `ChainDeltaRotation` 和沿链方向的平移量，然后把链上的 bodies 整体预旋转、预平移。

最终强度是：

```text
Effector.PullChainAlpha * Effector.StrengthAlpha * GlobalPullChainAlpha
```

这适合长链、稀疏链或骨骼很多的链。它的直觉是“先把整条手臂/腿朝目标方向摆过去”，然后再靠约束迭代修细节。对强限制机械链要谨慎，因为整体预拉可能和关节限制冲突。

### Constraint Iterations

`SolveConstraints` 有两个阶段：

1. 如果存在 sub-chain 且 `SubIterations > 0`，先锁住不属于 sub-chain 的 bodies，只解子链。
2. 再跑全局主迭代 `Iterations` 次。

每一次 constraint pass 都会：

1. 依次调用所有 constraint 的 `Solve`。
2. 如果 `bAllowStretch = false`，从末尾反向调用 `RemoveStretch`，并在前半段迭代中把去拉伸强度从小到大 ramp 到 1。

`FPinConstraint::Solve` 做的是：算出 body 上 pin point 到目标点的误差，用这个误差先推 body 旋转，再直接修 body 位置。Pin 约束不走 `PositionStiffness`，因为它要能有效把 effector 拉向目标。

`FJointConstraint::Solve` 做的是：算出父子 body 在关节点处的错位，用错位先转动两个 body，然后执行 joint limit，最后再按双方 `InvMass` 分配位置修正，让关节点重新对齐。

## Why Stiffness Works

`FRigidBody::ApplyPositionDelta` 中，位置修正会乘：

```text
1 - PositionStiffness
```

所以 `PositionStiffness = 0` 时完整吃下位置修正，`PositionStiffness = 1` 时几乎不吃位置修正。

旋转也是类似逻辑。`ApplyPushToRotateBody` 和 `FJointConstraint::ApplyRotationCorrection` 都会按：

```text
1 - RotationStiffness
```

降低旋转响应。

因此 stiffness 不是“这根骨骼完全不会动”的开关，而是“这根骨骼对约束修正的响应程度”。当一根骨骼 stiff，约束误差会更多转移给其他更自由的骨骼。

## Why MaxAngle And OverRelaxation Matter

PBIK 是迭代求解。每次迭代都做一小步，如果步子太小，收敛慢；步子太大，可能发散或抖动。

- `OverRelaxation` 把位置修正放大，让误差更快减少。默认 1.3 是“多推一点”。调高可能更快，但稳定性下降。
- `MaxAngle` 限制单次迭代旋转增量。目标很远、约束冲突、骨骼限制复杂时，过大的旋转增量可能让 body 翻得太猛；降低 `MaxAngle` 可以更稳，但要更多迭代。

常见调参顺序是：先保证 Root、effector、PreferredAngles 正确；再增加 `Iterations`；仍有发散/抖动时降低 `MaxAngle` 或 `OverRelaxation`；最后再考虑硬限制和 stiffness。

## Old Deprecated Jacobian FBIK

旧 `FRigUnit_FullbodyIK` 的显示名是 `Fullbody IK`，源码注释写着 “Based on Jacobian solver”，并在 USTRUCT meta 中标记 `Deprecated = "5.0"`。

它的主要配置是：

- `Root`：链的起点。
- `Effectors`：`FFBIKEndEffector` 数组。
- `Constraints`：`FFBIKConstraintOption` 数组。
- `SolverProperty`：`FSolverInput`。
- `MotionProperty`：`FMotionProcessInput`。
- `bPropagateToChildren`：求解后是否重算子骨骼全局 transform。
- `DebugOption`：旧求解器调试绘制。

旧 effector 包括：

- `Item`：目标骨骼。
- `Position`、`PositionAlpha`、`PositionDepth`：位置目标、位置权重和向父级影响的深度。
- `Rotation`、`RotationAlpha`、`RotationDepth`：旋转目标、旋转权重和向父级影响的深度。
- `Pull`：每次迭代中按比例 clamp 目标长度，用来稳定过远目标。

旧 constraint 包括：

- `bEnabled`：是否启用。
- `bUseStiffness`：是否使用 stiffness。
- `LinearStiffness`：局部轴向线性刚度。
- `AngularStiffness`：角刚度，xyz 对应 twist、swing1、swing2。
- `bUseAngularLimit`、`AngularLimit`：是否启用角度限制和限制值。
- `bUsePoleVector`、`PoleVectorOption`、`PoleVector`：是否使用 pole vector 以及它是局部方向还是全局位置。
- `OffsetRotation`：构造局部 frame 时额外应用的旋转偏移。

旧 solver 输入包括：

- `LinearMotionStrength`、`MinLinearMotionStrength`：位置目标影响关节运动的强度范围。
- `AngularMotionStrength`、`MinAngularMotionStrength`：旋转目标影响关节运动的强度范围。
- `DefaultTargetClamp`：稳定目标向量的 clamp 比例，越小越稳但收敛更慢。
- `Precision`：求解精度。
- `Damping`：Jacobian damping。
- `MaxIterations`：最大迭代次数。
- `bUseJacobianTranspose`：是否使用更便宜的 Jacobian Transpose，否则使用默认的 damped least square 变体。

旧 MotionProperty 包括：

- `bForceEffectorRotationTarget`：是否强制应用 effector 旋转目标。
- `bOnlyApplyWhenReachedToTarget`：是否只有到达位置目标后才应用旋转。

维护旧图时这些字段仍有价值；新图或 IK Rig 配置应优先看 PBIK/FBIK 这套属性。

## Practical Config Notes

- 脚 IK、手 IK、全身接触这类玩法，通常从 `Root = pelvis/hips`、`RootBehavior = PrePull`、脚/手作为 effectors 开始。
- 上半身瞄准或单链局部 IK，通常用局部 root，并考虑 `PinToInput`，避免 root 被目标拖动。
- 膝盖/手肘弯错方向，先调 `PreferredAngles`，再考虑硬限制。
- 目标够不到但又不想骨骼拉长，保持 `bAllowStretch = false`；卡通风格或夸张动作才开启 stretch。
- 多目标冲突或限制多时，优先增加 `Iterations`；局部链需要先稳定时再加 `SubIterations`。
- 链很长、收敛慢时提高 `PullChainAlpha`；机械臂、强限制链、刚性结构上谨慎使用。
- 想完全排除某骨骼，用 `ExcludedBones`，不要用极端 stiffness 或零角度限制硬顶。

## Verification

- `D:/UnrealEngine` 当前版本：`5.5.2-release-199-gdc0fe411c845`。
- 本轮检查的 FBIK/PBIK 文件相对 `5.5.2-release` 没有 diff。
- 关键源码入口：`RigUnit_PBIK.h`、`PBIK_Shared.h`、`PBIKSolver.h/.cpp`、`PBIKConstraint.cpp`、`PBIKBody.cpp`、`IKRig_FBIKSolver.h`、`IKRig_PBIKSolver.cpp`。
