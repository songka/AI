import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = process.cwd().replaceAll("\\", "/");
const OUT = `${ROOT}/outputs/06-大陆环境AI建立Skill工具选型.pptx`;
const PREVIEW = `${ROOT}/work/presentations/skill-training/tmp/preview/06-mainland-ai-platforms`;
const W = 1280;
const H = 720;

const colors = {
  ink: "#111111",
  muted: "#555555",
  pale: "#F5F5F5",
  panel: "#ECEFF3",
  line: "#C5CBD3",
  blue: "#2563EB",
  green: "#059669",
  orange: "#F97316",
  red: "#DC2626",
  purple: "#7C3AED",
};

function box(slide, x, y, w, h, fill = colors.pale, line = colors.line) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
  });
}

function text(slide, value, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    fontFace: "Microsoft YaHei",
    fontSize: opts.size ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? colors.ink,
    alignment: opts.align ?? "left",
  };
  return shape;
}

function notes(slide, lines) {
  slide.speakerNotes.textFrame.setText(Array.isArray(lines) ? lines : [lines]);
  slide.speakerNotes.setVisible(true);
}

function footer(slide, n) {
  text(slide, "大陆环境 AI / Agent / Skill 选型", 54, 30, 500, 26, { size: 15, bold: true, color: colors.muted });
  text(slide, String(n).padStart(2, "0"), W - 96, H - 46, 42, 24, { size: 14, color: colors.muted, align: "right" });
}

function title(slide, value, sub, n) {
  footer(slide, n);
  text(slide, value, 54, 80, 760, 88, { size: 42, bold: true });
  if (sub) text(slide, sub, 58, 165, 860, 42, { size: 21, color: colors.muted });
}

function bullets(slide, titleText, items, n, opts = {}) {
  slide.background.fill = "#FFFFFF";
  title(slide, titleText, opts.sub, n);
  let y = opts.startY ?? 235;
  for (const item of items) {
    const accent = item.color ?? colors.blue;
    box(slide, 62, y + 6, 8, 42, accent, accent);
    text(slide, item.head, 92, y, 330, 30, { size: 22, bold: true, color: accent });
    text(slide, item.body, 92, y + 34, 1010, 50, { size: 18, color: colors.ink });
    y += opts.gap ?? 82;
  }
}

function chip(slide, value, x, y, w, color) {
  box(slide, x, y, w, 34, "#FFFFFF", color);
  text(slide, value, x + 10, y + 7, w - 20, 18, { size: 14, bold: true, color, align: "center" });
}

function matrix(slide, titleText, rows, n, notesText) {
  slide.background.fill = "#FFFFFF";
  title(slide, titleText, "把“能不能用”拆成课堂体验、部门试点、企业落地三个层级。", n);
  const x = 56;
  const y = 218;
  const widths = [150, 168, 250, 244, 252, 102];
  const heads = ["平台", "适合阶段", "Skill 等价物", "优势", "注意点", "建议"];
  let cx = x;
  for (let i = 0; i < heads.length; i++) {
    box(slide, cx, y, widths[i], 46, colors.panel, colors.line);
    text(slide, heads[i], cx + 8, y + 14, widths[i] - 16, 18, { size: 14, bold: true, align: "center" });
    cx += widths[i];
  }
  let cy = y + 46;
  for (const row of rows) {
    cx = x;
    for (let i = 0; i < row.length; i++) {
      box(slide, cx, cy, widths[i], 70, i === 0 ? "#FFFFFF" : colors.pale, colors.line);
      text(slide, row[i], cx + 8, cy + 10, widths[i] - 16, 46, { size: i === 0 ? 15 : 13, bold: i === 0, color: i === 5 ? colors.green : colors.ink, align: i === 5 ? "center" : "left" });
      cx += widths[i];
    }
    cy += 70;
  }
  notes(slide, notesText);
}

function lane(slide, x, y, w, h, heading, body, color) {
  box(slide, x, y, w, h, "#FFFFFF", colors.line);
  box(slide, x, y, w, 42, color, color);
  text(slide, heading, x + 16, y + 12, w - 32, 18, { size: 16, bold: true, color: "#FFFFFF", align: "center" });
  text(slide, body, x + 18, y + 62, w - 36, h - 82, { size: 17, color: colors.ink });
}

function sourceSlide(slide, n) {
  slide.background.fill = "#FFFFFF";
  title(slide, "资料来源与课堂使用提醒", "课件按 2026-07-04 可查官方公开资料整理，正式采购前仍需复核价格、配额、合规条款。", n);
  const items = [
    ["Dify 官方文档", "docs.dify.ai"],
    ["FastGPT 官方文档", "doc.fastgpt.io / fastgpt.cn"],
    ["阿里云百炼官方文档", "help.aliyun.com/zh/model-studio"],
    ["百度千帆官方文档", "cloud.baidu.com/doc/qianfan"],
    ["腾讯元器官网", "yuanqi.tencent.com"],
    ["智谱开放平台文档", "docs.bigmodel.cn"],
  ];
  let y = 240;
  for (const [name, url] of items) {
    box(slide, 70, y, 280, 42, colors.pale, colors.line);
    text(slide, name, 88, y + 12, 240, 18, { size: 15, bold: true });
    text(slide, url, 380, y + 12, 680, 18, { size: 15, color: colors.blue });
    y += 56;
  }
  text(slide, "提醒：课堂演示尽量使用脱敏样例，不把真实客户资料、设备图纸、验证记录直接上传到公共测试环境。", 70, 602, 1040, 46, { size: 19, color: colors.red, bold: true });
  notes(slide, [
    "讲师提示：这一页要明确边界。选型建议是教学用，不是最终采购结论。",
    "正式落地需要 IT、质量、信息安全、采购一起确认：访问、账号、数据位置、合同、日志、权限、退出机制。",
  ]);
}

async function build() {
  const p = Presentation.create({ slideSize: { width: W, height: H } });

  let s = p.slides.add();
  s.background.fill = "#FFFFFF";
  box(s, 62, 86, 10, 500, colors.blue, colors.blue);
  text(s, "大陆环境下，哪些 AI 平台适合建立“Skill”", 96, 102, 860, 110, { size: 44, bold: true });
  text(s, "给非标自动化部门的课堂选型：免费体验、部门试点、企业落地", 100, 230, 880, 42, { size: 24, color: colors.muted });
  lane(s, 100, 330, 310, 180, "免费测试", "先让学员理解智能体、工作流、知识库、工具调用。重点是低门槛和能现场演示。", colors.green);
  lane(s, 470, 330, 310, 180, "部门试点", "围绕 IO 表、方案评审、资料归档、验证预检做小闭环。重点是可复用和可复核。", colors.blue);
  lane(s, 840, 330, 310, 180, "企业落地", "关注数据安全、私有化、权限、日志、合同、成本和系统集成。", colors.orange);
  text(s, "适用听众：电控、机构、软件、生物管、项目文职、管理人员", 100, 610, 840, 30, { size: 19, color: colors.muted });
  notes(s, [
    "开场主线：不要先问哪个平台最强，先问我们要把哪类工作变成稳定流程。",
    "把 Skill 翻译成更接地气的话：让 AI 按我们部门的 SOP、模板、脚本和经验做事。",
  ]);

  s = p.slides.add();
  bullets(s, "先统一概念：国内平台不一定叫 Skill", [
    { head: "Skill", body: "在 Codex/OpenAI 语境中，通常是说明书 + 文件 + 脚本 + 示例，让 AI 获得一项可复用能力。", color: colors.blue },
    { head: "智能体 / Agent", body: "国内平台常见叫法：给 AI 一个角色、目标、知识库和工具，让它按任务行动。", color: colors.green },
    { head: "工作流", body: "把步骤画出来：先解析文件，再查知识库，再调用工具，最后输出表格或报告。", color: colors.orange },
    { head: "插件 / 工具 / MCP", body: "让 AI 能连接外部系统，例如表格检查脚本、数据库、企业知识库、网页 API。", color: colors.purple },
    { head: "知识库", body: "把部门资料、模板、规范喂给 AI 查询，但不等于 AI 一定懂业务边界。", color: colors.red },
  ], 2, { sub: "课堂上可以告诉学员：名字不同，本质都是把“人会做的流程”交给 AI 稳定执行。", gap: 75 });
  notes(s, [
    "讲师提示：这一页解决术语焦虑。学员听到 Skill、Agent、智能体、应用、工作流时，不要以为是完全不同世界。",
    "强调：真正的价值不在名词，而在是否能把部门经验沉淀成可重复执行的流程。",
  ]);

  s = p.slides.add();
  bullets(s, "选型看六件事", [
    { head: "能不能访问", body: "大陆网络、实名、账号、支付、公司 IT 白名单是否可行。", color: colors.blue },
    { head: "能不能免费试", body: "是否有免费额度、沙盒、新人券、社区版，适不适合课堂演示。", color: colors.green },
    { head: "能不能做流程", body: "是否支持智能体、工作流、工具调用、脚本/API、知识库。", color: colors.orange },
    { head: "能不能接业务", body: "是否能接飞书、钉钉、企微、网页、API、内部系统。", color: colors.purple },
    { head: "能不能管数据", body: "文档是否脱敏，是否支持私有化、权限、日志、审计、合同条款。", color: colors.red },
    { head: "谁来维护", body: "文职可维护提示词和知识库，工程师维护脚本/API，IT 管部署和权限。", color: colors.muted },
  ], 3, { gap: 68, startY: 220 });
  notes(s, [
    "讲师提示：把平台选择从“品牌比较”拉回“工作条件”。",
    "可以让学员用这六项给自己熟悉的平台打分，马上会发现没有万能答案。",
  ]);

  s = p.slides.add();
  bullets(s, "免费测试优先清单", [
    { head: "腾讯元器 / 扣子", body: "适合低门槛课堂体验：快速创建智能体、客服/内容/PPT 类演示，适合让非技术同事先上手。", color: colors.green },
    { head: "Dify", body: "官方提供 Cloud Sandbox，也支持社区版自部署；适合理解 Agent、工作流、知识库、工具和 MCP。", color: colors.blue },
    { head: "FastGPT", body: "有中国大陆版入口，文档明确覆盖知识库、工作流、Agent 编排、工具调用和技能扩展。", color: colors.orange },
    { head: "智谱开放平台", body: "适合开发/API 体验，文档覆盖工具调用、知识库、智能体开发平台和 OpenAI SDK 兼容。", color: colors.purple },
    { head: "百度千帆", body: "官方文档显示新用户实名后有新人券；适合课堂展示云平台 Agent 能力和模型服务。", color: colors.red },
  ], 4, { sub: "免费测试的目标不是一次到位，而是让团队快速理解“能做什么、边界在哪里”。", gap: 76 });
  notes(s, [
    "讲师提示：免费测试阶段要用脱敏样例。不要为了演示方便上传真实客户文件。",
    "Dify、FastGPT 更像流程/应用平台；腾讯元器、扣子更适合快速感知；智谱、千帆更适合讲 API 和模型服务。",
  ]);

  s = p.slides.add();
  bullets(s, "付费好用 / 企业落地清单", [
    { head: "阿里云百炼", body: "适合企业云路线：模型、智能体、工作流、知识库、插件和 MCP 能力集中，API 兼容性强。", color: colors.orange },
    { head: "百度千帆", body: "适合已有百度云体系或需要企业级 Agent 平台、工具/MCP、模型服务的场景。", color: colors.blue },
    { head: "Dify 自部署 / 商业版", body: "适合有 IT 能力、希望流程可控、知识库和工具链可管理的部门试点到企业推广。", color: colors.green },
    { head: "FastGPT 商业 / 私有化", body: "适合知识库问答、工作流、部门内部资料助手，以及希望中文资料体验更顺手的团队。", color: colors.purple },
    { head: "腾讯生态", body: "适合公众号、客服、内容分发、腾讯办公生态；正式落地前需复核权限、数据和企业管理能力。", color: colors.red },
  ], 5, { sub: "付费不是买“更聪明的聊天”，而是买稳定、合规、可集成、可维护。", gap: 76 });
  notes(s, [
    "讲师提示：企业落地要把采购语言讲清楚：谁付费、谁维护、数据在哪里、出了问题谁负责。",
    "建议别只比较模型分数，要比较平台能否支撑部门 SOP。",
  ]);

  s = p.slides.add();
  matrix(s, "平台对比一览", [
    ["腾讯元器/扣子", "课堂体验", "智能体、插件、知识库", "上手快，适合内容和服务类场景", "企业数据与流程治理需复核", "先试"],
    ["Dify", "试点/落地", "Agent、Workflow、Tools、MCP", "开源、自部署、流程清晰", "需要一定技术维护", "推荐"],
    ["FastGPT", "试点/落地", "知识库、工作流、Agent、技能", "中文文档和知识库场景友好", "复杂集成需工程师参与", "推荐"],
    ["阿里云百炼", "企业落地", "智能体、工作流、插件、MCP", "云服务体系完整，API 兼容", "成本和权限需采购评估", "推荐"],
    ["百度千帆", "企业落地", "Agent、工具、MCP、模型服务", "企业级平台能力完整", "需评估生态匹配度", "可选"],
    ["智谱开放平台", "开发试验", "API、工具调用、知识库、智能体", "开发友好，适合模型/API 课", "非技术学员门槛略高", "补充"],
  ], 6, [
    "讲师提示：这一页是核心对比。不要把推荐理解成唯一答案。",
    "如果部门没有 IT 支撑，优先课堂体验平台；如果准备进入项目资料和内部流程，优先 Dify/FastGPT/企业云平台。",
  ]);

  s = p.slides.add();
  slide7(s);

  s = p.slides.add();
  bullets(s, "非标自动化工作如何映射到平台", [
    { head: "IO 表检查助手", body: "Dify/FastGPT：上传 CSV，先跑脚本检查空字段、重复地址，再由 AI 输出风险和整改表。", color: colors.blue },
    { head: "方案评审助手", body: "知识库放 URS、标准方案、评审清单；工作流按机械、电控、软件、验证分栏输出。", color: colors.green },
    { head: "项目资料归档助手", body: "文职同事可维护资料目录和命名规则，AI 根据会议纪要生成缺失清单。", color: colors.orange },
    { head: "FAT/SAT 文档预检助手", body: "质量或生物管人员维护模板规则，AI 只做预检和问题清单，最终结论必须人工确认。", color: colors.purple },
    { head: "供应商沟通助手", body: "用脱敏需求和历史邮件模板生成问题清单、会议纪要、待办项，不上传合同敏感信息。", color: colors.red },
  ], 8, { sub: "选型不要抽象比较，要拿本部门真实工作流试。", gap: 76 });
  notes(s, [
    "讲师提示：这里要把前面几份 Skill 案例串回来：IO 表、方案评审、归档、验证预检。",
    "强调：平台只是容器，真正要迁移进去的是部门的输入、流程、判断标准和输出格式。",
  ]);

  s = p.slides.add();
  bullets(s, "课堂练习：同一个任务，换三个平台思路", [
    { head: "任务", body: "建立“IO 表检查助手”：输入 IO 表样例，输出缺失字段、重复地址、命名问题、整改建议。", color: colors.blue },
    { head: "普通智能体路线", body: "用腾讯元器/扣子快速创建角色和提示词，让学员理解 Agent 的基本交互。", color: colors.green },
    { head: "工作流路线", body: "用 Dify/FastGPT 拆步骤：上传文件、脚本检查、知识库规则、生成表格。", color: colors.orange },
    { head: "企业云路线", body: "用阿里云百炼/百度千帆讲 API、权限、知识库、工具/MCP、日志和成本。", color: colors.purple },
    { head: "复盘", body: "比较三个结果：谁上手最快、谁最稳定、谁最适合真实项目。", color: colors.red },
  ], 9, { sub: "这页可以直接放进课堂提示：让学员带着问题比较，而不是听平台介绍。", gap: 78 });
  notes(s, [
    "讲师提示：课堂中可以安排 30-45 分钟小组练习。",
    "电控工程师关注地址和信号；机构工程师关注设备动作和风险；文职关注资料字段和输出表格；生物管关注合规边界。",
  ]);

  s = p.slides.add();
  slide10(s);

  s = p.slides.add();
  bullets(s, "符合国情的使用红线", [
    { head: "不上传敏感原件", body: "客户资料、合同、报价、设备总图、验证原始记录先脱敏，或只在公司批准环境使用。", color: colors.red },
    { head: "不让 AI 做最终放行", body: "AI 可以预检、归纳、提示风险；质量结论、设计结论、验收结论必须人工确认。", color: colors.orange },
    { head: "不把公共测试当生产系统", body: "免费平台适合学习和样例，不适合承载长期项目资料。", color: colors.blue },
    { head: "不只看模型聪明", body: "真实落地还要看权限、日志、成本、备份、退出、供应商合同。", color: colors.green },
    { head: "不让一个人维护全部", body: "业务规则由部门维护，脚本/API 由工程师维护，账号和数据由 IT/管理共同负责。", color: colors.purple },
  ], 11, { sub: "越接近真实项目，越要把 AI 当受控工具，而不是个人聊天窗口。", gap: 78 });
  notes(s, [
    "讲师提示：这一页要说得坚定一些。让大家敢用，但知道边界。",
    "非标自动化项目常有客户、工艺、验证、报价和设备资料，不能因为试用方便就破坏数据边界。",
  ]);

  s = p.slides.add();
  bullets(s, "推荐结论：三步走", [
    { head: "第一步：课堂认知", body: "用免费/低门槛平台建立智能体，让各岗位都知道 Agent、工作流、知识库、工具是什么。", color: colors.green },
    { head: "第二步：部门试点", body: "用 Dify 或 FastGPT 做 1-2 个小闭环：IO 表检查、方案评审、资料归档。", color: colors.blue },
    { head: "第三步：企业落地", body: "由 IT、质量、管理和采购一起评估阿里云百炼、百度千帆、自部署 Dify/FastGPT 等路线。", color: colors.orange },
    { head: "长期维护", body: "每次项目复盘，把新规则、新模板、新问题写回 Skill/工作流/知识库，形成部门资产。", color: colors.purple },
  ], 12, { sub: "不要一开始就追求“大而全平台”，先做一个能被复用的小流程。", gap: 92, startY: 250 });
  notes(s, [
    "结尾主线：选平台只是开始，真正的目标是建立部门自己的 AI 工作方法。",
    "建议下次课直接让各岗位带一个真实但脱敏的样例，现场做一个智能体或工作流。",
  ]);

  s = p.slides.add();
  sourceSlide(s, 13);

  await fs.mkdir(PREVIEW, { recursive: true });
  for (const [i, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(PREVIEW, `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);
}

function slide7(slide) {
  slide.background.fill = "#FFFFFF";
  title(slide, "按人群推荐路线", "同一堂课里，不同岗位关心点不同，练习也要分层。", 7);
  lane(slide, 70, 240, 250, 285, "电控 / 软件", "重点看：脚本、API、工具调用、MCP、日志。\n\n练习：IO 表检查、PLC tag 命名、报警清单生成。", colors.blue);
  lane(slide, 350, 240, 250, 285, "机构 / 工艺", "重点看：方案评审、动作逻辑、风险清单。\n\n练习：从 URS 生成评审问题和待确认项。", colors.green);
  lane(slide, 630, 240, 250, 285, "文职 / 项目", "重点看：资料归档、会议纪要、任务跟踪。\n\n练习：从会议记录生成缺失资料清单。", colors.orange);
  lane(slide, 910, 240, 250, 285, "生物管 / 质量", "重点看：边界、合规、预检、复核。\n\n练习：FAT/SAT 文档完整性预检。", colors.purple);
  text(slide, "讲法：同一个平台，不同岗位看到的是不同入口。工程师看工具，文职看模板，质量看边界。", 80, 592, 1040, 30, { size: 19, color: colors.muted });
  notes(slide, [
    "讲师提示：这页可用于分组。每组不需要都学 API，但每组都要学会把自己的工作标准说清楚。",
    "建议每组输出一个“本岗位最值得变成 Skill 的任务”。",
  ]);
}

function slide10(slide) {
  slide.background.fill = "#FFFFFF";
  title(slide, "选型决策树", "先判断数据和维护条件，再决定用免费平台、云平台还是自部署。", 10);
  box(slide, 90, 230, 320, 82, "#FFFFFF", colors.blue);
  text(slide, "只是课堂体验？", 112, 252, 276, 26, { size: 22, bold: true, align: "center", color: colors.blue });
  text(slide, "用免费/低门槛平台 + 脱敏样例", 112, 282, 276, 18, { size: 15, align: "center" });
  box(slide, 480, 230, 320, 82, "#FFFFFF", colors.orange);
  text(slide, "涉及部门资料？", 502, 252, 276, 26, { size: 22, bold: true, align: "center", color: colors.orange });
  text(slide, "优先 Dify/FastGPT 试点，明确权限", 502, 282, 276, 18, { size: 15, align: "center" });
  box(slide, 870, 230, 320, 82, "#FFFFFF", colors.red);
  text(slide, "涉及客户/验证/合同？", 892, 252, 276, 26, { size: 22, bold: true, align: "center", color: colors.red });
  text(slide, "走企业云或私有化审批", 892, 282, 276, 18, { size: 15, align: "center" });
  text(slide, "↓", 225, 340, 40, 40, { size: 28, bold: true, align: "center", color: colors.blue });
  text(slide, "↓", 615, 340, 40, 40, { size: 28, bold: true, align: "center", color: colors.orange });
  text(slide, "↓", 1005, 340, 40, 40, { size: 28, bold: true, align: "center", color: colors.red });
  lane(slide, 90, 400, 320, 158, "现场演示", "目标：理解概念。\n不要追求系统集成。\n课后保留样例提示词。", colors.blue);
  lane(slide, 480, 400, 320, 158, "小范围试点", "目标：让一个流程可复用。\n需要负责人和维护节奏。\n输出可复核表格。", colors.orange);
  lane(slide, 870, 400, 320, 158, "正式项目", "目标：受控、合规、可追踪。\n需要合同、权限、日志、成本预算。\n必须有人审。", colors.red);
  notes(slide, [
    "讲师提示：决策树要让大家知道，平台选择首先是数据和责任问题，不是功能炫不炫。",
    "可以问学员：你手上的资料属于哪一档？如果答案不确定，就按更高敏感级别处理。",
  ]);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
