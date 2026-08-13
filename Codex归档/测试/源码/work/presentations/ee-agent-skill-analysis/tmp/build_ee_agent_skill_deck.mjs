import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "C:/Users/lfaf-test/Documents/测试/outputs/电气工程师Agent-Skill分析与提问方法.pptx";
const PREVIEW_DIR = "C:/Users/lfaf-test/Documents/测试/work/presentations/ee-agent-skill-analysis/tmp/preview";

const W = 1280;
const H = 720;
const C = {
  ink: "#111111",
  muted: "#5B5B5B",
  rule: "#B8BCC4",
  panel: "#EDEDED",
  soft: "#F7F7F7",
  accent: "#FF6B35",
  blue: "#1F6FEB",
  green: "#2E8B57",
  amber: "#B7791F",
  red: "#C2410C",
  white: "#FFFFFF",
};
const FONT = "Microsoft YaHei";

function addText(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? "none",
    line: { style: "solid", fill: opts.line ?? "none", width: opts.lineWidth ?? 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    typeface: FONT,
    alignment: opts.align ?? "left",
  };
  return shape;
}

function rect(slide, x, y, w, h, opts = {}) {
  return slide.shapes.add({
    geometry: opts.geometry ?? "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? C.panel,
    line: { style: "solid", fill: opts.line ?? "none", width: opts.lineWidth ?? 0 },
  });
}

function title(slide, kicker, headline, sub = "") {
  addText(slide, kicker, 42, 36, 420, 30, { size: 15, bold: true, color: C.muted });
  addText(slide, headline, 42, 80, 900, 88, { size: 44, bold: true });
  if (sub) addText(slide, sub, 42, 168, 920, 52, { size: 20, color: C.muted });
  rect(slide, 42, 214, 1196, 1.5, { fill: C.rule });
}

function footer(slide, n) {
  addText(slide, "电气工程师 Agent Skill 分析与提问方法", 42, 666, 620, 24, { size: 13, color: C.muted });
  addText(slide, String(n).padStart(2, "0"), 1185, 660, 52, 28, { size: 15, bold: true, color: C.muted, align: "right" });
}

function bulletList(slide, items, x, y, w, opts = {}) {
  let cy = y;
  for (const item of items) {
    rect(slide, x, cy + 8, 8, 8, { fill: opts.dot ?? C.accent });
    addText(slide, item, x + 20, cy, w - 20, opts.lineH ?? 48, { size: opts.size ?? 19, color: opts.color ?? C.ink });
    cy += opts.step ?? 50;
  }
}

function labeledBox(slide, label, body, x, y, w, h, opts = {}) {
  rect(slide, x, y, w, h, { fill: opts.fill ?? C.soft, line: opts.line ?? C.rule, lineWidth: 1 });
  addText(slide, label, x + 18, y + 16, w - 36, 28, { size: opts.labelSize ?? 19, bold: true, color: opts.labelColor ?? C.ink });
  addText(slide, body, x + 18, y + 54, w - 36, h - 64, { size: opts.bodySize ?? 16, color: opts.bodyColor ?? C.muted });
}

function arrow(slide, x, y, w, h, color = C.ink) {
  rect(slide, x, y, w, h, { geometry: "rightArrow", fill: color, line: "none" });
}

function codeText(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? "#151515",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 15,
    color: opts.color ?? "#F6F6F6",
    typeface: "Consolas",
  };
  return shape;
}

const deck = Presentation.create({ slideSize: { width: W, height: H } });

// 1
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  addText(slide, "电气工程师 Agent Skill", 42, 44, 520, 42, { size: 18, bold: true, color: C.muted });
  addText(slide, "从文件夹看懂 Skill，\n再学会问 AI 生成它", 42, 160, 780, 190, { size: 56, bold: true });
  addText(slide, "基于“电气工程师agent skill”目录：31 个技能包，重点拆解 EE-AI-Toolkit 与 PLC-Programming。", 46, 398, 820, 64, { size: 22, color: C.muted });
  labeledBox(slide, "本 PPT 解决三个问题", "1. 现有 skill 覆盖了哪些工程场景\n2. 一个可复用 skill 需要哪些要素\n3. 如何向 AI 提问，让它写出同类 skill 包", 880, 132, 316, 328, { fill: C.panel, bodySize: 18 });
  rect(slide, 42, 596, 710, 2, { fill: C.ink });
  addText(slide, "输出物：结构图、动作流程图、可复制提示词", 42, 616, 620, 32, { size: 18, color: C.muted });
  footer(slide, 1);
}

// 2
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "目录扫描结论", "这些 skill 覆盖了电气工程的“算、画、编、查、管”");
  const cats = [
    ["工程计算", "UPS/逆变器、太阳能负载、支路 Pi 模型、潮流数据、电气 AI 工具包"],
    ["自动化与控制", "PLC 编程、INVT、Honeywell、ESP32、RDK GPIO、智能家居"],
    ["设计与文档", "CAD 编辑、CAD 脚本、DWG-DXF、格式导出、流程图、测试报告"],
    ["合规与项目", "中国标准合规、投标合规、项目调研、需求分析、资料归档"],
    ["仿真与算法", "MATLAB 基础、MATLAB 桥接、论文复现、预测性维护"],
  ];
  let x = 42;
  for (const [name, body] of cats) {
    labeledBox(slide, name, body, x, 260, 218, 250, { fill: C.soft, bodySize: 16, labelColor: C.accent });
    x += 238;
  }
  addText(slide, "看法：这批包不是单一知识库，而是“岗位动作库”。每个 skill 都试图把一个高频任务变成可触发、可复用、可交付的 AI 工作流程。", 72, 550, 1060, 58, { size: 20, color: C.ink });
  footer(slide, 2);
}

// 3
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "好的 skill 不是资料堆", "它至少需要 8 个关键要素");
  const rows = [
    ["1. 名称与触发描述", "告诉 AI 何时启用，何时不要启用"],
    ["2. 适用边界", "覆盖范围、排除范围、安全边界"],
    ["3. 资料地图", "先读什么、按什么问题读取哪份引用"],
    ["4. 工作流程", "分类、检索、计算、生成、验证、交付"],
    ["5. 模板与示例", "让输出稳定，不靠临场发挥"],
    ["6. 工具与脚本", "把可执行动作沉淀成 assets/scripts"],
    ["7. 输出格式", "报告、表格、代码、清单、图纸说明等"],
    ["8. 评测与安装", "evals、README、INSTALL、版本元数据"],
  ];
  let y = 250;
  for (let i = 0; i < rows.length; i++) {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const bx = 42 + col * 598;
    const by = 250 + row * 88;
    rect(slide, bx, by, 560, 68, { fill: i < 4 ? C.soft : C.panel, line: C.rule, lineWidth: 1 });
    addText(slide, rows[i][0], bx + 16, by + 12, 210, 24, { size: 18, bold: true, color: C.ink });
    addText(slide, rows[i][1], bx + 16, by + 38, 520, 22, { size: 15, color: C.muted });
  }
  footer(slide, 3);
}

// 4
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "最小可用 skill 包", "文件结构围绕“入口、资料、动作、验证”组织");
  const tree = `skill-name/
├─ SKILL.md
│  触发规则、边界、读取顺序
├─ README / INSTALL
│  安装和使用说明
├─ references/
│  规则、知识、路由、资料索引
├─ templates/
│  输出模板、代码骨架、检查清单
├─ assets/
│  示例数据、脚本、源资料、素材
├─ scripts/
│  检索、计算、转换、生成工具
└─ evals/
   触发、生成、审查、异常输入案例`;
  codeText(slide, tree, 60, 248, 510, 356, { size: 16 });
  const steps = [
    ["入口", "SKILL.md 决定是否触发"],
    ["资料", "references 提供可信上下文"],
    ["动作", "scripts/assets 执行可重复任务"],
    ["交付", "templates 约束输出形态"],
    ["验证", "evals 检查是否稳定"],
  ];
  let y = 262;
  for (const [a, b] of steps) {
    labeledBox(slide, a, b, 665, y, 460, 48, { fill: C.soft, labelSize: 18, bodySize: 15 });
    y += 62;
  }
  addText(slide, "判断标准：AI 不需要“猜流程”，它能根据入口说明找到资料、调用动作，并按模板交付。", 665, 580, 500, 44, { size: 18, color: C.accent, bold: true });
  footer(slide, 4);
}

// 5
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "EE-AI-Toolkit 是工具库型 skill", "它把课程资料、提示词库和 100 个 Python 示例脚本打包");
  const tree = `EE-AI-Toolkit/
├─ SKILL.md
├─ references/
│  ├─ course-index.md
│  ├─ condensed-lessons.md
│  ├─ prompt-library.md
│  ├─ python-script-catalog.md
│  └─ source-digest.md
├─ assets/python-scripts/
│  ├─ script_001_power_calculator.py
│  ├─ ...
│  └─ script_100_engineering_decision_support_system.py
└─ scripts/search_ee_ai.py`;
  codeText(slide, tree, 52, 250, 552, 350, { size: 16 });
  labeledBox(slide, "适合回答什么", "电气工程 AI、提示工程、电力系统、智能电网、电气计算、设计自动化、数据可视化、优化、职业工具包。", 660, 248, 500, 104, { fill: C.soft, bodySize: 14, labelColor: C.blue });
  labeledBox(slide, "关键机制", "先按问题类型读最小资料；资料大时用 search_ee_ai.py 检索；需要代码时优先复用 assets/python-scripts 中最接近的脚本。", 660, 370, 500, 116, { fill: C.soft, bodySize: 14, labelColor: C.blue });
  labeledBox(slide, "安全约束", "工程计算必须说明单位、假设、公式、验证方法；安全或合规相关结果只能作为草案，需标准、仿真、现场数据和资质审查验证。", 660, 504, 500, 112, { fill: C.soft, bodySize: 14, labelColor: C.red });
  footer(slide, 5);
}

// 6
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "EE-AI-Toolkit 的动作流程", "先路由，再检索，再复用脚本，最后给出工程化输出");
  const nodes = [
    ["用户问题", "计算、提示词、图表或工程报告"],
    ["SKILL.md 分类", "判断任务属于哪一类"],
    ["读取最小资料", "索引、提示库、脚本目录"],
    ["必要时检索", "用 search 工具定位资料"],
    ["复用脚本", "选择最接近的脚本"],
    ["输出并验证", "单位、假设、公式、代码"],
  ];
  let x = 50;
  for (let i = 0; i < nodes.length; i++) {
    const [a, b] = nodes[i];
    labeledBox(slide, a, b, x, i % 2 === 0 ? 270 : 390, 168, 104, { fill: i % 2 === 0 ? C.soft : C.panel, bodySize: 13, labelSize: 17 });
    if (i < nodes.length - 1) arrow(slide, x + 172, i % 2 === 0 ? 314 : 434, 54, 22, C.accent);
    x += 198;
  }
  addText(slide, "这类 skill 的价值：把“知识课程 + 工程脚本 + 提示词模板”变成一个可搜索、可复用、可验证的个人工具箱。", 76, 550, 1040, 48, { size: 22, bold: true });
  footer(slide, 6);
}

// 7
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "PLC-Programming 是专家路由型 skill", "它先判断控制任务，再区分通用层和厂商层");
  const tree = `PLC-Programming/package/
├─ SKILL.md
├─ references/
│  ├─ skill-architecture.md
│  ├─ common/
│  │  ├─ task-router.md
│  │  ├─ safety-boundaries.md
│  │  ├─ debugging-checklists.md
│  │  └─ code-review-checklists.md
│  └─ vendors/
│     ├─ vendor-routing.md
│     ├─ mitsubishi/
│     ├─ siemens/
│     ├─ rockwell/
│     └─ omron / schneider / delta / ...
├─ templates/common/
├─ examples/common/
└─ evals/`;
  codeText(slide, tree, 52, 240, 550, 382, { size: 15 });
  labeledBox(slide, "通用 PLC 层", "IEC 61131-3、顺控、状态机、报警/联锁、扫描周期、输出归属、调试、审查、模板。", 660, 246, 500, 106, { fill: C.soft, bodySize: 14, labelColor: C.green });
  labeledBox(slide, "厂商专用层", "三菱、西门子、欧姆龙、罗克韦尔、施耐德、台达、基恩士、松下、倍福、Codesys 等。", 660, 370, 500, 106, { fill: C.soft, bodySize: 14, labelColor: C.amber });
  labeledBox(slide, "边界意识", "不知道厂商时，不冒充具体语法；混合多个厂商术语时，先指出可能不匹配。", 660, 494, 500, 96, { fill: C.soft, bodySize: 14, labelColor: C.red });
  footer(slide, 7);
}

// 8
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "PLC-Programming 的动作流程", "它像一个有路由表的 PLC 专家，而不是泛泛百科");
  const topY = 282;
  const labels = [
    ["确认范围", "是否是 PLC/控制程序任务"],
    ["识别厂商", "软件、CPU、术语、指令线索"],
    ["选择资料层", "通用层或对应厂商层"],
    ["执行任务", "生成、解释、审查、调试、重构"],
    ["保守交付", "标注假设、厂商依赖和安全边界"],
  ];
  for (let i = 0; i < labels.length; i++) {
    labeledBox(slide, labels[i][0], labels[i][1], 62 + i * 236, topY, 190, 112, { fill: i === 2 ? C.panel : C.soft, bodySize: 14, labelSize: 18 });
    if (i < labels.length - 1) arrow(slide, 62 + i * 236 + 194, topY + 44, 44, 22, C.ink);
  }
  rect(slide, 190, 470, 360, 76, { fill: "#EAF4EE", line: C.green, lineWidth: 1 });
  addText(slide, "无厂商线索：用 common 层，并说明哪些细节依赖型号/软件", 210, 490, 320, 34, { size: 17, color: C.green, bold: true });
  rect(slide, 650, 470, 360, 76, { fill: "#FFF4E5", line: C.amber, lineWidth: 1 });
  addText(slide, "有厂商线索：读取 vendors/<vendor>，避免把一家语法套到另一家", 670, 490, 320, 34, { size: 17, color: C.amber, bold: true });
  footer(slide, 8);
}

// 9
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "向 AI 提问生成 skill", "把“我要一个 skill”改成“我要一个可安装的工程流程包”");
  const prompt = `请为【电气工程师】创建一个 Codex/Claude 可用的 skill 包，主题是【填写任务领域】。

要求：
1. 生成完整文件结构：SKILL.md、README、references、templates、assets、scripts、evals。
2. SKILL.md 必须包含：name、description、触发词、适用范围、排除范围、安全边界、读取资料顺序、输出规则。
3. references 要拆成：任务路由、知识规则、术语表、检查清单、官方资料索引。
4. templates 要包含至少 3 个可复用输出模板。
5. scripts 如有必要，提供可运行脚本，并说明输入、输出、依赖。
6. evals 要覆盖：正确触发、错误触发、输入不完整、生成质量、审查质量。
7. 最后输出安装步骤、示例提问、目录树和维护建议。

我的业务背景：
- 使用场景：【例如 PLC 调试 / 电气计算 / 图纸归档】
- 常见输入：【文件、表格、型号、现场描述】
- 期望输出：【报告、代码、清单、图表、脚本】
- 安全/合规限制：【标准、人工复核、现场验证】`;
  codeText(slide, prompt, 62, 236, 1120, 382, { size: 15, fill: "#101010" });
  footer(slide, 9);
}

// 10
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "两个例子的生成提问", "工具库型和专家路由型，提问重点不同");
  labeledBox(slide, "生成 EE-AI-Toolkit 类工具库", "请创建一个“电气工程师 AI 工具包”skill。它要整合课程资料、提示词库、100 个 Python 工程脚本、检索脚本和安全验证规则。请按主题路由资料：电气计算、电力系统、智能电网、数据可视化、优化、职业工具。需要输出 SKILL.md、references、assets/python-scripts、scripts/search 工具、evals 和安装说明。", 56, 244, 548, 236, { fill: C.soft, bodySize: 17, labelColor: C.blue });
  labeledBox(slide, "生成 PLC-Programming 类专家路由", "请创建一个“PLC 编程开发综合”skill。它要支持 IEC 61131-3 通用层和厂商专用层：三菱、西门子、欧姆龙、罗克韦尔、施耐德、台达、基恩士、松下、倍福、Codesys。要求先判断是否 PLC 任务，再识别厂商，再读取 common 或 vendors 资料。输出模板包含顺控、状态机、报警联锁、输出归属审查和调试清单。", 674, 244, 548, 236, { fill: C.soft, bodySize: 17, labelColor: C.amber });
  addText(slide, "一句话记忆：工具库型问“资料和脚本怎么组织”；专家路由型问“边界、分层和判断路径怎么组织”。", 80, 548, 1040, 48, { size: 25, bold: true });
  footer(slide, 10);
}

await fs.mkdir(PREVIEW_DIR, { recursive: true });
await fs.mkdir(path.dirname(OUT), { recursive: true });

for (const [index, slide] of deck.slides.items.entries()) {
  const png = await deck.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(PREVIEW_DIR, `slide-${String(index + 1).padStart(2, "0")}.png`), Buffer.from(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(PREVIEW_DIR, `slide-${String(index + 1).padStart(2, "0")}.layout.json`), await layout.text());
}
const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(PREVIEW_DIR, "montage.webp"), Buffer.from(await montage.arrayBuffer()));

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(OUT);
console.log(OUT);
