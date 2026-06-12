# 2026-06-12 Unity 2D Spec-Driven Rig Builder

Status: raw
Confidence: confirmed
Task: 将 NovaBot 自动骨骼工具改造成通用 Spec-Driven Rig Builder，并沉淀使用文档
Sources:
- D:/2DAnim/SekelonAnim/Assets/Editor/NovaBot/SpecDrivenRigBuilder.cs
- D:/2DAnim/SekelonAnim/Assets/Editor/NovaBot/SpecDrivenRigBuilderTests.cs
- D:/2DAnim/SekelonAnim/Assets/Art/Characters/NovaBot/layer_spec.json
- D:/2DAnim/SekelonAnim/Assets/Art/Characters/NovaBot/sorting_spec.json
- D:/2DAnim/SekelonAnim/Assets/Art/Characters/NovaBot/motion_spec.json
- Unity MCP EditMode 测试：13/13 passed

Observation:
Unity 2D PSB 角色的刚体骨骼 prefab、图层挂接、sortingOrder 和基础 Transform 动画可以由四个 JSON spec 驱动。核心风险是 AnimationClip 曲线必须绑定真实 Transform path，并且 Transform 曲线值应按 bind pose + offset 生成，不能把 motion spec 的值当绝对姿势。

Verification:
NovaBot 生成结果：
prefab=Assets/Art/Characters/NovaBot/NovaBot_SpecRig.prefab；
clips=NovaBot_SpecIdle.anim、NovaBot_SpecRun.anim；
missingLayers/missingBones/sortingConflicts 为空；
两个 clip 的 binding missing=0；
EditMode tests 13/13 passed。

Boundary:
当前 SpecDrivenRigBuilder 生成 Transform rig prefab 和 AnimationClip，不直接生成 SpriteSkin mesh/weights。自动蒙皮仍依赖 PSB metadata 写入流程。motion spec 当前支持 rotationZ、positionX、positionY、scaleY、sortingOrder，后续如需 foot lock、IK、Sprite Swap 或更复杂曲线，需要扩展 spec schema。
