# 2026-06-12 Unity 2D PSB 自动蒙皮

Status: raw
Confidence: confirmed
Task: NovaBot 通用自动蒙皮 C 方案验证
Sources:
- D:/2DAnim/SekelonAnim/Assets/Editor/NovaBot/NovaBotRigBuilder.cs
- D:/2DAnim/SekelonAnim/Assets/Editor/NovaBot/NovaBotRigBuilderTests.cs
- Unity MCP EditMode 测试结果：NovaBot.Editor.NovaBotRigBuilderTests 9/9 passed
- Unity MCP metadata 读回：withMesh=24，empty=1，totalVerts=594，totalTris=752，badWeightVerts=0
- Unity 截图：D:/2DAnim/SekelonAnim/Assets/Screenshots/NovaBot_auto_skin_grid_prefab.png

Observation:
通用 PSB 自动蒙皮第一版可以使用 alpha grid mesh 加距离权重。网格 cell 中心采样 PSB readable texture 的 alpha，透明 cell 不生成三角形；顶点权重按到候选骨骼线段的距离反比计算，取前 4 根并归一化。候选骨骼线段需要转换到 Sprite 局部空间，使用 `CharacterPart.spritePosition` 作为图层在角色画布中的原点。

Verification:
NovaBot 写入后读回 24 个图层有 mesh，1 个 shadow 图层为空，合计 594 顶点、752 三角形、0 个权重错误顶点。重新实例化 `NovaBot_layers.psb` prefab 后，25 个 SpriteRenderer、24 个 SpriteSkin，所有 SpriteSkin 都有 rootBone 和 boneTransforms，场景截图完整。

Boundary:
该方案是通用自动蒙皮 baseline，不等同于最终高质量蒙皮。它验证 importer metadata、mesh、权重、SpriteSkin prefab 闭环；后续可替换为轮廓三角剖分、BBW、图层级权重规则或人工修权重。
