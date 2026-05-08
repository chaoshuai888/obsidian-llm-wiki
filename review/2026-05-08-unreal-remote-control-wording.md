# 2026-05-08 Feedback

Status: review
Related: wiki/Unreal 远程控制.md
Trigger: user_feedback

What was wrong:
The headings "HTTP API 心智模型" and "WebSocket API 心智模型" were too abstract for an operational wiki note. The phrase "直接 UObject API" was also imprecise because Epic's documentation describes `remote/object/property` and related routes as Remote Control API HTTP endpoints that access a specified UObject by object path; it does not name a separate "UObject API".

Correction:
Use "HTTP API 使用方式" and "WebSocket API 使用方式". Describe `remote/object/*` routes as "对象路径端点" or "通过 ObjectPath 访问当前内存中的 UObject", and contrast them with Remote Control Preset endpoints.

Evidence:
- User feedback on 2026-05-08.
- Official Epic Remote Control API HTTP Reference: `remote/object/property` accesses property values exposed by a specified UObject currently in memory.
- Official Epic Remote Control API WebSocket Reference: WebSocket messages include `HTTP`, `Preset.Register`, and `Preset.Unregister`.
