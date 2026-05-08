# 2026-05-08 AI Unreal Remote Control Cases

Status: raw
Confidence: likely
Task: 查询 AI 通过 Unreal 远程控制操作 Unreal 编辑器的案例，整理分析并沉淀为文档
Sources:
- https://github.com/remiphilippe/mcp-unreal
- https://github.com/edi3on/py-ue5-mcp-server
- https://github.com/runreal/unreal-mcp
- https://github.com/ChiR24/Unreal_mcp
- https://github.com/flopperam/unreal-engine-mcp
- https://pypi.org/project/ue5rc-mcp/
- https://github.com/PRQELT/Autonomix
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-api-http-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-api-websocket-reference-for-unreal-engine

Observation:
There are real AI/MCP projects that connect Claude, Cursor, Claude Code, or other AI coding agents to Unreal Editor. Some explicitly use Epic Remote Control API on port 30010 for object properties and function calls; others use Unreal Python Remote Execution or custom C++ editor plugins while still presenting themselves as remote editor control. Remote Control API is useful as a low-friction bridge, but many projects add custom plugins for Blueprint graph editing, asset operations, screenshots, tests, transactions, and richer editor introspection.

Verification:
Public project pages and package listings were checked on 2026-05-08. mcp-unreal explicitly says it uses Remote Control API for `get_property`, `set_property`, `call_function`, and `move_actor`. py-ue5-mcp-server explicitly connects Claude to Unreal through the Remote Control API and port 30010. runreal/unreal-mcp uses Python Remote Execution rather than Epic Remote Control API. Other projects such as ChiR24/Unreal_mcp, flopperam/unreal-engine-mcp, ue5rc-mcp, and Autonomix are adjacent AI-editor automation cases with custom bridge/plugin architecture.

Boundary:
Repository claims and marketplace summaries can be inconsistent or stale. Treat "remote control" as a broad category unless a source explicitly names Epic Remote Control API endpoints or ports. Verify the actual transport and permissions before adopting a project.
