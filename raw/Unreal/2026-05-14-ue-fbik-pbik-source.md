# 2026-05-14 UE FBIK / PBIK Source

Status: raw
Confidence: confirmed
Task: 看 UE5 FBIK 源码，整理配置属性和核心原理
Sources:
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

Observation:
UE 5.5 的常用 Full Body IK 主要是 `PBIK` 模块里的 position-based solver，并由 IK Rig 的 `UIKRigFBIKSolver` 包装为 FBIK Solver；Control Rig 侧入口是 `FRigUnit_PBIK`，显示名也是 Full Body IK。源码里还有 `FullBodyIK` 模块的 `FRigUnit_FullbodyIK`，但它标记为 UE 5.0 deprecated，核心是 Jacobian solver，不应和当前 PBIK 版本混为一谈。

Verification:
- `git -C D:/UnrealEngine branch --show-current` 为 `nd-master`。
- `git -C D:/UnrealEngine describe --tags --always --dirty` 为 `5.5.2-release-199-gdc0fe411c845`。
- `git -C D:/UnrealEngine diff --name-status 5.5.2-release -- Engine/Plugins/Experimental/FullBodyIK Engine/Plugins/Animation/IKRig/Source/IKRig/Public/Rig/Solvers/IKRig_FBIKSolver.h Engine/Plugins/Animation/IKRig/Source/IKRig/Private/Rig/Solvers/IKRig_PBIKSolver.cpp` 无输出，说明本轮涉及的 FBIK/PBIK 文件相对 UE 5.5.2-release 没有本地 diff。

Boundary:
结论覆盖 UE 5.5.2 基线的 PBIK / IK Rig FBIK / deprecated Jacobian FullbodyIK 源码。运行时资产中的具体骨骼配置、目标权重和 Control Rig 图逻辑仍需回到项目资产验证。
