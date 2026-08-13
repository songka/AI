import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = process.cwd().replaceAll("\\", "/");
const OUT = `${ROOT}/outputs`;
const PREVIEW = `${ROOT}/work/presentations/skill-training/tmp/preview/ai-course-v2`;
const W = 1280;
const H = 720;

const c = {
  ink: "#111111",
  muted: "#555555",
  panel: "#EDEDED",
  panel2: "#F6F6F6",
  rule: "#B8BCC4",
  accent: "#FF6B35",
  blue: "#2563EB",
  green: "#059669",
  red: "#DC2626",
  purple: "#7C3AED",
};

const font = "Microsoft YaHei";

function normalizeTerms(value) {
  if (typeof value !== "string") return value;
  return value
    .replace(/MCP\/工具/g, "模型上下文协议（MCP）/工具")
    .replace(/工具\/MCP/g, "工具/模型上下文协议（MCP）")
    .replace(/Agent 智能体/g, "智能体（Agent）")
    .replace(/智能体 Agent/g, "智能体（Agent）")
    .replace(/大语言模型（LLM）/g, "大语言模型（LLM）")
    .replace(/(?<!（)LLM(?!）)/g, "大语言模型（LLM）")
    .replace(/(?<!（)Agent(?!）)/g, "智能体（Agent）")
    .replace(/(?<!（)Skill(?!）)/g, "技能（Skill）")
    .replace(/(?<!（)MCP(?!）)/g, "模型上下文协议（MCP）")
    .replace(/(?<!（)Prompt(?!）)/g, "提示词（Prompt）")
    .replace(/(?<!（)Workflow(?!）)/g, "工作流（Workflow）")
    .replace(/(?<!（)Memory(?!）)/g, "记忆（Memory）")
    .replace(/Knowledge Base/g, "知识库（Knowledge Base）");
}

function shape(slide, x, y, w, h, fill = "none", line = "none") {
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
  s.text = normalizeTerms(value);
  s.text.style = {
    fontFace: font,
    fontSize: opts.size ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? c.ink,
    alignment: opts.align ?? "left",
  };
  return s;
}

function notes(slide, lines) {
  const normalized = (Array.isArray(lines) ? lines : [lines]).map(normalizeTerms);
  slide.speakerNotes.textFrame.setText(normalized);
  slide.speakerNotes.setVisible(true);
}

function footer(slide, course, n) {
  text(slide, course, 56, 30, 760, 26, { size: 15, bold: true, color: c.muted });
  text(slide, String(n).padStart(2, "0"), W - 94, H - 46, 42, 24, { size: 14, color: c.muted, align: "right" });
}

function title(slide, course, n, t, sub = "") {
  slide.background.fill = "#FFFFFF";
  footer(slide, course, n);
  text(slide, t, 58, 82, 980, 68, { size: 40, bold: true });
  if (sub) text(slide, sub, 60, 154, 1060, 42, { size: 22, color: c.muted });
}

function cover(slide, course, t, sub, note) {
  slide.background.fill = "#FFFFFF";
  shape(slide, 58, 92, 10, 490, c.accent, c.accent);
  text(slide, course, 92, 96, 760, 28, { size: 18, bold: true, color: c.muted });
  text(slide, t, 92, 170, 930, 132, { size: 50, bold: true });
  text(slide, sub, 94, 326, 860, 54, { size: 24, color: c.muted });
  shape(slide, 96, 470, 920, 74, c.panel2, c.rule);
  text(slide, "课堂主线：一个聪明新人进部门，怎么从会聊天，变成能按规范帮忙干活。", 120, 494, 860, 24, { size: 20, bold: true });
  notes(slide, note);
}

function bullets(slide, course, n, t, sub, items, note) {
  title(slide, course, n, t, sub);
  let y = 230;
  for (const item of items) {
    const color = item.color ?? c.accent;
    shape(slide, 66, y + 6, 8, 42, color, color);
    text(slide, item.head, 96, y, 360, 30, { size: 24, bold: true, color });
    text(slide, item.body, 96, y + 36, 1000, 46, { size: 18, color: c.ink });
    y += item.gap ?? 86;
  }
  notes(slide, note);
}

function compare(slide, course, n, t, sub, rows, note) {
  title(slide, course, n, t, sub);
  const x = 64, y = 230;
  const widths = [170, 310, 310, 310];
  const heads = ["概念", "像什么", "负责什么", "不能替人做什么"];
  let cx = x;
  for (let i = 0; i < heads.length; i++) {
    shape(slide, cx, y, widths[i], 46, c.panel, c.rule);
    text(slide, heads[i], cx + 10, y + 13, widths[i] - 20, 20, { size: 16, bold: true, align: "center" });
    cx += widths[i];
  }
  let cy = y + 46;
  for (const row of rows) {
    cx = x;
    for (let i = 0; i < row.length; i++) {
      shape(slide, cx, cy, widths[i], 64, i === 0 ? "#FFFFFF" : c.panel2, c.rule);
      text(slide, row[i], cx + 10, cy + 10, widths[i] - 20, 40, { size: i === 0 ? 17 : 14, bold: i === 0 });
      cx += widths[i];
    }
    cy += 64;
  }
  notes(slide, note);
}

function exercise(slide, course, n, t, scenario, tasks, note) {
  title(slide, course, n, t, scenario);
  shape(slide, 70, 238, 360, 330, c.panel2, c.rule);
  text(slide, "模拟练习", 94, 264, 280, 30, { size: 26, bold: true, color: c.blue });
  text(slide, tasks.sim, 94, 318, 300, 190, { size: 19 });
  shape(slide, 490, 238, 360, 330, c.panel2, c.rule);
  text(slide, "实际练习", 514, 264, 280, 30, { size: 26, bold: true, color: c.green });
  text(slide, tasks.real, 514, 318, 300, 190, { size: 19 });
  shape(slide, 910, 238, 250, 330, c.panel2, c.rule);
  text(slide, "交付物", 934, 264, 180, 30, { size: 26, bold: true, color: c.accent });
  text(slide, tasks.output, 934, 318, 180, 190, { size: 19 });
  notes(slide, note);
}

function examplePair(slide, course, n, t, wrong, right, note) {
  title(slide, course, n, t, "先看真实做法，再进入练习。错误例子说明风险，正确例子说明可落地方式。");
  shape(slide, 74, 232, 500, 346, "#FFF5F5", c.rule);
  shape(slide, 706, 232, 500, 346, "#F0FDF4", c.rule);
  text(slide, "错误例子", 102, 260, 420, 32, { size: 28, bold: true, color: c.red });
  text(slide, wrong.title, 102, 314, 420, 28, { size: 21, bold: true });
  text(slide, wrong.body, 102, 358, 410, 96, { size: 18 });
  text(slide, `问题：${wrong.problem}`, 102, 482, 410, 56, { size: 17, color: c.red, bold: true });
  text(slide, "正确例子", 734, 260, 420, 32, { size: 28, bold: true, color: c.green });
  text(slide, right.title, 734, 314, 420, 28, { size: 21, bold: true });
  text(slide, right.body, 734, 358, 410, 96, { size: 18 });
  text(slide, `效果：${right.result}`, 734, 482, 410, 56, { size: 17, color: c.green, bold: true });
  notes(slide, note);
}

function qa(slide, course, n, t, qs, note) {
  title(slide, course, n, t, "这些问题来自模拟角色：电控、机构、软件、文职、生物管/质量、管理者。");
  let y = 232;
  for (const q of qs) {
    shape(slide, 72, y, 1040, 58, c.panel2, c.rule);
    text(slide, `问：${q.q}`, 92, y + 10, 1000, 20, { size: 17, bold: true, color: c.ink });
    text(slide, `答：${q.a}`, 92, y + 34, 1000, 18, { size: 15, color: c.muted });
    y += 72;
  }
  notes(slide, note);
}

function checklist(slide, course, n, t, columns, note) {
  title(slide, course, n, t, "先判断边界，再决定是否让 AI 继续做。");
  const xs = [70, 446, 822];
  columns.forEach((col, i) => {
    shape(slide, xs[i], 232, 320, 350, c.panel2, c.rule);
    text(slide, col.head, xs[i] + 22, 260, 270, 28, { size: 25, bold: true, color: col.color });
    text(slide, col.body, xs[i] + 22, 318, 260, 210, { size: 18 });
  });
  notes(slide, note);
}

async function saveDeck(deck) {
  const p = Presentation.create({ slideSize: { width: W, height: H } });
  deck.build(p);
  const deckPreview = `${PREVIEW}/${deck.slug}`;
  await fs.mkdir(deckPreview, { recursive: true });
  for (const [i, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(deckPreview, `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(deckPreview, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(`${OUT}/${deck.file}`);
}

const commonQ = [
  { q: "AI 写错了，责任怎么算？", a: "AI 做初稿和检查，人做确认和签发；关键技术、质量、合规结论不能交给 AI 自动决定。" },
  { q: "为什么不用普通聊天就够了？", a: "聊天适合临时问答；Skill 固定方法，Agent 完成多步任务，工具连接真实数据，记忆减少重复说明。" },
  { q: "会不会泄密或越权？", a: "公共环境只用脱敏样例；企业落地要有权限、日志、最小工具范围和人工确认点。" },
];

const decks = [
  {
    slug: "07-concepts",
    file: "07-新版01-AI名词比喻与关系-修订版-带讲师备注.pptx",
    build(p) {
      const course = "新版课程 01 / AI 名词比喻与关系";
      let s = p.slides.add();
      cover(s, course, "先看懂 AI 里的各个名词", "用“一个新人进部门”的比喻，讲清 LLM、Agent、Skill、MCP、记忆、知识库、工作流。", [
        "开场不要从定义开始。先问：如果一个新人今天入职，他要怎么从会聊天变成能帮部门干活？",
        "本课目标：让不同岗位听众能说出每个概念负责什么、不能负责什么。",
      ]);
      s = p.slides.add();
      bullets(s, course, 2, "AI 不是一个东西，而是一套协作系统", "不要把所有能力都叫“AI”。分清角色，后面才知道怎么用。", [
        { head: "大语言模型", body: "像一个会理解、会表达、会推理的新同事，但它不知道你们公司的内部资料。", color: c.blue },
        { head: "Agent", body: "像接到目标后能拆步骤、查资料、调用工具的助理。", color: c.green },
        { head: "Skill", body: "像岗位作业指导书，把老师傅的方法写成 AI 可复用能力。", color: c.accent },
        { head: "MCP/工具", body: "像助理能使用的电脑、Excel、ERP、图纸库、脚本和接口。", color: c.purple },
        { head: "记忆与知识库", body: "记忆像习惯本，知识库像资料室；两者不能混用。", color: c.red },
      ], ["讲师提示：用人、手册、工具箱、习惯本、资料室五个实物比喻讲。"]);
      s = p.slides.add();
      compare(s, course, 3, "七个概念的区别与联系", "每个概念只回答一个问题：它在团队里承担什么职责。", [
        ["LLM", "会说话的新同事", "理解、总结、生成、推理", "不能天然知道公司资料"],
        ["Agent", "项目助理", "拆任务、推进步骤、汇报结果", "不能越权行动"],
        ["Skill", "作业指导书", "固定方法、标准、输出格式", "不能替代责任判断"],
        ["MCP/工具", "工具箱", "读表、查库、跑脚本、连系统", "不能无限访问"],
        ["记忆", "习惯本", "记偏好、术语、长期背景", "不能存敏感资料"],
        ["知识库", "资料室", "查规范、SOP、历史案例", "不能放过期资料"],
      ], ["讲师提示：强调“联系”：Agent 通常调用 Skill、工具和知识库，模型负责理解与生成。"]);
      s = p.slides.add();
      bullets(s, course, 4, "同一个任务，可以看到所有概念", "例子：根据客户 URS 生成一次非标设备方案评审准备包。", [
        { head: "模型", body: "读懂 URS，提取功能、节拍、空间、安全、追溯要求。", color: c.blue },
        { head: "Skill", body: "按部门方案评审方法输出风险点、证据、责任专业。", color: c.accent },
        { head: "Agent", body: "拆成需求提取、资料查询、风险匹配、清单生成、人工确认。", color: c.green },
        { head: "工具/知识库", body: "读取 BOM、历史问题库、标准件库、验收模板。", color: c.purple },
        { head: "记忆", body: "记住部门常用术语和客户长期偏好，但不保存敏感项目细节。", color: c.red },
      ], ["讲师提示：这页作为贯穿案例，后面每课都回到同一个案例。"]);
      s = p.slides.add();
      examplePair(s, course, 5, "真实例子：同样是做项目周报，差别很大", {
        title: "只把会议纪要丢给 AI",
        body: "项目文职直接输入：帮我写一份周报。没有说明项目范围、数据来源、责任人、风险口径。",
        problem: "模型容易把猜测写成事实，漏掉延期风险，也无法区分哪些内容需要人工确认。",
      }, {
        title: "先拆清楚 AI 系统要做什么",
        body: "模型负责整理语言，技能（Skill）规定周报格式，智能体（Agent）读取任务清单，工具核对日期和责任人。",
        result: "输出包含进度、风险、待确认事项和来源，人只需按复核清单确认。",
      }, ["讲师提示：这页放在练习前，先让学员看到“会问 AI”和“会设计 AI 工作方式”的区别。"]);
      s = p.slides.add();
      exercise(s, course, 6, "练习：把名词放回真实任务", "不要背定义，要判断工作链条里缺哪种能力。", {
        sim: "发 5 张概念卡：模型、Skill、Agent、工具、记忆。让学员配对“大脑、手册、助理、工具箱、习惯本”。",
        real: "每组选择一个岗位任务，说明它需要哪些能力，例如会议纪要、IO 表检查、BOM 初筛、实验记录整理。",
        output: "一张任务拆解卡：任务、输入、需要能力、人工确认点。",
      }, ["讲师提示：先让非技术岗位发言，避免课堂被工程术语占满。"]);
      s = p.slides.add();
      checklist(s, course, 7, "哪些事情可以先用，哪些必须谨慎", [
        { head: "适合先用", body: "会议纪要\n周报草稿\nBOM 字段检查\n问题单归类\n报警文本整理", color: c.green },
        { head: "需要确认", body: "测试用例\nPLC 注释\n设计评审清单\n供应商邮件\n质量摘要", color: c.accent },
        { head: "默认禁止", body: "下发程序\n修改安全参数\n删除资料\n自动判定验收\n上传客户敏感文件", color: c.red },
      ], ["讲师提示：明确责任边界。AI 是助手，不是签字人。"]);
      s = p.slides.add();
      qa(s, course, 8, "模拟课堂问答", commonQ, ["讲师提示：回答时用三段式：承认边界，说明控制方法，给部门例子。"]);
    },
  },
  {
    slug: "08-skill",
    file: "08-新版02-Skill专项与岗位实操-修订版-带讲师备注.pptx",
    build(p) {
      const course = "新版课程 02 / Skill 专项";
      let s = p.slides.add();
      cover(s, course, "Skill 是岗位经验的作业指导书", "把电控、机构、软件、文职、生物管的重复工作，写成 AI 能稳定执行的方法。", [
        "开场复习：模型会说话，Skill 让它按专业方法干活。",
        "本课目标：每组产出一个岗位 Skill 草稿。",
      ]);
      s = p.slides.add();
      bullets(s, course, 2, "Skill 解决的是“每次都按同一套方法做”", "不要把 Skill 简化成一句 Prompt。", [
        { head: "适合", body: "格式固定、标准明确、反复出现、人工容易复核的任务。", color: c.green },
        { head: "不适合", body: "资料缺失、规则天天变、最终责任判断、高风险设备动作。", color: c.red },
        { head: "核心结构", body: "适用场景、输入材料、执行步骤、判断标准、输出格式、人工确认点。", color: c.blue },
        { head: "价值", body: "减少重复解释，让新人和 AI 都按同一套部门方法输出。", color: c.accent },
      ], ["讲师提示：强调 Skill 是可复用方法，不是万能插件。"]);
      s = p.slides.add();
      compare(s, course, 3, "Prompt、Skill、知识库不要混为一谈", "三者可以配合，但职责不同。", [
        ["Prompt", "临时口头提醒", "这一次怎么回答", "不能保证长期一致"],
        ["Skill", "作业指导书", "按固定流程做事", "不能提供所有业务资料"],
        ["知识库", "资料室", "提供规范、案例、模板", "不会自动形成流程"],
        ["工作流", "SOP 流程", "把多步任务固定下来", "不能替代审核责任"],
      ], ["讲师提示：举例：电气命名规范是知识库，按规范检查 IO 表是 Skill。"]);
      s = p.slides.add();
      bullets(s, course, 4, "岗位 Skill 示例", "每个岗位先从低风险、高频、输出可复核的任务开始。", [
        { head: "电控", body: "IO 表检查：安全信号、急停、复位、原点、报警、地址重复。", color: c.blue },
        { head: "机构", body: "方案评审：定位、夹紧、防呆、维护空间、易损件更换。", color: c.green },
        { head: "软件", body: "接口检查：异常处理、日志、重试、权限、配置项。", color: c.purple },
        { head: "文职", body: "会议纪要：待办、责任人、截止日期、风险和待确认事项。", color: c.accent },
        { head: "生物管/质量", body: "记录预检：样本编号、试剂批号、版本、签名、异常描述。", color: c.red },
      ], ["讲师提示：让每类岗位至少看到一个自己的例子。"]);
      s = p.slides.add();
      examplePair(s, course, 5, "真实例子：同样是 IO 表检查，Skill 写法决定结果", {
        title: "错误 Skill：只写一句要求",
        body: "“帮我检查 IO 表有没有问题。”没有说明输入字段、检查顺序、命名规则、输出格式和人工确认点。",
        problem: "AI 可能只做表面总结，漏掉重复地址、安全信号缺失和命名不一致。",
      }, {
        title: "正确 Skill：写成可执行检查流程",
        body: "先检查空字段和重复地址，再按安全、气缸、传感器、报警分类；最后输出问题、影响、建议和责任专业。",
        result: "每次都按同一套标准输出，电控工程师可以快速复核和补充判断。",
      }, ["讲师提示：这页要强调技能（Skill）不是一句提示词（Prompt），而是一套可复用检查方法。"]);
      s = p.slides.add();
      exercise(s, course, 6, "练习：写一个岗位 Skill 草稿", "把自己的日常重复流程写成 AI 能执行的说明。", {
        sim: "讲师给出反例：'帮我检查方案'。让学员指出它缺少输入、步骤、标准和输出格式。",
        real: "每组选择一个真实任务，填：适用场景、输入材料、执行步骤、检查清单、输出格式、人工确认点。",
        output: "一页 Skill 草稿，可直接作为后续试点输入。",
      }, ["讲师提示：不要追求完整系统，目标是写清楚一个小任务。"]);
      s = p.slides.add();
      checklist(s, course, 7, "一个 Skill 是否合格，看六项", [
        { head: "能触发", body: "适用场景清楚\n输入材料清楚\n岗位边界清楚", color: c.blue },
        { head: "能执行", body: "步骤是动作\n标准可检查\n输出有格式", color: c.green },
        { head: "能复核", body: "列出依据\n标记不确定\n保留人工确认点", color: c.accent },
      ], ["讲师提示：互评时按这六项打勾，不要只评价文字是否漂亮。"]);
      s = p.slides.add();
      qa(s, course, 8, "模拟课堂问答", [
        { q: "Skill 如果只是 Prompt，价值是不是被夸大了？", a: "一句 Prompt 是临时提醒；Skill 要包含流程、标准、边界和固定输出，能长期复用和复核。" },
        { q: "我们流程经常变，做 Skill 会不会维护成本很高？", a: "先做稳定部分。把经常变的项目参数放输入，把长期稳定的检查方法写进 Skill。" },
        { q: "AI 建议和老师傅经验冲突怎么办？", a: "先看 AI 依据。若老师傅经验正确但没文档化，应沉淀进 Skill 或知识库。" },
      ], ["讲师提示：用冲突问题引导大家把经验显性化。"]);
    },
  },
  {
    slug: "09-agent",
    file: "09-新版03-Agent智能体专项与岗位实操-修订版-带讲师备注.pptx",
    build(p) {
      const course = "新版课程 03 / Agent 智能体专项";
      let s = p.slides.add();
      cover(s, course, "Agent 让 AI 从回答问题变成完成任务", "重点不是人设，而是目标、步骤、工具、检查和汇报。", [
        "开场问题：'解释这段报警文本'和'读取全部报警表并生成修改建议'有什么区别？",
        "本课目标：每组设计一个岗位 Agent 卡片。",
      ]);
      s = p.slides.add();
      bullets(s, course, 2, "Agent 的关键是任务闭环", "它不是更会聊天，而是会把目标拆成步骤。", [
        { head: "目标", body: "要完成什么，范围到哪里，验收标准是什么。", color: c.blue },
        { head: "计划", body: "先读什么、再查什么、何时停下来问人。", color: c.green },
        { head: "工具", body: "读取文件、查询表格、调用脚本、连接系统。", color: c.purple },
        { head: "反馈", body: "检查中间结果，标记不确定项，输出证据和风险。", color: c.accent },
      ], ["讲师提示：Agent 的“自主”必须有边界，不是放任。"]);
      s = p.slides.add();
      bullets(s, course, 3, "岗位 Agent 示例", "同一个概念，要落回各岗位每天遇到的问题。", [
        { head: "电控 Agent", body: "读取 IO 表、动作流程和安全要求，生成缺失项、风险项、待确认项。", color: c.blue },
        { head: "机构 Agent", body: "读取方案说明和评审清单，整理定位、夹紧、防呆、维护空间问题。", color: c.green },
        { head: "软件 Agent", body: "读取接口文档、日志、异常截图，生成联调检查清单和测试用例草案。", color: c.purple },
        { head: "项目文职 Agent", body: "汇总会议纪要、任务清单、问题记录，生成周报和需协调事项。", color: c.accent },
        { head: "生物管/质量 Agent", body: "整理实验记录、样本清单、异常描述，输出补全项和复核清单。", color: c.red },
      ], ["讲师提示：强调每个 Agent 都有“不能做什么”。"]);
      s = p.slides.add();
      compare(s, course, 4, "Agent 的输入要写清楚", "目标越含糊，Agent 越容易跑偏。", [
        ["目标", "任务委托书", "说明要完成什么", "不能只写“帮我看看”"],
        ["范围", "边界线", "限定资料、时间、项目", "不能跨权限访问"],
        ["标准", "验收条件", "输出字段、证据、风险等级", "不能只看文字顺不顺"],
        ["确认点", "刹车", "关键动作前停下来问人", "不能自动做高风险动作"],
      ], ["讲师提示：让学员把一个模糊任务改写成合格 Agent 输入。"]);
      s = p.slides.add();
      examplePair(s, course, 5, "真实例子：同样是让 Agent 做评审准备，边界不同", {
        title: "错误 Agent：目标含糊还允许自动行动",
        body: "“帮我审一下方案，有问题就改。”没有资料范围，没有输出标准，也没有人工确认点。",
        problem: "智能体（Agent）可能越界修改文档，甚至把未经确认的建议写成结论。",
      }, {
        title: "正确 Agent：只做准备包和待确认项",
        body: "读取 URS、BOM、动作流程和历史问题，调用方案评审技能（Skill），输出风险清单和需人工确认项。",
        result: "AI 完成资料整理和初筛，工程师负责最终判断和签发。",
      }, ["讲师提示：这页回应“智能体（Agent）会不会自作主张”。正确做法是限定范围、工具和确认点。"]);
      s = p.slides.add();
      exercise(s, course, 6, "练习：设计自己的岗位 Agent", "Agent 设计必须包含人工确认点。", {
        sim: "角色扮演：一组当需求方，一组当 Agent 设计者。需求方故意说得模糊，设计者追问目标、范围、资料和验收标准。",
        real: "填写 Agent 卡片：名称、服务岗位、目标、资料、工具、执行步骤、人工确认点、交付物、风险控制。",
        output: "一个岗位 Agent 设计卡。",
      }, ["讲师提示：对抗点：如果 Agent 会调工具，会不会越权？答案必须回到权限和日志。"]);
      s = p.slides.add();
      checklist(s, course, 7, "Agent 权限分三级", [
        { head: "可自动", body: "读文件\n总结\n分类\n生成清单\n提示风险", color: c.green },
        { head: "需确认", body: "改文档\n生成代码\n发邮件\n修改参数草案\n输出质量摘要", color: c.accent },
        { head: "默认禁止", body: "控制设备\n下发程序\n改安全逻辑\n删除资料\n越权访问", color: c.red },
      ], ["讲师提示：这页回应“AI 撞机谁负责”。"]);
      s = p.slides.add();
      qa(s, course, 8, "模拟课堂问答", [
        { q: "Agent 会不会误操作设备？", a: "第一阶段只读和生成建议。涉及写入、下发、控制设备的动作默认禁止或必须审批。" },
        { q: "多 Agent 会不会更乱？", a: "初期不要多 Agent。先把一个岗位任务闭环做好，再考虑分工协作。" },
        { q: "Agent 输出看起来对但逻辑错怎么办？", a: "要求证据、列不确定项、设置人工确认点；关键工程判断必须复核。" },
      ], ["讲师提示：不要把 Agent 讲成“自动驾驶”，要讲成受控助理。"]);
    },
  },
  {
    slug: "10-tools-memory",
    file: "10-新版04-MCP工具记忆知识库专项-修订版-带讲师备注.pptx",
    build(p) {
      const course = "新版课程 04 / MCP 工具、记忆与知识库";
      let s = p.slides.add();
      cover(s, course, "让 AI 有工具，也要有边界", "MCP/工具解决“能不能查和做”，记忆与知识库解决“能不能懂我们公司”。", [
        "开场：聊天 AI 只能凭上下文说，接工具后才能读 Excel、查系统、跑脚本、看文件。",
        "本课目标：学员能设计工具链，并区分记忆和知识库。",
      ]);
      s = p.slides.add();
      bullets(s, course, 2, "MCP/工具是 AI 的手和眼", "它不是模型，也不是知识库，而是受控连接外部能力的方法。", [
        { head: "能读", body: "读取 Excel、PDF、日志、BOM、会议纪要、测试记录。", color: c.blue },
        { head: "能查", body: "查询 ERP、PDM、问题库、标准件库、项目系统。", color: c.green },
        { head: "能算", body: "跑脚本、做格式检查、统计缺失项、比对规则。", color: c.purple },
        { head: "能连", body: "通过接口连接内部系统，但必须受权限控制。", color: c.accent },
      ], ["讲师提示：MCP 可以类比标准接口层，普通学员只需懂作用和边界。"]);
      s = p.slides.add();
      compare(s, course, 3, "记忆和知识库不能混用", "记忆让 AI 更懂你，知识库让 AI 更懂业务依据。", [
        ["记忆", "个人习惯本", "偏好、术语、长期背景", "不存密码和客户机密"],
        ["知识库", "部门资料室", "SOP、标准、历史案例、模板", "不放过期矛盾资料"],
        ["临时上下文", "本次会议材料", "当前任务相关信息", "不长期保存敏感内容"],
        ["禁止保存", "红线信息", "密码、报价、未授权客户资料", "不能为了方便而保存"],
      ], ["讲师提示：质量资料更应进入受控知识库，不应只靠聊天记忆。"]);
      s = p.slides.add();
      bullets(s, course, 4, "非标自动化常见工具链", "工具设计先从只读开始。", [
        { head: "电控", body: "IO 表读取、报警清单读取、PLC 代码只读检索、电气标准库查询。", color: c.blue },
        { head: "机构", body: "BOM 查询、标准件库查询、历史问题库查询、图纸目录检索。", color: c.green },
        { head: "软件", body: "Git 查询、接口文档查询、测试报告读取、缺陷单查询。", color: c.purple },
        { head: "文职", body: "会议纪要读取、任务系统查询、邮件草稿、项目资料目录检查。", color: c.accent },
        { head: "生物管/质量", body: "SOP 查询、实验记录读取、耗材台账检查、异常记录归类。", color: c.red },
      ], ["讲师提示：第一阶段建议只读，不直接改生产系统。"]);
      s = p.slides.add();
      examplePair(s, course, 5, "真实例子：同样是接工具，权限设计决定风险", {
        title: "错误工具链：一上来给写权限",
        body: "让 AI 直接连接项目资料库、邮件和质量系统，并允许自动修改文件、发送邮件、更新判定结果。",
        problem: "一旦识别错误或越权调用，可能造成资料泄露、误发邮件或质量记录被错误改写。",
      }, {
        title: "正确工具链：第一阶段只读和需确认",
        body: "先只允许读取 BOM、会议纪要、SOP 和历史问题库；邮件、质量结论、文档修改必须人工确认。",
        result: "模型上下文协议（MCP）/工具带来真实数据，同时通过最小权限和留痕控制风险。",
      }, ["讲师提示：这页要让学员理解：工具不是越多越好，权限不是越大越好。"]);
      s = p.slides.add();
      exercise(s, course, 6, "练习：设计工具链和资料边界", "工具越强，边界越要清楚。", {
        sim: "给出场景：AI 想自动发送客户邮件、批量导出报价、修改质量判定。让学员判断允许、需确认或禁止。",
        real: "每组选择一个任务，写：需要读取的数据、工具、AI 负责判断、人负责判断、输出物、风险点。",
        output: "一张工具链边界表。",
      }, ["讲师提示：让管理者和质量岗位参与边界判断。"]);
      s = p.slides.add();
      exercise(s, course, 7, "练习：记忆、知识库、临时上下文分类", "分类错误会直接影响合规和准确性。", {
        sim: "卡片分类：老板喜欢风险先写、客户验收标准 V3.2、设备密码、历史 8D 报告、本周临时讨论草稿。",
        real: "为本部门设计一个知识库目录：电控标准、机构评审、软件接口、项目模板、质量/SOP、历史问题。",
        output: "一份知识库目录和记忆红线。",
      }, ["讲师提示：强调版本、审核人、更新周期。"]);
      s = p.slides.add();
      qa(s, course, 8, "模拟课堂问答", [
        { q: "MCP 和 API/插件有什么区别？", a: "可以理解为给 AI 使用外部工具的一种标准接口方式；不替代现有 API，而是降低多工具接入成本。" },
        { q: "记忆会不会把公司机密长期保存？", a: "所以记忆要有规则。只记稳定偏好和术语，不记密码、客户图纸、报价、程序片段。" },
        { q: "AI 会不会引用旧版本 SOP？", a: "知识库必须有版本和审核机制；输出时要求列来源、版本和不确定项。" },
      ], ["讲师提示：工具、记忆、知识库三者都要讲治理。"]);
    },
  },
  {
    slug: "11-workflows",
    file: "11-新版05-非标自动化场景综合练习-修订版-带讲师备注.pptx",
    build(p) {
      const course = "新版课程 05 / 非标自动化场景综合练习";
      let s = p.slides.add();
      cover(s, course, "把 AI 用进非标自动化部门的一天", "从单点问答，走向受控的部门工作流。", [
        "本课是综合实战，不再单讲名词。",
        "目标：每组输出一个可试点 AI 工作流方案。",
      ]);
      s = p.slides.add();
      bullets(s, course, 2, "先选高频、低风险、资料稳定的场景", "第一批不要做最复杂、风险最高的自动化。", [
        { head: "适合首批", body: "会议纪要、项目周报、BOM 初筛、IO 表字段检查、报警文本整理、问题单归类。", color: c.green },
        { head: "暂不建议", body: "自动下采购单、自动改工程图、自动批准验收、自动下发程序、自动修改安全参数。", color: c.red },
        { head: "评价标准", body: "高频、低风险、规则清楚、输入稳定、输出容易复核。", color: c.blue },
      ], ["讲师提示：这页回应管理者的投入产出问题。"]);
      s = p.slides.add();
      bullets(s, course, 3, "工作流案例：设计评审准备包", "用同一个案例串起模型、Skill、Agent、工具、记忆、知识库。", [
        { head: "输入", body: "客户需求、设备方案、BOM、动作流程、历史问题、验收模板。", color: c.blue },
        { head: "处理", body: "Agent 拆任务，Skill 生成评审清单，工具读取资料，知识库匹配规范。", color: c.green },
        { head: "输出", body: "风险点、缺失资料、责任专业、需客户确认事项、人工审核清单。", color: c.accent },
        { head: "边界", body: "AI 不做最终方案批准，不替代安全、结构、质量责任判断。", color: c.red },
      ], ["讲师提示：让每个岗位说明自己负责输入或复核哪一部分。"]);
      s = p.slides.add();
      checklist(s, course, 4, "部门 AI 使用规范草案", [
        { head: "资料规则", body: "脱敏样例先行\n敏感资料不上传公共环境\n知识库资料要有版本", color: c.blue },
        { head: "流程规则", body: "关键输出要复核\n高风险动作需审批\n工具调用要留痕", color: c.green },
        { head: "责任规则", body: "AI 不签字\n人负责确认\n问题回写 Skill 和知识库", color: c.red },
      ], ["讲师提示：这是落地前的最低治理框架。"]);
      s = p.slides.add();
      examplePair(s, course, 5, "真实例子：同样是项目问题闭环，工作流完整度不同", {
        title: "错误工作流：只让 AI 写总结",
        body: "把一堆问题记录丢给 AI：帮我总结一下。没有规定问题分类、责任人、关闭标准和复核流程。",
        problem: "输出像报告但不能闭环，责任和截止日期不清，历史问题也没有回写。",
      }, {
        title: "正确工作流：从输入到复盘都有节点",
        body: "读取问题单，按专业分类，匹配历史案例，生成责任人和截止时间，人工确认后回写知识库。",
        result: "工作流（Workflow）不仅产出文字，还能推动问题闭环和经验沉淀。",
      }, ["讲师提示：这页要把“会写总结”和“能形成工作流（Workflow）”区分开。"]);
      s = p.slides.add();
      exercise(s, course, 6, "综合实战：设计一个 AI 工作流", "每组选择一个真实流程，按模板输出。", {
        sim: "讲师提供样例：BOM 初筛。学员指出需要 Skill、Agent、工具、知识库、人工审核点。",
        real: "选择本组真实流程，填写：痛点、AI 介入位置、Skill、Agent、工具、知识库、记忆、审核点、收益、风险。",
        output: "一页部门 AI 试点方案。",
      }, ["讲师提示：要求每组明确“不让 AI 做什么”。"]);
      s = p.slides.add();
      exercise(s, course, 7, "实际练习：AI 输出复核", "会用 AI 的关键能力之一，是会检查 AI。", {
        sim: "给出一段 AI 生成的周报或质量摘要，让学员找错误、遗漏、猜测和旧版本引用。",
        real: "用真实但脱敏资料生成一份清单，再按复核表检查：数量、日期、料号、责任人、来源、版本、风险。",
        output: "一张 AI 输出复核记录。",
      }, ["讲师提示：质量岗位通常会关注这页，强调来源追溯。"]);
      s = p.slides.add();
      qa(s, course, 8, "模拟课堂问答", [
        { q: "培训有效的交付物是什么？", a: "每个岗位至少一个 Skill、一个 Agent 卡、一份知识库目录、一个可试点工作流。" },
        { q: "怎么评估收益？", a: "看节省时间、错误减少、响应速度、知识复用率、提前发现问题数量。" },
        { q: "员工会不会过度依赖 AI？", a: "训练重点之一就是复核 AI。AI 负责初筛和整理，人负责判断和签发。" },
      ], ["讲师提示：结尾要落到两周内试点，而不是只停留在听懂。"]);
    },
  },
  {
    slug: "12-role-simulation",
    file: "12-新版06-角色模拟课堂问答与讲师手册-修订版-带讲师备注.pptx",
    build(p) {
      const course = "新版课程 06 / 角色模拟课堂问答";
      let s = p.slides.add();
      cover(s, course, "用角色模拟提前处理课堂阻力", "把学员兴趣点、质疑点和讲师应答提前放进课件。", [
        "本课件可作为讲师备课和课堂互动手册。",
        "角色来自模拟：电控、机构、软件、项目文职、生物管/质量、管理者。",
      ]);
      s = p.slides.add();
      bullets(s, course, 2, "不同岗位的兴趣点不一样", "讲师要把同一个概念翻译成不同岗位的收益。", [
        { head: "电控", body: "IO 表、报警逻辑、PLC 注释、互锁检查、调试问题整理。", color: c.blue },
        { head: "机构", body: "方案评审、维护空间、防呆、标准件、历史问题复用。", color: c.green },
        { head: "软件", body: "日志、接口、测试用例、代码初筛、工具/MCP 可控性。", color: c.purple },
        { head: "文职", body: "会议纪要、周报、资料归档、任务追踪、邮件草稿。", color: c.accent },
        { head: "生物管/质量", body: "SOP、记录预检、异常归类、来源追溯、质量边界。", color: c.red },
      ], ["讲师提示：开课前按听众比例调整案例。"]);
      s = p.slides.add();
      qa(s, course, 3, "工程岗位可能会这样质疑", [
        { q: "AI 写错 PLC，设备撞机谁负责？", a: "不能让 AI 直接下发程序；AI 只做草稿、检查和建议，程序仍需评审、仿真、现场点检。" },
        { q: "AI 不懂现场经验，怎么判断？", a: "承认它不替代现场经验。它适合整理经验、补漏检查、生成草稿，关键判断仍由工程师确认。" },
        { q: "MCP 是不是新概念包装？", a: "对软件工程师可类比标准工具接口层，价值是让 AI 以统一方式接入多个系统。" },
        { q: "非标项目每个都不同，知识沉淀有意义吗？", a: "项目不同，但风险、模板、命名、评审方法有大量重复，适合先沉淀稳定部分。" },
      ], ["讲师提示：工程岗位更关心可靠性和责任，回答要具体到控制措施。"]);
      s = p.slides.add();
      qa(s, course, 4, "非工程岗位可能会这样质疑", [
        { q: "我不懂代码，真的能用吗？", a: "能。非技术岗位重点不是开发工具，而是把固定流程、资料格式和复核点说清楚。" },
        { q: "AI 写错周报，领导骂的是我怎么办？", a: "AI 只做初稿，岗位责任仍在本人；必须复核数量、日期、责任人、风险和来源。" },
        { q: "质量问题不能靠猜，AI 凭什么参与？", a: "AI 参与辅助筛查和证据整理，不做最终质量判定；所有结论必须回到标准和记录。" },
        { q: "记忆会不会保存公司机密？", a: "记忆只放稳定偏好和术语；客户资料、报价、合同、密码、图纸不应进入记忆。" },
      ], ["讲师提示：非工程岗位更关心责任、替代和使用门槛。"]);
      s = p.slides.add();
      checklist(s, course, 5, "讲师应答三段式", [
        { head: "先承认边界", body: "AI 会错\nAI 不签字\nAI 不替代现场经验\nAI 不应越权", color: c.red },
        { head: "再给控制方法", body: "脱敏\n权限\n日志\n来源\n人工确认\n版本管理", color: c.blue },
        { head: "最后给岗位例子", body: "IO 表检查\nBOM 初筛\n会议纪要\n记录预检\n问题归类", color: c.green },
      ], ["讲师提示：不要用“AI 很强”回应质疑。必须讲边界、流程和验证。"]);
      s = p.slides.add();
      examplePair(s, course, 6, "真实例子：同样面对质疑，讲师回应方式不同", {
        title: "错误回应：只强调 AI 很强",
        body: "学员问“AI 写错程序撞机怎么办”，讲师回答“现在模型很强，基本不会错”。",
        problem: "没有承认边界，也没有控制措施，工程师会更不信任这门课。",
      }, {
        title: "正确回应：边界、控制、例子三段式",
        body: "先承认 AI 不能直接下发程序；再说明只读、日志、人工确认；最后举 IO 表检查和报警文本整理例子。",
        result: "质疑被转化成可执行规则，课堂阻力变成风险共识。",
      }, ["讲师提示：这页是讲师自己的练习。不要用口号压过质疑，要把质疑变成边界设计。"]);
      s = p.slides.add();
      exercise(s, course, 7, "课堂对抗练习", "让学员主动提出反对意见，再用课程概念回应。", {
        sim: "分组扮演电控、机构、软件、文职、质量、管理者。每组提出一个最尖锐问题。",
        real: "另一组用三段式回答：边界、控制方法、岗位例子。讲师现场修正不完整回答。",
        output: "一张本部门 AI 使用 FAQ。",
      }, ["讲师提示：这项练习能提高兴趣度，也能暴露真实顾虑。"]);
      s = p.slides.add();
      bullets(s, course, 8, "课后完善动作", "模拟课堂不是结束，而是用反馈修课件和试点。", [
        { head: "收集问题", body: "把课堂提问按概念、岗位、风险、工具、数据分类。", color: c.blue },
        { head: "回写课件", body: "高频问题进入讲师备注，尖锐问题进入问答页。", color: c.green },
        { head: "形成模板", body: "输出 Skill 模板、Agent 卡、知识库目录、风险红线、试点评分表。", color: c.accent },
        { head: "选择试点", body: "两周内选 1 到 2 个低风险场景试运行，记录节省时间和发现问题数。", color: c.red },
      ], ["讲师提示：下一轮课程应基于真实反馈迭代。"]);
    },
  },
];

async function main() {
  await fs.mkdir(OUT, { recursive: true });
  await fs.mkdir(PREVIEW, { recursive: true });
  for (const deck of decks) await saveDeck(deck);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
