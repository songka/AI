import fs from "node:fs/promises";
import path from "node:path";

const root = "C:/Users/lfaf-test/Documents/测试/电气工程师agent skill";
const eeDir = path.join(root, "EE-AI-Toolkit(电气工程师AI工具包)", "package");
const plcDir = path.join(root, "PLC-Programming(PLC编程开发综合)", "package");

const markerStart = "<!-- 中文导读开始 -->";
const markerEnd = "<!-- 中文导读结束 -->";

const eeSkill = `---
name: ee-ai-toolkit
description: 电气工程师 AI 工具包。用于 AI in Electrical Engineering、电气工程 AI、prompt engineering、power systems、smart grids、electrical calculations、design automation、data visualization、optimization、career toolkit、以及 100 个电气工程 Python 示例脚本相关问题。
compatibility: 需要 python3；可选使用 numpy、pandas、matplotlib、scikit-learn 运行部分附录示例。
metadata: {"openclaw":{"requires":{"bins":["python3"]}}}
---

# EE AI Toolkit（电气工程师 AI 工具包）

这个 skill 来自电气工程 AI 课程资料，面向电气工程师日常的计算、设计、分析、自动化、优化、数据可视化、提示词工程和职业发展任务。

使用这个 skill 时，要把它理解成一个“电气工程师 AI 工具箱”：

- \`references/\` 是资料库，用来查课程结构、知识点、提示词和脚本目录。
- \`assets/python-scripts/\` 是 Python 示例脚本库，用来复用或改造已有工程脚本。
- \`scripts/search_ee_ai.py\` 是资料检索工具，资料较大时先用它定位相关内容。

## 触发场景

当用户的问题涉及以下内容时，优先使用本 skill：

- 电气工程中的 AI 应用、提示词工程、AI 工具使用方法。
- 电力系统、智能电网、负载预测、故障分类、电能质量、优化决策。
- 电气计算，例如欧姆定律、电压降、三相功率、变压器、电缆选型、功率因数补偿。
- 数据处理和可视化，例如 CSV/Excel 数据读取、负载曲线、电压趋势、谐波图、异常检测。
- 需要复用 100 个电气工程 Python 示例脚本的任务。
- 电气工程职业工具，例如简历关键词、技能差距、面试题、项目作品集等。

## 资料读取顺序

激活本 skill 后，不要一次性读取全部资料。请根据问题类型读取最小必要资料：

- 课程结构、资料来源、主题路由：读取 \`references/course-index.md\`。
- 快速回答、复习或概念梳理：读取 \`references/condensed-lessons.md\`。
- 需要接近原文、练习、示例流程或完整上下文：读取 \`references/source-digest.md\`。
- 提示词、提示词改写、提示词模板：读取 \`references/prompt-library.md\`。
- Python 示例脚本、脚本编号、脚本用途：读取 \`references/python-script-catalog.md\`，再使用 \`assets/python-scripts/\` 中对应脚本。
- 需要核对原始 HTML 课程资料时：使用 \`assets/source-html/\`，或解压 \`assets/source-html.tar.gz\`。

资料较大时，先用检索脚本定位，再读取相关引用文件：

\`\`\`bash
python3 {baseDir}/scripts/search_ee_ai.py --query "load forecasting"
\`\`\`

## 输出规则

生成或修改工程答案时，必须保持以下约束：

- 明确单位、输入假设、公式、计算步骤和验证方法。
- AI 生成的设计、保护、配电、并网、优化和故障分析结果只能作为工程草案或教学示例。
- 对安全关键或合规相关电气工程问题，必须提醒用户结合适用标准、仿真工具、现场数据和有资质工程审查进行验证。
- 需要代码时，优先复用或改造 \`assets/python-scripts/\` 中最接近的脚本，不要从零编造。
- 用户用中文提问时，默认用中文回答；必要的英文术语、文件名、脚本名和变量名保持原样。
`;

const plcSkill = `---
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

- \`references/skill-architecture.md\`
- \`references/common/scope-and-trigger-rules.md\`
- \`references/common/task-router.md\`
- \`references/common/knowledge-priority.md\`
- \`references/vendors/vendor-routing.md\`
- \`templates/common/template-map.md\`

然后只加载当前问题需要的最小文件，不要把所有资料一次性读完。

## 通用 PLC 层职责

当厂商未知或问题属于跨厂商通用工程方法时，使用通用层。

通用层负责：

- IEC 61131-3 框架和语言级概念。
- 顺控、状态、报警、联锁、复位、输出归属、扫描周期推理。
- 工程结构、模块化和可维护性建议。
- 通用调试、审查、输入完整性处理。
- 通用模板、检查清单和输出格式。

厂商未知时，优先读取 \`references/common/\` 和 \`templates/common/\`。

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

- \`references/common/scope-and-trigger-rules.md\`
- \`references/common/task-router.md\`
- \`references/common/knowledge-priority.md\`
- \`references/common/query-to-doc-routing.md\`
- \`references/common/glossary.md\`
- \`references/common/plcopen-and-iec-notes.md\`
- \`references/common/st-style-guide.md\`
- \`references/common/st-output-style.md\`
- \`references/common/program-templates.md\`
- \`references/common/alarm-and-interlock-patterns.md\`
- \`references/common/scan-cycle-and-output-ownership.md\`
- \`references/common/debugging-and-review.md\`
- \`references/common/debugging-checklists.md\`
- \`references/common/code-review-checklists.md\`
- \`references/common/input-completeness-rules.md\`
- \`references/common/response-fallback-rules.md\`
- \`references/common/output-format.md\`
- \`references/common/safety-boundaries.md\`
- \`references/common/ide-integration-formats.md\`
- \`references/common/hmi-interface-patterns.md\`
- \`references/common/hardware-abstraction-mapping.md\`
- \`references/common/vendor-pitfalls-and-pro-tips.md\`
- \`references/common/version-control-and-code-review.md\`

路由资料：

- \`references/skill-architecture.md\`
- \`references/vendors/vendor-routing.md\`
- \`references/vendors/vendor-module-map.md\`
- \`references/vendors/vendor-recognition-signals.md\`

Mitsubishi：

- \`references/vendors/mitsubishi/mitsubishi-overview.md\`
- \`references/vendors/mitsubishi/mitsubishi-fx3u-rules.md\`
- \`references/vendors/mitsubishi/fx3u-focus.md\`
- \`references/vendors/mitsubishi/fx3u-device-and-instruction-notes.md\`
- \`references/vendors/mitsubishi/gxworks2-structured-project.md\`
- \`references/vendors/mitsubishi/gxworks2-structured-project-deep-notes.md\`
- \`references/vendors/mitsubishi/gxworks2-project-review-patterns.md\`
- \`references/vendors/mitsubishi/official-doc-index.md\`

成熟厂商模块：

Siemens:
- \`references/vendors/siemens/siemens-overview.md\`
- \`references/vendors/siemens/siemens-s7-1200-1500-rules.md\`
- \`references/vendors/siemens/siemens-st-programming-guide.md\`
- \`references/vendors/siemens/official-doc-index.md\`

Rockwell / Allen-Bradley:
- \`references/vendors/rockwell/rockwell-overview.md\`
- \`references/vendors/rockwell/rockwell-logix-rules.md\`
- \`references/vendors/rockwell/rockwell-st-programming-guide.md\`
- \`references/vendors/rockwell/official-doc-index.md\`

Omron:
- \`references/vendors/omron/omron-overview.md\`
- \`references/vendors/omron/omron-nj-nx-rules.md\`
- \`references/vendors/omron/official-doc-index.md\`

Schneider:
- \`references/vendors/schneider/schneider-overview.md\`
- \`references/vendors/schneider/schneider-modicon-rules.md\`
- \`references/vendors/schneider/official-doc-index.md\`

Beckhoff:
- \`references/vendors/beckhoff/beckhoff-overview.md\`
- \`references/vendors/beckhoff/beckhoff-twincat-rules.md\`
- \`references/vendors/beckhoff/official-doc-index.md\`

Codesys:
- \`references/vendors/codesys/codesys-overview.md\`
- \`references/vendors/codesys/codesys-v3-rules.md\`
- \`references/vendors/codesys/official-doc-index.md\`

Delta:
- \`references/vendors/delta/delta-overview.md\`
- \`references/vendors/delta/delta-dvp-rules.md\`
- \`references/vendors/delta/official-doc-index.md\`

Keyence:
- \`references/vendors/keyence/keyence-overview.md\`
- \`references/vendors/keyence/keyence-kv-rules.md\`
- \`references/vendors/keyence/official-doc-index.md\`

Panasonic:
- \`references/vendors/panasonic/panasonic-overview.md\`
- \`references/vendors/panasonic/panasonic-fpwin-rules.md\`
- \`references/vendors/panasonic/official-doc-index.md\`
`;

function summaryFor(filePath, rootDir) {
  const rel = path.relative(rootDir, filePath).replaceAll("\\", "/");
  const name = path.basename(rel);
  if (rel === "SKILL.md") return null;
  if (rel === "README.md") return "本文件是英文 README 的中文导读版补充，用于快速了解 skill 的用途、安装方式和目录结构。原英文内容保留在下方，避免破坏原始说明。";
  if (rel === "INSTALL.md") return "本文件说明如何安装和启用该 skill。中文导读用于快速定位安装步骤，原命令和路径保持不变。";
  if (rel === "CONTRIBUTING.md") return "本文件说明如何维护、扩展和贡献该 skill。中文导读帮助理解贡献规则，原流程保留。";
  if (rel === "SHOWCASE.md") return "本文件展示 skill 的典型能力和使用场景。中文导读帮助课堂讲解，原示例保留。";
  if (rel.startsWith("evals/")) return "本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。";
  if (rel.startsWith("examples/")) return "本文件属于 examples/（通用示例），用于展示典型输入、期望输出和正确/错误触发方式。";
  if (rel.startsWith("templates/")) return "本文件属于 templates/（输出模板），用于约束 AI 的交付格式，让代码、报告、检查清单或调试步骤稳定可复用。";
  if (rel.includes("references/common/")) return "本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。";
  if (rel.includes("references/vendors/")) return "本文件属于 references/vendors/（厂商资料），记录具体 PLC 厂商的软件环境、术语、型号线索、指令规则或官方文档入口。";
  if (rel.startsWith("references/")) {
    if (name.includes("course-index")) return "本文件是课程索引，说明资料来源、主题路由和不同问题应该读取哪些资料。";
    if (name.includes("condensed-lessons")) return "本文件是精简知识点，用于快速复习和回答概念类问题。";
    if (name.includes("prompt-library")) return "本文件是提示词库，用于提示词设计、改写和模板复用。";
    if (name.includes("python-script-catalog")) return "本文件是 Python 脚本目录，用于查找脚本编号、用途和对应脚本文件。";
    if (name.includes("source-digest")) return "本文件是原始课程资料摘要，内容较长。使用时应先通过索引或检索脚本定位相关段落。";
    return "本文件属于 references/（资料库），用于提供 skill 回答问题时需要查阅的规则、索引、术语或资料地图。";
  }
  return "本文件已加入中文导读，便于理解其用途；原始内容保留在下方以保持兼容。";
}

function removeExistingGuide(text) {
  const start = text.indexOf(markerStart);
  const end = text.indexOf(markerEnd);
  if (start !== -1 && end !== -1 && end > start) {
    return text.slice(0, start) + text.slice(end + markerEnd.length).replace(/^\s*\n/, "");
  }
  return text;
}

function insertGuide(text, guide) {
  const block = `${markerStart}\n\n## 中文导读\n\n${guide}\n\n> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。\n\n${markerEnd}\n\n`;
  const cleaned = removeExistingGuide(text);
  if (cleaned.startsWith("---\n")) {
    const end = cleaned.indexOf("\n---\n", 4);
    if (end !== -1) {
      return cleaned.slice(0, end + 5) + "\n" + block + cleaned.slice(end + 5).replace(/^\s*\n/, "");
    }
  }
  return block + cleaned.replace(/^\s*\n/, "");
}

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await walk(full));
    else files.push(full);
  }
  return files;
}

async function localizePackage(dir, skillText) {
  await fs.writeFile(path.join(dir, "SKILL.md"), skillText, "utf8");
  const files = (await walk(dir)).filter((file) => file.toLowerCase().endsWith(".md"));
  for (const file of files) {
    if (path.basename(file) === "SKILL.md") continue;
    const guide = summaryFor(file, dir);
    if (!guide) continue;
    const text = await fs.readFile(file, "utf8");
    await fs.writeFile(file, insertGuide(text, guide), "utf8");
  }
}

await localizePackage(eeDir, eeSkill);
await localizePackage(plcDir, plcSkill);
console.log("localized", eeDir, plcDir);
