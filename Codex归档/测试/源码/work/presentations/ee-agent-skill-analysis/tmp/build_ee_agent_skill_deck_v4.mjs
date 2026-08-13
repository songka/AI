import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/lfaf-test/Documents/测试";
const OUT = `${ROOT}/outputs/电气工程师Agent-Skill分析与提问方法_课堂讲解版.pptx`;
const PREVIEW_DIR = `${ROOT}/work/presentations/ee-agent-skill-analysis/tmp/preview-v4`;

const W = 1280;
const H = 720;
const FONT = "Microsoft YaHei";
const C = {
  ink: "#121212",
  muted: "#5F6368",
  faint: "#F7F8FA",
  panel: "#ECEFF3",
  line: "#C8CDD4",
  orange: "#E85D2A",
  blue: "#1F6FEB",
  green: "#238636",
  amber: "#A66A00",
  red: "#B42318",
  purple: "#6F42C1",
  white: "#FFFFFF",
  black: "#171717",
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
    fontSize: opts.size ?? 18,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    typeface: FONT,
    alignment: opts.align ?? "left",
  };
  return shape;
}

function box(slide, x, y, w, h, opts = {}) {
  return slide.shapes.add({
    geometry: opts.geometry ?? "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? C.faint,
    line: { style: "solid", fill: opts.line ?? C.line, width: opts.lineWidth ?? 1 },
  });
}

function title(slide, section, headline, sub = "") {
  addText(slide, section, 48, 32, 760, 28, { size: 15, bold: true, color: C.muted });
  addText(slide, headline, 48, 74, 1050, 88, { size: 39, bold: true });
  if (sub) addText(slide, sub, 50, 166, 1040, 38, { size: 18, color: C.muted });
  box(slide, 48, 218, 1184, 1.5, { fill: C.line, line: "none", lineWidth: 0 });
}

function footer(slide, n) {
  addText(slide, "电气工程师 Agent Skill 分析与提问方法", 48, 666, 620, 24, { size: 13, color: C.muted });
  addText(slide, String(n).padStart(2, "0"), 1180, 660, 58, 26, { size: 15, bold: true, color: C.muted, align: "right" });
}

function card(slide, head, body, x, y, w, h, opts = {}) {
  box(slide, x, y, w, h, { fill: opts.fill ?? C.faint, line: opts.line ?? C.line });
  addText(slide, head, x + 16, y + 12, w - 32, 28, {
    size: opts.headSize ?? 18,
    bold: true,
    color: opts.color ?? C.ink,
  });
  addText(slide, body, x + 16, y + 48, w - 32, h - 56, {
    size: opts.bodySize ?? 15,
    color: opts.bodyColor ?? C.muted,
  });
}

function codeBox(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill ?? C.black,
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 14,
    color: opts.color ?? "#F8FAFC",
    typeface: "Consolas",
  };
  return shape;
}

function relationRow(slide, idx, name, role, where, kind, y, color) {
  addText(slide, String(idx), 58, y + 12, 42, 28, { size: 22, bold: true, color });
  box(slide, 108, y, 1070, 58, { fill: idx % 2 ? C.faint : C.panel, line: C.line });
  addText(slide, name, 128, y + 9, 190, 24, { size: 18, bold: true, color });
  addText(slide, role, 332, y + 11, 300, 24, { size: 15, color: C.ink });
  addText(slide, where, 650, y + 11, 300, 24, { size: 15, color: C.muted });
  addText(slide, kind, 970, y + 11, 170, 24, { size: 15, bold: true, color: C.ink });
}

const deck = Presentation.create({ slideSize: { width: W, height: H } });

// 1
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  addText(slide, "电气工程师 Agent Skill", 50, 48, 620, 34, { size: 18, bold: true, color: C.muted });
  addText(slide, "Skill 要素拆解：\n从会用，到会让 AI 写出来", 50, 138, 860, 170, { size: 52, bold: true });
  addText(slide, "课堂版课件：先建立概念，再拆 8 个要素，最后用两个真实 skill 看文件结构、动作流程和提问方法。", 54, 382, 860, 58, { size: 21, color: C.muted });
  card(slide, "本课目标", "1. 看懂 skill 像什么\n2. 知道 8 个要素放在哪里\n3. 分清必须名称、约定名称、自定义名称\n4. 会写出让 AI 生成 skill 的提问", 910, 140, 300, 320, { fill: C.panel, color: C.orange, bodySize: 18 });
  box(slide, 52, 596, 720, 2, { fill: C.ink, line: "none" });
  addText(slide, "关键词：SKILL.md、references、templates、assets、scripts、evals、package.zip", 52, 616, 910, 30, { size: 18, color: C.muted });
  footer(slide, 1);
}

// 2
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "课程目录", "按“先认结构，再看例子，再写提问”的顺序讲");
  const items = [
    ["01", "先给 skill 分类", "判断它像知识库、工具箱、流程 SOP，还是专家分诊台。"],
    ["02", "拆 8 个要素", "每个要素对应哪个文件或文件夹，并配一个通俗例子。"],
    ["03", "文件名规则", "哪些英文名必须保留，哪些只是常见约定，哪些可自定义。"],
    ["04", "两个真实例子", "EE-AI-Toolkit 和 PLC-Programming 的目录结构与动作流程。"],
    ["05", "如何向 AI 提问", "给出可直接复制的真实提问，让 AI 生成完整 skill 包。"],
  ];
  for (let i = 0; i < items.length; i++) {
    const y = 250 + i * 72;
    addText(slide, items[i][0], 74, y + 8, 56, 32, { size: 24, bold: true, color: i < 3 ? C.orange : C.muted });
    box(slide, 146, y, 980, 52, { fill: i % 2 ? C.panel : C.faint, line: C.line });
    addText(slide, items[i][1], 168, y + 11, 240, 24, { size: 18, bold: true });
    addText(slide, items[i][2], 420, y + 12, 650, 24, { size: 16, color: C.muted });
  }
  footer(slide, 2);
}

// 3
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "第一步：先给 skill 分类", "类型决定目录重点。先分清它像什么，再决定资料、模板、脚本要放多重");
  const parts = [
    ["知识库型", "像带目录的手册\n重点：references/、术语、索引", C.blue],
    ["工具库型", "像工程工具箱\n重点：scripts/、assets/、示例脚本", C.green],
    ["流程型", "像作业指导书 SOP\n重点：步骤、检查点、输出模板", C.orange],
    ["专家路由型", "像会分诊的老师傅\n重点：触发边界、任务路由、分层资料", C.amber],
    ["集成控制型", "像设备遥控台\n重点：工具调用、权限、安全保护", C.red],
    ["评测守护型", "像出厂测试台\n重点：evals/、正反例、失败处理", C.purple],
  ];
  for (let i = 0; i < parts.length; i++) {
    const x = 56 + (i % 3) * 392;
    const y = 250 + Math.floor(i / 3) * 148;
    card(slide, parts[i][0], parts[i][1], x, y, 340, 108, { color: parts[i][2], bodySize: 16 });
  }
  addText(slide, "例子：EE-AI-Toolkit 偏工具库型；PLC-Programming 偏专家路由型。", 82, 590, 1030, 34, { size: 23, bold: true, color: C.orange });
  footer(slide, 3);
}

// 4
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "8 个要素分别放在哪些文件或文件夹", "先记住位置，再去理解内容，课堂讲解会顺很多");
  addText(slide, "要素", 128, 238, 120, 24, { size: 16, bold: true });
  addText(slide, "作用", 332, 238, 120, 24, { size: 16, bold: true });
  addText(slide, "主要位置", 650, 238, 160, 24, { size: 16, bold: true });
  addText(slide, "名称性质", 970, 238, 160, 24, { size: 16, bold: true });
  relationRow(slide, 1, "名称触发", "名称、描述、触发词", "SKILL.md 顶部和正文", "必须有", 262, C.blue);
  relationRow(slide, 2, "适用边界", "覆盖、排除、安全限制", "SKILL.md 或 references/边界文件", "内容必须", 310, C.red);
  relationRow(slide, 3, "资料地图", "资料目录、读取顺序", "references/ 或 SKILL.md", "约定常用", 358, C.green);
  relationRow(slide, 4, "工作流程", "分类、路由、处理、验证", "SKILL.md + references/流程文件", "内容必须", 406, C.orange);
  relationRow(slide, 5, "输出模板", "报告、代码、清单模板", "templates/ examples/", "约定常用", 454, C.amber);
  relationRow(slide, 6, "脚本工具", "检索、计算、转换、生成", "scripts/ assets/", "约定常用", 502, C.green);
  relationRow(slide, 7, "交付格式", "字段、格式、假设、风险", "SKILL.md + templates/", "内容必须", 550, C.blue);
  relationRow(slide, 8, "安装评测", "安装、版本、正反案例", "README/INSTALL、_meta.json、evals/", "按场景选择", 598, C.purple);
  footer(slide, 4);
}

// 5
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "文件名分三类：必须、约定、自定义", "英文目录名不要随便翻译成中文路径，PPT 可写中文备注，真实文件名最好保留英文");
  card(slide, "必须保留的名称", "SKILL.md：skill 的入口文件，必须存在。\n\npackage.zip：导入时常用的压缩包名称。\n\n_meta.json：平台包里可能出现的元数据，通常不要改字段。", 58, 252, 354, 284, { color: C.red, bodySize: 17 });
  card(slide, "约定俗成的名称", "references/：资料库\nscripts/：执行脚本\nassets/：示例资源或原始素材\ntemplates/：输出模板\nexamples/：示例输入输出\nevals/：评测案例\nREADME.md / INSTALL.md：说明文档", 462, 252, 354, 284, { color: C.green, bodySize: 17 });
  card(slide, "用户自定义的名称", "skill 文件夹名可以按主题命名。\n\nreferences/ 里面的文件名可按业务命名，例如：task-router.md、safety-boundaries.md。\n\n脚本名、模板名、案例名也可以按你的工程习惯命名。", 866, 252, 354, 284, { color: C.blue, bodySize: 17 });
  addText(slide, "建议：文件名用英文，括号里备注中文。这样 AI 和系统容易识别，你自己也容易找到原文件。", 76, 588, 1060, 34, { size: 22, bold: true, color: C.orange });
  footer(slide, 5);
}

// 6
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "最小可用目录长这样", "括号里是中文含义，真实文件名仍保留英文，方便直接导入");
  const tree = `skill-name/（用户自定义 skill 文件夹名）
├── SKILL.md（技能说明书，必须）
├── README.md / INSTALL.md（安装说明，约定）
├── references/（资料库，约定）
│   ├── task-router.md（任务路由，自定义）
│   └── safety-boundaries.md（安全边界，自定义）
├── templates/（输出模板，约定）
├── examples/（示例输入输出，约定）
├── assets/（示例资源，约定）
├── scripts/（执行脚本，约定）
└── evals/（评测案例，约定）`;
  codeBox(slide, tree, 68, 252, 550, 344, { size: 16 });
  card(slide, "课堂讲法", "先问：AI 从哪里进来？答案是 SKILL.md。\n\n再问：AI 的依据在哪里？答案是 references/。\n\n再问：AI 怎么稳定输出？答案是 templates/、examples/、scripts/。\n\n最后问：怎么证明它靠谱？答案是 evals/ 和安装说明。", 690, 252, 470, 276, { color: C.orange, bodySize: 18 });
  addText(slide, "注意：不是每个 skill 都必须有所有文件夹，但 SKILL.md 必须有，且里面要写清楚如何读取其它资料。", 690, 558, 470, 48, { size: 18, bold: true, color: C.red });
  footer(slide, 6);
}

// 7
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "8 个要素不是每类 skill 都同样重", "必须讲清的是规则，不一定必须单独建文件夹");
  const rows = [
    ["名称触发", "所有类型必备", "必须写在 SKILL.md"],
    ["适用边界", "所有类型必备", "工程、安全、工具调用类尤其要细"],
    ["资料地图", "知识库型、专家路由型必备", "简单流程型可写在 SKILL.md 里"],
    ["工作流程", "所有类型必备", "流程型、专家路由型要最详细"],
    ["输出模板", "流程型、评测型、交付型强烈建议", "问答型可只写格式规则"],
    ["执行脚本", "工具库型、集成控制型必备", "纯知识库型可没有 scripts/"],
    ["交付格式", "所有类型必备", "至少说明输出字段、假设和风险"],
    ["安装评测", "可导入包必备；正式发布必备", "课堂练习可简化，但不建议省略"],
  ];
  addText(slide, "要素", 96, 246, 150, 22, { size: 16, bold: true });
  addText(slide, "是否必须", 344, 246, 240, 22, { size: 16, bold: true });
  addText(slide, "讲课时的判断方法", 674, 246, 360, 22, { size: 16, bold: true });
  for (let i = 0; i < rows.length; i++) {
    const y = 278 + i * 42;
    box(slide, 72, y, 1080, 34, { fill: i % 2 ? C.panel : C.faint, line: C.line });
    addText(slide, `${i + 1}. ${rows[i][0]}`, 94, y + 7, 210, 18, { size: 15, bold: true, color: i < 4 || i === 6 ? C.orange : C.ink });
    addText(slide, rows[i][1], 344, y + 7, 280, 18, { size: 15, color: C.ink });
    addText(slide, rows[i][2], 674, y + 7, 420, 18, { size: 15, color: C.muted });
  }
  addText(slide, "一句话：所有 skill 都必须讲清“入口、边界、流程、交付”；其它要素按类型决定强弱。", 84, 620, 1060, 28, { size: 19, bold: true, color: C.red });
  footer(slide, 7);
}

// 8
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "要素 1-2：名称触发和适用边界", "先让 AI 知道何时启动，再让 AI 知道不能越界");
  card(slide, "1. 名称与触发描述\n位置：SKILL.md", "要写清楚：\n- skill 名称\n- description 描述\n- 典型触发词\n- 典型任务\n\n例子：看到“PLC、顺控、联锁、梯形图、ST”时，才触发 PLC skill。", 64, 252, 520, 300, { color: C.blue, bodySize: 18 });
  card(slide, "2. 适用边界\n位置：SKILL.md 或 references/safety-boundaries.md", "要写清楚：\n- 覆盖什么\n- 不覆盖什么\n- 哪些结论必须人工复核\n- 信息不够时先问什么\n\n例子：不知道 PLC 厂商和 CPU 型号时，不直接给专用指令。", 676, 252, 520, 300, { color: C.red, bodySize: 18 });
  addText(slide, "通俗理解：名称触发像“工具标签”；适用边界像“安全警示牌”。", 94, 590, 1010, 34, { size: 21, bold: true, color: C.orange });
  footer(slide, 8);
}

// 9
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "要素 3-4：资料地图和动作流程", "好 skill 不是让 AI 乱翻资料，而是让 AI 按路线查、按步骤做");
  card(slide, "3. 资料地图\n位置：references/ 或 SKILL.md", "要写清楚：\n- 哪些资料文件存在\n- 每份资料解决什么问题\n- 先读哪份，再读哪份\n- 大资料如何检索\n\n例子：提示词问题读 prompt-library.md；脚本问题读 python-script-catalog.md。", 64, 252, 520, 306, { color: C.green, bodySize: 18 });
  card(slide, "4. 动作流程\n位置：SKILL.md + references/流程文件", "要写清楚：\n- 先判断任务类型\n- 再补齐输入条件\n- 再检索、计算或生成\n- 最后验证并交付\n\n例子：PLC 任务先识别厂商，再选择通用资料或厂商资料。", 676, 252, 520, 306, { color: C.orange, bodySize: 18 });
  addText(slide, "通俗理解：资料地图像维修手册目录；动作流程像开机调试 SOP。", 94, 600, 1010, 34, { size: 22, bold: true, color: C.orange });
  footer(slide, 9);
}

// 10
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "要素 5-6：输出模板和执行脚本", "模板让结果稳定，脚本让动作可重复");
  card(slide, "5. 输出模板与示例\n位置：templates/ examples/", "要写清楚：\n- 报告模板\n- 代码模板\n- 检查清单\n- 好例子和反例\n\n例子：用模板输出“问题、依据、风险、建议”。", 64, 252, 520, 310, { color: C.amber, bodySize: 18 });
  card(slide, "6. 执行脚本与工具\n位置：scripts/ assets/", "要写清楚：\n- 脚本用途\n- 输入输出\n- 依赖环境\n- 失败时怎么处理\n\n例子：用 Python 脚本算电压降、画负载曲线、检索资料。", 676, 252, 520, 310, { color: C.green, bodySize: 18 });
  addText(slide, "通俗理解：输出模板像图纸标题栏；执行脚本像万用表和专用测试仪。", 94, 604, 1010, 34, { size: 22, bold: true, color: C.orange });
  footer(slide, 10);
}

// 11
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "要素 7-8：交付格式和安装评测", "交付格式决定别人能不能用，安装评测决定 skill 能不能长期用");
  card(slide, "7. 交付格式\n位置：SKILL.md + templates/", "要写清楚：\n- 输出是报告、表格、代码还是清单\n- 字段顺序\n- 必须说明的假设\n- 哪些结论要标注风险\n\n例子：输出“问题、风险等级、依据、建议动作、人工复核点”。", 64, 252, 520, 310, { color: C.blue, bodySize: 18 });
  card(slide, "8. 安装说明与评测案例\n位置：README/INSTALL、_meta.json、evals/", "要写清楚：\n- 如何安装或导入\n- 版本信息\n- 正确触发案例\n- 不该触发案例\n- 输入不完整案例\n\n例子：放“应该触发 PLC skill”和“不应该触发 PLC skill”的案例。", 676, 252, 520, 310, { color: C.purple, bodySize: 18 });
  addText(slide, "通俗理解：交付格式像验收报告；安装评测像出厂测试记录。", 94, 604, 1010, 34, { size: 22, bold: true, color: C.orange });
  footer(slide, 11);
}

// 12 EE
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "例子一：EE-AI-Toolkit 的文件结构", "这是工具库型 skill，重点是资料库、提示词库、脚本目录和检索工具");
  const tree = `EE-AI-Toolkit/（电气工程师 AI 工具包）
├── SKILL.md（技能说明书，必须）
├── references/（资料库）
│   ├── course-index.md（课程索引）
│   ├── condensed-lessons.md（精简知识点）
│   ├── prompt-library.md（提示词库）
│   ├── python-script-catalog.md（脚本目录）
│   └── source-digest.md（原始资料摘要）
├── assets/python-scripts/（示例资源：Python 脚本）
│   ├── script_001_power_calculator.py（功率计算）
│   ├── script_010_voltage_drop_calculator.py（电压降计算）
│   └── script_100_engineering_decision_support_system.py
└── scripts/search_ee_ai.py（执行脚本：资料检索工具）`;
  codeBox(slide, tree, 56, 248, 600, 368, { size: 15 });
  card(slide, "8 个要素落点", "名称触发：SKILL.md\n适用边界：SKILL.md\n资料地图：references/\n工作流程：SKILL.md 的读取顺序\n输出模板：SKILL.md 输出规则\n执行脚本：assets/python-scripts/、scripts/\n交付格式：SKILL.md\n安装评测：_meta.json、package.zip、导入检查", 704, 252, 430, 236, { color: C.green, bodySize: 16 });
  card(slide, "动作流程", "用户问题 → SKILL.md 判断任务 → 读取最小资料 → 必要时调用 search_ee_ai.py → 复用 Python 示例 → 输出计算依据、假设和验证方法", 704, 502, 430, 100, { color: C.orange, bodySize: 16 });
  footer(slide, 12);
}

// 13 PLC
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "例子二：PLC-Programming 的文件结构", "这是专家路由型 skill，重点是先分诊，再进入通用层或厂商层");
  const tree = `PLC-Programming/（PLC 编程开发综合）
├── SKILL.md（技能说明书，必须）
├── references/（资料库）
│   ├── skill-architecture.md（技能架构）
│   ├── common/（通用资料）
│   │   ├── task-router.md（任务路由）
│   │   ├── safety-boundaries.md（安全边界）
│   │   └── code-review-checklists.md（代码审查清单）
│   └── vendors/（厂商资料）
│       ├── vendor-routing.md（厂商路由）
│       ├── mitsubishi/（三菱）
│       ├── siemens/（西门子）
│       └── rockwell / omron / codesys ...
├── templates/common/（输出模板）
├── examples/common/（通用示例）
└── evals/（评测案例）`;
  codeBox(slide, tree, 56, 244, 600, 380, { size: 15 });
  card(slide, "8 个要素落点", "名称触发：SKILL.md\n适用边界：SKILL.md、safety-boundaries.md\n资料地图：references/common、references/vendors\n工作流程：task-router.md、vendor-routing.md\n输出模板：templates/、examples/\n执行脚本：本例可选\n交付格式：templates/common/\n安装评测：evals/、_meta.json、package.zip", 704, 248, 430, 246, { color: C.amber, bodySize: 16 });
  card(slide, "动作流程", "确认是否 PLC 任务 → 识别厂商/软件/CPU → 通用层或厂商层 → 生成/审查/调试 → 标注假设、安全边界和现场复核点", 704, 510, 430, 106, { color: C.orange, bodySize: 16 });
  footer(slide, 13);
}

// 14 prompt method
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "向 AI 提问时，要把 8 个要素一次说清楚", "不要只说“帮我做一个 skill”，要让 AI 知道类型、边界、资料、流程、模板、工具、交付和验收");
  const prompt = `请为【电气工程师】创建一个可导入使用的 skill 包，主题是【填写任务领域】。

一、先判断 skill 类型
- 它更像：知识库型 / 工具库型 / 流程型 / 专家路由型 / 集成控制型 / 评测守护型？
- 如果有多个类型，请说明主类型和辅助类型。

二、必须包含 8 个要素
1. 入口说明：写入 SKILL.md，说明名称、description、触发词、典型任务。
2. 边界规则：说明覆盖范围、排除范围、安全限制、何时需要人工复核。
3. 资料地图：说明 references/ 中有哪些资料，每份资料解决什么问题。
4. 动作流程：说明从用户输入到最终交付的处理步骤和读取顺序。
5. 输出模板与示例：说明 templates/、examples/ 中有哪些模板和正反例。
6. 执行脚本与工具：说明 scripts/、assets/ 是否需要，以及输入输出和依赖。
7. 交付格式：说明最终报告、表格、代码或清单的字段、格式、假设和风险标注。
8. 安装说明与评测案例：说明 README/INSTALL、_meta.json、evals/、package.zip 如何安排。

三、输出要求
先给完整目录树，再逐个文件给内容草稿。
文件名保留英文，后面用括号标注中文含义。`;
  codeBox(slide, prompt, 62, 242, 1130, 394, { size: 14 });
  footer(slide, 14);
}

// 15 real PLC prompt
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "真实提问范例：生成 PLC-Programming skill", "这段可以直接复制给 AI，用来生成 PLC 编程开发综合 skill");
  const prompt = `请帮我创建一个“PLC 编程开发综合”skill 包，供电气工程师在 AI Agent 中使用。

主类别：专家路由型。辅助类别：流程型、知识库型。

使用场景：
用于 PLC 程序开发、顺控逻辑设计、联锁报警、状态机、定时器/计数器、I/O 映射、程序审查、调试排故。
常见输入包括：PLC 品牌、CPU 型号、I/O 点表、设备动作流程、报警需求、已有 ST/梯形图逻辑、现场故障描述。

必须生成的结构：
1. SKILL.md（技能说明书）：触发词、适用边界、排除范围、安全边界、读取顺序、输出规则。
2. references/（资料库）：包含 common/（通用资料）和 vendors/（厂商资料）。
3. templates/（输出模板）：顺控步骤、状态机、报警联锁、输出归属审查模板。
4. examples/（示例）：至少 3 个典型输入和对应输出。
5. evals/（评测案例）：应该触发、不应该触发、输入不完整三类案例。
6. README.md / INSTALL.md（安装说明）：说明怎么安装、怎么使用、依赖什么。

要求：
先给目录树，再写每个文件的中文内容草稿。
目录名和文件名必须保留英文原名，并在后面用括号标注中文含义。`;
  codeBox(slide, prompt, 62, 238, 1130, 402, { size: 13 });
  footer(slide, 15);
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

const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(PREVIEW_DIR, "deck-montage.webp"), Buffer.from(await montage.arrayBuffer()));

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(OUT);
console.log(OUT);
