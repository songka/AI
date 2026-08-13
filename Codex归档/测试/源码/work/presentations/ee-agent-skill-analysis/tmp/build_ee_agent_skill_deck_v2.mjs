import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/lfaf-test/Documents/测试";
const OUT = `${ROOT}/outputs/电气工程师Agent-Skill分析与提问方法.pptx`;
const PREVIEW_DIR = `${ROOT}/work/presentations/ee-agent-skill-analysis/tmp/preview-v2`;

const W = 1280;
const H = 720;
const FONT = "Microsoft YaHei";
const C = {
  ink: "#111111",
  muted: "#5B5B5B",
  rule: "#C7CBD1",
  panel: "#EEEEEE",
  soft: "#F8F8F8",
  accent: "#FF6B35",
  blue: "#1F6FEB",
  green: "#238636",
  amber: "#B7791F",
  red: "#C2410C",
  white: "#FFFFFF",
};

function addText(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? "none",
    line: { style: "solid", fill: opts.line ?? "none", width: opts.lineWidth ?? 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 20,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    typeface: opts.face ?? FONT,
    alignment: opts.align ?? "left",
  };
  return shape;
}

function rect(slide, x, y, w, h, opts = {}) {
  return slide.shapes.add({
    geometry: opts.geometry ?? "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? C.soft,
    line: { style: "solid", fill: opts.line ?? C.rule, width: opts.lineWidth ?? 1 },
  });
}

function title(slide, kicker, headline, sub = "") {
  addText(slide, kicker, 42, 34, 620, 30, { size: 15, bold: true, color: C.muted });
  addText(slide, headline, 42, 80, 1040, 96, { size: 43, bold: true });
  if (sub) addText(slide, sub, 42, 174, 930, 42, { size: 20, color: C.muted });
  rect(slide, 42, 216, 1196, 1.5, { fill: C.rule, line: "none", lineWidth: 0 });
}

function footer(slide, n) {
  addText(slide, "电气工程师 Agent Skill 分析与提问方法", 42, 666, 620, 24, { size: 13, color: C.muted });
  addText(slide, String(n).padStart(2, "0"), 1186, 660, 52, 28, { size: 15, bold: true, color: C.muted, align: "right" });
}

function card(slide, label, body, x, y, w, h, opts = {}) {
  rect(slide, x, y, w, h, { fill: opts.fill ?? C.soft, line: opts.line ?? C.rule, lineWidth: 1 });
  addText(slide, label, x + 18, y + 16, w - 36, 28, {
    size: opts.labelSize ?? 19,
    bold: true,
    color: opts.labelColor ?? C.ink,
  });
  addText(slide, body, x + 18, y + 54, w - 36, h - 64, {
    size: opts.bodySize ?? 15,
    color: opts.bodyColor ?? C.muted,
  });
}

function codeBox(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? "#151515",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 14,
    color: opts.color ?? "#F7F7F7",
    typeface: "Consolas",
  };
  return shape;
}

function arrow(slide, x, y, w = 42, h = 20, color = C.accent) {
  rect(slide, x, y, w, h, { geometry: "rightArrow", fill: color, line: "none", lineWidth: 0 });
}

function twoElementSlide(deck, pageNo, kicker, headline, left, right) {
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, kicker, headline);
  card(slide, left.title, left.body, 52, 252, 546, 308, { labelColor: left.color, bodySize: 18 });
  card(slide, right.title, right.body, 682, 252, 546, 308, { labelColor: right.color, bodySize: 18 });
  addText(slide, left.example, 82, 585, 480, 42, { size: 19, bold: true, color: left.color });
  addText(slide, right.example, 712, 585, 480, 42, { size: 19, bold: true, color: right.color });
  footer(slide, pageNo);
}

const deck = Presentation.create({ slideSize: { width: W, height: H } });

// 1
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  addText(slide, "电气工程师 Agent Skill", 42, 44, 620, 40, { size: 18, bold: true, color: C.muted });
  addText(slide, "Skill 要素拆解：\n从会用，到会让 AI 写出来", 42, 152, 860, 190, { size: 54, bold: true });
  addText(slide, "重点不再盘点现有 skill 覆盖了什么，而是讲清楚一个 skill 为什么能稳定工作、怎样分类、怎样组织文件、怎样向 AI 提问生成。", 46, 394, 900, 70, { size: 22, color: C.muted });
  card(slide, "这版讲法", "先分类型\n再拆要素\n每个要素配工程例子\n最后给可复制提问", 900, 140, 300, 322, { fill: C.panel, bodySize: 20, labelColor: C.accent });
  rect(slide, 42, 598, 710, 2, { fill: C.ink, line: "none" });
  addText(slide, "适合培训、内部分享、让同事照着做 skill", 42, 618, 620, 32, { size: 18, color: C.muted });
  footer(slide, 1);
}

// 2
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "先给 skill 分类", "先判断它是哪类，文件结构才不会乱", "不同类别的 skill，核心资产不一样。");
  const cats = [
    ["知识库型", "像一本带目录的手册\n核心：references、术语表、索引", C.blue],
    ["工具库型", "像一个工程工具箱\n核心：scripts、assets、示例数据", C.green],
    ["流程型", "像一张作业指导书\n核心：步骤、检查点、输出模板", C.accent],
    ["专家路由型", "像一个会分诊的老师傅\n核心：触发边界、任务路由、分层资料", C.amber],
    ["集成控制型", "像一个设备遥控台\n核心：工具调用、权限、安全保护", C.red],
    ["评测守护型", "像出厂测试台\n核心：evals、正反例、失败处理", C.muted],
  ];
  for (let i = 0; i < cats.length; i++) {
    const [a, b, color] = cats[i];
    const x = 52 + (i % 3) * 394;
    const y = 258 + Math.floor(i / 3) * 156;
    card(slide, a, b, x, y, 344, 112, { labelColor: color, bodySize: 16 });
  }
  addText(slide, "例子：EE-AI-Toolkit 偏“工具库型”；PLC-Programming 偏“专家路由型”。", 76, 590, 1000, 34, { size: 22, bold: true });
  footer(slide, 2);
}

// 3
twoElementSlide(deck, 3, "要素 1-2", "先写清楚“什么时候用”，再写清楚“什么时候不用”", {
  title: "1. 名称与触发描述",
  color: C.blue,
  body: "作用：让 AI 一眼知道这个 skill 负责什么。\n\n要写细：\n- skill 名称\n- 典型触发词\n- 典型任务\n- 不要只写“电气助手”这种大词\n\n通俗理解：像工具柜上的标签，标签越清楚，拿错工具的概率越低。",
  example: "例：看到“PLC、顺控、联锁、梯形图”才触发 PLC skill",
}, {
  title: "2. 适用边界",
  color: C.red,
  body: "作用：防止 AI 把 skill 用到不该用的地方。\n\n要写细：\n- 覆盖范围\n- 排除范围\n- 安全/合规边界\n- 输入不够时要先问什么\n\n通俗理解：像电气柜门上的警示牌，告诉你哪些能碰，哪些必须停机确认。",
  example: "例：不知道 PLC 厂商时，不直接给三菱专用指令",
});

// 4
twoElementSlide(deck, 4, "要素 3-4", "好 skill 会告诉 AI 先看哪份资料、按什么顺序做事", {
  title: "3. 资料地图",
  color: C.green,
  body: "作用：让 AI 不用全文乱翻。\n\n要写细：\n- 资料目录\n- 每份资料解决什么问题\n- 读取顺序\n- 大资料如何检索\n\n通俗理解：像维修手册目录。你查报警代码，就直接翻报警章节，不从第一页读到最后。",
  example: "例：提示词问题读 prompt-library；脚本问题读 script-catalog",
}, {
  title: "4. 工作流程",
  color: C.accent,
  body: "作用：把经验步骤固定下来。\n\n要写细：\n- 先分类\n- 再补充输入\n- 再检索/计算/生成\n- 最后验证和交付\n\n通俗理解：像开机调试 SOP。先检查电源，再查 I/O，再跑程序，不是想到哪做哪。",
  example: "例：PLC 任务先识别厂商，再选 common 或 vendors 资料",
});

// 5
twoElementSlide(deck, 5, "要素 5-6", "模板让输出稳定，脚本让动作可重复", {
  title: "5. 模板与示例",
  color: C.amber,
  body: "作用：让输出格式稳定。\n\n要写细：\n- 报告模板\n- 代码模板\n- 检查清单\n- 好例子和反例\n\n通俗理解：像电气图纸标题栏。每张图都按同一格式填，别人一看就知道去哪里找信息。",
  example: "例：报警联锁模板、顺控步骤模板、输出归属审查模板",
}, {
  title: "6. 工具与脚本",
  color: C.green,
  body: "作用：让 AI 不只会说，还能执行。\n\n要写细：\n- 脚本用途\n- 输入输出\n- 依赖环境\n- 失败时怎么处理\n\n通俗理解：像万用表和压线钳。能用工具量出来、算出来，就不要全靠嘴说。",
  example: "例：EE-AI-Toolkit 用 Python 脚本算电压降、画负载曲线",
});

// 6
twoElementSlide(deck, 6, "要素 7-8", "交付格式决定能不能用，评测决定能不能长期用", {
  title: "7. 输出格式",
  color: C.blue,
  body: "作用：让结果能直接交给人或系统。\n\n要写细：\n- 输出是报告、表格、代码还是清单\n- 字段顺序\n- 必须说明的假设\n- 哪些结论要标注风险\n\n通俗理解：像验收报告。不是写一堆话，而是让项目经理、调试员、客户都能看懂。",
  example: "例：输出“问题、风险等级、依据、建议动作、责任人”",
}, {
  title: "8. 评测与安装",
  color: C.red,
  body: "作用：让 skill 可安装、可测试、可维护。\n\n要写细：\n- README / INSTALL\n- 元数据和版本\n- 正确触发案例\n- 错误触发案例\n- 输入不完整案例\n\n通俗理解：像设备出厂测试。不能只说能用，要拿测试用例证明它稳定。",
  example: "例：evals 里放“该触发 PLC skill”和“不该触发 PLC skill”的案例",
});

// 7
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "最小可用 skill 包", "文件结构围绕“入口、资料、动作、交付、验证”组织");
  const tree = `skill-name/
├─ SKILL.md
│  触发规则、边界、读取顺序、输出规则
├─ README.md / INSTALL.md
│  安装方式、使用方式、依赖说明
├─ references/
│  任务路由、知识规则、术语表、资料索引
├─ templates/
│  报告模板、代码骨架、检查清单
├─ assets/
│  示例数据、脚本、源资料、素材
├─ scripts/
│  检索、计算、转换、生成工具
└─ evals/
   触发、生成、审查、异常输入案例`;
  codeBox(slide, tree, 58, 248, 560, 364, { size: 16 });
  const steps = [
    ["入口", "SKILL.md 决定是否触发"],
    ["资料", "references 提供可信上下文"],
    ["动作", "scripts/assets 执行重复任务"],
    ["交付", "templates 固定输出形态"],
    ["验证", "evals 检查是否稳定"],
  ];
  for (let i = 0; i < steps.length; i++) {
    const y = 252 + i * 66;
    rect(slide, 690, y, 430, 54, { fill: C.soft, line: C.rule, lineWidth: 1 });
    addText(slide, steps[i][0], 716, y + 10, 80, 22, { size: 18, bold: true });
    addText(slide, steps[i][1], 815, y + 13, 270, 22, { size: 15, color: C.muted });
  }
  addText(slide, "判断标准：AI 不需要猜流程，它能根据入口说明找到资料、调用动作，并按模板交付。", 690, 592, 470, 42, { size: 18, bold: true, color: C.accent });
  footer(slide, 7);
}

// 8
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "EE-AI-Toolkit 示例", "工具库型 skill 把资料、提示词和脚本组织成一个工具箱");
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
  codeBox(slide, tree, 52, 248, 552, 350, { size: 16 });
  card(slide, "类别", "工具库型 + 知识库型", 660, 248, 500, 70, { labelColor: C.green, bodySize: 18 });
  card(slide, "动作流程", "用户问题 → SKILL.md 分类 → 读取最小资料 → 必要时检索 → 复用脚本 → 输出并声明单位、假设和验证方法", 660, 340, 500, 134, { labelColor: C.accent, bodySize: 16 });
  card(slide, "通俗例子", "像电气工程师的“计算器抽屉”。要算电压降，就拿电压降脚本；要改提示词，就翻提示词库。", 660, 496, 500, 102, { labelColor: C.blue, bodySize: 16 });
  footer(slide, 8);
}

// 9
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "PLC-Programming 示例", "专家路由型 skill 先分诊，再进入通用层或厂商层");
  const tree = `PLC-Programming/
├─ SKILL.md
├─ references/
│  ├─ skill-architecture.md
│  ├─ common/
│  │  ├─ task-router.md
│  │  ├─ safety-boundaries.md
│  │  └─ code-review-checklists.md
│  └─ vendors/
│     ├─ vendor-routing.md
│     ├─ mitsubishi/
│     ├─ siemens/
│     └─ rockwell / omron / codesys ...
├─ templates/common/
├─ examples/common/
└─ evals/`;
  codeBox(slide, tree, 52, 244, 552, 366, { size: 16 });
  card(slide, "类别", "专家路由型 + 流程型", 660, 244, 500, 70, { labelColor: C.amber, bodySize: 18 });
  card(slide, "动作流程", "确认是否 PLC 任务 → 识别厂商线索 → 选择 common 或 vendors → 生成/审查/调试 → 标注假设和安全边界", 660, 336, 500, 134, { labelColor: C.accent, bodySize: 16 });
  card(slide, "通俗例子", "像调试现场的老师傅。你说“三菱 FX3U”，他进三菱资料；你只说“顺控”，他先按通用 PLC 方法处理。", 660, 492, 500, 116, { labelColor: C.blue, bodySize: 16 });
  footer(slide, 9);
}

// 10
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "向 AI 提问生成 skill", "不要只说“帮我做一个 skill”，要把类别、要素和例子一次讲清楚");
  const prompt = `请为【电气工程师】创建一个可安装的 skill 包，主题是【填写任务领域】。

一、先判断 skill 类别
- 它更像：知识库型 / 工具库型 / 流程型 / 专家路由型 / 集成控制型 / 评测守护型？
- 如果有多种类别，请说明主类别和辅助类别。

二、必须包含 8 个要素
1. 名称与触发描述：什么时候启用，典型触发词是什么。
2. 适用边界：覆盖什么，不覆盖什么，安全/合规限制是什么。
3. 资料地图：references 里有哪些资料，每份资料解决什么问题。
4. 工作流程：从用户输入到最终交付的步骤。
5. 模板与示例：至少 3 个输出模板，包含好例子和反例。
6. 工具与脚本：如需脚本，说明输入、输出、依赖和失败处理。
7. 输出格式：报告、表格、代码、清单的字段和格式。
8. 评测与安装：README、INSTALL、evals、版本元数据。

三、业务背景
- 使用场景：【例如 PLC 调试 / 电气计算 / 图纸归档】
- 常见输入：【文件、型号、现场描述、表格】
- 期望输出：【报告、代码、清单、图表、脚本】
- 安全限制：【人工复核、现场验证、适用标准】`;
  codeBox(slide, prompt, 58, 238, 1128, 398, { size: 14 });
  footer(slide, 10);
}

// 11
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "两个可直接复制的例子", "工具库型问资料和脚本，专家路由型问边界和分层");
  card(slide, "生成 EE-AI-Toolkit 类工具库", "请创建一个“电气工程师 AI 工具包”skill。主类别是工具库型，辅助类别是知识库型。它要整合课程资料、提示词库、100 个 Python 工程脚本、检索脚本和安全验证规则。请输出 SKILL.md、references、assets/python-scripts、scripts/search 工具、templates、evals、README 和 INSTALL，并为每个要素配一个电气工程例子。", 56, 246, 548, 250, { labelColor: C.green, bodySize: 16 });
  card(slide, "生成 PLC-Programming 类专家路由", "请创建一个“PLC 编程开发综合”skill。主类别是专家路由型，辅助类别是流程型。它要支持 IEC 61131-3 通用层和三菱、西门子、欧姆龙、罗克韦尔、施耐德、台达、基恩士、松下、倍福、Codesys 厂商层。要求先判断是否 PLC 任务，再识别厂商，再读取 common 或 vendors 资料，并输出顺控、状态机、报警联锁、调试清单等模板。", 674, 246, 548, 250, { labelColor: C.amber, bodySize: 16 });
  addText(slide, "一句话记忆：先定类别，再补 8 个要素，最后给真实输入和期望输出。", 90, 558, 1040, 48, { size: 25, bold: true });
  footer(slide, 11);
}

await fs.mkdir(PREVIEW_DIR, { recursive: true });
await fs.mkdir(path.dirname(OUT), { recursive: true });

for (const [index, slide] of deck.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await deck.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(PREVIEW_DIR, `${stem}.png`), Buffer.from(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(PREVIEW_DIR, `${stem}.layout.json`), await layout.text());
}

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(OUT);
console.log(OUT);
