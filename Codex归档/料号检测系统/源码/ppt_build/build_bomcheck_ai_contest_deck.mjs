import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const W = 1280;
const H = 720;
const WORK = "C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/bomcheck-ai-contest";
const ASSETS = path.join(WORK, "assets");
const OUT = "C:/Users/lfaf-test/Documents/料号检测系统/AI大赛_BOMCheck项目复盘_章节故事版.pptx";

async function readImage(name) {
  const bytes = await fs.readFile(path.join(ASSETS, name));
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addText(slide, text, x, y, w, h, style = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    fontSize: style.fontSize ?? 28,
    bold: style.bold ?? false,
    color: style.color ?? "#12323f",
    alignment: style.alignment ?? "left",
  };
  return box;
}

function addTitle(slide, title, subtitle = "") {
  addText(slide, title, 70, 54, 900, 70, { fontSize: 38, bold: true, color: "#0b2533" });
  if (subtitle) addText(slide, subtitle, 72, 118, 760, 44, { fontSize: 19, color: "#4b6470" });
}

function addTag(slide, text, x, y, fill = "#d9f99d") {
  const tag = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: 154, height: 36 },
    fill,
    line: { style: "solid", fill: "#ffffff", width: 0 },
    borderRadius: "rounded-xl",
  });
  tag.text = text;
  tag.text.style = { fontSize: 17, bold: true, color: "#0b2533", alignment: "center" };
  return tag;
}

function addCard(slide, title, body, x, y, w, h, fill = "#ffffff") {
  const card = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: "#cbdde4", width: 1 },
    borderRadius: "rounded-xl",
    shadow: "shadow-sm",
  });
  addText(slide, title, x + 22, y + 20, w - 44, 34, { fontSize: 22, bold: true, color: "#0b2533" });
  addText(slide, body, x + 22, y + 64, w - 44, h - 82, { fontSize: 17, color: "#365260" });
  return card;
}

function addStep(slide, n, title, x, y, color) {
  const circle = slide.shapes.add({
    geometry: "ellipse",
    position: { left: x, top: y, width: 58, height: 58 },
    fill: color,
    line: { style: "solid", fill: "#ffffff", width: 2 },
  });
  circle.text = String(n);
  circle.text.style = { fontSize: 24, bold: true, color: "#ffffff", alignment: "center" };
  addText(slide, title, x - 38, y + 72, 134, 46, { fontSize: 17, bold: true, color: "#0b2533", alignment: "center" });
}

function addFooter(slide, i) {
  addText(slide, `BOMCheck AI 落地实践`, 72, 674, 220, 26, { fontSize: 13, color: "#78909c" });
}

function addNotes(slide, notes) {
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(true);
}

function bg(slide, fill = "#f7fbfc") {
  slide.background.fill = fill;
  slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: 0, width: W, height: 720 },
    fill,
    line: { style: "solid", fill: fill, width: 0 },
  });
}

function addSectionSlide(p, chapter, title, subtitle, color = "#0f766e") {
  const s = p.slides.add(); bg(s, "#eefbf7");
  addText(s, chapter, 88, 96, 260, 42, { fontSize: 26, bold: true, color });
  addText(s, title, 88, 220, 920, 90, { fontSize: 50, bold: true, color: "#0b2533" });
  addText(s, subtitle, 92, 340, 760, 52, { fontSize: 26, color: "#4b6470" });
  const bar = s.shapes.add({
    geometry: "rect",
    position: { left: 88, top: 450, width: 760, height: 8 },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
  addFooter(s, 0);
  return s;
}

async function main() {
  await fs.mkdir(path.dirname(OUT), { recursive: true });
  const imgBom = await readImage("bom_mountain.png");
  const imgFlow = await readImage("workflow.png");
  const imgSearch = await readImage("erp_search.png");
  const imgSmb = await readImage("smb_launcher.png");

  const p = Presentation.create({ slideSize: { width: W, height: H } });

  // 1
  {
    const s = p.slides.add(); bg(s, "#eef9f8");
    s.images.add({ blob: imgBom, contentType: "image/png", fit: "cover", position: { left: 640, top: 0, width: 640, height: 720 } });
    addText(s, "AI 如何帮我做出\n电控 BOM 料号检测系统", 72, 96, 520, 180, { fontSize: 50, bold: true, color: "#082f3a" });
    addText(s, "从人工审核到现场可用工具", 78, 306, 480, 40, { fontSize: 26, color: "#2f6f73" });
    addTag(s, "公司 AI 大赛", 78, 382, "#b7f3e9");
    addTag(s, "真实项目", 248, 382, "#d9f99d");
    addFooter(s, 1);
    addNotes(s, "开场先讲身份和场景：我是电控主管，日常要审核大量电控 BOM。这个项目不是为了演示 AI，而是为了解决真实工作中的漏检、查询慢、资料难找这些问题。");
  }

  // Agenda
  {
    const s = p.slides.add(); bg(s);
    addTitle(s, "今天按四个章节讲清楚", "少讲代码，多讲 AI 如何把业务经验变成可用工具");
    addCard(s, "01 业务起点", "为什么电控 BOM 审核需要一个 AI 辅助工具", 100, 190, 480, 120, "#ffffff");
    addCard(s, "02 AI 迭代", "从需求文件到桌面版、查询和资料入口", 700, 190, 480, 120, "#ffffff");
    addCard(s, "03 现场落地", "共享盘、编码、窗口、打包和启动速度", 100, 385, 480, 120, "#ffffff");
    addCard(s, "04 成果方法", "最终成果、可复制步骤和注意事项", 700, 385, 480, 120, "#ffffff");
    addText(s, "主线：业务专家提出判断，AI 把判断做成工具", 165, 585, 950, 44, { fontSize: 31, bold: true, color: "#0f766e", alignment: "center" });
    addFooter(s, 0);
    addNotes(s, "目录页先给评委一个结构：我会分四章讲，不是流水账。第一章讲为什么做，第二章讲怎么迭代，第三章讲现场落地，第四章讲成果和方法。");
  }

  addNotes(
    addSectionSlide(p, "第一章", "业务起点", "从电控主管的审核痛点开始", "#0f766e"),
    "这一页作为章节过渡，提醒听众接下来先看业务问题。不要急着讲 AI 和代码，先让大家理解为什么这个工具值得做。"
  );

  // 2
  {
    const s = p.slides.add(); bg(s);
    addTitle(s, "问题不是不会审，而是太容易漏", "BOM 料多、规则多，ERP 不适合做灵活审核");
    addCard(s, "料号很多", "一个 BOM 里有大量电控物料，人工逐项判断容易疲劳。", 80, 205, 330, 170, "#ffffff");
    addCard(s, "规则复杂", "停产替换、绑定组合、重要物料都依赖经验。", 475, 205, 330, 170, "#ffffff");
    addCard(s, "资料分散", "ERP、Excel、公共槽、说明书不在一个入口。", 870, 205, 330, 170, "#ffffff");
    addText(s, "核心目标：把主管经验变成可重复执行的工具", 150, 472, 980, 56, { fontSize: 34, bold: true, color: "#006d77", alignment: "center" });
    addFooter(s, 2);
    addNotes(s, "这里强调痛点不是个人能力，而是工作量和复杂度。ERP 有主数据，但无法灵活处理现场审核规则，所以我们需要一个辅助层。");
  }

  // 3
  {
    const s = p.slides.add(); bg(s, "#f8fff3");
    addTitle(s, "第一步不是写代码，是写清楚规则", "最初我提供的是一份需求文件");
    addCard(s, "输入", "BOM Excel\n失效料号库\n绑定料号库\n重要物料库", 90, 190, 280, 260, "#ffffff");
    addCard(s, "处理", "替换失效料\n识别数量列\n计算必备组合\n标记重要物料", 500, 190, 280, 260, "#ffffff");
    addCard(s, "输出", "界面 OK/NG\n统计工作表\n剩余物料表\n维护页面", 910, 190, 280, 260, "#ffffff");
    addText(s, "经验：需求文件越接近真实流程，AI 越容易落地", 170, 545, 940, 44, { fontSize: 30, bold: true, color: "#306b34", alignment: "center" });
    addFooter(s, 3);
    addNotes(s, "这一页讲方法：我没有只说帮我做个软件，而是把审核流程拆成输入、处理和输出。AI 能快速落地，是因为业务规则被结构化了。");
  }

  // 4
  {
    const s = p.slides.add(); bg(s);
    s.images.add({ blob: imgFlow, contentType: "image/png", fit: "cover", position: { left: 0, top: 155, width: 1280, height: 410 } });
    addTitle(s, "先做可运行闭环，再一点点变准", "从需求文件到桌面 UI，再到 Web 和共享盘部署");
    addText(s, "不要一开始追求完美，先让真实用户能试", 220, 600, 840, 44, { fontSize: 30, bold: true, color: "#0b6b70", alignment: "center" });
    addFooter(s, 4);
    addNotes(s, "第一版先做桌面 UI：选择 Excel、执行、看结果。只要能跑，真实 BOM 就会暴露问题，后续再迭代规则。");
  }

  addNotes(
    addSectionSlide(p, "第二章", "AI 迭代", "真实样本把软件一步步磨出来", "#2563eb"),
    "这一章开始讲 AI 怎么参与开发。重点不是一次生成，而是每次用真实样本发现问题，再让 AI 快速修复。"
  );

  // 5
  {
    const s = p.slides.add(); bg(s, "#fffaf0");
    addTitle(s, "真实 BOM 把边界问题都带出来了");
    addStep(s, 1, "数量列识别", 150, 230, "#0ea5a5");
    addStep(s, 2, "多工作表", 365, 230, "#2f80ed");
    addStep(s, 3, "已替换料", 580, 230, "#f59e0b");
    addStep(s, 4, "简繁体", 795, 230, "#10b981");
    addStep(s, 5, "缺料组合", 1010, 230, "#8b5cf6");
    addText(s, "AI 搭框架很快，业务准确性来自真实样本反复验证", 150, 500, 980, 60, { fontSize: 34, bold: true, color: "#78350f", alignment: "center" });
    addFooter(s, 5);
    addNotes(s, "这一页讲迭代：Excel 不是标准数据库，表头、数量列、工作表、人工标记都可能不一样。每一次真实样本出错，都变成下一条规则。");
  }

  // 6
  {
    const s = p.slides.add(); bg(s);
    addTitle(s, "企业现场问题，经常不在算法里", "SMB 公共槽、中文路径、编码和多人维护都要处理");
    addCard(s, "共享盘路径", "配置和数据库放在 SMB，盘符、UNC、权限都可能不同。", 82, 190, 340, 180, "#ffffff");
    addCard(s, "中文编码", "UTF-8、GBK、BOM、中文文件名都会影响读取和保存。", 470, 190, 340, 180, "#ffffff");
    addCard(s, "写入可靠性", "多人维护时要有备份、锁、原子写入和错误提示。", 858, 190, 340, 180, "#ffffff");
    addText(s, "从“能跑”到“现场稳”，靠的是部署细节", 220, 512, 840, 48, { fontSize: 34, bold: true, color: "#005f73", alignment: "center" });
    addFooter(s, 6);
    addNotes(s, "这里讲现场环境：很多问题不是 AI 算法，而是公司环境。共享盘、中文编码、权限和多人读写，如果不处理，软件就不稳定。");
  }

  // 7
  {
    const s = p.slides.add(); bg(s, "#effafe");
    s.images.add({ blob: imgSearch, contentType: "image/png", fit: "cover", position: { left: 615, top: 120, width: 590, height: 420 } });
    addTitle(s, "料号查询要按人的习惯来", "ERP 要 % 通配符，软件里只需要空格关键词");
    addText(s, "ERP 语法", 110, 210, 220, 42, { fontSize: 28, bold: true, color: "#64748b" });
    addText(s, "%电机%400W%", 115, 266, 360, 46, { fontSize: 30, bold: true, color: "#94a3b8" });
    addText(s, "软件习惯", 110, 385, 220, 42, { fontSize: 28, bold: true, color: "#006d77" });
    addText(s, "电机 400W", 115, 441, 360, 46, { fontSize: 34, bold: true, color: "#0f766e" });
    addFooter(s, 7);
    addNotes(s, "这页讲产品判断：ERP 查询需要百分号，但现场人员更习惯输入几个关键词。AI 工具的价值，是把系统语法翻译成人的自然习惯。");
  }

  // 8
  {
    const s = p.slides.add(); bg(s, "#f6fffb");
    addTitle(s, "查询功能长成了资料入口", "员工不只要料号，还想看图片、说明书和项目资料");
    addCard(s, "看得见", "物料图片帮助快速判断，不只看相似描述。", 90, 205, 330, 180, "#ffffff");
    addCard(s, "找得到", "说明书、规格书、接线资料连接到公共槽位置。", 475, 205, 330, 180, "#ffffff");
    addCard(s, "连得上", "UA 专案料号关联整个项目资料包。", 860, 205, 330, 180, "#ffffff");
    addText(s, "真正有用的工具，是把每天要找的资料放到同一个入口", 115, 505, 1050, 54, { fontSize: 31, bold: true, color: "#047857", alignment: "center" });
    addFooter(s, 8);
    addNotes(s, "这里讲功能自然扩展：当系统已经抓取 ERP 料号，就可以顺便支持查询。员工提出看图片，于是工具又连接了公共槽资料。");
  }

  // 9
  {
    const s = p.slides.add(); bg(s, "#fff7ed");
    addTitle(s, "自动检索资料有边界", "这一段尝试过，但不能盲目全自动");
    addCard(s, "来源不标准", "官网、图片、公共槽命名都不统一。", 100, 200, 300, 170, "#ffffff");
    addCard(s, "结果要确认", "抓到图片不代表图片一定正确。", 490, 200, 300, 170, "#ffffff");
    addCard(s, "更适合协同", "AI 推荐候选，人确认后入库。", 880, 200, 300, 170, "#ffffff");
    addText(s, "教训：资料类任务先做候选推荐，再做人为确认", 170, 500, 940, 48, { fontSize: 32, bold: true, color: "#c2410c", alignment: "center" });
    addFooter(s, 9);
    addNotes(s, "这一页要讲得坦诚：自动找图片和资料不是每次都可靠。AI 能减少搜索成本，但资料入库仍需要人工确认，这样更可信。");
  }

  addNotes(
    addSectionSlide(p, "第三章", "现场落地", "企业环境里的问题，必须在现场解决", "#c2410c"),
    "这一章讲落地细节。评委可能更关心实际可用性，所以这里要突出 Windows 本地测试、共享盘、打包和启动速度。"
  );

  // 10
  {
    const s = p.slides.add(); bg(s);
    addTitle(s, "Windows 本地 Codex 缩短了验证闭环", "从云端改代码，变成在本机直接试用和修正");
    addCard(s, "直接运行", "本地打开 app.py，登录 admin/admin，逐个进子界面。", 88, 200, 330, 190, "#ffffff");
    addCard(s, "直接验证", "检查拖选复制、窗口显示、按钮布局和数据刷新。", 475, 200, 330, 190, "#ffffff");
    addCard(s, "直接打包", "桌面版和 Web 版分别打包，启动后做健康检查。", 862, 200, 330, 190, "#ffffff");
    addText(s, "从“写代码”变成“陪着用户在现场试软件”", 190, 515, 900, 50, { fontSize: 33, bold: true, color: "#0b6b70", alignment: "center" });
    addFooter(s, 10);
    addNotes(s, "这里讲工具链变化：云端开发快，但 Windows GUI、鼠标拖选、打包和共享盘必须本地试。Windows Codex 让反馈闭环明显变短。");
  }

  // 11
  {
    const s = p.slides.add(); bg(s, "#f7fbfc");
    s.images.add({ blob: imgSmb, contentType: "image/png", fit: "cover", position: { left: 595, top: 130, width: 600, height: 410 } });
    addTitle(s, "共享盘启动慢，也要算进落地成本", "本地 5 秒，SMB 直接打开超过 1 分钟");
    addText(s, "解决方案", 92, 210, 280, 44, { fontSize: 30, bold: true, color: "#0b2533" });
    addText(s, "小启动器\n先缓存到本机\n数据仍走共享盘", 95, 278, 390, 150, { fontSize: 31, bold: true, color: "#006d77" });
    addFooter(s, 11);
    addNotes(s, "这一页讲部署细节：onefile exe 从 SMB 启动会慢，因为要从网络盘读和解包。后来做小启动器，把主程序缓存到本地，但配置和业务数据仍在共享盘。");
  }

  addNotes(
    addSectionSlide(p, "第四章", "成果和方法", "把一次项目经验变成可复制路径", "#7c3aed"),
    "最后一章收束到成果和方法论。这里要让评委看到这个案例不仅解决了一个问题，也总结出其他项目可复制的方法。"
  );

  // 12
  {
    const s = p.slides.add(); bg(s, "#f8fff3");
    addTitle(s, "最终成果不是一个按钮，而是一套工具链");
    addCard(s, "BOM 检测", "失效替换\n绑定组合\n重要物料\n结果 Excel", 84, 185, 255, 260, "#ffffff");
    addCard(s, "料号查询", "空格搜索\n简繁转换\n分类浏览\n详情复制", 378, 185, 255, 260, "#ffffff");
    addCard(s, "资料入口", "图片预览\n公共槽路径\nUA 项目资料\n资源维护", 672, 185, 255, 260, "#ffffff");
    addCard(s, "交付体系", "桌面 + Web\nSMB 部署\n说明文档\n验收清单", 966, 185, 255, 260, "#ffffff");
    addFooter(s, 12);
    addNotes(s, "这里展示成果，不要讲太多技术细节。强调它已经覆盖审核、查询、资料和交付四类价值。");
  }

  // 13
  {
    const s = p.slides.add(); bg(s);
    addTitle(s, "这套方法可以复制到其他项目");
    addStep(s, 1, "写流程", 130, 230, "#0ea5a5");
    addStep(s, 2, "做闭环", 315, 230, "#2f80ed");
    addStep(s, 3, "喂样本", 500, 230, "#10b981");
    addStep(s, 4, "进现场", 685, 230, "#f59e0b");
    addStep(s, 5, "写文档", 870, 230, "#8b5cf6");
    addStep(s, 6, "再复用", 1055, 230, "#ef4444");
    addText(s, "业务专家负责判断，AI 负责把判断快速变成工具", 150, 508, 980, 54, { fontSize: 33, bold: true, color: "#0f766e", alignment: "center" });
    addFooter(s, 13);
    addNotes(s, "这一页是方法论：先把业务流程写清楚，再做最小闭环，用真实样本迭代，进入现场处理部署和交付，最后沉淀成文档和模板。");
  }

  // 14
  {
    const s = p.slides.add(); bg(s, "#fffaf0");
    addTitle(s, "我学到的三个注意事项");
    addCard(s, "不要只给结论", "给 AI 看真实样本、错误现象和期望输出。", 115, 205, 310, 210, "#ffffff");
    addCard(s, "不要只看编译", "一定要打开窗口、点按钮、跑实际业务流程。", 485, 205, 310, 210, "#ffffff");
    addCard(s, "不要迷信全自动", "高风险资料和规则，要保留人工确认。", 855, 205, 310, 210, "#ffffff");
    addFooter(s, 14);
    addNotes(s, "这一页可以作为经验总结。强调 AI 很强，但不是魔法。业务人员要给清楚上下文，测试要走真实流程，自动化要有边界。");
  }

  // 15
  {
    const s = p.slides.add(); bg(s, "#eafff7");
    addText(s, "AI 不是替代业务专家", 180, 148, 920, 70, { fontSize: 48, bold: true, color: "#064e3b", alignment: "center" });
    addText(s, "它把专家经验放大成\n可执行、可复用、可交付的工具", 185, 260, 910, 120, { fontSize: 42, bold: true, color: "#0f766e", alignment: "center" });
    addText(s, "谢谢", 555, 500, 170, 60, { fontSize: 38, bold: true, color: "#0b2533", alignment: "center" });
    addFooter(s, 15);
    addNotes(s, "收尾时回到主题：这个项目的价值不是 AI 单独完成，而是业务专家和 AI 协作，把经验沉淀成工具。最后可以补一句：这套方式还可以复制到其他工程管理场景。");
  }

  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);

  const previewDir = path.join(WORK, "preview");
  await fs.mkdir(previewDir, { recursive: true });
  for (const [index, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(WORK, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
