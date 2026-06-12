# 2026-06-12 Unity 2D PSB 骨骼绑定流程

Status: raw
Confidence: confirmed
Task: NovaBot 自动骨骼创建工具调试与修复
Sources:
- D:/2DAnim/SekelonAnim/Assets/Editor/NovaBot/NovaBotRigBuilder.cs
- D:/2DAnim/SekelonAnim/Assets/Editor/NovaBot/NovaBotRigBuilderTests.cs
- Unity MCP EditMode 测试结果：NovaBot.Editor.NovaBotRigBuilderTests 6/6 passed
- Unity MCP metadata 读回：CharacterData.bones=19，MeshSprites=24，EmptyMesh=1
- Unity 包源码：Library/PackageCache/com.unity.2d.animation@9.2.0/Editor/SkinningModule/SkinningCache/SkinningCache.cs
- Unity 包源码：Library/PackageCache/com.unity.2d.psdimporter@8.1.0/Editor/PSDImporterDataProvider.cs
- Unity 包源码：Library/PackageCache/com.unity.2d.psdimporter@8.1.0/Editor/PSDImporter.cs

Observation:
Unity 2022.3、2D Animation 9.2.0、PSD Importer 8.1.0 下，PSB 角色主骨架 `CharacterData.bones` 的 root bone 使用左下角原点的角色画布坐标。子骨骼的 `SpriteBone.position` 和 `SpriteBone.rotation` 必须是父骨骼局部空间值，不能使用世界坐标差值。单个 Sprite 的 root bone 需要相对 `CharacterPart.spritePosition`，不能相对 atlas `SpriteRect.rect`。通过 `ISpriteMeshDataProvider` 写 mesh 时，顶点使用 Sprite 局部 `(0,0)-(width,height)`，因为 Unity postprocess 会自行减 pivot。

Verification:
NovaBot metadata 通过 `SpriteDataProviderFactories` 写入，再通过 `ICharacterDataProvider`、`ISpriteBoneDataProvider`、`ISpriteMeshDataProvider` 读回验证。修复后的示例值：CharacterData root pos=(1024,588)，hip pos=(175,0)，spine_01 pos=(125,0)，upper_arm_L pos=(45,234)，forearm_L pos=(239.401,0)；torso per-sprite root pos=(269,-223)，使用 character part position=(755,811)。EditMode 测试 6/6 通过，重新实例化 `NovaBot_layers.psb` prefab 后角色完整。

Boundary:
已在 Unity 2022.3.62f3c1、com.unity.2d.animation 9.2.0、com.unity.2d.psdimporter 8.1.0 验证。其他 Unity 或包版本需要重新确认 provider 行为和包源码。该流程修改 Unity import metadata，不修改原始 PSB 二进制文件。
