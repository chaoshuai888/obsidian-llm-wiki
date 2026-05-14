---
confidence: confirmed
created: 2026-05-14
sources:
- raw/Unreal/2026-05-14-unreal-control-rig-asset-parse.md
- E:/NDSVN_UE_ARPG_Battle/Saved/Codex/export_controlrig_full.py
- E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootLock_full.json
- E:/NDSVN_UE_ARPG_Battle/Saved/Codex/CRFL_FootLock_summary.md
status: published
tags:
- unreal-engine
- control-rig
- rigvm
- python
- asset-automation
title: Unreal Control Rig 资产解析
updated: '2026-05-14'
---

# Unreal Control Rig 资产解析

## 摘要

解析 Unreal Control Rig `.uasset` 时，优先使用匹配版本的 Unreal Editor 加载资产，再通过 Python Editor API 遍历 `ControlRigBlueprint`、`RigVMGraph`、`RigVMNode`、`RigVMPin` 和 `RigVMLink`。这种方式得到的是可用于分析和调试的语义结构，比直接硬读 `.uasset` 二进制更可靠。

这不是逐 byte 反序列化所有私有字段，而是让 UE 自己完成包加载和版本兼容，再把 Control Rig / RigVM 图导出成 JSON 或 Markdown。

## 适用场景

适合用于：

- 分析 Control Rig 主图、函数库、节点、Pin、连线和默认值。
- 对比两个 Control Rig 资产的逻辑结构。
- 查找脚锁、足 IK、骨骼控制等 RigVM 图中的数据流。
- 给 AI 或工具提供可读的 Control Rig 上下文。

不适合替代：

- 逐 byte 的 `.uasset` 法证分析。
- 修改资产并保存回 Unreal 的编辑器事务流程。
- 跨引擎版本无验证地解析私有序列化字段。

## 基本流程

1. 找到项目匹配的 Unreal Editor。

   优先读 `.uproject` 的 `EngineAssociation`，再查注册表或项目 target 文件。这个项目的 `ARPG_Battle.uproject` 指向 `D:/UnrealEngine`，`ARPG_BattleEditor.target` 和 `D:/UnrealEngine/Engine/Build/Build.version` 确认为 UE 5.5.2。

2. 用 `UnrealEditor-Cmd.exe` 跑 Python commandlet。

   示例：

   ```powershell
   & "D:/UnrealEngine/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" `
     "E:/NDSVN_UE_ARPG_Battle/ARPG_Battle.uproject" `
     -run=pythonscript `
     -script="E:/NDSVN_UE_ARPG_Battle/Saved/Codex/export_controlrig_full.py" `
     -unattended -nop4 -nosplash -NoSound -stdout -FullStdOutLogOutput
   ```

3. 在脚本中加载资产。

   使用完整对象路径，例如：

   ```python
   asset = unreal.load_asset("/Game/ArtRes/Character/AnimBPTemplate/Common/CRFunctionLibrary/CRFL_FootLock.CRFL_FootLock")
   ```

4. 识别并遍历 Control Rig 对象。

   常用入口：

   - `asset.get_model()`：主 `RigVMGraph`。
   - `asset.get_local_function_library()`：本地函数库。
   - `asset.get_member_variables()`：成员变量。
   - `asset.get_hierarchy_controller()`：Hierarchy 编辑控制器。
   - `function_library.get_functions()`：函数库函数节点。
   - `function_library.get_contained_graphs()`：函数图。

5. 对每个 `RigVMGraph` 递归导出。

   常用 getter：

   - `graph.get_nodes()`
   - `graph.get_links()`
   - `graph.get_contained_graphs()`
   - `graph.get_variable_descriptions()`
   - `graph.get_local_variables()`

6. 对每个节点导出结构。

   常用 getter：

   - `node.get_node_path()`
   - `node.get_node_title()`
   - `node.get_position()`
   - `node.get_pins()`
   - `node.get_all_pins_recursively()`
   - `node.get_script_struct()`，适用于 unit node。
   - `node.get_method_name()`，适用于 unit node。
   - `node.get_variable_name()`、`node.get_cpp_type()`，适用于 variable node。

7. 对每个 Pin 和 Link 导出数据流。

   Pin 常用 getter：

   - `pin.get_pin_path()`
   - `pin.get_direction()`
   - `pin.get_cpp_type()`
   - `pin.get_default_value()`
   - `pin.get_sub_pins()`
   - `pin.get_linked_source_pins()`
   - `pin.get_linked_target_pins()`

   Link 常用 getter：

   - `link.get_source_pin()`
   - `link.get_target_pin()`
   - `link.get_source_node()`
   - `link.get_target_node()`

8. 写出 UTF-8 JSON 和摘要。

   建议导出两份：

   - 完整 JSON：保留图、节点、Pin、连线和默认值，供工具继续分析。
   - Markdown 摘要：保留图统计、函数列表和主图节点顺序，供人快速阅读。

## 先反射再深挖

UE Python API 在不同版本里会有差异。第一次解析陌生 Control Rig 时，先写一个反射脚本，打印 `dir(asset)`、`dir(model)`、`dir(node)`、`dir(pin)` 中和 `rig`、`graph`、`node`、`pin`、`link`、`function` 相关的方法，再根据实际暴露的 getter 写正式导出器。

在 UE 5.5.2 中，`CRFL_FootLock` 资产暴露了这些关键入口：

- `get_model`
- `get_controller`
- `get_all_models`
- `get_local_function_library`
- `get_hierarchy_controller`
- `get_member_variables`

`RigVMGraph` 暴露了 `get_nodes`、`get_links`、`get_contained_graphs`；`RigVMPin` 暴露了 `get_cpp_type`、`get_default_value`、`get_linked_source_pins`、`get_linked_target_pins`。

## 验证标准

一次 Control Rig 解析至少检查：

- Commandlet 输出 `Success - 0 error(s)`。
- JSON 可以被重新读取并统计。
- `asset.class` 是 `ControlRigBlueprint` 或目标 Control Rig 相关类。
- 主图、函数库图、节点数、连线数不为空。
- 脚本记录的 `errors` 数组为空，或每个错误都有明确边界说明。

本次 `CRFL_FootLock` 验证结果：

- 资产类：`/Script/ControlRigDeveloper.ControlRigBlueprint`
- 图数量：5
- 成员变量：12
- 函数库函数：4
- 主图：74 nodes、81 links、422 recursive pins
- 函数图：`LerpFootPos`、`InitFootHeight`、`FootTrace`、`GetIKRootBeavior`
- 脚本记录错误：0

## 常见坑

- 不要用不匹配的 UE 版本直接加载资产，否则可能加载失败或 silently 失真。
- 不要把 PowerShell 里的乱码当成资产内容损坏；优先检查导出的 UTF-8 文件。
- 不要把旧 wiki 或推断当事实，最终要回到源码、资产加载结果和 commandlet 输出。
- 不要把个人导出脚本和 JSON 默认提交到项目仓库；长期知识写入个人 vault。
- 如果要进一步修改 Control Rig，应该使用 `RigVMController` 并考虑事务、撤销和保存流程；只读解析不需要修改资产。

## 下次如何应用

遇到需要解析 Control Rig 的任务时：

1. 先定位项目引擎版本和 Editor-Cmd 路径。
2. 用反射脚本确认该 UE 版本暴露的 Control Rig Python getter。
3. 用 `export_controlrig_full.py` 这类只读脚本导出 JSON。
4. 读 JSON 中每个 `graphs` 条目的 `nodes`、`links` 和函数图，分析实际数据流。
5. 若需要沉淀项目经验，只记录可复用流程、验证命令和边界，不复制大段资产数据。
