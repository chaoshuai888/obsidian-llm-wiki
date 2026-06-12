# 2026-06-12 Unity 2D PSB Bindpose 坐标修正

Status: review
Related: D:/obsidian-llm-wiki/wiki/unity-2d-psb-bone-binding-workflow.md
Trigger: user_feedback

What was wrong:
早期流程笔记暗示 per-sprite root bone 可以用 `SpriteRect.rect.position` 定位。NovaBot 实测中，`SpriteRect.rect` 是 mosaic/atlas 贴图矩形，不是 PSB 角色画布中的图层位置。这个错误会导致拖动 PSB importer prefab 到场景时角色散开，因为 SpriteSkin bind pose 和 CharacterData 主骨架 Transform 对不上。

Correction:
PSB 角色绑定中，per-sprite root bone 必须使用 `ICharacterDataProvider` 里的 `CharacterPart.spritePosition.position` 作为 Sprite 在角色画布中的原点。mesh 顶点仍然使用 Sprite 局部坐标 `(0,0)-(width,height)`。

Evidence:
- 用户截图显示 `NovaBot_layers.psb` prefab 拖入场景后散开，而生成的刚体版 `NovaBot_Rig.prefab` 保持完整。
- 修复前 metadata 读回：`torso` per-sprite root pos 为 `(1020,1456)`，来源是 atlas rect `(4,4)`。
- 修复后 metadata 读回：`torso` per-sprite root pos 为 `(269,-223)`，来源是 character part position `(755,811)`。
- Unity 包源码显示 `PSDImporter.OnProducePrefab` 会用 CharacterData 主骨架 Transform 和每个 Sprite 的 bind pose 创建 SpriteSkin。
- 修复后重新实例化 PSB prefab：25 个 SpriteRenderer，24 个 SpriteSkin，root local `(0,-4.36,0)`，截图完整。
