import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const W = 1280;
const H = 720;
const WORK = "C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/bomcheck-ai-contest";
const ASSETS = path.join(WORK, "assets");
const OUT = "C:/Users/lfaf-test/Documents/料号检测系统/AI大赛_BOMCheck项目复盘_评委问答优化版.pptx";

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
  addText(slide, text, 66, 42, 980, 58, { fontSize: 38, bold: true, color: "#062c33" });
  if (sub) addText(slide, sub, 68, 104, 960, 34, { fontSize: 20, color: "#526b73" });
}

function footer(slide, n) {
  addText(slide, "BOMCheck AI 落地实践", 64, 674, 230, 24, { fontSize: 13, color: "#78909c" });
  addText(slide, String(n).padStart(2, "0"), 1184, 674, 40, 24, { fontSize: 13, color: "#78909c", alignment: "right" });
}

function pill(slide, text, x, y, fill, color = "#052d35", w = 150) {
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

function card(slide, text, x, y, w, h, fill = "#ffffff", fontSize = 25) {
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
  addText(slide, name, 90, 206, 830, 76, { fontSize: 50, bold: true, color: "#ffffff" });
  addText(slide, sentence, 92, 306, 830, 48, { fontSize: 25, color: "#eafffb" });
}

function metric(slide, top, main, bottom, x, y, fill) {
  card(slide, "", x, y, 250, 180, fill, 20);
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
    s.images.add({ blob: imgMountain, contentType: "image/png", fit: "cover", position: { left: 668, top: 0, width: 612, height: 720 } });
    addText(s, "我用 AI 把一个电控想法\n做成了 BOM 审核软件", 70, 88, 720, 150, { fontSize: 46, bold: true, color: "#063238" });
    addText(s, "BOMCheck 项目复盘｜从需求文件到桌面版落地", 74, 266, 650, 38, { fontSize: 23, color: "#3f5961" });
    pill(s, "AI 实现想法", 78, 352, "#ccfbf1", "#0f766e", 154);
    pill(s, "真实业务落地", 252, 352, "#dbeafe", "#1d4ed8", 154);
    pill(s, "降低缺料风险", 426, 352, "#fef3c7", "#92400e", 154);
    footer(s, 1);
    addNotes(s, "开场要明确 AI 大赛主题：这个项目不是单纯做软件，而是我把电控 BOM 审核的经验、痛点和想法交给 AI，AI 帮我快速做出软件、持续迭代并最终交付。");
  }

  // 2
  {
    const s = p.slides.add(); bg(s);
    title(s, "目录", "既讲 AI 怎么帮我实现，也讲软件带来的业务效益");
    const items = [
      ["01", "业务痛点", "为什么这个想法值得做"],
      ["02", "AI 参与", "它怎样把需求变成软件"],
      ["03", "软件进化", "从旧版工具到新版工作台"],
      ["04", "业务效益", "省时间、少漏买、少返工"],
      ["05", "方法复用", "这套 AI 协作方式怎么推广"],
    ];
    items.forEach((it, i) => {
      const y = 170 + i * 86;
      pill(s, it[0], 96, y, "#0f766e", "#ffffff", 70);
      addText(s, it[1], 198, y - 4, 310, 42, { fontSize: 30, bold: true, color: "#09343b" });
      addText(s, it[2], 535, y + 2, 610, 34, { fontSize: 21, color: "#4a6570" });
    });
    footer(s, 2);
    addNotes(s, "目录页先告诉评委：这不是纯业务汇报，也不是纯技术汇报，而是一个业务人员如何用 AI 把想法做成工具，并产生管理效益的案例。");
  }

  // 3
  {
    const s = p.slides.add(); section(s, 1, "业务痛点", "BOM 错误越晚发现，代价越高", "#0f766e");
    addNotes(s, "第一章进入业务现场。先让评委理解为什么这个想法值得做。");
  }

  // 4
  {
    const s = p.slides.add(); bg(s, "#fffdf4");
    title(s, "原来主要靠主管最后一道关", "料多、规则多、资料分散，人工审核容易有遗漏");
    card(s, "个人提交\nBOM", 98, 214, 220, 100, "#dbeafe");
    card(s, "主管集中\n审核", 388, 214, 220, 100, "#fef3c7");
    card(s, "问题发现\n偏晚", 678, 214, 220, 100, "#fee2e2");
    card(s, "采购/组装\n受影响", 968, 214, 220, 100, "#fee2e2");
    addText(s, "主管审核仍然重要，但不应该是唯一防线。", 186, 448, 910, 54, { fontSize: 36, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 4);
    addNotes(s, "这里讲原来的管理风险：电控 BOM 料号多，停产替换、绑定料号、重要物料和资料位置都靠经验。个人提交前缺少工具自检，主管最后审核压力大。");
  }

  // 5
  {
    const s = p.slides.add(); bg(s, "#fff7f7");
    title(s, "漏买一个关联物料，影响的不只是一个料号", "缺料会把问题一路传到组装现场");
    card(s, "关联料号\n漏买", 92, 206, 210, 100, "#fee2e2");
    card(s, "组装时\n才发现", 350, 206, 210, 100, "#fef3c7");
    card(s, "临时\n补采购", 608, 206, 210, 100, "#fef3c7");
    card(s, "等待\n到料", 866, 206, 170, 100, "#dbeafe");
    card(s, "交期\n被拖慢", 1058, 206, 170, 100, "#fee2e2");
    addText(s, "BOMCheck 的关键价值，是把问题提前拦在提交前。", 144, 456, 990, 58, { fontSize: 36, bold: true, color: "#b42318", alignment: "center" });
    footer(s, 5);
    addNotes(s, "这一页讲用户补充的重点：料号关联如果没检查到，采购没有买齐，到组装才发现缺料，就要重新购买并等待到料，影响交付。");
  }

  // 6
  {
    const s = p.slides.add(); section(s, 2, "AI 参与", "我的经验负责判断，AI 负责把判断变成工具", "#2563eb");
    addNotes(s, "第二章回到 AI 大赛主题。强调 AI 不是替代业务专家，而是帮业务专家把想法变成可执行软件。");
  }

  // 7
  {
    const s = p.slides.add(); bg(s, "#f8fbff");
    title(s, "第一步不是写代码，而是把想法讲清楚", "我提供需求文件，AI 把它拆成界面、规则和数据结构");
    card(s, "我的输入\n需求.txt\n业务规则\n真实样本", 108, 190, 250, 210, "#dbeafe", 25);
    card(s, "AI 的工作\n理解流程\n生成代码\n设计界面", 506, 190, 250, 210, "#ccfbf1", 25);
    card(s, "得到结果\n第一版 UI\n可执行流程\n可继续迭代", 904, 190, 250, 210, "#fef3c7", 25);
    addText(s, "AI 能快，是因为业务问题先被结构化了。", 176, 500, 930, 54, { fontSize: 36, bold: true, color: "#075985", alignment: "center" });
    footer(s, 7);
    addNotes(s, "这里讲开发规律：我不是只说帮我做个软件，而是把 BOM 审核流程、失效料号、绑定料号、重要物料、输出结果写给 AI。AI 才能快速做出第一版。");
  }

  // 8
  {
    const s = p.slides.add(); bg(s, "#f9fbfc");
    title(s, "AI 在项目里承担了四类工作", "不是只生成代码，而是贯穿实现、测试和交付");
    card(s, "写代码\n桌面界面\n检查逻辑", 94, 206, 240, 150, "#dbeafe", 25);
    card(s, "改体验\n复制方式\n窗口布局", 374, 206, 240, 150, "#ccfbf1", 25);
    card(s, "做交付\n打包 exe\n共享盘启动器", 654, 206, 240, 150, "#fef3c7", 25);
    card(s, "写文档\n说明书\n任务交底", 934, 206, 240, 150, "#ede9fe", 25);
    addText(s, "人给方向和判断，AI 把想法快速变成可验证版本。", 170, 482, 940, 54, { fontSize: 34, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 8);
    addNotes(s, "这一页要把 AI 的作用讲完整：写代码只是其中一部分，后续界面优化、打包、共享盘启动、文档交付也都在 AI 协作中完成。");
  }

  // 9
  {
    const s = p.slides.add(); bg(s, "#f7fffb");
    title(s, "我会主动回答评委最关心的事", "AI 大赛看创新，也要看能不能放心用");
    card(s, "AI 在哪里\n需求拆解\n代码生成\n界面优化", 86, 190, 250, 180, "#dbeafe", 24);
    card(s, "准确性怎么保证\n真实 BOM 测试\n规则可维护\n主管确认", 376, 190, 250, 180, "#ccfbf1", 24);
    card(s, "效益怎么证明\n审核时长\n拦截问题\n补采购次数", 666, 190, 250, 180, "#fef3c7", 24);
    card(s, "如何推广\n共享盘部署\n启动器\n说明书交底", 956, 190, 250, 180, "#ede9fe", 24);
    addText(s, "这不是让 AI 直接做决定，而是让 AI 把人工经验做成可检查、可追溯的工具。", 138, 494, 1000, 60, { fontSize: 31, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 9);
    addNotes(s, "这一页是为现场评委准备的主动回应。老板可能关心效益，技术团队可能关心准确性和维护，业务评委可能关心推广。这里先把答案框架放出来。");
  }

  // 10
  {
    const s = p.slides.add(); bg(s, "#fffdf4");
    title(s, "AI 迭代靠真实现场问题推动", "每次测试暴露的问题，都变成下一版功能");
    s.images.add({ blob: imgWorkflow, contentType: "image/png", fit: "cover", position: { left: 700, top: 110, width: 470, height: 400 } });
    card(s, "真实 BOM\n暴露问题", 94, 200, 210, 100, "#dbeafe");
    card(s, "我判断\n规则怎么改", 346, 200, 210, 100, "#ccfbf1");
    card(s, "AI 修改\n代码和界面", 94, 360, 210, 100, "#fef3c7");
    card(s, "本地测试\n再进入现场", 346, 360, 210, 100, "#ede9fe");
    footer(s, 10);
    addNotes(s, "这里讲云端和本地 Codex 的过程：早期云端做功能，后面 Windows 版 Codex 出来后，可以直接本地看窗口、点界面、打包测试，反馈闭环更快。");
  }

  // 11
  {
    const s = p.slides.add(); section(s, 3, "软件进化", "从旧版能跑，到新版好用", "#0f766e");
    addNotes(s, "第三章用截图证明成果，不只讲概念。");
  }

  // 12
  {
    const s = p.slides.add(); bg(s);
    title(s, "BOM 执行页从工具变成工作台", "状态、入口和流程都更清楚");
    screenshot(s, oldExec, 62, 160, 540, 315, "旧版");
    screenshot(s, newExec, 682, 120, 520, 390, "新版");
    card(s, "旧版：能执行\n但状态提示弱", 132, 532, 260, 64, "#fee2e2", 22);
    card(s, "新版：侧边导航\n状态条 + 流程卡片", 746, 532, 350, 64, "#dcfce7", 22);
    footer(s, 12);
    addNotes(s, "展示新旧桌面版。旧版先解决能不能跑的问题，新版解决员工能不能舒服地反复用的问题。");
  }

  // 13
  {
    const s = p.slides.add(); bg(s);
    title(s, "料号查询从 ERP 语法变成员工习惯", "ERP 要 % 通配符，软件里用空格关键词即可");
    screenshot(s, oldQuery, 62, 156, 540, 315, "旧版");
    screenshot(s, newQuery, 682, 112, 520, 400, "新版");
    card(s, "空格搜索", 126, 536, 180, 54, "#ccfbf1", 24);
    card(s, "简繁体兼容", 356, 536, 210, 54, "#dbeafe", 24);
    card(s, "鼠标拖选复制", 618, 536, 230, 54, "#fef3c7", 24);
    card(s, "减少反复问料号", 900, 536, 260, 54, "#ede9fe", 24);
    footer(s, 13);
    addNotes(s, "这一页讲体验价值：ERP 查询需要百分号，现场员工更习惯输入几个关键词。软件把系统语法翻译成人的习惯，还支持拖选复制。");
  }

  // 14
  {
    const s = p.slides.add(); bg(s, "#f7fffb");
    title(s, "新版桌面版已经形成现场工具", "不是一个脚本，而是日常工作入口");
    screenshot(s, newExec, 74, 142, 520, 350, "BOM 执行");
    screenshot(s, newQuery, 688, 142, 520, 350, "料号查询");
    card(s, "网络配置状态", 112, 536, 190, 52, "#ccfbf1", 22);
    card(s, "快速跳转查询", 344, 536, 190, 52, "#dbeafe", 22);
    card(s, "结果区友好提示", 576, 536, 210, 52, "#fef3c7", 22);
    card(s, "多行复制", 828, 536, 170, 52, "#ede9fe", 22);
    footer(s, 14);
    addNotes(s, "这里把成果落到软件本体：新版已经不是一个单独脚本，而是包含执行、查询、状态提示和操作优化的桌面工具。");
  }

  // 15
  {
    const s = p.slides.add(); section(s, 4, "业务效益", "审核前移，风险提前暴露", "#7c3aed");
    addNotes(s, "第四章讲老板关心的效益。");
  }

  // 16
  {
    const s = p.slides.add(); bg(s, "#f7fffb");
    title(s, "审核从主管兜底前移到个人自检", "主管还是把关人，但不用承担所有基础核对");
    card(s, "过去\n主管集中查", 130, 206, 240, 140, "#fee2e2", 28);
    card(s, "现在\n个人先自检", 520, 206, 240, 140, "#dcfce7", 28);
    card(s, "主管\n处理异常判断", 910, 206, 240, 140, "#dbeafe", 28);
    addText(s, "直接效益：减少重复审核时间，把经验用在真正需要判断的地方。", 122, 486, 1040, 58, { fontSize: 33, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 16);
    addNotes(s, "这页讲时间效益：个人提交前先检查，主管把精力留给异常项和特殊判断，减少重复核对。");
  }

  // 17
  {
    const s = p.slides.add(); bg(s, "#fffdf4");
    title(s, "料号关联规则降低了缺料风险", "把主管经验变成软件自动提醒");
    card(s, "绑定料号", 130, 210, 220, 120, "#dbeafe", 28);
    card(s, "缺少组合料", 410, 210, 220, 120, "#fef3c7", 28);
    card(s, "执行时提醒", 690, 210, 220, 120, "#ccfbf1", 28);
    card(s, "提交前修正", 970, 210, 220, 120, "#dcfce7", 28);
    addText(s, "管理价值：减少漏买导致的补采购、等待到料和组装延误。", 184, 478, 912, 58, { fontSize: 34, bold: true, color: "#92400e", alignment: "center" });
    footer(s, 17);
    addNotes(s, "这页讲缺料风险：料号关联避免漏买关联物料，减少到组装阶段才发现缺料、再重新购买造成延误。");
  }

  // 18
  {
    const s = p.slides.add(); bg(s, "#f8fbff");
    title(s, "效益后续可以用数据继续跑实", "避免空喊节省，用现场记录形成闭环");
    metric(s, "时间", "审核时长", "提交前与主管复核耗时", 78, 190, "#ccfbf1");
    metric(s, "风险", "拦截次数", "缺料、失效、绑定异常", 362, 190, "#dbeafe");
    metric(s, "采购", "补买次数", "漏买后补采购记录", 646, 190, "#fef3c7");
    metric(s, "交付", "等待次数", "因缺料等待到料次数", 930, 190, "#ede9fe");
    addText(s, "这让 AI 项目从“做出来”，进一步走到“看得见收益”。", 160, 486, 960, 58, { fontSize: 34, bold: true, color: "#075985", alignment: "center" });
    footer(s, 18);
    addNotes(s, "如果老板追问具体节省多少，可以这样答：目前已经看到审核前移和风险提前暴露，下一步会记录平均审核时长、拦截问题、补采购次数和缺料等待次数，把收益量化。");
  }

  // 19
  {
    const s = p.slides.add(); bg(s, "#fffaf0");
    title(s, "可靠性来自规则库和人工确认", "AI 帮忙实现工具，但不直接替代审核责任");
    card(s, "规则来源\n主管经验\n真实 BOM\nERP 料号", 96, 202, 250, 170, "#dbeafe", 24);
    card(s, "执行方式\n自动检查\n结果提示\n日志输出", 386, 202, 250, 170, "#ccfbf1", 24);
    card(s, "风险边界\n异常人工确认\n资料人工维护\n规则持续更新", 676, 202, 250, 170, "#fef3c7", 24);
    card(s, "技术落地\nUTF-8 编码\n共享盘配置\n账号权限", 966, 202, 250, 170, "#ede9fe", 24);
    addText(s, "关键原则：AI 提高效率，最终判断仍由业务负责人把关。", 186, 500, 910, 54, { fontSize: 34, bold: true, color: "#92400e", alignment: "center" });
    footer(s, 19);
    addNotes(s, "这页应对 IIC 技术团队或审慎型评委。说明数据来源、规则维护、异常确认和技术问题处理。尤其强调 AI 不直接替代审批，避免被质疑风险过大。");
  }

  // 20
  {
    const s = p.slides.add(); bg(s, "#f7f5ff");
    s.images.add({ blob: imgSmb, contentType: "image/png", fit: "cover", position: { left: 674, top: 114, width: 500, height: 424 } });
    title(s, "AI 项目也要解决交付问题", "共享盘慢、打包、文档，都是落地的一部分");
    card(s, "小启动器", 110, 216, 230, 90, "#dcfce7", 28);
    card(s, "主程序缓存本地", 110, 360, 260, 90, "#dbeafe", 26);
    card(s, "配置和数据仍在共享盘", 410, 360, 230, 90, "#fef3c7", 23);
    footer(s, 20);
    addNotes(s, "这里讲项目落地细节：SMB 直接启动慢，AI 帮忙做启动器和打包方案。软件能不能被同事顺利打开，也属于 AI 落地成果。");
  }

  // 21
  {
    const s = p.slides.add(); section(s, 5, "方法复用", "把一次成功，变成下一次更快", "#ea580c");
    addNotes(s, "最后一章总结方法，让它符合 AI 大赛的推广意义。");
  }

  // 22
  {
    const s = p.slides.add(); bg(s, "#f8fff3");
    title(s, "这套 AI 协作方法可以复制", "业务人员不一定会写代码，但一定要会定义问题");
    card(s, "1\n写清流程", 92, 214, 170, 120, "#dbeafe", 26);
    card(s, "2\n给真实样本", 300, 214, 190, 120, "#ccfbf1", 26);
    card(s, "3\n让 AI 做闭环", 528, 214, 200, 120, "#fef3c7", 26);
    card(s, "4\n现场迭代", 766, 214, 180, 120, "#ede9fe", 26);
    card(s, "5\n文档交付", 984, 214, 180, 120, "#dcfce7", 26);
    addText(s, "AI 不是替代业务专家，而是把专家经验放大成工具。", 174, 486, 930, 58, { fontSize: 36, bold: true, color: "#0f766e", alignment: "center" });
    footer(s, 22);
    addNotes(s, "总结可复制方法：业务人员定义问题、提供样本和判断标准，AI 负责快速实现和迭代。这个方法可以复制到其他工程管理和内部工具项目。");
  }

  // 23
  {
    const s = p.slides.add(); bg(s, "#eafff7");
    addText(s, "这次 AI 大赛项目的核心收获", 142, 124, 996, 62, { fontSize: 46, bold: true, color: "#064e3b", alignment: "center" });
    addText(s, "我把经验讲给 AI\nAI 把经验做成软件\n团队把软件用在现场", 190, 244, 900, 150, { fontSize: 42, bold: true, color: "#0f766e", alignment: "center" });
    screenshot(s, newExec, 340, 466, 600, 160, "BOMCheck 桌面版");
    footer(s, 23);
    addNotes(s, "收尾要回扣 AI 大赛主题：这个项目证明 AI 可以帮助业务人员把想法快速落地。最终价值不是 AI 单独完成，而是业务专家、AI 和现场使用形成闭环。");
  }

  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);

  const previewDir = path.join(WORK, "preview-final");
  await fs.mkdir(previewDir, { recursive: true });
  for (const [index, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(WORK, "deck-montage-final.webp"), new Uint8Array(await montage.arrayBuffer()));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
