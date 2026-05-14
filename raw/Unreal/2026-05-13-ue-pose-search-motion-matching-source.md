# 2026-05-13 UE PoseSearch Motion Matching Source

Status: raw
Confidence: confirmed
Task: 读取 D:/UnrealEngine 中 UE5 PoseSearch / Motion Matching 源码，沉淀 Motion Matching 核心原理
Sources:
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/AnimNode_MotionMatching.h:104
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchLibrary.h:25
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchLibrary.h:46
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchLibrary.h:183
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/AnimNode_MotionMatching.cpp:34
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/AnimNode_MotionMatching.cpp:91
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchLibrary.cpp:235
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchLibrary.cpp:284
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchLibrary.cpp:488
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchLibrary.cpp:845
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:173
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:1041
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:1103
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:1241
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchDatabase.cpp:1336
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchIndex.cpp:516
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchIndex.cpp:710
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchSchema.cpp:26
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchSchema.cpp:71
- D:/UnrealEngine/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Private/PoseSearchSchema.cpp:246
- command: git -C D:/UnrealEngine diff --stat 5.5.2-release -- Engine/Plugins/Animation/PoseSearch

Observation:
UE Motion Matching 在 PoseSearch 插件中实现，本质是运行时构建 query feature vector，然后在已索引的动画数据库 pose feature vector 中找代价最低的候选。Schema 决定采样率、骨骼/角色和 feature channels；Database 离线或异步构建 SearchIndex；运行时 `FAnimNode_MotionMatching::UpdateAssetPlayer` 调用 `UPoseSearchLibrary::UpdateMotionMatchingState`，先评估 continuing pose，再按数据库搜索新 pose，若新候选代价更低则跳转并通过 BlendStack 或 inertial blend 过渡。

Verification:
相对 `5.5.2-release`，`Engine/Plugins/Animation/PoseSearch` 未显示 diff 统计输出，本地 PoseSearch/Motion Matching 源码可作为 UE 5.5.2 基线逻辑阅读。核心证据来自 `AnimNode_MotionMatching.cpp`、`PoseSearchLibrary.cpp`、`PoseSearchDatabase.cpp`、`PoseSearchIndex.cpp` 和 `PoseSearchSchema.cpp` 的函数实现。

Boundary:
本观察解释的是 PoseSearch 插件源码的核心算法骨架，不覆盖编辑器 UI、调试器面板、资产制作规范、多人 Interaction Motion Matching 全流程，也不保证 UE 5.6/5.7 后续版本没有调整。
