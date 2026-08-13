import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/lfaf-test/Documents/测试";
const OUT = `${ROOT}/outputs`;
const TMP = `${ROOT}/work/presentations/skill-training/tmp`;
const ASSET = `${TMP}/assets/ai-assistant-cartoon.png`;
const PREVIEW = `${TMP}/preview/05-agent-analogy`;

const W = 1280;
const H = 720;
const colors = {
  ink: "#111111",
  muted: "#555555",
  pale: "#F2F2F2",
  panel: "#E9E9E9",
  rule: "#B8BCC4",
  orange: "#FF6B35",
  blue: "#2563EB",
  green: "#059669",
};

async function imageBytes(file) {
  const bytes = await fs.readFile(file);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
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

function notes(slide, lines) {
  slide.speakerNotes.textFrame.setText(Array.isArray(lines) ? lines : [lines]);
  slide.speakerNotes.setVisible(true);
}

function footer(slide, n) {
  text(slide, "Agent / Skill / MCP / 记忆 / 大模型", 54, 30, 450, 26, { size: 15, bold: true, color: colors.muted });
  text(slide, String(n).padStart(2, "0"), W - 96, H - 46, 42, 24, { size: 14, color: colors.muted, align: "right" });
}

async function addPerson(slide, x, y, w, h) {
  slide.images.add({
    blob: await imageBytes(ASSET),
    contentType: "image/png",
    alt: "卡通 AI 工程助理人物",
    fit: "contain",
    position: { left: x, top: y, width: w, height: h },
  });
}

async function buildAnalogyDeck() {
  const p = Presentation.create({ slideSize: { width: W, height: H } });

  let s = p.slides.add();
  s.background.fill = "#FFFFFF";
  box(s, 54, 42, 1172, 6, colors.ink, "none");
  text(s, "教学课件", 54, 92, 320, 32, { size: 20, bold: true, color: colors.orange });
  text(s, "把 AI 系统想象成一个人", 54, 168, 760, 130, { size: 58, bold: true });
  text(s, "Agent、Skill、MCP、记忆和大语言模型之间的关系", 54, 382, 760, 78, { size: 27, color: colors.muted });
  await addPerson(s, 850, 125, 310, 430);
  notes(s, [
    "开场：告诉学员今天不讲抽象术语，全部用“一个会做事的人”来类比。",
    "核心句：大语言模型是大脑，Agent 是带着这个大脑去干活的人，Skill 是岗位 SOP，MCP 是连接外部世界的工具接口，记忆是长期习惯。",
  ]);

  s = p.slides.add();
  footer(s, 2);
  text(s, "先建立一张总图", 54, 78, 900, 56, { size: 42, bold: true });
  const items = [
    ["大语言模型", "这个人的大脑", colors.orange],
    ["Agent", "被安排去做事的人", colors.blue],
    ["Skill", "他的岗位技能和 SOP", colors.green],
    ["MCP / 工具", "他的手、眼睛和系统接口", colors.orange],
    ["记忆", "他长期记住的偏好", colors.blue],
  ];
  items.forEach((it, i) => {
    const y = 170 + i * 86;
    text(s, `0${i + 1}`, 70, y + 4, 54, 34, { size: 26, bold: true, color: it[2] });
    box(s, 142, y, 880, 58, i % 2 ? "#F8F8F8" : "#FFFFFF", colors.rule);
    text(s, it[0], 166, y + 14, 220, 28, { size: 22, bold: true });
    text(s, it[1], 430, y + 14, 520, 28, { size: 21, color: colors.muted });
  });
  await addPerson(s, 1038, 188, 150, 260);
  notes(s, [
    "这一页先讲总图，不急着展开细节。",
    "讲法：以后大家听到 Agent、Skill、MCP、记忆、大模型，就先把它们放回“人”的比喻里。",
  ]);

  s = p.slides.add();
  footer(s, 3);
  text(s, "大语言模型是“大脑”", 54, 78, 900, 56, { size: 42, bold: true });
  text(s, "它提供理解语言、推理、总结、生成和解释的底层能力。", 54, 150, 840, 44, { size: 25, color: colors.muted });
  box(s, 76, 238, 470, 260, "#FFFFFF", colors.rule);
  text(s, "能做的事", 106, 270, 300, 34, { size: 28, bold: true, color: colors.orange });
  text(s, "理解你的要求\n分析资料之间的关系\n生成表格、报告、代码或课件\n解释为什么这样做", 106, 332, 390, 130, { size: 22, color: colors.muted });
  box(s, 610, 238, 470, 260, colors.pale, "none");
  text(s, "不能单独完成的事", 640, 270, 360, 34, { size: 28, bold: true });
  text(s, "自己打开你的文件\n自己访问公司系统\n长期记住部门规则\n保证每次都按同一套 SOP 做", 640, 332, 390, 130, { size: 22, color: colors.muted });
  notes(s, [
    "强调：大模型是底层智力，不等于完整工作系统。",
    "类比：一个人很聪明，但如果没有文件、工具、岗位手册和权限，也无法稳定完成公司流程。",
  ]);

  s = p.slides.add();
  footer(s, 4);
  text(s, "Agent 是“这个人本身”", 54, 78, 900, 56, { size: 42, bold: true });
  text(s, "Agent 把大脑能力组织成行动：理解任务、拆步骤、调用工具、检查结果、汇报输出。", 54, 150, 1000, 44, { size: 24, color: colors.muted });
  await addPerson(s, 76, 225, 260, 340);
  const steps = ["接任务", "拆步骤", "找资料", "用工具", "交结果"];
  steps.forEach((v, i) => {
    const x = 390 + i * 155;
    box(s, x, 300, 115, 112, "#FFFFFF", colors.rule);
    text(s, String(i + 1), x + 16, 318, 32, 30, { size: 24, bold: true, color: colors.orange });
    text(s, v, x + 16, 366, 82, 28, { size: 20, bold: true, align: "center" });
    if (i < steps.length - 1) text(s, "→", x + 120, 342, 30, 36, { size: 28, color: colors.muted });
  });
  notes(s, [
    "讲法：Agent 不是另一个大脑，而是“做事形态”。",
    "例子：你说检查 IO 表，Agent 会决定先读表、再跑脚本、再按 Skill 输出问题清单。",
  ]);

  s = p.slides.add();
  footer(s, 5);
  text(s, "Skill 是“专业技能 / SOP”", 54, 78, 900, 56, { size: 42, bold: true });
  text(s, "没有 Skill，Agent 靠临场发挥；有 Skill，Agent 按部门沉淀的流程做。", 54, 150, 980, 44, { size: 24, color: colors.muted });
  const cols = [
    ["电控 Skill", "检查 IO 表、PLC tag、报警清单、安全互锁资料完整性。"],
    ["机构 Skill", "检查方案评审、夹治具、节拍、维护空间、换型和防呆。"],
    ["资料 Skill", "整理会议纪要、归档目录、客户确认和问题追踪。"],
  ];
  cols.forEach((col, i) => {
    const x = 70 + i * 385;
    box(s, x, 250, 330, 240, i === 1 ? "#F8F8F8" : "#FFFFFF", colors.rule);
    box(s, x, 250, 330, 8, [colors.orange, colors.blue, colors.green][i], "none");
    text(s, col[0], x + 24, 286, 280, 36, { size: 26, bold: true });
    text(s, col[1], x + 24, 350, 270, 90, { size: 21, color: colors.muted });
  });
  notes(s, [
    "把 Skill 和 SOP 绑定讲：Skill 的价值不是让 AI 自由发挥，而是让 AI 按部门标准工作。",
    "提醒：初级 Skill 不一定有脚本，先把触发场景、步骤、输出格式和人工边界写清楚。",
  ]);

  s = p.slides.add();
  footer(s, 6);
  text(s, "MCP 和工具是“手、眼睛、系统接口”", 54, 78, 1000, 56, { size: 42, bold: true });
  text(s, "大脑会思考，Agent 会组织行动，但要真正读文件、查系统、跑脚本，就需要工具和 MCP。", 54, 150, 1040, 44, { size: 24, color: colors.muted });
  const tools = [["文件", "读写项目资料"], ["浏览器", "查看网页和系统"], ["数据库", "查询结构化数据"], ["脚本", "做确定性检查"]];
  tools.forEach((t, i) => {
    const x = 90 + i * 280;
    box(s, x, 260, 220, 190, "#FFFFFF", colors.rule);
    text(s, t[0], x + 24, 300, 170, 34, { size: 28, bold: true, color: i % 2 ? colors.blue : colors.orange });
    text(s, t[1], x + 24, 370, 160, 42, { size: 21, color: colors.muted });
  });
  notes(s, [
    "讲法：MCP 像公司给这个人开的系统接口和权限。",
    "安全提醒：有工具不代表随便操作，涉及删除、发送、审批、移动文件等动作仍要确认。",
  ]);

  s = p.slides.add();
  footer(s, 7);
  text(s, "记忆是“长期记住的习惯”", 54, 78, 900, 56, { size: 42, bold: true });
  text(s, "记忆不是万能知识库，更像这个人记住了你的偏好和团队习惯。", 54, 150, 980, 44, { size: 24, color: colors.muted });
  box(s, 80, 240, 500, 250, "#FFFFFF", colors.rule);
  text(s, "适合记住", 112, 272, 300, 34, { size: 28, bold: true, color: colors.green });
  text(s, "常用输出格式\n部门偏好\n术语习惯\n你希望简洁还是详细", 112, 332, 390, 120, { size: 23, color: colors.muted });
  box(s, 650, 240, 500, 250, colors.pale, "none");
  text(s, "不适合记住", 682, 272, 300, 34, { size: 28, bold: true });
  text(s, "敏感客户资料\n合同金额\n个人隐私\n未确认的项目事实", 682, 332, 390, 120, { size: 23, color: colors.muted });
  notes(s, [
    "强调：记忆用来提高协作连续性，不是拿来存放敏感项目资料。",
    "例子：可以记住你喜欢问题清单字段，但不应该记住客户合同细节。",
  ]);

  s = p.slides.add();
  footer(s, 8);
  text(s, "Prompt 是“这次你对他说的话”", 54, 78, 900, 56, { size: 42, bold: true });
  text(s, "同一个 Agent，收到不同 Prompt，会执行不同任务；Prompt 越清楚，结果越稳定。", 54, 150, 1000, 44, { size: 24, color: colors.muted });
  box(s, 90, 250, 500, 210, "#FFFFFF", colors.rule);
  text(s, "普通问法", 120, 286, 220, 34, { size: 28, bold: true });
  text(s, "帮我看看这个 IO 表有没有问题。", 120, 360, 400, 34, { size: 24, color: colors.muted });
  box(s, 660, 250, 500, 210, colors.pale, "none");
  text(s, "更好问法", 690, 286, 220, 34, { size: 28, bold: true, color: colors.orange });
  text(s, "按 IO 表检查 Skill，检查空字段、重复地址、命名不规范和安全点遗漏，输出问题清单。", 690, 345, 400, 70, { size: 22, color: colors.muted });
  notes(s, [
    "讲法：Prompt 是当下指令，Skill 是长期方法。",
    "课堂互动：让学员把一句模糊请求改成包含输入、检查点、输出格式和人工边界的请求。",
  ]);

  s = p.slides.add();
  footer(s, 9);
  text(s, "放到一个非标自动化任务里看", 54, 78, 1000, 56, { size: 42, bold: true });
  const flow = [
    ["你说", "检查这个 IO 表"],
    ["Agent", "拆成读取、检查、输出"],
    ["Skill", "按 IO 表 SOP 检查"],
    ["工具", "读取 CSV 并跑脚本"],
    ["大模型", "解释风险和建议"],
    ["输出", "问题清单和结论"],
  ];
  flow.forEach((f, i) => {
    const x = 70 + i * 190;
    box(s, x, 245, 145, 160, i % 2 ? "#F8F8F8" : "#FFFFFF", colors.rule);
    text(s, f[0], x + 16, 275, 110, 30, { size: 23, bold: true, color: i === 0 ? colors.orange : colors.ink, align: "center" });
    text(s, f[1], x + 16, 340, 110, 44, { size: 18, color: colors.muted, align: "center" });
    if (i < flow.length - 1) text(s, "→", x + 150, 305, 32, 34, { size: 28, color: colors.muted });
  });
  notes(s, [
    "这一页把所有概念串起来。",
    "重点：不是某一个概念单独完成任务，而是 Prompt、Agent、Skill、工具/MCP、大模型一起工作。",
  ]);

  s = p.slides.add();
  footer(s, 10);
  text(s, "最后用一句话记住", 54, 92, 900, 64, { size: 48, bold: true });
  box(s, 78, 210, 1020, 210, colors.pale, "none");
  text(s, "大语言模型是脑子，Agent 是带着脑子去干活的人；Skill 是他的岗位 SOP，MCP 是连接外部系统的手和眼睛，记忆是长期习惯，Prompt 是你这次交代的任务。", 116, 258, 940, 108, { size: 30, bold: true });
  await addPerson(s, 980, 430, 180, 210);
  notes(s, [
    "收尾：让学员复述这句话。",
    "下一步引导：每个部门先选一个高频任务，把它写成“这个人该怎么做”的 SOP，就是 Skill 的雏形。",
  ]);

  await fs.mkdir(PREVIEW, { recursive: true });
  for (const [i, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(PREVIEW, `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(`${OUT}/05-Agent-Skill-MCP-记忆-大模型人的比喻教学.pptx`);
}

const noteSets = {
  "01-Skill入门认知-非标自动化部门.pptx": [
    "开场：告诉大家这节课不讲抽象 AI 概念，只讲如何把反复做、容易漏、靠经验判断的工作变成 Skill。强调 Skill 是给 AI 的标准作业指导书，不是替代岗位责任人。",
    "讲这页时问大家：每个岗位现在最重复、最容易漏的工作是什么？把回答写在白板上，为后面转成 Skill 做铺垫。",
    "核心讲法：Skill 是工作流说明书加资料包。指令像 SOP，资源像部门知识库，脚本像小工具。不要把 Skill 讲成神奇能力。",
    "回答常见问题：提示词解决一次问题，Skill 解决一类重复问题，插件用于分发安装。强调普通员工也能贡献规则。",
    "讲触发流程：用户点名或描述命中 Skill 后，Agent 读取 SKILL.md，再按需读取 references/assets/scripts。",
    "结合部门岗位讲：电控看 IO 表，机构看方案风险，文职看资料归档，质量看验证资料。让每个岗位都看到自己的入口。",
    "提醒：先选高频、稳定、有验收标准的任务，不要一开始做“自动完成整个项目”。",
    "现场互动：让学员用五句话描述一个候选 Skill：谁用、何时触发、先看什么、产出什么、怎么验收。",
    "收尾：Skill 的目标是少漏项、少重复、标准统一。请每个岗位课后提交一个候选 Skill。",
  ],
  "02-Skill建立与使用实操.pptx": [
    "开场：承接第一课，今天从“知道 Skill 是什么”进入“怎样建一个能用的 Skill”。强调先建小而稳的版本。",
    "这页用于建立学习路线：放在哪里、SKILL.md 怎么写、怎么测试。告诉大家今天不是写程序课，而是 SOP 设计课。",
    "讲最小结构：一个文件夹加 SKILL.md 就能开始。name 要短，description 决定能否被正确叫醒。",
    "讲存放范围：个人试点先放个人或教学目录，团队稳定后再考虑项目级或插件分发。范围越大越要谨慎。",
    "演示五步：选场景、写触发、写流程、放资料、试运行。提醒：先 instruction-only，脚本是进阶项。",
    "重点讲 description：要写具体触发和禁用边界。举反例“帮助自动化部门做事情”太泛，无法稳定触发。",
    "讲输出格式：没有固定格式就不利于评审、归档和追踪。问题清单字段要提前定好。",
    "测试方法：触发测试、样例测试、边界测试、验收测试。用真实项目资料比空想更有效。",
    "迭代节奏：把 Skill 当作可维护 SOP。每周收集错触发、漏项、格式问题，然后更新。",
    "讲脚本边界：确定性检查用脚本，判断和解释用 Skill。安全签核、报价承诺、最终审批不能交给 AI。",
    "现场练习：每个岗位写一个 Skill 草稿，至少包括触发条件、输入材料、输出字段和人工确认点。",
  ],
  "03-非标自动化工作转换Skill案例.pptx": [
    "开场：今天重点是把真实工作转换成 Skill。先声明：不是所有工作都适合，先从重复、标准、资料驱动的工作开始。",
    "讲三件事：找可转换任务、看四类岗位案例、形成部门路线图。",
    "讲优先级：高优先是重复检查、资料整理、模板生成；低优先或禁止的是直接替代签核、安全判断和自动控制设备。",
    "电控案例：强调 IO 表检查可以先做空字段、重复地址、命名、信号类型；安全回路只能做风险提醒和资料完整性检查。",
    "电控触发演示：输入 IO 表，调用 Skill，输出异常项。提醒误判要支持人工备注和例外规则。",
    "机构案例：讲方案评审不要套话，要列动作干涉、定位基准、维护空间、换型、防呆、节拍依据。",
    "机构问题清单生成器：让机构同事现场补充最常漏的 5 个评审问题，说明这些就是 references 的来源。",
    "文职案例：资料归档先输出建议目录、缺失清单和行动项，不要一开始自动移动或删除文件。",
    "质量案例：强调验证资料检查是预检查，不能直接给最终合规结论。原始记录只读检查。",
    "路线图：建议先做 3 个试点：资料整理、方案评审、IO 检查。两周后复盘。",
    "边界页：让大家记住“AI 可整理、可提醒、可查漏；最终签核、承诺、审批必须人工”。",
    "课后动作：每个岗位提交一个候选 Skill，并给出输入、输出、验收和人工确认点。",
  ],
  "04-Skill实际案例与文件结构解析.pptx": [
    "开场：今天打开真实 Skill 文件夹，不只看概念。目标是让学员能看懂 SKILL.md、references、assets、scripts 各自作用。",
    "六步建立法：选任务、定边界、建目录、写流程、放资源、验证迭代。强调每一步都对应实际文件。",
    "四个示例：scheme-review、io-table-review、project-doc-archive、validation-doc-check。让不同岗位找到自己的例子。",
    "讲结构：SKILL.md 是大脑，agents/openai.yaml 是名片，references 是规则，assets 是模板，scripts 是工具。",
    "frontmatter：name 和 description 最关键。description 要写触发场景、输入类型、任务边界和禁止事项。",
    "正文 Workflow：要写做事顺序，不写空泛原则。让学员判断这段是否能让另一个人照着执行。",
    "scheme-review：讲方案评审 Skill 如何把老工程师经验转成评审问题清单。",
    "io-table-review：说明为什么有脚本。脚本抓重复地址、空字段，Skill 再解释影响和责任人。",
    "脚本演示：告诉大家脚本结果不是最终报告，最终要转成工程语言：问题、影响、优先级、建议动作。",
    "project-doc-archive：强调文职不需要写代码，能说清目录、命名、缺失项和行动项就是核心贡献。",
    "validation-doc-check：强调质量边界，做完整性和追溯预检查，不替代 QA 批准。",
    "课堂带练：打开文件树，读 description，读 Workflow，读 references，跑脚本，最后让学员改一个真实字段。",
    "判断合格：能触发、能执行、能复核、有边界、能迭代。用这五条评价每个部门提交的 Skill 草稿。",
  ],
};

async function addNotesToExistingDecks() {
  for (const [fileName, notesBySlide] of Object.entries(noteSets)) {
    const src = `${OUT}/${fileName}`;
    const p = await PresentationFile.importPptx(await FileBlob.load(src));
    p.slides.items.forEach((slide, index) => {
      const content = notesBySlide[index] ?? "讲师提示：围绕本页标题，用部门真实工作举例。讲完后追问：这页内容能转成哪个岗位的 Skill 检查项？";
      notes(slide, content);
    });
    const outName = fileName.replace(".pptx", "-带讲师提示版.pptx");
    const pptx = await PresentationFile.exportPptx(p);
    await pptx.save(`${OUT}/${outName}`);
  }
}

await addNotesToExistingDecks();
await buildAnalogyDeck();
