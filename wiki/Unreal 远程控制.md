---
confidence: likely
created: 2026-05-08
sources:
- raw/Unreal/2026-05-08-unreal-remote-control-docs.md
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-quick-start-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-panel-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-api-http-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-api-websocket-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-preset-api-http-reference-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-cplusplus-api-for-unreal-engine
- https://dev.epicgames.com/documentation/zh-cn/unreal-engine/remote-control-protocols-for-unreal-engine
status: published
tags:
- unreal-engine
- remote-control
- automation
- virtual-production
- tools
title: Unreal 远程控制
updated: '2026-05-08'
---

# Unreal 远程控制

## 摘要

Unreal Engine Remote Control 用来让外部客户端远程操作 Unreal 项目。它的核心思路是：在 Unreal 侧暴露属性或函数，外部工具通过 HTTP、WebSocket、C++ API 或协议映射来读取、写入、调用和订阅变化。

官方文档把 Remote Control 放在“远程操作虚幻引擎项目”的场景下，常见用途包括虚拟制片控制台、现场调参、外部工具链集成、Web 控制面板、MIDI/OSC/DMX 设备映射，以及不打开编辑器细节面板也能调整 Actor、材质、灯光、关卡或蓝图参数。

## 关键组成

Remote Control Preset 是推荐入口。它是一个资产，用来收集需要暴露给外部的属性和函数，并提供稳定的标签、分组、元数据和 Web UI 布局。Preset 比直接操作任意 UObject 更适合做工具接口，因为它能把项目内部路径收束成可维护的控制面。

Remote Control Panel 是编辑器里的配置面板。它负责创建和编辑 Preset，暴露属性或函数，调整分组、标签、元数据、Widget 类型、描述等信息，并可打开 Web Application。

Remote Control Web Application 是浏览器控制台。它通常用于快速搭建控制界面，面向非程序用户或现场操作人员。默认访问地址常见为 `http://127.0.0.1:7000`，实际端口和可用性要以目标引擎版本与插件配置为准。

Remote Control API 提供 HTTP 和 WebSocket 两类接口。HTTP 适合一次性查询、写入和调用；WebSocket 适合持续连接、事件订阅和低延迟同步。

Remote Control Protocols 用来把暴露字段映射到 DMX、MIDI、OSC 等外部控制协议。它适合把硬件控制台、音视频系统或现场设备接入 Unreal。

## 启用与运行

通常需要在项目插件中启用 Remote Control 相关插件。基础 API 依赖 Remote Control API；如果要使用浏览器控制台，还需要 Web Remote Control / Remote Control Web Interface 相关插件；如果要接 DMX、MIDI 或 OSC，需要对应协议插件。

典型流程是：

1. 启用插件并重启编辑器。
2. 创建 Remote Control Preset 资产。
3. 在 Remote Control Panel 中暴露属性或函数。
4. 为暴露项设置稳定、可读的 Label 和分组。
5. 用 Web Application、HTTP 或 WebSocket 验证外部访问。

默认情况下，Remote Control 主要面向本机开发环境。HTTP API 常见默认端口是 `30010`，WebSocket 常见默认端口是 `30020`，Web UI 常见默认端口是 `7000`。如果要从其他设备访问，需要检查监听地址、端口、防火墙和项目设置。

如果在 `-game` 或打包运行时启用，需要显式传入相应启动参数，例如 `-RCWebControlEnable` 或 `-RCWebInterfaceEnable`。这类运行方式更要谨慎评估安全边界。

## HTTP API 使用方式

HTTP API 可以按“访问目标”分成两类来理解：一类是通过对象路径直接访问当前内存里的 UObject，另一类是通过 Remote Control Preset 访问已经暴露好的字段和函数。这不是官方的层级划分，只是实践中选择接口时更容易理解的分类。

第一类是对象路径端点。调用方提供 `ObjectPath`，指向编辑器或运行时内存中的 UObject，通常是 Actor、Component 或 Asset，然后读取属性、写入属性或调用函数。常见端点包括：

- `GET /remote/info`：检查 Remote Control 服务信息。
- `PUT /remote/object/property`：读取或写入对象属性。
- `PUT /remote/object/call`：调用对象函数。
- `PUT /remote/object/describe`：描述对象可用属性和函数。
- `PUT /remote/batch`：批量执行多个请求。

对象路径端点适合调试、内部自动化或临时工具。它的代价是调用方必须知道对象路径、属性名、函数名以及对象当前是否已加载；场景结构、Actor 命名或资产路径变化时，外部工具也容易失效。

第二类是 Preset 端点。调用方不直接依赖任意 UObject 路径，而是通过 Remote Control Preset 中已经暴露、命名和分组的字段或函数来访问。常见用法包括：

- 查询所有 Preset。
- 获取某个 Preset 的字段、函数、分组和元数据。
- 读取或写入 Preset 暴露的属性。
- 调用 Preset 暴露的函数。
- 读取、更新或删除 Preset 元数据。

实践上，面向外部工具、现场控制台或长期维护的集成，优先设计 Preset，再通过 Preset 端点访问。对象路径端点能力很强，但更像底层访问方式；Preset 端点更适合作为稳定的对外工具契约。

## WebSocket API 使用方式

WebSocket 默认常见地址是 `ws://127.0.0.1:30020`。消息通常采用 JSON 结构，包含消息名、参数和请求 ID。

WebSocket 不是另一套独立资源模型，而是 Remote Control API 的长连接通道。它主要有两类用途：

- 通过 `HTTP` 消息类型调用已有 HTTP 路由，例如把 `/remote/object/property` 或 Preset 相关 HTTP 请求包装进 WebSocket 消息。
- 通过 `Preset.Register` / `Preset.Unregister` 订阅或取消订阅 Remote Control Preset 事件，例如字段变化、删除、重命名等。

一次性查询或写入用 HTTP 更直接；需要实时同步 UI、监听 Preset 变化、减少轮询，或让外部控制台持续刷新状态时，WebSocket 更合适。

## 暴露属性和函数

并不是所有属性都应该直接远程暴露。适合暴露的是稳定、可解释、对外部用户安全的控制项，例如灯光强度、材质参数、摄像机开关、关卡切换函数、蓝图事件入口等。

暴露项需要有清晰 Label。外部工具最好依赖稳定的 Preset 标签或字段 ID，而不是容易变化的对象路径。团队可以把 Preset 当作“远程控制接口层”：内部对象可以调整，但对外标签和行为尽量稳定。

对于蓝图或 C++ 函数，只有适合外部调用的函数才应暴露。函数参数、返回值、副作用和执行时机都要明确，避免把危险操作或编辑器内部维护函数直接开放给外部控制端。

## Web UI 与现场控制

Remote Control Web Application 的价值在于快速从 Preset 生成控制面。它适合现场调参和跨设备操作，也适合给非工程用户提供一个不需要打开 Unreal Editor 细节面板的界面。

使用时优先整理分组和命名。一个好的 Preset 应该像控制台，而不是 UObject 内部结构的投影：字段少、标签清楚、分组稳定、默认 Widget 合理，必要时补充描述。

如果 Web UI 或外部客户端刷新不及时，先确认服务端口、插件启用状态、浏览器连接状态和 Unreal 输出日志。编辑器后台节能设置也可能影响交互体验，排查时应让编辑器保持活跃。

## 协议映射

Remote Control Protocols 让 Preset 暴露项可以绑定到 DMX、MIDI 或 OSC。它更适合实时控制、舞台设备、音视频系统和硬件控制台。

这类映射要注意数值范围和单位。外部设备常用归一化值、通道值或控制器编号；Unreal 内部字段可能是浮点范围、颜色、枚举或结构体。建议把映射规则写在 Preset 元数据、项目文档或控制台说明里。

## C++ 集成

C++ API 适合做更深的编辑器工具、自动化插件或自定义桌面控制端。可以通过代码访问 Preset、暴露实体、元数据和 Remote Control 模块能力。

如果只是外部脚本或 Web 工具，HTTP/Preset API 通常更轻；如果需要和编辑器扩展、资产管理或自定义面板深度结合，再考虑 C++ API。

## 安全边界

Remote Control 本质上是在开放项目内部控制面。不要把 Remote Control 端口暴露到不可信网络，也不要在没有鉴权、隔离或防火墙约束的情况下让外部设备访问。

尤其要避免把危险函数暴露给外部：文件操作、命令执行、关卡破坏性修改、资产保存、批量删除、运行时状态重置等，都应该有额外保护或根本不暴露。

如果要在打包程序、现场局域网或多人环境使用，至少要明确：

- 哪些端口开放。
- 监听地址是否仅限本机。
- 哪些 Preset 是公开控制面。
- 哪些字段和函数允许远程写入或调用。
- 是否有网络隔离、VPN、防火墙或上层鉴权。

## Codex 使用提示

处理 Unreal Remote Control 相关任务时，优先问清目标是“配置 Preset”“写外部 HTTP/WebSocket 客户端”“做 Web 控制界面”“接 MIDI/OSC/DMX 设备”，还是“写编辑器 C++ 扩展”。不同路径需要看的文档和验证方式不同。

调试时先跑最小链路：确认插件启用，访问 `GET /remote/info`，再列出 Preset，然后读写一个无副作用的测试字段。不要一上来就调用复杂蓝图函数或批量写入场景参数。

如果用户给的是对象路径或蓝图函数名，要确认它在当前运行上下文中真实存在。编辑器、PIE、独立游戏和打包运行时的对象生命周期不同，远程调用应以实际可查询结果为准。

相关案例可参考 [[AI 操作 Unreal 编辑器案例分析]]，其中区分了 Epic Remote Control API、Python Remote Execution、自定义 C++ 插件桥和编辑器内 Agent 的不同架构。

## 验证

- 官方总览页标题为 Unreal Engine 5.7 的“虚幻引擎远程控制”，描述为“在客户端远程操作虚幻引擎项目”。
- 官方 Remote Control Panel 文档说明该面板用于创建 Remote Control Preset、暴露 Actor 属性和函数，并启动 Web Application。
- 官方 HTTP API 参考包含 `/remote/info`、`/remote/object/property`、`/remote/object/call`、`/remote/object/describe`、`/remote/batch` 等端点。
- `remote/object/property` 官方描述为访问当前内存中指定 UObject 的属性；本文使用“对象路径端点”作为解释性称呼，避免误称为独立的 “UObject API”。
- 官方 WebSocket/Preset/API/Protocols/C++ 页面作为本条目的结构来源；具体端点和运行参数在项目落地时应以目标 Unreal 版本文档和本机验证为准。
