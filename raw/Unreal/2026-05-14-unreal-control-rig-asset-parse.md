# 2026-05-14 Unreal Control Rig Asset Parse

Status: raw
Confidence: confirmed
Task: 解析 `CRFL_FootLock.uasset` 并沉淀 Control Rig 解析方法
Sources:
- `E:/NDSVN_UE_ARPG_Battle/ARPG_Battle.uproject`
- `E:/NDSVN_UE_ARPG_Battle/Binaries/Win64/ARPG_BattleEditor.target`
- `D:/UnrealEngine/Engine/Build/Build.version`
- `E:/NDSVN_UE_ARPG_Battle/Saved/Codex/export_controlrig_full.py`
- `E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootLock_full.json`
- `E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootLock_summary.md`
- Command: `D:/UnrealEngine/Engine/Binaries/Win64/UnrealEditor-Cmd.exe E:/NDSVN_UE_ARPG_Battle/ARPG_Battle.uproject -run=pythonscript -script=E:/NDSVN_UE_ARPG_Battle/Saved/Codex/export_controlrig_full.py -unattended -nop4 -nosplash -NoSound -stdout -FullStdOutLogOutput`

Observation:
Control Rig `.uasset` should be parsed by loading it with a matching Unreal Editor and traversing its `ControlRigBlueprint` / `RigVMGraph` objects through the UE Python API, rather than treating the file as a generic binary blob. In this project, UE 5.5.2 at `D:/UnrealEngine` loaded `CRFL_FootLock` successfully and exported the main graph, function library graphs, nodes, pins, links, member variables, and hierarchy-related metadata to JSON.

Verification:
The commandlet completed with `Success - 0 error(s)` and wrote `CRFL_FootLock_full.json` plus `CRFL_FootLock_summary.md`. The exported asset class was `/Script/ControlRigDeveloper.ControlRigBlueprint`; it contained 5 graphs, 12 member variables, 4 function-library functions, and no script-recorded export errors. Main graph stats were 74 nodes, 81 links, and 422 recursive pins.

Boundary:
This is a semantic Control Rig / RigVM export, not a byte-for-byte parse of every private serialized field inside `.uasset`. It depends on the matching project engine version, enabled ControlRig/RigVM/PythonScriptPlugin modules, and UE Python getter availability. Python API names can vary across UE versions; use a reflection pass first when porting. Console output may display Chinese labels incorrectly in PowerShell if encoding is not UTF-8, while the exported UTF-8 files preserve them.
