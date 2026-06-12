# Unity 2D PSB 自动蒙皮流程

Status: wiki
Last verified: 2026-06-12
Sources:
- Unity MCP EditMode 测试结果：NovaBot.Editor.NovaBotRigBuilderTests 9/9 passed
- Unity MCP metadata 读回：withMesh=24，empty=1，totalVerts=594，totalTris=752，badWeightVerts=0

Summary:
通用 PSB 自动蒙皮可以先用“alpha grid mesh + 骨骼距离权重”的方案验证闭环。该方案不依赖复杂轮廓三角剖分或第三方库，能为每个 Sprite 自动生成可变形网格，并根据候选骨骼线段给顶点分配最多 4 路归一化权重。它适合作为通用管线第一版，再逐步升级到轮廓 mesh、BBW 或人工修权重。

## 适用目标

该方案适合验证通用自动蒙皮流程：
- 输入是 PSB 多图层角色。
- 已有 `bone_spec.json` 描述全角色骨架。
- 已有 `layer_spec.json` 描述图层到控制骨骼的映射。
- 希望所有可绑定图层都获得自动 mesh 和权重。
- 允许第一版 mesh 是规则网格近似，而不是完全贴合轮廓的三角剖分。

不适合直接作为最终美术质量方案：
- 高精度表情变形。
- 复杂衣摆、头发、布料。
- 对轮廓贴合要求很高的商用品质角色。

## 核心思路

每个 Sprite 独立生成 mesh：
1. 根据 Sprite 尺寸确定 grid 分辨率。
2. 读取 PSB importer 的 readable texture。
3. 对每个 grid cell 的中心点采样 alpha。
4. 透明 cell 不生成三角形。
5. 不透明 cell 生成两个三角形。
6. 复用相邻 cell 的顶点。
7. 根据顶点到候选骨骼线段的距离计算权重。
8. 取权重最高的 4 根骨骼。
9. 权重归一化后写入 `Vertex2DMetaData.boneWeight`。

## 数据来源

使用 Unity provider：
- `ITextureDataProvider.GetReadableTexture2D()`：读取 mosaic/atlas 贴图 alpha。
- `ISpriteMeshDataProvider.SetVertices/SetIndices/SetEdges()`：写 mesh 与权重。
- `ICharacterDataProvider.GetCharacterData()`：读取 `CharacterPart.spritePosition`，用于角色画布坐标换算。
- `ISpriteBoneDataProvider.SetBones()`：写单个 Sprite 的骨骼 bind pose。

注意：alpha 采样使用 `SpriteRect.rect`，因为它指向 mosaic/atlas 贴图中的裁剪区域；骨骼定位使用 `CharacterPart.spritePosition`，因为它指向角色画布中的图层位置。这两个坐标不能混用。

## 网格生成规则

第一版推荐按尺寸自适应：

```text
columns = clamp(ceil(sprite_width / 64), 2, 16)
rows    = clamp(ceil(sprite_height / 64), 2, 16)
```

生成 cell：

```text
cell_center = ((x + 0.5) * width / columns,
               (y + 0.5) * height / rows)
```

alpha 判断：

```text
texture_x = sprite_rect.x + cell_center.x
texture_y = sprite_rect.y + cell_center.y
opaque = readable_texture.GetPixel(texture_x, texture_y).a > 0.05
```

不透明 cell 生成两个三角形：

```text
bottomLeft, topLeft, bottomRight
bottomRight, topLeft, topRight
```

边列表使用去重后的 cell 四边，供 Sprite Editor 显示和编辑 mesh。

## 候选骨骼

对每个图层，从 `layer_spec.json` 的目标骨骼向父链回溯，形成候选骨骼链。例如 `forearm_L`：

```text
root -> hip -> spine_01 -> spine_02 -> upper_arm_L -> forearm_L
```

每根候选骨骼要转换成 Sprite 局部空间线段：

```text
bone_start = bottom_left(head_px) - character_part.spritePosition.position
bone_end   = bottom_left(tail_px) - character_part.spritePosition.position
```

`boneIndex` 必须对应当前 Sprite 的 bones 数组索引，而不是 CharacterData 全局骨骼索引。

## 权重计算

第一版使用距离反比权重：

```text
score = 1 / (distance_to_bone_segment + 1)
```

流程：
1. 计算顶点到每根候选骨骼线段的距离。
2. 按 score 从高到低排序。
3. 取前 4 根骨骼。
4. 对 score 求和。
5. 每个通道权重除以总和。
6. 写入 `BoneWeight.boneIndex0..3` 与 `weight0..3`。

验证要求：

```text
weight0 + weight1 + weight2 + weight3 ~= 1.0
```

## 写入流程

1. 先写 per-sprite bones，确保 Sprite bind pose 与 CharacterData 主骨架一致。
2. 读取 readable texture。
3. 对每个映射图层生成 alpha grid mesh。
4. 未映射图层，例如 `shadow_ground`，写空 mesh。
5. 写入 mesh vertices、indices、edges。
6. 写入 CharacterData 主骨架和 part-to-bone index。
7. `provider.Apply()`。
8. `importer.SaveAndReimport()`。
9. 重新实例化 PSB prefab 检查 SpriteSkin 是否完整。

## NovaBot 验证结果

2026-06-12 的 NovaBot 案例读回结果：

```text
withMesh=24
empty=1
totalVerts=594
totalTris=752
badWeightVerts=0
```

部分图层：

```text
head: verts=92, tris=146
torso: verts=86, tris=136
face_panel: verts=36, tris=48
upper_arm_L: verts=24, tris=26
forearm_L: verts=24, tris=26
```

重新实例化 `NovaBot_layers.psb` 后：

```text
renderers=25
spriteSkins=24
skinsWithRoot=24
skinsWithBones=24
```

场景截图完整：`D:/2DAnim/SekelonAnim/Assets/Screenshots/NovaBot_auto_skin_grid_prefab.png`。

## 测试清单

至少覆盖以下纯算法测试：
- grid mesh 能生成预期顶点、三角形和边。
- 透明 cell 被剔除。
- 所有顶点权重归一化。
- `CreateAutoSkinBonesForSprite` 使用 `CharacterPart.spritePosition` 局部空间。
- mesh 顶点仍保持 Sprite 局部 `(0,0)-(width,height)`。

运行 Unity EditMode 测试后，再做 importer metadata 读回：
- mesh 数量。
- 顶点总数。
- 三角形总数。
- badWeightVerts 是否为 0。
- PSB prefab 实例化后 SpriteSkin 是否都有 rootBone 和 boneTransforms。

## 常见问题

- mesh 很方：grid 只是第一版近似，后续可升级 alpha 轮廓提取和三角剖分。
- 小图层生成过多顶点：降低最大 grid 密度，或给装饰图层加刚体策略。
- 面部被身体骨骼影响：需要图层级权重规则，例如 face/eye/mouth 只允许 head 链。
- 关节变形不自然：距离权重只是 baseline，可改为投影权重、关节混合区或 BBW。
- 拖入场景散开：优先检查 per-sprite bones 是否相对 `CharacterPart.spritePosition`，再检查 mesh 顶点是否提前减 pivot。

How to use:
先用 alpha grid 方案打通自动蒙皮闭环，确保 importer metadata、SpriteSkin、prefab 实例化都稳定。之后再替换 mesh 生成器或权重生成器，不要同时改坐标系统和蒙皮算法。

Verification:
运行 EditMode 测试，执行写入菜单，读回 mesh/weight 统计，重新实例化 PSB prefab 并截图。
