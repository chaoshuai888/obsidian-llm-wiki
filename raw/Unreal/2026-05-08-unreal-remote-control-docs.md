# 2026-05-08 Unreal Remote Control Docs

Status: raw
Confidence: likely
Task: 读取 Unreal 远程控制相关官方文档，沉淀为 wiki
Sources:
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-quick-start-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-panel-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-api-http-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-api-websocket-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-preset-api-http-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-cplusplus-api-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-protocols-for-unreal-engine

Observation:
Unreal Engine Remote Control lets external clients operate an Unreal project through a web server exposed by the editor or runtime. The system centers on Remote Control Presets, exposed properties/functions, the Remote Control Panel and Web Application, HTTP endpoints, WebSocket messages, C++ APIs, and optional protocol integrations such as DMX, MIDI, and OSC.

Verification:
Official Epic documentation pages were checked on 2026-05-08. The 5.7 documentation shell exposes page titles and descriptions directly; endpoint-level details were cross-checked against official Remote Control HTTP/WebSocket/Preset reference pages from the same Epic documentation set. Local `olw` model ingestion is unavailable on this machine, so the current Codex session generated the wiki note manually.

Boundary:
Remote Control documentation changes across Unreal versions. Always verify port numbers, plugin names, endpoint shape, runtime flags, and Beta status against the target engine version before wiring production tools. Do not expose Remote Control ports to untrusted networks.
