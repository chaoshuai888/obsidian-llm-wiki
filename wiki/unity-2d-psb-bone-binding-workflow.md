# Unity 2D PSB 骨骼绑定流程

Status: wiki
Last verified: 2026-06-12
Sources:
- Unity 包源码: Library/PackageCache/com.unity.2d.animation@9.2.0/Editor/SkinningModule/SkinningCache/SkinningCache.cs
- Unity 包源码: Library/PackageCache/com.unity.2d.psdimporter@8.1.0/Editor/PSDImporterDataProvider.cs
- Unity 包源码: Library/PackageCache/com.unity.2d.psdimporter@8.1.0/Editor/PSDImporter.cs

Summary:
Unity 2D PSB 角色绑定应把原始 PSB 当作美术源文件，通过 `SpriteDataProviderFactories` 把骨骼、Sprite 骨骼、网格和权重写入 Unity importer metadata。不要直接改 PSB 二进制内容。`CharacterData`、单个 Sprite 的骨骼数据、网格顶点、场景刚体 prefab 分别使用不同坐标系，必须分开处理。

## 资源标准

每个角色使用稳定目录结构：

```text
Assets/Art/Characters/<CharacterName>/
├── <CharacterName>_layers.psb
├── <CharacterName>_bone_spec.json
├── <CharacterName>_layer_spec.json
├── <CharacterName>_idle_motion_spec.json
├── <CharacterName>_Rig.prefab
└── <CharacterName>_Idle.anim
```

PSB 图层要求：
- 一个可运动部件对应一个清晰命名的图层，例如 `head`、`torso`、`upper_arm_L`、`forearm_L`、`hand_L`。
- 自动化绑定优先使用稳定 ASCII 图层名。
- 左右命名保持一致，例如 `_L`、`_R`。
- 阴影、特效、装饰等不参与绑定的图层要明确标为 unmapped 或使用刚体/空 mesh 策略。
- 原始 PSB 只作为源文件保存；脚本只改 Unity import metadata。

Unity 导入要求：
- 使用 PSD Importer 导入 PSB。
- 安装 2D Animation 包。
- PSB importer 开启 Character Rig/`Use as Rig` 时，拖入场景会生成 `SpriteSkin` 和骨骼 Transform。
- Sprite Editor/Skinning Editor 能通过 `ICharacterDataProvider` 读写 `CharacterData`。

## 数据格式

`bone_spec.json` 保存美术源坐标。推荐使用“画布像素，左上角为原点”：

```json
{
  "character": "NovaBot",
  "coordinate_space": "canvas pixels, origin top-left",
  "bones": {
    "root": { "parent": null, "head_px": [1024, 1460], "tail_px": [1024, 1285] },
    "hip": { "parent": "root", "head_px": [1024, 1285], "tail_px": [1024, 1160] }
  }
}
```

`layer_spec.json` 把 PSB 图层映射到控制它的叶子骨骼：

```json
{
  "layers": [
    { "name": "torso", "bone": "spine_01" },
    { "name": "upper_arm_L", "bone": "upper_arm_L" },
    { "name": "forearm_L", "bone": "forearm_L" }
  ]
}
```

`idle_motion_spec.json` 可以描述待生成动画的目标骨骼、振幅和节奏；真正生成 `AnimationClip` 时，应绑定到 prefab 里的 Transform path，而不是直接绑定 importer metadata。

## 坐标规则

源数据一般是左上角原点的画布像素。写入 Unity 时至少要区分四套坐标。

### CharacterData 主骨架

CharacterData 的 root bone 使用角色画布坐标，原点在左下角：

```text
character_x = canvas_x
character_y = canvas_height - canvas_y
```

CharacterData 的子骨骼使用父骨骼局部坐标，不是世界坐标差值：

```text
child_world = bottom_left(child_head_px)
parent_world = bottom_left(parent_head_px)
child_local = inverse(parent_world_rotation) * (child_world - parent_world)
```

子骨骼旋转也必须是父骨骼局部旋转：

```text
child_local_rotation = inverse(parent_world_rotation) * child_world_rotation
```

典型验证值：如果 root 朝上旋转 90 度，hip 接在 root 尾端，那么 hip 的 local position 应为 `(root.length, 0)`，不是 `(0, root.length)`。

### 单个 Sprite 的骨骼数据

单个 Sprite 的 root bone 位置要相对该图层在角色画布里的位置：

```text
sprite_root_local = bottom_left_canvas_head_px - character_part.spritePosition.position
```

这里必须使用 `ICharacterDataProvider` 里的 `CharacterPart.spritePosition`，不能使用 `SpriteRect.rect.position`。`SpriteRect.rect` 可能是 mosaic/atlas 贴图里的裁剪矩形，不是 PSB 角色画布中的图层位置。

单个 Sprite 的子骨骼同样要使用父骨骼局部坐标和局部旋转。不要把 head-to-head 的世界坐标差直接写进 `SpriteBone.position`。

### Mesh 顶点

写 `ISpriteMeshDataProvider` 时，顶点坐标使用 Sprite 自己的矩形局部坐标：

```text
(0, 0) 到 (sprite_rect.width, sprite_rect.height)
```

不要提前减 pivot。Unity 的 postprocess 会内部执行 `vertex.position - rect.size * pivot`。

### 场景刚体 prefab

如果额外生成 Transform 版刚体 prefab，通常使用以画布中心为原点、按 PPU 缩放的 Unity 世界坐标：

```text
unity_x = (canvas_x - canvas_width * 0.5) / pixels_per_unit
unity_y = (canvas_height * 0.5 - canvas_y) / pixels_per_unit
```

这套坐标只用于场景 Transform，不要混到 `CharacterData` 或 Sprite mesh metadata 中。

## 网格与权重

写入 `ISpriteMeshDataProvider` 时：
- 刚体图层可使用一个 quad，所有顶点权重绑定到同一根骨骼。
- 手臂、小腿等需要弯曲的肢体可使用分段条带 mesh，在起始骨和结束骨之间线性插值权重。
- 验证通用自动蒙皮时，可使用 [[unity-2d-psb-auto-skinning-workflow|alpha grid mesh + 自动距离权重]]：所有映射图层统一生成 grid mesh，按 alpha 剔除透明 cell，并按顶点到候选骨骼线段的距离分配最多 4 路归一化权重。
- 不参与绑定的图层，例如地面阴影，可以写空 bones 和空 mesh。
- mesh 顶点必须有有效权重，否则 SpriteSkin 运行时可能变形异常或报警。

## 实现流程

1. 把 PSB 和 JSON spec 放入角色目录。
2. 读取 `bone_spec.json` 和 `layer_spec.json`。
3. 用 `SpriteDataProviderFactories` 从 PSB importer 获取 `ISpriteEditorDataProvider`。
4. 调用 `InitSpriteEditorDataProvider()`。
5. 从 `ICharacterDataProvider.GetCharacterData()` 读取 `CharacterPart.spritePosition`，建立 spriteId 到角色画布位置的映射。
6. 对每个 `SpriteRect` 调用 `ISpriteBoneDataProvider.SetBones`，写入单个 Sprite 的骨骼数据。
7. 通过 `ISpriteMeshDataProvider` 写入顶点、三角索引、边和 bone weights。
8. 通过 `ICharacterDataProvider.SetCharacterData` 写入全角色主骨架和 part-to-bone index。
9. 调用 `provider.Apply()`。
10. 调用 `importer.SaveAndReimport()`。
11. 如果需要 Transform 动画，再生成独立的刚体版 `*_Rig.prefab`。
12. 生成 idle 等动画片段时绑定 prefab Transform path。

## 验证清单

写入 metadata 后要反向读回检查：
- `CharacterData.bones` 数量符合预期。
- root bone 在角色画布坐标内。
- 子骨骼 local position 符合父骨骼局部轴，例如竖直链在父骨旋转 90 度后应表现为 `(length,0)`。
- per-sprite root bone 使用 `CharacterPart.spritePosition` 计算，而不是 atlas rect。
- per-sprite mesh 有顶点、索引、边和非零权重。
- 静态/未匹配图层被明确列出。
- Console 无 importer 相关错误。
- 关闭并重新打开 Skinning Editor，避免 UI 缓存误导。
- 把 PSB importer prefab 拖入场景，确认 SpriteSkin 版角色不散。
- 截图检查额外生成的刚体 prefab 是否仍完整。

## 常见失败模式

- 骨骼列表有但画布没有线：`CharacterData.bones` 坐标原点错了，骨骼被写到画布外。
- 骨骼线有但乱连：子骨骼 `SpriteBone.position` 写成了世界坐标差值，没有转成父骨骼局部坐标。
- 拖 PSB prefab 到场景后角色散开：per-sprite bones 使用了 atlas `SpriteRect.rect`，导致 SpriteSkin bind pose 和 CharacterData 主骨架不一致。
- 角色 reimport 后炸开：mesh 顶点提前减了 pivot，Unity postprocess 又减了一次。
- 只有单个 Sprite 的骨骼，没有完整角色骨架：没有写 `ICharacterDataProvider`。
- 刚体 prefab 正常但 Skinning Editor 不正常：Transform 刚体层级和 importer metadata 用的是不同坐标系，要分别验证。

How to use:
自动化新角色绑定时，先把骨骼 spec 固定在美术源坐标中，再在写入阶段按目标数据结构转换坐标。必须为坐标转换、mesh 顶点范围、per-sprite root bone 来源写测试。

Verification:
运行 EditMode 测试，执行写入菜单，读回 `CharacterData`、`ISpriteBoneDataProvider`、`ISpriteMeshDataProvider`，再检查 Skinning Editor、PSB prefab 场景实例和生成的刚体 prefab 截图。
