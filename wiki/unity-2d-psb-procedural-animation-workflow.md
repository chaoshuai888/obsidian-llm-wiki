# Unity 2D PSB 程序化动画生成流程

Status: wiki
Last verified: 2026-06-12

Summary:
Unity 2D PSB 的程序化动画要面向场景或 Prefab 里真实存在的 Transform path 生成 `AnimationClip`。Transform 曲线是绝对值，不是增量值；因此必须先读取 bind pose，再把 motion spec 的偏移量叠加到基准姿势上。正面 2D 角色的 walk/run 不能主要靠大幅 Z 轴旋转表达前后摆动，否则会变成左右甩动。

## 资源标准

推荐每个角色至少生成：

```text
Assets/Art/Characters/<CharacterName>/
├── <CharacterName>_layers.psb
├── <CharacterName>_Idle.anim
├── <CharacterName>_Walk.anim
├── <CharacterName>_Run.anim
└── <CharacterName>_Locomotion.controller
```

动画生成菜单应能重复执行，且重复执行后不破坏 controller 引用。

## Transform Path 必须来自真实实例

PSB importer 生成的骨骼名可能和 spec 不完全一致。例如 Unity 可能为了避免和同名 Sprite 图层冲突，把骨骼改成：

```text
root/hip_1/spine_01/spine_02/neck_1/head_1
```

而不是：

```text
root/hip/spine_01/spine_02/neck/head
```

生成 clip 前必须检查绑定对象下是否存在 path：

```csharp
target.transform.Find(binding.path) != null
```

验证要求：

```text
missing == 0
```

如果 Animation 窗口出现黄色 `(Missing!)`，说明 clip 里的曲线路径和当前选中的对象层级不一致。

## 曲线是绝对值，不是增量

Unity 的 Transform 曲线会直接覆盖属性。例如：

```text
upper_arm_L localEulerAnglesRaw.z = -4
```

意思不是“在当前角度上减 4 度”，而是把骨骼 Z 角度设置为 `-4`。如果 bind pose 原本是 `126.68`，这样会把手臂拉到错误方向。

正确流程：

```text
base = bindPose.localEulerAngles.z
curveValue = base + offset
```

位置和缩放同理：

```text
curveY = bindPose.localPosition.y + offsetY
scaleY = bindPose.localScale.y + offsetScaleY
```

生成器应从当前场景对象或 prefab 实例读取 bind pose。没有读取到目标 Transform 时，才使用保守默认值。

## 不要删除重建 AnimationClip

如果每次生成都：

```csharp
AssetDatabase.DeleteAsset(path);
AssetDatabase.CreateAsset(clip, path);
```

会导致 `AnimatorController` 里的 state motion 引用断裂，Animation 窗口可能显示 `[No Clip]`，controller 的 `animationClips` 也可能变成 0。

推荐保留资产 GUID，覆盖已有 clip 内容：

```csharp
var existingClip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
if (existingClip == null)
{
    AssetDatabase.CreateAsset(clip, path);
}
else
{
    EditorUtility.CopySerialized(clip, existingClip);
    existingClip.name = Path.GetFileNameWithoutExtension(path);
    EditorUtility.SetDirty(existingClip);
}
```

保存后要重新确认 controller state：

```text
Idle -> <CharacterName>_Idle
Walk -> <CharacterName>_Walk
Run  -> <CharacterName>_Run
```

## 验证清单

每次生成后至少检查：

```text
clip.length 符合预期
clip.frameRate == 24
loopTime == true
controller.animationClips.Length >= 目标 clip 数
所有 state.motion 非空
所有 EditorCurveBinding.path 在目标对象下能找到
missing == 0
```

视觉检查：

- Idle 不应把手臂、腿或头拉离 bind pose。
- Walk/Run 不应出现四肢大幅左右甩。
- 正面角色跑步应以身体弹跳、肢体前后深度和轻微压缩为主。
- Animation 窗口不应显示黄色 `(Missing!)`。

Boundary:
该流程适合 Unity 2D Animation + PSD Importer 的 Transform 骨骼动画。若使用 Sprite Swap、2D IK、Timeline 或自定义运行时骨骼系统，需要额外验证绑定路径、采样方式和 controller 管理策略。
