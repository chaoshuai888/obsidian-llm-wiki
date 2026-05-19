# 2026-05-14 Unreal Control Rig FootLock

Status: raw
Confidence: confirmed
Task: 介绍 CRFL_FootLock 如何配合 UMeshRotationSmoothCpt 将左右脚锁定到原地，并沉淀到 wiki。
Sources:
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

Observation:
CRFL_FootLock 不是自己决定锁哪只脚，而是消费 UMeshRotationSmoothCpt 写入 AnimInstance 的 FootLockData。技能蒙太奇中的 AttackRotation Notify 提供 ERoatationAxis，UMeshRotationSmoothCpt 在平滑 Mesh 旋转前采样轴脚世界坐标 FootLockPos，并设置 bEnableLFootLock 或 bEnableRFootLock。Control Rig 主图分别用 EnableLFootLock / EnableRFootLock 驱动左、右脚分支，将 FootLockPos 或经 FootTrace 修正后的 GroundPos 写入 LFootLockLocation / RFootLockLocation，再喂给 ExcuteFootIK。ExcuteFootIK 位于 CRFL_FootIKLibrary，内部把 FFootIKInfo 转成 PBIK effector 并执行 RigUnit_PBIK，因此“把脚逆补偿回锁点”的反解动作由 PBIK 根据当前骨骼姿态和目标 Transform 的差值完成。ActorFollow 最后将骨盆世界位置回传给 UMeshRotationSmoothCpt 做 Actor XY 补偿。

Verification:
使用 UE 5.5.2 的 UnrealEditor-Cmd.exe 加载 ControlRigBlueprint 导出 RigVM 图；CRFL_FootLock 导出统计为主图 74 nodes、81 links、422 recursive pins，函数库包含 LerpFootPos、InitFootHeight、FootTrace、GetIKRootBeavior，errors 为空。CRFL_FootIKLibrary 导出统计为 1 个函数 ExcuteFootIK，函数内包含 RigUnit_PBIK。源码侧确认 StartMeshSmooth 设置 FootLockData，UpdateMeshRotation 在平滑结束时清锁，FRigUnit_ActorFollow 调用 UMeshRotationSmoothCpt::FollowMesh。

Boundary:
当前结论覆盖 CRFL_FootLock、CRFL_FootIKLibrary 与 UMeshRotationSmoothCpt 的脚步锁定闭环。RigUnit_PBIK 的 C++ 求解器内部数学未逐行展开；但 CRFL_FootLock 如何生成固定目标点、ExcuteFootIK 如何把目标转成 PBIK effector、锁定完成后如何释放锁点，已经由导出图和源码确认。
