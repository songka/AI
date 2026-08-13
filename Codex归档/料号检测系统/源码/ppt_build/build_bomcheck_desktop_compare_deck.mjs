import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const W = 1280;
const H = 720;
const WORK = "C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/bomcheck-ai-contest";
const ASSETS = path.join(WORK, "assets");
const OUT = "C:/Users/lfaf-test/Documents/料号检测系统/AI大赛_BOMCheck项目复盘_桌面截图对比版.pptx";

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
    fontSize: style.fontSize ?? 24,
    bold: style.bold ?? false,
    color: style.color ?? "#102a32",
    alignment: style.alignment ?? "left",
  };
  return box;
}

function addNotes(slide, notes) {
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(true);
}

function bg(slide, fill = "#f6fbfc") {
  slide.background.fill = fill;
}

function title(slide, text, sub = "") {
  addText(slide, text, 64, 42, 880, 58, { fontSize: 36, bold: true, color: "#062c33" });
  if (sub) addText(slide, sub, 66, 102, 930, 34, { fontSize: 18, color: "#526b73" });
}

function footer(slide, n) {
  addText(slide, "BOMCheck AI 落地实践", 64, 674, 230, 24, { fontSize: 13, color: "#78909c" });
  addText(slide, String(n).padStart(2, "0"), 1184, 674, 40, 24, { fontSize: 13, color: "#78909c", alignment: "right" });
}

function pill(slide, text, x, y, fill, color = "#052d35", w = 130) {
  const shape = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: 34 },
    fill,
    line: { style: "solid", fill: "none", width: 0 },
    borderRadius: "rounded-xl",
  });
  shape.text = text;
  shape.text.style = { fontSize: 16, bold: true, color, alignment: "center" };
  return shape;
}

function card(slide, text, x, y, w, h, fill = "#ffffff") {
  const shape = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: "#c9dde3", width: 1 },
    borderRadius: "rounded-lg",
    shadow: "shadow-sm",
  });
  shape.text = text;
  shape.text.style = { fontSize: 22, bold: true, color: "#08323a", alignment: "center" };
  return shape;
}

function screenshot(slide, blob, x, y, w, h, label = "") {
  slide.shapes.add({
    geometry: "roundRect",
    position: { left: x - 8, top: y - 8, width: w + 16, height: h + 16 },
    fill: "#ffffff",
    line: { style: "solid", fill: "#bed3da", width: 1 },
    borderRadius: "rounded-lg",
    shadow: "shadow-md",
  });
  slide.images.add({
    blob,
    contentType: "image/png",
    fit: "contain",
    position: { left: x, top: y, width: w, height: h },
  });
  if (label) pill(slide, label, x + 14, y + 12, "#e0f2fe", "#075985", Math.max(126, label.length * 18));
}

function section(slide, n, name, sentence, color) {
  bg(slide, "#0a3f3a");
  slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: 0, width: W, height: H },
    fill: color,
    line: { style: "solid", fill: "none", width: 0 },
  });
  addText(slide, `第 ${n} 章`, 90, 128, 240, 54, { fontSize: 32, bold: true, color: "#ffffff" });
  addText(slide, name, 90, 206, 760, 76, { fontSize: 48, bold: true, color: "#ffffff" });
  addText(slide, sentence, 92, 304, 760, 46, { fontSize: 24, color: "#e7fff5" });
}

function callout(slide, text, x, y, w, h, fill = "#fef3c7") {
  const shape = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: "#ffffff", width: 1 },
    borderRadius: "rounded-lg",
  });
  shape.text = text;
  shape.text.style = { fontSize: 18, bold: true, color: "#17343a", alignment: "center" };
  return shape;
}

async function main() {
  const imgMountain = await readImage("bom_mountain.png");
  const imgWorkflow = await readImage("workflow.png");
  const imgErp = await readImage("erp_search.png");
  const imgSmb = await readImage("smb_launcher.png");
  const oldExec = await readImage("desktop_old_execute.png");
  const oldQuery = await readImage("desktop_old_query.png");
  const newExec = await readImage("desktop_new_execute.png");
  const newQuery = await readImage("desktop_new_query.png");

  const p = await Presentation.create({ slideSize: { width: W, height: H } });

  // 1
  {
    const s = p.slides.add(); bg(s, "#eefaf7");
    s.images.add({ blob: imgMountain, contentType: "image/png", fit: "cover", position: { left: 660, top: 0, width: 620, height: 720 } });
    addText(s, "AI 如何把电控 BOM 审核\n做成可交付软件", 72, 92, 690, 150, { fontSize: 46, bold: true, color: "#063238" });
    addText(s, "BOMCheck 项目复盘｜桌面版截图对比", 76, 262, 560, 38, { fontSize: 23, color: "#3f5961" });
    pill(s, "从需求文件到现场工具", 78, 346, "#ccfbf1", "#0f766e", 210);
    pill(s, "真实截图", 306, 346, "#dbeafe", "#1d4ed8", 112);
    pill(s, "可复制方法", 436, 346, "#fef3c7", "#92400e", 132);
    footer(s, 1);
    addNotes(s, "开场先讲身份：我是电控主管，日常要审核大量电控 BOM。这个项目不是为了展示 AI 炫技，而是把真实工作中的漏检、查询慢、资料难找，变成一个桌面软件。");
  }

  // 2
  {
    const s = p.slides.add(); bg(s);
    title(s, "目录", "像讲故事一样，看一个内部工具怎样一步步落地");
    const items = [
      ["01", "为什么做", "电控 BOM 审核的真实痛点"],
      ["02", "怎么做出来", "需求文件、样本、迭代"],
      ["03", "怎么变好用", "从旧版到新版桌面工作台"],
      ["04", "怎么落地", "共享盘、打包、启动速度"],
      ["05", "经验沉淀", "其他项目也能复用的方法"],
    ];
    items.forEach((it, i) => {
      const y = 174 + i * 86;
      pill(s, it[0], 96, y, "#0f766e", "#ffffff", 70);
      addText(s, it[1], 198, y - 4, 260, 42, { fontSize: 30, bold: true, color: "#09343b" });
      addText(s, it[2], 460, y + 2, 590, 34, { fontSize: 21, color: "#4a6570" });
    });
    footer(s, 2);
    addNotes(s, "目录页告诉评委：这不是纯技术汇报，而是一段落地过程。先讲业务问题，再讲开发迭代，然后用新旧截图证明软件确实变好用，最后总结方法。");
  }

  // 3
  {
    const s = p.slides.add(); section(s, 1, "为什么做", "ERP 有数据，但审核还缺一层现场规则", "#0f766e");
    addNotes(s, "第一章先进入业务现场。重点讲：这不是因为人不细心，而是工作复杂度太高，需要工具辅助。");
  }

  // 4
  {
    const s = p.slides.add(); bg(s, "#fffdf4");
    s.images.add({ blob: imgWorkflow, contentType: "image/png", fit: "cover", position: { left: 690, top: 94, width: 520, height: 470 } });
    title(s, "痛点不是一个按钮能解决", "电控 BOM 审核里有很多“现场知识”");
    card(s, "料多\n容易漏", 82, 206, 150, 130, "#ffffff");
    card(s, "停产\n要替换", 262, 206, 150, 130, "#ffffff");
    card(s, "组合料\n要绑定", 442, 206, 150, 130, "#ffffff");
    card(s, "资料\n不好找", 172, 386, 150, 130, "#ffffff");
    card(s, "ERP 查询\n不顺手", 352, 386, 170, 130, "#ffffff");
    footer(s, 4);
    addNotes(s, "这一页用少量词讲业务痛点：ERP 有料号主数据，但它不适合处理审核现场的规则，比如失效替换、组合绑定、重要物料提醒、资料位置。");
  }

  // 5
  {
    const s = p.slides.add(); bg(s);
    title(s, "第一步：把经验写成需求文件", "先让 AI 看懂工作流，再让它写代码");
    callout(s, "输入\nBOM Excel", 108, 238, 170, 120, "#dbeafe");
    callout(s, "规则\n失效/绑定/重要物料", 344, 238, 230, 120, "#ccfbf1");
    callout(s, "输出\n检查结果", 640, 238, 170, 120, "#fef3c7");
    callout(s, "沉淀\n配置和文档", 876, 238, 210, 120, "#ede9fe");
    addText(s, "最开始提供：需求.txt", 116, 474, 560, 42, { fontSize: 34, bold: true, color: "#0f766e" });
    addText(s, "不是一句“帮我做软件”，而是把审核动作拆给 AI。", 118, 526, 850, 34, { fontSize: 24, color: "#526b73" });
    footer(s, 5);
    addNotes(s, "这里讲关键经验：AI 落地项目最重要的不是一开始就写代码，而是把业务流程、数据文件、判断规则、输出结果描述清楚。需求越像工作说明书，AI 越容易做出第一版。");
  }

  // 6
  {
    const s = p.slides.add(); section(s, 2, "怎么做出来", "先做能跑，再用真实样本把规则补齐", "#2563eb");
    addNotes(s, "第二章讲开发过程。不要把它讲成一次完成，而是讲成真实样本驱动的一轮轮修正。");
  }

  // 7
  {
    const s = p.slides.add(); bg(s, "#f8fbff");
    title(s, "旧版：先把核心流程跑起来", "选择 Excel，执行，输出结果");
    screenshot(s, oldExec, 80, 164, 1040, 332, "旧版 BOM 执行页");
    callout(s, "优点：能跑通主流程", 92, 552, 260, 54, "#dcfce7");
    callout(s, "不足：界面像工具箱，状态不够直观", 382, 552, 420, 54, "#fee2e2");
    footer(s, 7);
    addNotes(s, "这张是真实旧版截图。可以说：第一版的价值是打通闭环，能选择 BOM、执行检查、看日志。但它还是传统标签页，视觉提示弱，适合开发验证，不够适合现场长期使用。");
  }

  // 8
  {
    const s = p.slides.add(); bg(s, "#f8fbff");
    title(s, "真实测试不断提出新规则", "每一次问题，都会变成下一版功能");
    const steps = [
      ["数量列/多工作表", "#dbeafe"],
      ["简繁体兼容", "#ccfbf1"],
      ["失效替换", "#fef3c7"],
      ["绑定料号", "#ede9fe"],
      ["重要物料", "#fee2e2"],
      ["结果统计", "#e0f2fe"],
    ];
    steps.forEach((item, i) => {
      const x = 92 + (i % 3) * 360;
      const y = 202 + Math.floor(i / 3) * 152;
      callout(s, item[0], x, y, 250, 90, item[1]);
    });
    addText(s, "开发规律：真实 BOM 样本 > 暴露问题 > AI 修改 > 本地验证", 118, 558, 980, 48, { fontSize: 32, bold: true, color: "#075985", alignment: "center" });
    footer(s, 8);
    addNotes(s, "这里讲迭代规律：真实 BOM 文件比口头描述更重要。比如数量列、多个 worksheet、简繁体、失效替换、绑定料号、统计显示，都是在测试中逐步补上的。");
  }

  // 9
  {
    const s = p.slides.add(); section(s, 3, "怎么变好用", "同样的功能，从旧版工具变成新版工作台", "#0f766e");
    addNotes(s, "第三章开始展示最直观的新旧对比。评委能从截图看出：AI 不是只写算法，也在不断改善操作体验。");
  }

  // 10
  {
    const s = p.slides.add(); bg(s);
    title(s, "对比 1：BOM 执行页", "从“能执行”到“知道当前状态、下一步做什么”");
    screenshot(s, oldExec, 62, 160, 540, 315, "旧版");
    screenshot(s, newExec, 682, 120, 520, 390, "新版");
    callout(s, "旧版：入口简单\n但状态弱", 112, 532, 260, 76, "#fee2e2");
    callout(s, "新版：侧边导航\n状态条 + 流程卡片", 746, 532, 340, 76, "#dcfce7");
    footer(s, 10);
    addNotes(s, "这一页重点讲界面进化。旧版能完成执行，但用户要自己判断现在处于什么状态。新版把工作区、配置状态、执行流程和查询入口放在同一张工作台里。");
  }

  // 11
  {
    const s = p.slides.add(); bg(s);
    title(s, "对比 2：料号查询页", "从系统表格，到更符合员工习惯的查询工作台");
    screenshot(s, oldQuery, 62, 156, 540, 315, "旧版");
    screenshot(s, newQuery, 682, 112, 520, 400, "新版");
    callout(s, "ERP 原本要 % 通配符", 96, 532, 260, 58, "#fef3c7");
    callout(s, "软件里输入空格关键词即可", 396, 532, 330, 58, "#ccfbf1");
    callout(s, "支持鼠标拖选复制", 766, 532, 270, 58, "#dbeafe");
    footer(s, 11);
    addNotes(s, "这一页讲查询体验。ERP 查询需要百分号通配符，但现场员工更习惯输入几个关键词，新版把系统语法翻译成自然查询，并加入拖选复制。");
  }

  // 12
  {
    const s = p.slides.add(); bg(s, "#f7fffb");
    title(s, "新版桌面版：已经像一个现场工具", "不是单页脚本，而是工作台");
    screenshot(s, newExec, 74, 142, 520, 350, "BOM 执行");
    screenshot(s, newQuery, 688, 142, 520, 350, "料号查询");
    callout(s, "网络配置状态", 112, 536, 190, 52, "#ccfbf1");
    callout(s, "快速跳转查询", 344, 536, 190, 52, "#dbeafe");
    callout(s, "结果区友好提示", 576, 536, 210, 52, "#fef3c7");
    callout(s, "多行复制", 828, 536, 170, 52, "#ede9fe");
    footer(s, 12);
    addNotes(s, "这里把新版当作成果展示。讲它不仅有执行检查，还把查询和配置入口整合起来，适合电控同事日常反复使用。");
  }

  // 13
  {
    const s = p.slides.add(); bg(s, "#fffaf0");
    s.images.add({ blob: imgErp, contentType: "image/png", fit: "cover", position: { left: 688, top: 96, width: 500, height: 444 } });
    title(s, "功能扩展：从审核，顺手做到查询和资料入口", "系统料号已经抓取，就不要只用一次");
    callout(s, "料号 / 描述\n空格搜索", 92, 202, 230, 100, "#dbeafe");
    callout(s, "简繁体\n自动兼容", 360, 202, 220, 100, "#ccfbf1");
    callout(s, "图片 / 说明书\n公共槽路径", 92, 360, 230, 100, "#fef3c7");
    callout(s, "UA 专案资料\n集中入口", 360, 360, 220, 100, "#ede9fe");
    footer(s, 13);
    addNotes(s, "这一页讲功能扩展的逻辑：因为系统料号都已经抓取到本地，顺便做查询就是自然的。后来员工提出希望看到图片，于是又加入了图片和资料路径。UA 是专案料号，公共槽里有整套专案资料。");
  }

  // 14
  {
    const s = p.slides.add(); section(s, 4, "怎么落地", "公司环境里的问题，才是真正的交付考验", "#7c3aed");
    addNotes(s, "第四章讲现场交付。这里要强调：开发代码只是前半段，部署到共享盘、多人使用、打包启动速度，才决定能不能真的用起来。");
  }

  // 15
  {
    const s = p.slides.add(); bg(s, "#f7f5ff");
    s.images.add({ blob: imgSmb, contentType: "image/png", fit: "cover", position: { left: 674, top: 114, width: 500, height: 424 } });
    title(s, "落地问题：共享盘启动太慢", "本地约 5 秒，SMB 直接打开超过 1 分钟");
    callout(s, "onefile exe\n网络读取 + 解包", 110, 208, 260, 110, "#fee2e2");
    callout(s, "小启动器\n先缓存到本地", 110, 370, 260, 110, "#dcfce7");
    callout(s, "配置和数据\n仍在共享盘", 410, 370, 220, 110, "#dbeafe");
    footer(s, 15);
    addNotes(s, "这一页讲部署细节。PyInstaller onefile 从 SMB 启动会慢，所以后来做了小启动器，把主程序缓存到本机，只有程序更新才重新复制，但配置和业务数据仍然走公共槽。");
  }

  // 16
  {
    const s = p.slides.add(); bg(s, "#f9fbfc");
    title(s, "Windows Codex 带来的变化", "从云端反复下载测试，到本地直接看窗口、点界面、改体验");
    const items = [
      ["窗口显示不全", "加滚动与尺寸收敛"],
      ["列表要手动刷新", "打开后自动加载"],
      ["复制不直观", "鼠标拖选 + Ctrl+C"],
      ["配置界面拥挤", "子界面分组美化"],
      ["打包交付", "桌面版/Web 版 exe"],
    ];
    items.forEach((item, i) => {
      const y = 164 + i * 82;
      pill(s, item[0], 124, y, "#e0f2fe", "#075985", 210);
      addText(s, item[1], 380, y + 2, 520, 34, { fontSize: 26, bold: true, color: "#0f3d46" });
    });
    footer(s, 16);
    addNotes(s, "这一页讲工具链升级。云端 Codex 做早期功能很快，但 Windows 桌面界面、打包、共享盘、鼠标操作必须本地看。本地 Codex 出来后，体验问题修得更快。");
  }

  // 17
  {
    const s = p.slides.add(); section(s, 5, "经验沉淀", "把一次项目，变成下一次也能复用的方法", "#ea580c");
    addNotes(s, "第五章收束到方法论，准备升华。");
  }

  // 18
  {
    const s = p.slides.add(); bg(s, "#f8fff3");
    title(s, "最终成果：一套电控 BOM 辅助审核工具", "桌面版为主，覆盖审核、查询、资料和交付");
    card(s, "BOM 检查\n失效替换\n绑定规则", 84, 180, 240, 190, "#ffffff");
    card(s, "料号查询\n空格搜索\n拖选复制", 374, 180, 240, 190, "#ffffff");
    card(s, "资料入口\n图片/说明书\nUA 专案", 664, 180, 240, 190, "#ffffff");
    card(s, "现场交付\n共享盘\n启动器", 954, 180, 240, 190, "#ffffff");
    addText(s, "AI 的价值：把电控主管的经验，变成同事可以反复使用的工具。", 130, 490, 1020, 58, { fontSize: 34, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 18);
    addNotes(s, "这里总结成果。它不只是一个检查按钮，而是一套辅助审核工具链：BOM 检查、料号查询、资料入口、共享盘交付。重点突出桌面版已经可以给同事使用。");
  }

  // 19
  {
    const s = p.slides.add(); bg(s);
    title(s, "可复制的 AI 项目步骤", "下一次做其他内部工具，可以按这个节奏");
    const steps = [
      ["1", "写清业务流程"],
      ["2", "给真实样本"],
      ["3", "先做最小闭环"],
      ["4", "用现场问题迭代"],
      ["5", "处理部署细节"],
      ["6", "沉淀文档和规则"],
    ];
    steps.forEach((step, i) => {
      const x = 92 + i * 190;
      pill(s, step[0], x, 214, "#0f766e", "#ffffff", 58);
      addText(s, step[1], x - 42, 276, 150, 70, { fontSize: 23, bold: true, color: "#0f3d46", alignment: "center" });
    });
    addText(s, "业务人员负责判断，AI 负责把判断快速变成工具。", 176, 478, 920, 54, { fontSize: 36, bold: true, color: "#075985", alignment: "center" });
    footer(s, 19);
    addNotes(s, "这一页给评委一个可复制框架：写流程、给样本、做闭环、真实迭代、处理部署、沉淀文档。强调业务专家的判断仍然是核心，AI 是放大器。");
  }

  // 20
  {
    const s = p.slides.add(); bg(s, "#eafff7");
    addText(s, "AI 不是替代业务专家", 174, 150, 930, 62, { fontSize: 50, bold: true, color: "#064e3b", alignment: "center" });
    addText(s, "而是把专家经验\n放大成可执行、可复用、可交付的工具", 190, 270, 900, 128, { fontSize: 42, bold: true, color: "#0f766e", alignment: "center" });
    screenshot(s, newExec, 340, 460, 600, 170, "BOMCheck 桌面版");
    footer(s, 20);
    addNotes(s, "收尾升华：AI 的意义不是代替我审核，而是把我的电控审核经验沉淀成工具，让团队减少重复劳动和人为遗漏。最后可以说，这种方式还能复制到其他工程管理场景。");
  }

  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);

  const previewDir = path.join(WORK, "preview-desktop");
  await fs.mkdir(previewDir, { recursive: true });
  for (const [index, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(WORK, "deck-montage-desktop.webp"), new Uint8Array(await montage.arrayBuffer()));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
