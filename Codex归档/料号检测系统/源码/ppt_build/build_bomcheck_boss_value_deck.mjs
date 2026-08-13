import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const W = 1280;
const H = 720;
const WORK = "C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/bomcheck-ai-contest";
const ASSETS = path.join(WORK, "assets");
const OUT = "C:/Users/lfaf-test/Documents/料号检测系统/AI大赛_BOMCheck项目复盘_老板汇报版.pptx";

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
  addText(slide, text, 66, 42, 950, 58, { fontSize: 38, bold: true, color: "#062c33" });
  if (sub) addText(slide, sub, 68, 104, 930, 34, { fontSize: 20, color: "#526b73" });
}

function footer(slide, n) {
  addText(slide, "BOMCheck AI 落地实践", 64, 674, 230, 24, { fontSize: 13, color: "#78909c" });
  addText(slide, String(n).padStart(2, "0"), 1184, 674, 40, 24, { fontSize: 13, color: "#78909c", alignment: "right" });
}

function pill(slide, text, x, y, fill, color = "#052d35", w = 140) {
  const shape = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: 36 },
    fill,
    line: { style: "solid", fill: "none", width: 0 },
    borderRadius: "rounded-xl",
  });
  shape.text = text;
  shape.text.style = { fontSize: 17, bold: true, color, alignment: "center" };
  return shape;
}

function callout(slide, text, x, y, w, h, fill = "#ffffff", fontSize = 24) {
  const shape = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: "#c7dce3", width: 1 },
    borderRadius: "rounded-lg",
    shadow: "shadow-sm",
  });
  shape.text = text;
  shape.text.style = { fontSize, bold: true, color: "#0a3440", alignment: "center" };
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
  bg(slide, color);
  addText(slide, `第 ${n} 章`, 90, 128, 240, 54, { fontSize: 32, bold: true, color: "#ffffff" });
  addText(slide, name, 90, 206, 820, 76, { fontSize: 50, bold: true, color: "#ffffff" });
  addText(slide, sentence, 92, 306, 820, 48, { fontSize: 25, color: "#eafffb" });
}

function metric(slide, top, main, bottom, x, y, fill) {
  callout(slide, "", x, y, 250, 180, fill, 20);
  addText(slide, top, x + 22, y + 24, 206, 30, { fontSize: 20, bold: true, color: "#27515a", alignment: "center" });
  addText(slide, main, x + 22, y + 64, 206, 48, { fontSize: 34, bold: true, color: "#08323a", alignment: "center" });
  addText(slide, bottom, x + 18, y + 126, 214, 36, { fontSize: 18, color: "#526b73", alignment: "center" });
}

async function main() {
  const imgMountain = await readImage("bom_mountain.png");
  const imgWorkflow = await readImage("workflow.png");
  const imgSmb = await readImage("smb_launcher.png");
  const oldExec = await readImage("desktop_old_execute.png");
  const oldQuery = await readImage("desktop_old_query.png");
  const newExec = await readImage("desktop_new_execute.png");
  const newQuery = await readImage("desktop_new_query.png");

  const p = await Presentation.create({ slideSize: { width: W, height: H } });

  // 1
  {
    const s = p.slides.add(); bg(s, "#eefaf7");
    s.images.add({ blob: imgMountain, contentType: "image/png", fit: "cover", position: { left: 670, top: 0, width: 610, height: 720 } });
    addText(s, "AI 把 BOM 审核\n从主管兜底变成全员预防", 70, 92, 720, 150, { fontSize: 46, bold: true, color: "#063238" });
    addText(s, "BOMCheck 项目价值汇报｜桌面版落地成果", 74, 266, 620, 38, { fontSize: 23, color: "#3f5961" });
    pill(s, "减少审核时间", 78, 352, "#ccfbf1", "#0f766e", 154);
    pill(s, "降低缺料风险", 252, 352, "#dbeafe", "#1d4ed8", 154);
    pill(s, "沉淀审核经验", 426, 352, "#fef3c7", "#92400e", 154);
    footer(s, 1);
    addNotes(s, "开场面向老板讲结果：这个项目不是单纯做了一个软件，而是把 BOM 审核从主管最后兜底，前移到每个设计或提交人员可以提前自检。核心价值是省时间、降风险、沉淀经验。");
  }

  // 2
  {
    const s = p.slides.add(); bg(s);
    title(s, "目录", "这次重点讲价值，而不是代码细节");
    const items = [
      ["01", "问题在哪里", "主管最后审核，风险发现偏晚"],
      ["02", "软件解决了什么", "把规则变成人人可用的检查工具"],
      ["03", "带来了什么效益", "省时间、少漏买、少返工"],
      ["04", "为什么能落地", "适配共享盘、桌面版和现场习惯"],
      ["05", "下一步怎么推广", "从一个工具变成一套方法"],
    ];
    items.forEach((it, i) => {
      const y = 170 + i * 86;
      pill(s, it[0], 96, y, "#0f766e", "#ffffff", 70);
      addText(s, it[1], 198, y - 4, 310, 42, { fontSize: 30, bold: true, color: "#09343b" });
      addText(s, it[2], 535, y + 2, 610, 34, { fontSize: 21, color: "#4a6570" });
    });
    footer(s, 2);
    addNotes(s, "目录页说明汇报顺序：先讲管理痛点，再讲软件功能，然后讲效益和推广。这样老板会更容易抓住项目价值。");
  }

  // 3
  {
    const s = p.slides.add(); section(s, 1, "问题在哪里", "BOM 错误越晚发现，代价越高", "#0f766e");
    addNotes(s, "第一章讲为什么值得做。重点不是抱怨审核辛苦，而是说明错误发现太晚会影响采购、组装和交期。");
  }

  // 4
  {
    const s = p.slides.add(); bg(s, "#fffdf4");
    title(s, "原来的风险集中在主管最后一道关", "料多、规则多、资料分散，人工审核容易有遗漏");
    callout(s, "个人提交 BOM", 98, 214, 220, 100, "#dbeafe");
    callout(s, "主管集中审核", 388, 214, 220, 100, "#fef3c7");
    callout(s, "问题发现偏晚", 678, 214, 220, 100, "#fee2e2");
    callout(s, "采购/组装受影响", 968, 214, 220, 100, "#fee2e2");
    addText(s, "主管审核仍然重要，但不应该是唯一防线。", 186, 448, 910, 54, { fontSize: 36, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 4);
    addNotes(s, "这一页讲管理问题：以前主要靠主管最后审核，个人提交前缺少工具自检。料号多、规则多、资料分散，一旦遗漏进入采购和组装阶段，代价就会放大。");
  }

  // 5
  {
    const s = p.slides.add(); bg(s, "#fff7f7");
    title(s, "漏买一个关联物料，影响的不只是一个料号", "缺料会把问题一路传到组装现场");
    callout(s, "关联料号漏买", 92, 206, 210, 100, "#fee2e2");
    callout(s, "到组装才发现", 350, 206, 210, 100, "#fef3c7");
    callout(s, "临时补采购", 608, 206, 210, 100, "#fef3c7");
    callout(s, "等待到料", 866, 206, 170, 100, "#dbeafe");
    callout(s, "交期被拖慢", 1058, 206, 170, 100, "#fee2e2");
    addText(s, "BOMCheck 的关键价值，是把这种问题提前拦在提交前。", 144, 456, 990, 58, { fontSize: 36, bold: true, color: "#b42318", alignment: "center" });
    footer(s, 5);
    addNotes(s, "这页可以讲一个典型链条：料号关联没检查到，采购没有买齐，到最后组装时缺料，再临时补买，等待到料会造成延误。软件里的绑定料号规则，就是为了提前打断这个链条。");
  }

  // 6
  {
    const s = p.slides.add(); section(s, 2, "软件解决了什么", "把主管经验变成可执行的检查规则", "#2563eb");
    addNotes(s, "第二章讲解决方案。强调不是做一个单点功能，而是把主管经验转成规则库，让每个人都能提前用。");
  }

  // 7
  {
    const s = p.slides.add(); bg(s);
    title(s, "新版桌面版已经形成工作台", "BOM 执行、料号查询、配置状态放在同一个入口");
    screenshot(s, newExec, 94, 142, 500, 356, "BOM 执行");
    screenshot(s, newQuery, 688, 142, 500, 356, "料号查询");
    callout(s, "个人提交前可自检", 118, 538, 250, 54, "#ccfbf1");
    callout(s, "主管聚焦异常项", 404, 538, 230, 54, "#dbeafe");
    callout(s, "查询和资料更顺手", 670, 538, 250, 54, "#fef3c7");
    callout(s, "规则统一沉淀", 956, 538, 190, 54, "#ede9fe");
    footer(s, 7);
    addNotes(s, "展示新版真实截图。讲它现在不是脚本，而是工作台：个人可先执行 BOM 检查，主管可以把精力放在异常和判断上，同时料号查询也整合进来了。");
  }

  // 8
  {
    const s = p.slides.add(); bg(s, "#f8fbff");
    title(s, "旧版能跑，新版更适合现场反复用", "界面升级带来的不是美观，而是使用门槛下降");
    screenshot(s, oldExec, 62, 160, 540, 315, "旧版");
    screenshot(s, newExec, 682, 120, 520, 390, "新版");
    callout(s, "旧版：靠人理解流程", 132, 532, 260, 64, "#fee2e2");
    callout(s, "新版：状态、入口、流程更明确", 746, 532, 350, 64, "#dcfce7");
    footer(s, 8);
    addNotes(s, "这页讲新旧对比。旧版已经能跑通流程，但更像开发验证工具；新版把状态、入口、流程卡片做清楚，普通员工更容易使用。");
  }

  // 9
  {
    const s = p.slides.add(); bg(s, "#f8fbff");
    title(s, "料号查询也从系统语法变成员工习惯", "ERP 需要 % 通配符，软件里用空格关键词即可");
    screenshot(s, oldQuery, 62, 156, 540, 315, "旧版");
    screenshot(s, newQuery, 682, 112, 520, 400, "新版");
    callout(s, "查询更快", 120, 536, 180, 54, "#ccfbf1");
    callout(s, "简繁体兼容", 346, 536, 210, 54, "#dbeafe");
    callout(s, "支持拖选复制", 602, 536, 230, 54, "#fef3c7");
    callout(s, "减少反复问料号", 878, 536, 260, 54, "#ede9fe");
    footer(s, 9);
    addNotes(s, "这页讲查询价值。ERP 查询需要百分号，员工不一定习惯。软件把它变成空格关键词搜索，还支持简繁体和拖选复制，减少查料号和沟通成本。");
  }

  // 10
  {
    const s = p.slides.add(); section(s, 3, "带来了什么效益", "不是多了一个软件，而是改变了审核位置", "#0f766e");
    addNotes(s, "第三章是老板最关心的部分。讲效益时不要只说感觉变好，而要落到时间、风险、协作和经验沉淀。");
  }

  // 11
  {
    const s = p.slides.add(); bg(s, "#f7fffb");
    title(s, "审核从“事后兜底”前移到“提交前自检”", "主管还是把关人，但不再承担所有基础检查");
    callout(s, "过去\n主管集中查", 130, 206, 240, 140, "#fee2e2", 28);
    callout(s, "现在\n个人先自检", 520, 206, 240, 140, "#dcfce7", 28);
    callout(s, "主管\n处理异常和判断", 910, 206, 240, 140, "#dbeafe", 28);
    addText(s, "直接效益：减少主管重复核对时间，把精力留给真正需要经验判断的地方。", 122, 486, 1040, 58, { fontSize: 33, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 11);
    addNotes(s, "这一页讲审核模式变化。以前主管承担大量基础核对，现在个人可以先用工具检查，主管再看异常项和特殊判断。这样节省的是高经验人员的时间。");
  }

  // 12
  {
    const s = p.slides.add(); bg(s, "#fffdf4");
    title(s, "关联料号规则降低了缺料风险", "把“经验提醒”变成软件自动提醒");
    callout(s, "绑定料号", 130, 210, 220, 120, "#dbeafe", 28);
    callout(s, "缺少组合料", 410, 210, 220, 120, "#fef3c7", 28);
    callout(s, "执行时提醒", 690, 210, 220, 120, "#ccfbf1", 28);
    callout(s, "提交前修正", 970, 210, 220, 120, "#dcfce7", 28);
    addText(s, "管理价值：减少漏买导致的补采购、等待到料和组装延误。", 184, 478, 912, 58, { fontSize: 34, bold: true, color: "#92400e", alignment: "center" });
    footer(s, 12);
    addNotes(s, "这页重点讲用户刚补充的效益：料号关联避免一些物料漏买。如果到组装才发现缺料，就要重新购买并等待，影响进度。软件把这类经验固化成绑定规则。");
  }

  // 13
  {
    const s = p.slides.add(); bg(s);
    title(s, "效益可以从五个方面看", "有些已经直接感受到，有些可以继续用数据跟踪");
    metric(s, "时间", "更快", "减少重复人工核对", 78, 190, "#ccfbf1");
    metric(s, "风险", "更早", "提交前发现缺料隐患", 362, 190, "#dbeafe");
    metric(s, "采购", "更准", "减少漏买和补买", 646, 190, "#fef3c7");
    metric(s, "经验", "可复用", "主管规则沉淀下来", 930, 190, "#ede9fe");
    addText(s, "建议后续持续记录：平均审核时长、检查出的缺料次数、补采购次数、因缺料造成的等待次数。", 116, 486, 1040, 70, { fontSize: 28, bold: true, color: "#0f3d46", alignment: "center" });
    footer(s, 13);
    addNotes(s, "这里不要编具体数字。可以说目前已经看到审核前移和风险提前暴露，下一步建议把平均审核时长、缺料次数、补采购次数等指标记录起来，形成更量化的改善报告。");
  }

  // 14
  {
    const s = p.slides.add(); section(s, 4, "为什么能落地", "工具必须适应公司现场，而不是只在演示里好看", "#7c3aed");
    addNotes(s, "第四章讲落地能力。老板通常会关心：这个软件是不是只在开发电脑能跑？能不能给团队用？");
  }

  // 15
  {
    const s = p.slides.add(); bg(s, "#f7f5ff");
    s.images.add({ blob: imgSmb, contentType: "image/png", fit: "cover", position: { left: 674, top: 114, width: 500, height: 424 } });
    title(s, "共享盘启动慢，也被纳入交付问题处理", "本地约 5 秒，SMB 直接打开超过 1 分钟");
    callout(s, "小启动器", 110, 216, 230, 90, "#dcfce7", 28);
    callout(s, "主程序缓存本地", 110, 360, 260, 90, "#dbeafe", 26);
    callout(s, "配置和数据仍在共享盘", 410, 360, 230, 90, "#fef3c7", 23);
    footer(s, 15);
    addNotes(s, "这页说明项目不是停在功能完成，还处理了部署体验。共享盘直接打开 onefile exe 很慢，于是做了启动器，主程序缓存到本地，业务数据仍在共享盘。");
  }

  // 16
  {
    const s = p.slides.add(); bg(s, "#f9fbfc");
    title(s, "从需求到交付，AI 负责提速，人负责判断", "这个协作模式可以复制到其他内部工具");
    const rows = [
      ["业务人员", "给流程、样本、判断标准"],
      ["AI / Codex", "写代码、改界面、做打包"],
      ["现场测试", "用真实 BOM 暴露问题"],
      ["交付沉淀", "说明书、任务交底、版本规则"],
    ];
    rows.forEach((row, i) => {
      const y = 166 + i * 94;
      pill(s, row[0], 126, y, "#e0f2fe", "#075985", 190);
      addText(s, row[1], 380, y + 2, 670, 36, { fontSize: 28, bold: true, color: "#0f3d46" });
    });
    footer(s, 16);
    addNotes(s, "这里讲协作方法。AI 的价值是提速，但业务判断仍然来自人。只要流程、样本和判断标准清楚，就能把类似内部工具更快做出来。");
  }

  // 17
  {
    const s = p.slides.add(); section(s, 5, "下一步怎么推广", "从一个工具，变成一套可复用的方法", "#ea580c");
    addNotes(s, "第五章给老板一个下一步方向，不只是展示成果，还说明怎么继续产生价值。");
  }

  // 18
  {
    const s = p.slides.add(); bg(s, "#fffaf0");
    title(s, "下一步建议用数据把效益跑实", "先小范围用起来，再用事实决定推广范围");
    callout(s, "1\n选定试用人员", 122, 214, 190, 130, "#dbeafe", 28);
    callout(s, "2\n记录审核时长", 350, 214, 190, 130, "#ccfbf1", 28);
    callout(s, "3\n记录拦截问题", 578, 214, 190, 130, "#fef3c7", 28);
    callout(s, "4\n完善规则库", 806, 214, 190, 130, "#ede9fe", 28);
    callout(s, "5\n推广到更多项目", 1034, 214, 190, 130, "#dcfce7", 26);
    addText(s, "目标：让 AI 项目从“做出来”，走到“看得见收益”。", 174, 486, 930, 58, { fontSize: 36, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 18);
    addNotes(s, "这页提出建议：先选定试用人员，记录审核时间和拦截问题，再持续补规则库。这样下一次汇报就可以用数据证明收益。");
  }

  // 19
  {
    const s = p.slides.add(); bg(s, "#eafff7");
    addText(s, "这个项目解决的不是一个软件问题", 128, 136, 1020, 62, { fontSize: 46, bold: true, color: "#064e3b", alignment: "center" });
    addText(s, "而是把关键岗位经验\n前移、标准化、团队化", 188, 258, 900, 118, { fontSize: 48, bold: true, color: "#0f766e", alignment: "center" });
    screenshot(s, newExec, 340, 456, 600, 170, "BOMCheck 桌面版");
    footer(s, 19);
    addNotes(s, "收尾升华：它解决的不只是写一个工具，而是让主管经验前移到个人自检阶段，变成团队可用的标准能力。");
  }

  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);

  const previewDir = path.join(WORK, "preview-boss");
  await fs.mkdir(previewDir, { recursive: true });
  for (const [index, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(WORK, "deck-montage-boss.webp"), new Uint8Array(await montage.arrayBuffer()));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
