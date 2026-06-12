# Unity 2D Spec-Driven Rig Builder

Status: wiki
Last verified: 2026-06-12

Summary:
Spec-Driven Rig Builder 是一个 Unity Editor 工具，用 JSON 描述 2D PSB 角色的骨骼、图层绑定、排序和动画。目标是不把角色名、骨骼名、图层名、左右命名、坐标和动画曲线写死在 C# 里，而是通过 spec 支持 Front A Pose、SideRight Pose、ThreeQuarter Pose 等不同视角和命名规则。

相关笔记：
- [[unity-2d-psb-bone-binding-workflow|Unity 2D PSB 骨骼绑定流程]]
- [[unity-2d-psb-auto-skinning-workflow|Unity 2D PSB 自动蒙皮流程]]
- [[unity-2d-psb-procedural-animation-workflow|Unity 2D PSB 程序化动画生成流程]]

## 工具入口

Unity 菜单：

```text
Tools/AI Rig/Build From Selected Spec
Tools/AI Rig/Generate Animation From Motion Spec
Tools/AI Rig/Validate Character Rig
```

选择方式：
1. 在 Project 中选中角色目录下任意 spec/json/psb 资产。
2. 工具会从该目录读取标准 spec 文件。
3. 也可以在代码里调用 `SpecDrivenRigBuilder.LoadSpecSet(folder)`。

工具核心函数：

```text
LoadSpecSet(folder)
ValidateSpecSet(spec, availableLayerNames)
CreateBoneHierarchy(root, boneSpec, pixelsPerUnit)
BuildRigPrefab(spec, report)
GenerateAnimationClips(spec)
```

## 工具源码

完整源码快照见：

```text
[[unity-2d-spec-driven-rig-builder-source|Unity 2D Spec-Driven Rig Builder 源码快照]]
```

该源码快照内嵌 `SpecDrivenRigBuilder.cs` 和 `SpecDrivenRigBuilderTests.cs` 的完整内容，避免只记录本地源码路径导致项目移动后无法追溯。

关键结构：

```csharp
namespace NovaBot.Editor
{
    public static class SpecDrivenRigBuilder
    {
        public sealed class SpecSet
        {
            public string folder;
            public BoneSpec boneSpec = new BoneSpec();
            public LayerSpec layerSpec = new LayerSpec();
            public SortingSpec sortingSpec = new SortingSpec();
            public MotionSpec motionSpec = new MotionSpec();
        }

        public sealed class BoneSpec
        {
            public string character = "Character";
            public string pose = "FrontAPose";
            public CanvasSpec canvas = new CanvasSpec();
            public OutputSpec output = new OutputSpec();
            public Dictionary<string, BoneEntry> bones =
                new Dictionary<string, BoneEntry>(StringComparer.OrdinalIgnoreCase);
        }

        public sealed class LayerSpec
        {
            public string psb_path;
            public List<LayerEntry> layers = new List<LayerEntry>();
        }

        public sealed class SortingSpec
        {
            public List<SortingEntry> orders = new List<SortingEntry>();
        }

        public sealed class MotionSpec
        {
            public List<MotionClipSpec> clips = new List<MotionClipSpec>();
        }

        public sealed class ValidationReport
        {
            public readonly List<string> missingLayers = new List<string>();
            public readonly List<string> missingBones = new List<string>();
            public readonly List<string> duplicateLayers = new List<string>();
            public readonly List<string> duplicateBones = new List<string>();
            public readonly List<string> sortingConflicts = new List<string>();
            public readonly List<string> motionBindingIssues = new List<string>();
        }
    }
}
```

菜单入口：

```csharp
[MenuItem("Tools/AI Rig/Build From Selected Spec")]
public static void BuildFromSelectedSpec()

[MenuItem("Tools/AI Rig/Generate Animation From Motion Spec")]
public static void GenerateAnimationFromMotionSpec()

[MenuItem("Tools/AI Rig/Validate Character Rig")]
public static void ValidateCharacterRig()
```

公共 API：

```csharp
public static SpecSet LoadSpecSet(string folder)

public static ValidationReport ValidateSpecSet(
    SpecSet spec,
    IEnumerable<string> availableLayerNames)

public static Dictionary<string, Transform> CreateBoneHierarchy(
    GameObject rigRoot,
    BoneSpec boneSpec,
    float pixelsPerUnit)

public static GameObject BuildRigPrefab(
    SpecSet spec,
    ValidationReport report)

public static List<AnimationClip> GenerateAnimationClips(
    SpecSet spec)
```

核心实现点：

```text
LoadSpecSet:
  从同目录读取 bone_spec.json、layer_spec.json、sorting_spec.json、motion_spec.json。

ValidateSpecSet:
  检查缺失图层、缺失骨骼、重复图层、重复骨骼、sortingOrder 冲突、motion 目标缺失。

CreateBoneHierarchy:
  按 bone_spec 的 parent 拓扑顺序创建 Transform。
  坐标从 top-left canvas pixels 转换到 Unity local units。

BuildRigPrefab:
  实例化 PSB prefab。
  创建骨骼层级。
  按 layer_spec 把 SpriteRenderer 图层挂到对应骨骼。
  按 sorting_spec 设置 SpriteRenderer.sortingOrder。
  保存到 output.prefab_path。

GenerateAnimationClips:
  按 motion_spec 生成 AnimationClip。
  bone track 使用 bind pose + offset。
  layer track 支持 SpriteRenderer.sortingOrder。
  保存到 clip path，并可写入 AnimatorController。
```

关键私有模块：

```text
AddTrackCurve:
  把 motion track 转成 AnimationCurve。
  支持 rotationZ、positionX、positionY、scaleY、sortingOrder。

BuildBonePathMap:
  从当前选中对象或场景对象读取真实 Transform path。
  兼容 Unity PSB importer 生成的 *_1 骨骼名。

ApplyLayerParenting:
  按 layer_spec 把 SpriteRenderer 重新挂到骨骼 Transform。

ApplySorting:
  按 sorting_spec 设置静态 sortingOrder。

Json:
  内置小型 JSON parser，用于读取 dictionary 结构。
  避免 Unity JsonUtility 不能直接读取 Dictionary 的限制。
```

测试覆盖：

```text
LoadSpecSet_SupportsNearFarNamesWithoutLeftRight
ValidateSpecSet_ReportsMissingBonesDuplicateLayersAndSortingConflicts
CreateBoneHierarchy_UsesSpecCanvasAndTopLeftCoordinates
```

测试文件：

```text
D:/2DAnim/SekelonAnim/Assets/Editor/NovaBot/SpecDrivenRigBuilderTests.cs
```

## 目录约定

推荐角色目录：

```text
Assets/Art/Characters/<CharacterName>/
├── <CharacterName>_layers.psb
├── bone_spec.json
├── layer_spec.json
├── sorting_spec.json
├── motion_spec.json
├── <CharacterName>_SpecRig.prefab
├── <CharacterName>_SpecIdle.anim
└── <CharacterName>_SpecRun.anim
```

为了兼容旧资产，当前工具也能读取类似 `NovaBot_bone_spec.json`、`NovaBot_layer_spec.json` 这种带角色名前缀的文件；新项目优先使用标准名。

## bone_spec.json

职责：
- 描述角色画布。
- 描述骨骼树。
- 描述输出路径。
- 标记视角/姿势，例如 FrontAPose、SideRight、ThreeQuarter。

示例：

```json
{
  "character": "NovaBot",
  "pose": "FrontAPose",
  "canvas": {
    "width": 2048,
    "height": 2048,
    "origin": "top_left_pixels"
  },
  "output": {
    "prefab_path": "Assets/Art/Characters/NovaBot/NovaBot_SpecRig.prefab",
    "clip_folder": "Assets/Art/Characters/NovaBot",
    "controller_path": "Assets/Art/Characters/NovaBot/NovaBot_SpecLocomotion.controller"
  },
  "bones": {
    "root": {
      "parent": null,
      "head_px": [1024, 1460],
      "tail_px": [1024, 1285]
    },
    "hip": {
      "parent": "root",
      "head_px": [1024, 1285],
      "tail_px": [1024, 1160]
    }
  }
}
```

坐标规则：

```text
unity_x = (canvas_x - canvas_width * 0.5) / pixels_per_unit
unity_y = (canvas_height * 0.5 - canvas_y) / pixels_per_unit
```

骨骼 Transform 层级完全由 `parent` 决定。骨骼名可以是：

```text
upper_arm_L / upper_arm_R
arm_near / arm_far
leg_front / leg_back
side_arm / hidden_arm
```

工具不强制使用 L/R。

## layer_spec.json

职责：
- 指定 PSB 路径。
- 指定 Sprite 图层挂到哪根骨骼。
- 允许一个骨骼控制多个装饰层。

示例：

```json
{
  "character": "NovaBot",
  "psb_path": "Assets/Art/Characters/NovaBot/NovaBot_layers.psb",
  "layers": [
    { "name": "torso", "bone": "spine_01" },
    { "name": "upper_arm_L", "bone": "upper_arm_L" },
    { "name": "forearm_L", "bone": "forearm_L" },
    { "name": "antenna_ball", "bone": "antenna_tip" }
  ]
}
```

ThreeQuarter 或 SideRight 可以这样命名：

```json
{
  "layers": [
    { "name": "upper_arm_near", "bone": "arm_near" },
    { "name": "upper_arm_far", "bone": "arm_far" },
    { "name": "leg_front", "bone": "leg_front" },
    { "name": "leg_back", "bone": "leg_back" }
  ]
}
```

不参与骨骼挂接的视觉层，例如地面阴影，可以只放在 `sorting_spec.json`，不放进 `layer_spec.json`。

## sorting_spec.json

职责：
- 设置 SpriteRenderer.sortingOrder。
- 描述静态层级。
- 可以包含不参与骨骼挂接但需要排序的视觉层。

示例：

```json
{
  "orders": [
    { "layer": "shadow_ground", "order": 1 },
    { "layer": "arm_far", "order": 8 },
    { "layer": "torso", "order": 17 },
    { "layer": "arm_near", "order": 22 }
  ]
}
```

验证规则：
- 如果 layer 不在 `layer_spec.json`，但存在于 PSB prefab，可以作为纯视觉层通过。
- 如果多个绑定层使用同一个 sortingOrder，会输出排序冲突报告。
- 对 ThreeQuarter，near 通常排序高于 torso，far 通常低于 torso。

## motion_spec.json

职责：
- 生成 AnimationClip。
- 使用 bind pose + offset 语义。
- 支持 bone track 和 layer track。

示例：

```json
{
  "clips": [
    {
      "name": "NovaBot_SpecIdle",
      "path": "Assets/Art/Characters/NovaBot/NovaBot_SpecIdle.anim",
      "fps": 24,
      "duration": 2.0,
      "loop": true,
      "tracks": [
        { "target": "hip", "property": "positionY", "keys": [[0, 0], [12, 0.025], [24, 0]] },
        { "target": "spine_01", "property": "rotationZ", "keys": [[0, 0], [12, 1.0], [24, 0]] },
        { "target": "antenna_tip", "property": "scaleY", "keys": [[0, 0], [12, 0.05], [24, 0]] }
      ]
    }
  ]
}
```

bone track：

```json
{ "target": "arm_near", "property": "rotationZ", "keys": [[0, 0], [6, 2], [12, 0]] }
```

layer track：

```json
{
  "target": "upper_arm_near",
  "target_type": "layer",
  "property": "sortingOrder",
  "keys": [[0, 8], [6, 16], [12, 8]]
}
```

支持的 property：

```text
rotationZ
positionX
positionY
scaleY
sortingOrder
```

关键点：
`rotationZ`、`positionX/Y`、`scaleY` 都是 offset，不是绝对值。工具会读取当前目标对象的 bind pose，并叠加 key 里的值。

例如：

```text
bind upper_arm_L.z = 126.68
spec key = 1.5
final curve value = 128.18
```

这能避免把手臂直接写成 1.5 度导致姿势飞掉。

## 三种视角的表达方式

### Front A Pose

适合正面角色：
- 可以使用 L/R，也可以使用 near/far。
- 四肢默认分布在身体两侧。
- 跑步不要大幅 Z 旋转，否则会变成左右甩动。
- 前后运动主要靠 `positionY`、`scaleY` 和 `sortingOrder` 表达。

### SideRight Pose

适合侧面角色：
- 推荐命名 `leg_front`、`leg_back`、`arm_front`、`arm_back`。
- 可以使用较明显的腿部摆动，但要检查脚底接触点。
- 前后层级由 sorting_spec 决定。

### ThreeQuarter Pose

适合 3/4 视角：
- 推荐命名 `arm_near`、`arm_far`、`leg_near`、`leg_far`。
- near 层通常 sortingOrder 更高。
- run/walk 中可以用 layer track 动态交换 near/far 前后关系。
- 不要在 C# 中推断 near/far；全部写进 spec。

## 验证报告

`Validate Character Rig` 输出：

```text
missingLayers
missingBones
duplicateLayers
duplicateBones
sortingConflicts
motionBindingIssues
```

常见问题：

```text
missingLayers:
  layer_spec 或 sorting_spec 引用了 PSB 中不存在的图层。

missingBones:
  layer_spec 或 motion_spec 引用了 bone_spec 中不存在的骨骼。

duplicateLayers:
  layer_spec 中同名图层重复。

sortingConflicts:
  多个绑定层使用同一个 sortingOrder，可能导致前后关系不稳定。

motionBindingIssues:
  motion track 的目标或属性无法映射到有效 AnimationCurve。
```

验证完成后，还应检查 clip 曲线：

```text
AnimationUtility.GetCurveBindings(clip)
target.transform.Find(binding.path) != null
```

目标值：

```text
missing == 0
```

如果 Animation 窗口出现黄色 `(Missing!)`，说明曲线路径和当前对象层级不一致。

## NovaBot 当前验证结果

2026-06-12 验证：

```text
prefab=Assets/Art/Characters/NovaBot/NovaBot_SpecRig.prefab
clips=Assets/Art/Characters/NovaBot/NovaBot_SpecIdle.anim,
      Assets/Art/Characters/NovaBot/NovaBot_SpecRun.anim

missingLayers=
missingBones=
sortingConflicts=

NovaBot_SpecIdle: curves=18, missing=0
NovaBot_SpecRun: curves=28, missing=0
EditMode tests: 13/13 passed
Console errors: 0
```

## 使用清单

新角色接入：

1. 准备 PSB，图层名稳定。
2. 写 `bone_spec.json`，包含 canvas、pose、output、bones。
3. 写 `layer_spec.json`，把图层映射到骨骼。
4. 写 `sorting_spec.json`，设置静态前后层级。
5. 写 `motion_spec.json`，用 offset tracks 描述动画。
6. 选中角色目录下任意 spec 或 PSB。
7. 执行 `Tools/AI Rig/Validate Character Rig`。
8. 无严重报告后执行 `Build From Selected Spec`。
9. 选中生成的角色或场景实例，执行 `Generate Animation From Motion Spec`。
10. 打开 Animation 窗口确认没有 `(Missing!)`。

## 设计边界

当前工具生成的是 Transform 层级 rig prefab 和 AnimationClip，不直接写 SpriteSkin mesh/weights。PSB importer metadata、SpriteBones、网格权重仍由 [[unity-2d-psb-bone-binding-workflow]] 和 [[unity-2d-psb-auto-skinning-workflow]] 中的流程处理。

如果要做最终商业质量动画，还需要：
- 更完整的 motion spec 属性。
- IK 或脚底锁定。
- per-view 的动作模板。
- 自动截图/像素级视觉回归验证。
- 对 motionBindingIssues 做更严格的路径验证。
