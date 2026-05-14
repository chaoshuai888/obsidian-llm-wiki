---
confidence: confirmed
created: 2026-05-13
sources:
- raw/Unreal/2026-05-13-ue-pose-search-motion-matching-source.md
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/AnimNode_MotionMatching.h:104
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchLibrary.h:25
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchLibrary.h:46
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchLibrary.h:183
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/AnimNode_MotionMatching.cpp:34
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/AnimNode_MotionMatching.cpp:91
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchLibrary.cpp:235
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchLibrary.cpp:488
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:173
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:1041
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:1241
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:1336
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchIndex.cpp:516
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchIndex.cpp:710
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchSchema.cpp:26
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchSchema.cpp:71
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchSchema.cpp:246
status: published
tags:
- unreal-engine
- motion-matching
- pose-search
- animation
- source-code
title: Unreal Motion Matching 核心原理
updated: '2026-05-13'
---

# Unreal Motion Matching 核心原理

## 结论

UE 的 Motion Matching 由 PoseSearch 插件实现，核心不是神经网络推理，而是“特征向量检索”。离线或异步构建阶段，数据库把动画资产按 Schema 采样成 pose feature vectors；运行时根据当前姿态历史和未来意图构建 query feature vector；搜索阶段在数据库里找总代价最低的 pose；动画节点再跳到该资产和时间点，并通过 BlendStack 或 inertial blend 过渡。

一句话概括：

```text
Schema 定义要比较什么
Database 把动画采样成可搜索向量
Query 描述当前和未来想要什么
Search 计算哪个 pose 最像 query
Blend 把当前播放平滑切到选中的 pose
```

本机 `D:/UnrealEngine` 相对 `5.5.2-release`，`Engine/Plugins/Animation/PoseSearch` 未显示 diff 统计输出，因此本条目可作为 UE 5.5.2 PoseSearch 基线逻辑阅读。

## Schema

`UPoseSearchSchema` 定义搜索空间。它负责采样率、角色/骨架、feature channels、数据预处理和最终向量维度。

默认 Schema 会添加两个适合 locomotion 的 channel：

- `UPoseSearchFeatureChannel_Trajectory`
- `UPoseSearchFeatureChannel_Pose`

`BuildQuery` 的实现很直接：先让 `FSearchContext` 创建 feature vector builder，然后遍历 `GetChannels()`，逐个调用 channel 的 `BuildQuery`。也就是说，Motion Matching 的 query 不是一个固定结构，而是由 Schema 中的 channel 组合出来的。

`Finalize` 会做这些事：

- 检查角色和 skeleton 配置。
- 确保每个角色有 root bone 引用。
- Finalize 每个 channel。
- 让 channel 注入 dependent channels。
- 如果使用 permutation time，自动补 `PermutationTime` channel。
- 必要时补 padding，让数据适合 16 bytes 对齐计算。

## Database 和 SearchIndex

`UPoseSearchDatabase` 持有可搜索动画资产和搜索模式。构建索引时，每个动画片段按 Schema sample rate 采样，写入 `FSearchIndex`。

`FSearchIndex` 保存的核心数据包括：

- pose feature values。
- pose metadata，包括 cost addend、asset index、block transition 等。
- 权重平方根 `WeightsSqrt`。
- PCA 数据和投影矩阵。
- KDTree 或 VPTree 加速结构。

代价计算在 `FSearchIndex::ComparePoses` 和 `CompareAlignedPoses` 中完成。总代价由三部分组成：

```text
TotalCost = DissimilarityCost + NotifyCostAddend + ContinuingPoseCostAddend
```

`DissimilarityCost` 是 pose vector 和 query vector 的加权差异；`NotifyCostAddend` 来自动画 notify 或 schema base cost bias；`ContinuingPoseCostAddend` 用来给继续播放当前 pose 加偏置。

## AnimNode 运行链路

`FAnimNode_MotionMatching::Initialize_AnyThread` 会初始化 BlendStack，并调用 `MotionMatchingState.Reset`。Reset 会清空当前搜索结果，并把 `ElapsedPoseSearchTime` 设为 infinity，保证第一次更新立刻搜索。

`UpdateAssetPlayer` 是主入口：

1. 执行暴露输入。
2. 节点重新变 relevant 或数据库索引失效时 reset。
3. 否则用当前 asset player 的 accumulated time 修正 `MotionMatchingState`。
4. 准备 `DatabasesToSearch`。
5. 调用 `UPoseSearchLibrary::UpdateMotionMatchingState`。
6. 如果 `MotionMatchingState.bJumpedToPose` 为 true，取搜索结果里的 animation asset、asset time、loop、mirror 和 blend parameters，调用 `BlendTo`。
7. 更新 play rate 和 blendspace parameters。
8. tick BlendStack。

`Evaluate_AnyThread` 主要负责评估 BlendStack 输出。源码里还保留了旧的 `ComponentDeltaYaw` 相关逻辑，用于调整 root bone/root motion yaw，但这些字段在 5.4 起已标记 deprecated，源码建议改用 Steering、OrientationWarping、OffsetRootBone 等节点。

## MotionMatchingState

`FMotionMatchingState` 是运行时状态盒子：

- `CurrentSearchResult`：当前数据库、pose index、asset time 和 cost。
- `ElapsedPoseSearchTime`：上次跳 pose 后经过的时间。
- `WantedPlayRate`：为了匹配 query 速度而希望使用的播放速率。
- `bJumpedToPose`：本帧是否选中了新 pose。
- `PoseIndicesHistory`：近期选中过的 pose，用于避免反复选回同一批 pose。

`JumpToPose` 只是把 `CurrentSearchResult` 换成新结果，并标记 `bJumpedToPose = true`。实际动画切换由 AnimNode 后续 `BlendTo` 完成。

`UpdateWantedPlayRate` 会从当前结果对应的 `Trajectory` channel 中估计 query 与候选动画的速度比例，然后 clamp 到节点配置的 `PlayRate` 区间。如果没有可用 trajectory channel，就不能用该方式自动匹配速度。

## 搜索决策

`UPoseSearchLibrary::UpdateMotionMatchingState` 是核心决策函数。它先从动画上下文拿 `IPoseHistory`，构造 `FSearchContext`，再判断当前结果是否还能继续推进：

```text
bCanAdvance = CurrentSearchResult.CanAdvance(DeltaTime)
bSearch = !bCanAdvance || (bShouldSearch && ElapsedPoseSearchTime >= SearchThrottleTime)
```

如果不需要搜索，只累加 `ElapsedPoseSearchTime`。如果需要搜索：

1. 根据 `EPoseSearchInterruptMode` 判断是否强制打断 continuing pose，或者让 continuing pose 失效。
2. 如果没有强制打断且当前 pose 可推进，先调用 `CurrentResultDatabase->SearchContinuingPose`。
3. 遍历 `Databases`，逐个调用 `Database->Search(SearchContext)`。
4. 如果新搜索结果 cost 小于 continuing pose cost，就 `JumpToPose`。
5. 如果没有更好结果，只把 cost 回写到当前结果，方便调试。
6. 更新 `WantedPlayRate` 和 `PoseIndicesHistory`。

这解释了 Motion Matching 为什么不会每帧盲目切片段：continuing pose 也参与比较；只有新候选比继续播放更便宜时才跳。`SearchThrottleTime`、`PoseJumpThresholdTime`、`PoseReselectHistory` 和 `ContinuingPoseCostBias` 都是在控制“什么时候值得跳”。

## Database 搜索模式

`UPoseSearchDatabase::Search` 根据 `PoseSearchMode` 选择搜索路径：

- `BruteForce`：遍历候选 pose，直接算精确 cost。
- `VPTree`：用 VP tree 做近邻加速。
- `PCAKDTree`：先把 query 投影到 PCA 空间，用 KDTree 找近邻，再对候选做精确 cost 计算。

`PCAKDTree` 的路径是：

1. `SearchContext.GetOrBuildQuery(Schema)` 构建 query。
2. 准备 selectable asset 过滤、non-selectable pose 过滤和 block transition 过滤。
3. `FSearchIndex::PCAProject` 把 query 投影到 PCA 空间。
4. `KDTree.FindNeighbors` 找近邻。
5. 对 KDTree 返回的候选调用 `EvaluatePoseKernel`。
6. `EvaluatePoseKernel` 先跑过滤器，再调用 `ComparePoses` 或 `CompareAlignedPoses`，保留 cost 最低的 pose。

如果 PCA values 被裁剪成多个 pose 共享同一个 PCA vector，搜索会展开这些 pose 再逐个精算。若数据库只保留 PCA 数据、未保留原始 values，则会先 `GetReconstructedPoseValues` 再比较。

## Continuing Pose 和过滤

`SearchContinuingPose` 用当前 `CurrentSearchResult.PoseIdx` 计算继续播放当前动画的 cost。它还会在当前采样时间检查 `UAnimNotifyState_PoseSearchOverrideContinuingPoseCostBias`，允许动画片段局部改写 continuing pose bias。

`PopulateNonSelectableIdx` 会把一些 pose 排除掉：

- 当前 asset 设置了 disable reselection 时，排除同源 asset 的 pose。
- `PoseJumpThresholdTime` 排除当前片段附近时间窗口内的 pose。
- `PoseIndicesHistory` 排除近期选过的 pose。
- block transition 由过滤器根据 pose metadata 排除。

这些过滤不是为了找到数学上最近的 pose，而是为了避免视觉上来回跳、选到禁止转场区间、或在同一动画附近抖动。

## 调参抓手

Motion Matching 最重要的调参点在几层：

- Schema：channels、weights、sample rate、是否加入 trajectory、pose、phase、velocity、curve 等信息。
- Database：资产范围、mirroring、looping、sampling range、search mode、PCA/KDTree 参数。
- Runtime：`BlendTime`、`bUseInertialBlend`、`MaxActiveBlends`、`PlayRate`。
- 切换控制：`SearchThrottleTime`、`PoseJumpThresholdTime`、`PoseReselectHistory`、`ContinuingPoseCostBias`、interrupt mode。
- Query 来源：PoseHistory、future animation、轨迹预测和角色意图。

实际问题通常不是“Motion Matching 有没有搜到最近 pose”，而是 query 是否表达了正确意图、channel 权重是否合理、数据库是否覆盖目标动作，以及 continuing pose 的 bias 和过滤是否让系统过度保守或过度跳转。

## 下次如何使用

解释 UE Motion Matching 时，优先用“Schema 组 query，Database 存 pose vectors，Search 选最低 cost，State 控制是否跳，BlendStack 执行过渡”这条线。需要定位问题时，先看 `UpdateMotionMatchingState` 的 `bSearch/bCanAdvance/bJumpToPose`，再看 `SearchContext` 构建出的 query、Database 的 search mode、`ComparePoses` 的 cost 组成和过滤器排除了哪些 pose。

如果问题来自网络模拟代理的位置平滑或 capsule/mesh 不一致，先看 [[Unreal 模拟端移动插值]]，不要把动画选姿问题和网络移动插值问题混在一起。
