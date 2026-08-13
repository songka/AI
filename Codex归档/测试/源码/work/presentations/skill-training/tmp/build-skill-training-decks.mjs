import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "C:/Users/lfaf-test/Documents/测试/outputs";
const PREVIEW = "C:/Users/lfaf-test/Documents/测试/work/presentations/skill-training/tmp/preview";

const W = 1280;
const H = 720;
const M = { left: 54, top: 46, right: 54, bottom: 46 };
const colors = {
  ink: "#111111",
  muted: "#555555",
  pale: "#F0F0F0",
  panel: "#E7E7E7",
  rule: "#B8BCC4",
  orange: "#FF6B35",
  blue: "#2563EB",
  green: "#059669",
  red: "#DC2626",
};

function deck() {
  return Presentation.create({ slideSize: { width: W, height: H } });
}

function box(slide, x, y, w, h, fill = colors.pale, line = colors.rule) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
  });
}

function text(slide, value, x, y, w, h, opts = {}) {
  const s = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  s.text = value;
  s.text.style = {
    fontSize: opts.size ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? colors.ink,
    alignment: opts.align ?? "left",
    fontFace: "Microsoft YaHei",
  };
  return s;
}

function label(slide, value, n) {
  text(slide, value, M.left, 30, 360, 28, { size: 15, bold: true, color: colors.muted });
  text(slide, String(n).padStart(2, "0"), W - 96, H - 46, 42, 24, {
    size: 14,
    color: colors.muted,
    align: "right",
  });
}

function titleSlide(p, course, title, subtitle) {
  const slide = p.slides.add();
  slide.background.fill = "#FFFFFF";
  box(slide, M.left, 42, W - M.left - M.right, 6, colors.ink, "none");
  text(slide, course, M.left, 92, 520, 34, { size: 20, bold: true, color: colors.orange });
  text(slide, title, M.left, 168, 920, 168, { size: 58, bold: true });
  text(slide, subtitle, M.left, 405, 720, 80, { size: 26, color: colors.muted });
  box(slide, 890, 170, 250, 250, colors.panel, "none");
  box(slide, 935, 215, 250, 250, "#FFFFFF", colors.ink);
  text(slide, "Skill", 965, 292, 200, 70, { size: 52, bold: true, align: "center" });
  text(slide, "工作流知识包", 965, 370, 200, 30, { size: 18, color: colors.muted, align: "center" });
}

function agendaSlide(p, course, n, items) {
  const slide = p.slides.add();
  label(slide, course, n);
  text(slide, "这一课解决三个问题", M.left, 78, 760, 60, { size: 42, bold: true });
  const y0 = 182;
  items.forEach((item, i) => {
    const y = y0 + i * 126;
    text(slide, `0${i + 1}`, M.left, y + 8, 90, 48, { size: 34, bold: true, color: colors.orange });
    box(slide, 150, y, 1010, 86, i === 1 ? "#F7F7F7" : "#FFFFFF", colors.rule);
    text(slide, item.title, 184, y + 14, 360, 34, { size: 24, bold: true });
    text(slide, item.body, 560, y + 16, 560, 48, { size: 19, color: colors.muted });
  });
}

function threeColumn(slide, y, cols, accent = colors.orange) {
  const w = 350;
  cols.forEach((c, i) => {
    const x = M.left + i * 392;
    box(slide, x, y, w, 318, i === 1 ? "#F8F8F8" : "#FFFFFF", colors.rule);
    box(slide, x, y, w, 8, c.color ?? accent, "none");
    text(slide, c.head, x + 24, y + 30, w - 48, 46, { size: 26, bold: true });
    text(slide, c.body, x + 24, y + 96, w - 48, 160, { size: 20, color: colors.muted });
    if (c.foot) text(slide, c.foot, x + 24, y + 260, w - 48, 32, { size: 17, bold: true, color: c.color ?? accent });
  });
}

function claimSlide(p, course, n, heading, claim, cols) {
  const slide = p.slides.add();
  label(slide, course, n);
  text(slide, heading, M.left, 78, 1000, 56, { size: 38, bold: true });
  text(slide, claim, M.left, 148, 1040, 52, { size: 22, color: colors.muted });
  threeColumn(slide, 250, cols);
}

function processSlide(p, course, n, heading, steps, bottom) {
  const slide = p.slides.add();
  label(slide, course, n);
  text(slide, heading, M.left, 78, 1000, 58, { size: 39, bold: true });
  const startX = 82;
  steps.forEach((s, i) => {
    const x = startX + i * 222;
    box(slide, x, 210, 178, 230, "#FFFFFF", colors.rule);
    text(slide, String(i + 1), x + 20, 230, 56, 44, { size: 34, bold: true, color: colors.orange });
    text(slide, s.head, x + 20, 292, 136, 54, { size: 22, bold: true });
    text(slide, s.body, x + 20, 358, 136, 54, { size: 17, color: colors.muted });
    if (i < steps.length - 1) text(slide, "→", x + 184, 298, 40, 40, { size: 34, color: colors.muted, align: "center" });
  });
  box(slide, M.left, 520, 1130, 82, colors.pale, "none");
  text(slide, bottom, M.left + 28, 542, 1080, 38, { size: 23, bold: true });
}

function tableSlide(p, course, n, heading, rows) {
  const slide = p.slides.add();
  label(slide, course, n);
  text(slide, heading, M.left, 78, 1040, 60, { size: 39, bold: true });
  const x = M.left;
  const y = 176;
  const widths = [240, 310, 310, 290];
  ["场景", "输入材料", "Skill 该做什么", "验收结果"].forEach((h, i) => {
    const left = x + widths.slice(0, i).reduce((a, b) => a + b, 0);
    box(slide, left, y, widths[i], 54, colors.ink, colors.ink);
    text(slide, h, left + 14, y + 14, widths[i] - 28, 26, { size: 18, bold: true, color: "#FFFFFF" });
  });
  rows.forEach((r, ri) => {
    const top = y + 54 + ri * 82;
    r.forEach((cell, ci) => {
      const left = x + widths.slice(0, ci).reduce((a, b) => a + b, 0);
      box(slide, left, top, widths[ci], 82, ri % 2 ? "#FAFAFA" : "#FFFFFF", colors.rule);
      text(slide, cell, left + 14, top + 14, widths[ci] - 28, 50, { size: 17, color: ci === 0 ? colors.ink : colors.muted, bold: ci === 0 });
    });
  });
}

function closeSlide(p, course, n, title, actions) {
  const slide = p.slides.add();
  label(slide, course, n);
  text(slide, title, M.left, 92, 1000, 86, { size: 46, bold: true });
  actions.forEach((a, i) => {
    const y = 230 + i * 96;
    text(slide, `0${i + 1}`, M.left, y + 2, 70, 40, { size: 30, bold: true, color: colors.orange });
    text(slide, a, 150, y, 900, 44, { size: 25, bold: true });
    box(slide, 150, y + 62, 850, 1, colors.rule, "none");
  });
}

async function saveDeck(p, fileName, slug) {
  await fs.mkdir(OUT, { recursive: true });
  await fs.mkdir(path.join(PREVIEW, slug), { recursive: true });
  for (const [i, slide] of p.slides.items.entries()) {
    const stem = `slide-${String(i + 1).padStart(2, "0")}`;
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(PREVIEW, slug, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(PREVIEW, `${slug}-montage.webp`), new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(path.join(OUT, fileName));
}

async function buildIntro() {
  const p = deck();
  const course = "课程一｜Skill 入门认知";
  titleSlide(p, course, "把重复经验变成可复用 AI 工作流", "面向非标自动化部门的共同语言课");
  agendaSlide(p, course, 2, [
    { title: "Skill 是什么", body: "它不是一句提示词，而是一套可重复执行的工作方法。" },
    { title: "为什么现在需要", body: "非标项目多、知识分散、交付靠经验，Skill 可以把经验沉淀下来。" },
    { title: "每个岗位怎么用", body: "电控、机构、文职和生物管都可以把稳定流程交给 Skill 协助。" },
  ]);
  claimSlide(p, course, 3, "Skill 的本质是“工作流说明书 + 资料包”", "Codex 手册把 Skill 描述为可复用工作流的作者格式：它包装指令、资源和可选脚本，让 Codex 更可靠地完成特定任务。", [
    { head: "指令", body: "告诉 AI 遇到什么任务时该怎么做、先看什么、按什么步骤产出。", foot: "像标准作业指导书" },
    { head: "资源", body: "放模板、术语表、验收表、历史案例、格式规范等可复用资料。", foot: "像部门知识库" },
    { head: "脚本", body: "需要确定性处理时加入脚本，例如批量检查表格、生成目录、校验格式。", foot: "像自动化小工具" },
  ]);
  claimSlide(p, course, 4, "不要把 Skill 和普通提示词混为一谈", "提示词解决一次问题，Skill 让一类问题以后都按同一套方法解决。", [
    { head: "提示词", body: "适合一次性提问、临时分析、快速改写。结果质量取决于这次描述是否完整。", color: colors.blue },
    { head: "Skill", body: "适合反复出现的任务。规则、输入、输出和验收要求可以长期保留。", color: colors.orange },
    { head: "插件", body: "适合分发安装。插件可以打包多个 Skill，也可以带工具、MCP 或应用连接。", color: colors.green },
  ]);
  processSlide(p, course, 5, "一个 Skill 从触发到产出通常这样工作", [
    { head: "识别任务", body: "用户点名或描述命中 Skill 范围" },
    { head: "读取说明", body: "AI 打开 SKILL.md 获取完整流程" },
    { head: "调用资料", body: "按需读取模板、清单、脚本" },
    { head: "执行产出", body: "生成文档、代码、表格或检查结论" },
    { head: "验证交付", body: "按 Skill 的验收规则检查结果" },
  ], "关键点：Skill 的描述写得越清楚，AI 越容易在正确场景自动使用它。");
  tableSlide(p, course, 6, "非标自动化部门天然适合沉淀 Skill", [
    ["方案评审", "客户 URS、节拍、工艺流程", "提取风险、列问题清单、补齐评审要点", "评审表和待确认问题"],
    ["电控设计", "IO 表、元件清单、动作流程", "检查点位、命名、互锁和报警逻辑", "异常项清单"],
    ["机构设计", "布局图、工站说明、限制条件", "整理设计边界、装配风险、维护空间", "机构评审提纲"],
    ["文职资料", "会议纪要、报价信息、验收模板", "归档、汇总、生成标准格式资料", "可提交文档"],
  ]);
  claimSlide(p, course, 7, "好的 Skill 先从“小而稳定”的工作开始", "不要一开始就做“自动完成整个项目”。先找边界清楚、资料稳定、验收明确的任务。", [
    { head: "高频", body: "每周都会出现，重复写法或检查点很多。" },
    { head: "有标准", body: "部门已经知道什么算合格，只是执行靠人记。" },
    { head: "低风险", body: "AI 辅助整理、检查、提醒，人最终确认。" },
  ]);
  processSlide(p, course, 8, "把一个岗位经验变成 Skill 的五句话", [
    { head: "谁用", body: "岗位和场景" },
    { head: "何时触发", body: "什么输入出现" },
    { head: "先看什么", body: "资料与判断顺序" },
    { head: "产出什么", body: "格式、字段、口径" },
    { head: "怎么验收", body: "检查清单和禁区" },
  ], "只要这五句话能讲清楚，就已经具备写 Skill 初稿的条件。");
  closeSlide(p, course, 9, "第一课结束时，希望大家形成三个判断", [
    "Skill 是把部门经验固化给 AI 使用，不是让 AI 自由发挥。",
    "越稳定、越重复、越有验收标准的工作，越适合先做 Skill。",
    "不同岗位都可以贡献 Skill，代码能力不是前提，流程清楚才是前提。",
  ]);
  await saveDeck(p, "01-Skill入门认知-非标自动化部门.pptx", "01-intro");
}

async function buildCreate() {
  const p = deck();
  const course = "课程二｜建立与使用 Skill";
  titleSlide(p, course, "从一个好流程到一个可用 Skill", "带大家看懂结构、写法、触发和验证");
  agendaSlide(p, course, 2, [
    { title: "Skill 放在哪里", body: "了解本地、项目、团队共享和插件分发的差别。" },
    { title: "SKILL.md 怎么写", body: "用名称、描述、步骤、输入输出、验收标准搭出骨架。" },
    { title: "怎么测试", body: "用真实提示词和真实样例检查触发是否准确、结果是否稳定。" },
  ]);
  claimSlide(p, course, 3, "一个最小 Skill 只需要一个文件夹和一个 SKILL.md", "SKILL.md 顶部必须有 name 和 description；后面写 AI 执行这类任务时应遵守的步骤。", [
    { head: "name", body: "短、唯一、好记。建议使用英文小写加短横线，便于点名调用。" },
    { head: "description", body: "写清何时使用、何时不要用。隐式触发主要靠这一句。" },
    { head: "instructions", body: "按顺序写输入、处理步骤、输出格式和验证要求。" },
  ]);
  tableSlide(p, course, 4, "Skill 可以按范围存放，范围越大越要谨慎", [
    ["项目 Skill", ".agents/skills", "只服务某个项目或模块", "跟项目一起沉淀"],
    ["个人 Skill", "$HOME/.agents/skills", "个人跨项目复用", "适合先试点"],
    ["管理 Skill", "共享机器或容器位置", "统一发给一组人", "需要管理员维护"],
    ["系统 Skill", "Codex 自带", "通用能力", "直接使用即可"],
  ]);
  processSlide(p, course, 5, "创建 Skill 的实操路径", [
    { head: "选场景", body: "找高频、稳定、有标准的任务" },
    { head: "写触发", body: "description 讲清范围" },
    { head: "写流程", body: "拆成可执行步骤" },
    { head: "放资料", body: "模板、表格、范例" },
    { head: "试运行", body: "用真实输入修正" },
  ], "先做 instruction-only 版本，等流程稳定后再考虑脚本。");
  claimSlide(p, course, 6, "description 决定 Skill 会不会被正确叫醒", "它应该像门牌：让 AI 一眼知道什么时候进这个房间，什么时候不要进。", [
    { head: "好描述", body: "用于根据客户 URS 和项目资料生成非标自动化方案评审问题清单，并识别节拍、工艺、验收风险。" },
    { head: "差描述", body: "帮助自动化部门做事情。范围太大，AI 不知道什么时候该用。" },
    { head: "边界句", body: "不要用于最终工程签核、报价承诺或未经人工确认的安全判断。" },
  ]);
  claimSlide(p, course, 7, "一个可用 Skill 要把输出格式写死", "当输出字段稳定，后续复制、归档、评审和统计才会省力。", [
    { head: "标题", body: "说明项目、资料版本、生成日期和输入来源。" },
    { head: "表格", body: "字段固定，例如问题、影响、建议确认人、优先级、依据。" },
    { head: "结论", body: "用“可继续/需补充/风险较高”这类可行动状态收尾。" },
  ]);
  tableSlide(p, course, 8, "测试 Skill 时不要只看一次漂亮输出", [
    ["触发测试", "三条真实提示词", "该触发时触发，不该触发时沉默", "减少误用"],
    ["样例测试", "历史项目资料", "是否漏掉关键字段", "补齐流程"],
    ["边界测试", "资料不完整或冲突", "能否主动列待确认项", "防止瞎编"],
    ["验收测试", "部门标准模板", "格式和口径是否一致", "便于交付"],
  ]);
  processSlide(p, course, 9, "Skill 的迭代节奏像改一份部门 SOP", [
    { head: "先可用", body: "能覆盖 60% 常见情况" },
    { head: "收反馈", body: "记录错触发、漏项、格式问题" },
    { head: "改说明", body: "优先改触发和验收" },
    { head: "加资料", body: "补模板、术语、案例" },
    { head: "再共享", body: "稳定后给更多人用" },
  ], "不要追求一次写完。Skill 的价值来自持续把真实工作反馈写回去。");
  claimSlide(p, course, 10, "什么时候该加脚本，什么时候只写说明", "脚本适合确定性处理；判断、整理、改写和评审逻辑通常先用说明就够。", [
    { head: "只写说明", body: "会议纪要整理、方案评审提纲、风险问题提取、文档润色。" },
    { head: "加脚本", body: "批量读取 Excel、检查 IO 命名、统计 BOM 字段、生成固定编号。" },
    { head: "先别做", body: "直接控制设备、替代签核、绕过安全评审、自动承诺成本交期。" },
  ]);
  closeSlide(p, course, 11, "第二课的现场练习", [
    "每个岗位选一个高频任务，写出“谁用、何时触发、输入、输出、验收”。",
    "用三条真实提示词测试 description 是否准确。",
    "把第一版 Skill 当作草稿 SOP，先让同岗位同事试用一周。",
  ]);
  await saveDeck(p, "02-Skill建立与使用实操.pptx", "02-create");
}

async function buildCases() {
  const p = deck();
  const course = "课程三｜非标自动化工作转换案例";
  titleSlide(p, course, "把现在的工作转换成 Skill", "电控、机构、文职和生物管岗位的案例工作坊");
  agendaSlide(p, course, 2, [
    { title: "先找可转换任务", body: "从重复、标准、资料驱动的工作里选题。" },
    { title: "看四类岗位案例", body: "电控、机构、文职、生物管分别给出 Skill 设计样例。" },
    { title: "形成部门路线图", body: "从 3 个试点 Skill 开始，逐步建立部门知识资产。" },
  ]);
  tableSlide(p, course, 3, "岗位任务转换 Skill 的优先级判断", [
    ["高优先", "重复检查、资料整理、模板生成", "标准清楚、风险低", "先做"],
    ["中优先", "方案初审、风险提示、会议追踪", "需要人工复核", "试点"],
    ["低优先", "报价承诺、最终设计签核", "责任重大", "只做辅助"],
    ["不建议", "跳过安全流程、直接控制设备", "后果不可控", "禁止"],
  ]);
  tableSlide(p, course, 4, "案例一：电控工程师的 IO 表检查 Skill", [
    ["输入", "IO 表、元件清单、动作说明", "读取点位命名、设备归属、信号类型", "资料缺口清单"],
    ["检查", "命名规则、DI/DO/AI/AO 分类", "识别重复点位、未归属点位、异常缩写", "异常项表格"],
    ["逻辑", "报警、互锁、安全回路描述", "提示缺少复位、急停、门禁或气压条件", "风险等级"],
    ["输出", "Excel 或 Markdown 表格", "按问题、依据、建议处理人输出", "评审用清单"],
  ]);
  processSlide(p, course, 5, "电控 Skill 的触发语可以这样写", [
    { head: "收到资料", body: "客户动作流程和 IO 表" },
    { head: "调用 Skill", body: "$io-review" },
    { head: "列问题", body: "重复、缺失、命名异常" },
    { head: "分风险", body: "安全、调试、维护" },
    { head: "给结论", body: "可继续或需补资料" },
  ], "定位：辅助评审和查漏，不替代电气设计签核。");
  tableSlide(p, course, 6, "案例二：机构工程师的方案评审 Skill", [
    ["输入", "布局图、工站说明、产品限制", "提取机构动作、夹治具、空间边界", "工站摘要"],
    ["检查", "上料、定位、压装、检测、下料", "追问维护空间、换型、避让和防呆", "评审问题"],
    ["风险", "节拍、刚性、装配、可达性", "按影响程度排序", "风险清单"],
    ["输出", "评审提纲", "按工站列出确认项和建议", "会议材料"],
  ]);
  claimSlide(p, course, 7, "机构类 Skill 特别适合做“问题清单生成器”", "非标方案早期最贵的不是多问问题，而是关键问题没有被问出来。", [
    { head: "客户边界", body: "产品公差、来料状态、节拍目标、验收方式。" },
    { head: "设计边界", body: "空间、气源、电源、治具寿命、维护可达性。" },
    { head: "交付边界", body: "换型频率、备件、现场调试、培训资料。" },
  ]);
  tableSlide(p, course, 8, "案例三：文职人员的项目资料归档 Skill", [
    ["输入", "会议纪要、报价单、合同节点、验收模板", "识别项目编号和版本", "缺失资料清单"],
    ["整理", "按阶段归档", "方案、采购、装配、调试、验收分层", "目录结构建议"],
    ["生成", "周报、问题追踪表、会议纪要", "统一格式和字段", "可提交文件"],
    ["提醒", "责任人、截止日期、待客户确认", "生成跟进清单", "减少遗漏"],
  ]);
  tableSlide(p, course, 9, "案例四：生物管/质量资料岗位的合规检查 Skill", [
    ["输入", "URS、验证方案、测试记录", "提取关键要求和验收标准", "要求矩阵"],
    ["检查", "签名、日期、版本、偏差记录", "识别缺项和不一致", "整改清单"],
    ["追溯", "需求到测试项", "确认每条要求是否有证据", "追溯表"],
    ["输出", "合规检查摘要", "按严重程度列问题", "复核材料"],
  ]);
  processSlide(p, course, 10, "部门级 Skill 路线图建议从 3 个试点开始", [
    { head: "资料整理", body: "低风险、高频、全员受益" },
    { head: "方案评审", body: "沉淀经验、减少漏问" },
    { head: "IO 检查", body: "规则明确、技术收益高" },
    { head: "试用修订", body: "每周收集问题" },
    { head: "扩展岗位", body: "再做机构和质量类" },
  ], "先让 Skill 帮大家少漏项、少重复、少格式返工。");
  claimSlide(p, course, 11, "建立 Skill 清单时，每条都要写清风险边界", "AI 可以帮助整理、提醒和检查，但项目责任仍在岗位负责人和评审流程。", [
    { head: "可让 AI 做", body: "提取、归类、生成初稿、查漏、改格式、总结差异。" },
    { head: "必须人工定", body: "安全判断、设计签核、报价承诺、客户最终回复。" },
    { head: "必须留痕", body: "输入资料版本、输出时间、人工确认人、修改记录。" },
  ]);
  closeSlide(p, course, 12, "课后落地动作", [
    "每个岗位提交 1 个候选 Skill，说明输入、输出和验收标准。",
    "部门先选 3 个试点，试用两周后统一修订。",
    "把有效 Skill 纳入项目启动、方案评审和资料归档流程。",
  ]);
  await saveDeck(p, "03-非标自动化工作转换Skill案例.pptx", "03-cases");
}

await buildIntro();
await buildCreate();
await buildCases();
