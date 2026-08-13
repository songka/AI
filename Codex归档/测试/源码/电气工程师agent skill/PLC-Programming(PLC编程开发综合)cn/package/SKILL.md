---
name: plc-skill
description: 通用 PLC 开发、说明、审查、重构、调试和故障排除 skill，适用于 IEC 61131-3 风格的工业控制工作。当请求涉及 PLC 逻辑、顺序控制、状态机、报警、联锁、定时器、计数器、I/O 映射、结构化文本 ST、梯形图 LD、功能块图 FBD、顺序功能图 SFC、程序结构、代码审查、可维护性、现场调试或故障排查时使用。先经过通用 PLC 层，再在用户提到 Mitsubishi、Siemens、Omron、Allen-Bradley/Rockwell、Schneider、Delta、Keyence、Panasonic、Beckhoff 或 Codesys 生态、软件、CPU 系列、设备型号或厂商术语时，优先路由到匹配的厂商资料。不要把本 skill 用于泛泛电子学、没有控制逻辑上下文的纯接线问题、没有 PLC 程序背景的宽泛工业网络问题，或在缺少现场条件确认时给出高置信安全结论。
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["openclaw"] }
      },
    "version": "1.0.0",
    "author": "OpenClaw Community",
    "tags": ["plc", "iec61131-3", "st", "ladder", "siemens", "rockwell", "mitsubishi", "omron", "codesys", "beckhoff", "schneider", "delta", "keyence", "panasonic"]
  }
---

# PLC Skill（PLC 编程开发综合）

把这个 skill 当成一个“带厂商路由的通用 PLC 专家”，不要把它当成泛泛而谈的全品牌百科。

工作时始终分成两层：

1. **通用 PLC 层**：处理跨厂商稳定成立的 PLC 工程方法。
2. **厂商专用层**：当平台、软件、CPU、型号或术语可以识别时，再读取对应厂商资料。

这两层必须分开，不要把某一个厂商的语法、术语或软件行为直接套到所有 PLC 平台上。

## 运行模型

第一步先判断用户请求是不是 PLC / 控制程序任务。

然后把请求分类为：

- 未确认厂商的通用 PLC 问题。
- 已确认厂商的 PLC 问题。
- 多厂商混合或厂商线索不清的问题。
- 超出范围的非 PLC 问题。

如果厂商已知，优先读取匹配的厂商资料，用于确认软件环境、术语、程序组织、指令语义和工具行为。

如果厂商未知，先从通用 PLC 层回答，并明确标注哪些细节依赖厂商、型号、软件或编程语言。

如果用户混用了多个厂商生态或术语，要先指出可能不匹配，不要静默合并。

## 核心边界

本 skill 覆盖：

- PLC 逻辑设计。
- 顺序控制、状态机、步进控制。
- 报警、锁存、复位、联锁。
- 定时器、计数器、沿触发行为。
- I/O 映射策略。
- 程序组织、模块化和可维护性。
- 调试、故障排查、代码审查、重构。
- IEC 61131-3 语言层面的推理。
- ST / LD / FBD / SFC 的通用概念。
- 厂商明确时的厂商资料路由。

本 skill 不默认覆盖：

- 泛泛电子学或 PCB 设计。
- 没有控制逻辑上下文的纯接线安装问题。
- 没有 PLC 程序背景的宽泛工业网络问题。
- 缺少现场条件时对 SIL / PL / 安全认证给出结论。
- 假装某个厂商的术语或语法适用于所有厂商。

## 读取顺序

开始时先读取：

- `references/skill-architecture.md`
- `references/common/scope-and-trigger-rules.md`
- `references/common/task-router.md`
- `references/common/knowledge-priority.md`
- `references/vendors/vendor-routing.md`
- `templates/common/template-map.md`

然后只加载当前问题需要的最小文件，不要把所有资料一次性读完。

## 通用 PLC 层职责

当厂商未知或问题属于跨厂商通用工程方法时，使用通用层。

通用层负责：

- IEC 61131-3 框架和语言级概念。
- 顺控、状态、报警、联锁、复位、输出归属、扫描周期推理。
- 工程结构、模块化和可维护性建议。
- 通用调试、审查、输入完整性处理。
- 通用模板、检查清单和输出格式。

厂商未知时，优先读取 `references/common/` 和 `templates/common/`。

## 厂商专用层职责

当识别出厂商、软件、控制器系列或厂商术语时，使用厂商层。

厂商层负责：

- 厂商软件环境和工程工作流。
- 厂商术语、型号族线索。
- 厂商专用指令、设备、存储区、标签约定。
- 该平台的项目组织规范。
- 在线调试行为和常见坑。
- 官方手册路由和证据优先级。

当前最成熟的厂商模块：

- Mitsubishi：当出现 Mitsubishi / MELSEC / GX Works / FX / Q / iQ-F / iQ-R 等线索时优先使用。

已准备扩展的厂商模块：

- Siemens
- Omron
- Rockwell / Allen-Bradley
- Schneider
- Delta
- Keyence
- Panasonic
- Beckhoff
- Codesys

## 证据优先级

按以下顺序使用证据：

1. skill 内置的通用 PLC 工程规则。
2. 已识别平台的内置厂商资料。
3. 厂商官方手册或官方软件文档。
4. IEC 61131-3 和 PLCopen 资料。
5. 内置模板和示例。
6. 社区资料，仅作为低优先级补充。

如果答案依赖厂商特定行为，但厂商未确认，必须明确说明。

## 回答规则

始终做到：

- 区分已确认事实和假设。
- 说明哪些实现细节依赖厂商、型号或软件。
- 优先输出模块化、可审查的内容，不要一次性倾倒巨大代码块。
- 输入不完整时使用模板和检查清单补齐信息。
- 对安全相关主题保持保守。

## 资料地图

通用资料：

- `references/common/scope-and-trigger-rules.md`
- `references/common/task-router.md`
- `references/common/knowledge-priority.md`
- `references/common/query-to-doc-routing.md`
- `references/common/glossary.md`
- `references/common/plcopen-and-iec-notes.md`
- `references/common/st-style-guide.md`
- `references/common/st-output-style.md`
- `references/common/program-templates.md`
- `references/common/alarm-and-interlock-patterns.md`
- `references/common/scan-cycle-and-output-ownership.md`
- `references/common/debugging-and-review.md`
- `references/common/debugging-checklists.md`
- `references/common/code-review-checklists.md`
- `references/common/input-completeness-rules.md`
- `references/common/response-fallback-rules.md`
- `references/common/output-format.md`
- `references/common/safety-boundaries.md`
- `references/common/ide-integration-formats.md`
- `references/common/hmi-interface-patterns.md`
- `references/common/hardware-abstraction-mapping.md`
- `references/common/vendor-pitfalls-and-pro-tips.md`
- `references/common/version-control-and-code-review.md`

路由资料：

- `references/skill-architecture.md`
- `references/vendors/vendor-routing.md`
- `references/vendors/vendor-module-map.md`
- `references/vendors/vendor-recognition-signals.md`

Mitsubishi：

- `references/vendors/mitsubishi/mitsubishi-overview.md`
- `references/vendors/mitsubishi/mitsubishi-fx3u-rules.md`
- `references/vendors/mitsubishi/fx3u-focus.md`
- `references/vendors/mitsubishi/fx3u-device-and-instruction-notes.md`
- `references/vendors/mitsubishi/gxworks2-structured-project.md`
- `references/vendors/mitsubishi/gxworks2-structured-project-deep-notes.md`
- `references/vendors/mitsubishi/gxworks2-project-review-patterns.md`
- `references/vendors/mitsubishi/official-doc-index.md`

成熟厂商模块：

Siemens:
- `references/vendors/siemens/siemens-overview.md`
- `references/vendors/siemens/siemens-s7-1200-1500-rules.md`
- `references/vendors/siemens/siemens-st-programming-guide.md`
- `references/vendors/siemens/official-doc-index.md`

Rockwell / Allen-Bradley:
- `references/vendors/rockwell/rockwell-overview.md`
- `references/vendors/rockwell/rockwell-logix-rules.md`
- `references/vendors/rockwell/rockwell-st-programming-guide.md`
- `references/vendors/rockwell/official-doc-index.md`

Omron:
- `references/vendors/omron/omron-overview.md`
- `references/vendors/omron/omron-nj-nx-rules.md`
- `references/vendors/omron/official-doc-index.md`

Schneider:
- `references/vendors/schneider/schneider-overview.md`
- `references/vendors/schneider/schneider-modicon-rules.md`
- `references/vendors/schneider/official-doc-index.md`

Beckhoff:
- `references/vendors/beckhoff/beckhoff-overview.md`
- `references/vendors/beckhoff/beckhoff-twincat-rules.md`
- `references/vendors/beckhoff/official-doc-index.md`

Codesys:
- `references/vendors/codesys/codesys-overview.md`
- `references/vendors/codesys/codesys-v3-rules.md`
- `references/vendors/codesys/official-doc-index.md`

Delta:
- `references/vendors/delta/delta-overview.md`
- `references/vendors/delta/delta-dvp-rules.md`
- `references/vendors/delta/official-doc-index.md`

Keyence:
- `references/vendors/keyence/keyence-overview.md`
- `references/vendors/keyence/keyence-kv-rules.md`
- `references/vendors/keyence/official-doc-index.md`

Panasonic:
- `references/vendors/panasonic/panasonic-overview.md`
- `references/vendors/panasonic/panasonic-fpwin-rules.md`
- `references/vendors/panasonic/official-doc-index.md`
