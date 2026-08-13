import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

process.on("uncaughtException", (error) => {
  console.error(`UNCAUGHT: ${error?.name}: ${error?.message}`);
  process.exit(1);
});
process.on("unhandledRejection", (error) => {
  console.error(`UNHANDLED: ${error?.name}: ${error?.message}`);
  process.exit(1);
});

const SOURCE = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\宋佳骥_晉升人評會報告.pptx";
const OUT = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\宋佳骥_晉升人評會報告_口播稿優化版.pptx";
const QA = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\.codex-promotion-revision\\final-qa";

const C = {
  navy: "#004B7A",
  cyan: "#2FA9D6",
  orange: "#F28C28",
  dark: "#303030",
  mid: "#5A5A5A",
  light: "#E7EEF3",
  pale: "#F3F7FA",
  white: "#FFFFFF",
  gray: "#A7B0B7",
};

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function setText(shape, text, style = {}, position) {
  shape.text.set(text);
  shape.text.style = {
    typeface: "Microsoft JhengHei",
    fontSize: 22,
    color: C.dark,
    ...style,
  };
  shape.text.autoFit = "shrinkText";
  shape.text.wrap = true;
  shape.text.insets = { left: 8, right: 8, top: 5, bottom: 5 };
  if (position) shape.position = position;
  return shape;
}

function addText(slide, name, text, position, style = {}, options = {}) {
  const shape = slide.shapes.add({
    geometry: options.geometry ?? "textbox",
    name,
    position,
    fill: options.fill ?? "none",
    line: options.line ?? { style: "solid", fill: "none", width: 0 },
    ...(options.borderRadius ? { borderRadius: options.borderRadius } : {}),
  });
  setText(shape, text, style);
  if (options.verticalAlignment) shape.text.verticalAlignment = options.verticalAlignment;
  return shape;
}

function addMetric(slide, name, value, label, position, accent = C.orange) {
  const box = slide.shapes.add({
    geometry: "roundRect",
    name,
    position,
    fill: C.pale,
    line: { style: "solid", fill: C.light, width: 1 },
    borderRadius: "rounded-lg",
  });
  box.text.set([[
    { run: value, textStyle: { fontSize: "34px", bold: true, color: accent, typeface: "Arial" } },
    { run: `\n${label}`, textStyle: { fontSize: "17px", bold: true, color: C.dark, typeface: "Microsoft JhengHei" } },
  ]]);
  box.text.alignment = "center";
  box.text.verticalAlignment = "middle";
  box.text.insets = { left: 6, right: 6, top: 8, bottom: 8 };
  return box;
}

function addPhotoPlaceholder(slide, name, label, position) {
  const frame = slide.shapes.add({
    geometry: "roundRect",
    name,
    position,
    fill: "#F6F6F6",
    line: { style: "solid", fill: C.gray, width: 2 },
    borderRadius: "rounded-lg",
  });
  frame.text.set([[
    { run: "＋", textStyle: { fontSize: "38px", bold: true, color: C.cyan, typeface: "Arial" } },
    { run: `\n请补充设备图片\n${label}`, textStyle: { fontSize: "17px", bold: true, color: C.mid, typeface: "Microsoft JhengHei" } },
  ]]);
  frame.text.alignment = "center";
  frame.text.verticalAlignment = "middle";
  frame.text.insets = { left: 12, right: 12, top: 10, bottom: 10 };
  return frame;
}

function addStage(slide, x, number, period, title, detail) {
  const circle = slide.shapes.add({
    geometry: "ellipse",
    name: `stage-${number}`,
    position: { left: x, top: 235, width: 72, height: 72 },
    fill: number === 1 ? C.orange : C.navy,
    line: { style: "solid", fill: C.white, width: 2 },
  });
  circle.text.set(String(number));
  circle.text.style = { fontSize: 28, bold: true, color: C.white, typeface: "Arial", alignment: "center" };
  circle.text.verticalAlignment = "middle";
  addText(slide, `period-${number}`, period, { left: x - 35, top: 190, width: 142, height: 34 }, { fontSize: 18, bold: true, color: C.orange, alignment: "center" });
  addText(slide, `stage-title-${number}`, title, { left: x - 95, top: 330, width: 262, height: 46 }, { fontSize: 22, bold: true, color: C.navy, alignment: "center" });
  addText(slide, `stage-detail-${number}`, detail, { left: x - 100, top: 380, width: 272, height: 88 }, { fontSize: 17, color: C.dark, alignment: "center" });
}

function setNotes(slide, talk, sources) {
  slide.speakerNotes.textFrame.setText(`${talk}\n\n[Sources]\n${sources.map((source) => `- ${source}`).join("\n")}`);
  slide.speakerNotes.setVisible(true);
}

await fs.mkdir(QA, { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));

// Duplicate the original development slide twice and place both copies before the end slide.
const developmentSource = presentation.slides.getItem(6);
const organizationSlide = developmentSource.duplicate();
organizationSlide.moveTo(7);
organizationSlide.elements.items.find((item) => item.name === "Slide Number Placeholder 3").text.set("8");

// Slide 1: cover.
setNotes(
  presentation.slides.getItem(0),
  "【建议用时：12秒】\n各位主管好，我是MPTK LFAF精益弹性自动化中心电控处宋佳骥。今天我从个人经历、绩效成果、未来工作，以及个人和组织发展四个方面，汇报我从工程师转任课长的准备。",
  ["宋佳骥_晉升人評會報告.pptx 原稿；用户确认个人信息。"],
);

// Slide 2: preserve the PBG promotion-report template agenda exactly.

// Slide 3: personal profile with career timeline and team composition chart.
{
  const slide = presentation.slides.getItem(2);
  setText(presentation.resolve("sh/cza94vmx"), "个人简介｜从现场、技术到管理", { fontSize: 48, bold: true, color: C.navy });
  const body = presentation.resolve("sh/d0jax03i");
  setText(
    body,
    "现职：工程师／电控课代理课长\n本次晋升：课长\n学历：本科，电气工程及其自动化\n毕业院校：华中科技大学武昌分校",
    { fontSize: 20, color: C.dark, lineSpacing: 1.2 },
    { left: 88, top: 176, width: 390, height: 260 },
  );

  // Timeline connector first, then nodes.
  slide.shapes.add({
    geometry: "line",
    name: "career-line",
    position: { left: 98, top: 492, width: 985, height: 0 },
    line: { style: "solid", fill: C.cyan, width: 4 },
    fill: "none",
  });
  const milestones = [
    { x: 100, year: "2011", label: "毕业后从事\n现场设备维修" },
    { x: 410, year: "2015", label: "加入LFAF\n从事电控" },
    { x: 720, year: "2021", label: "担任电控课\n代理课长" },
    { x: 1030, year: "现在", label: "管理19人团队\n推动标准化交付" },
  ];
  milestones.forEach((m, index) => {
    const node = slide.shapes.add({
      geometry: "ellipse",
      name: `career-node-${index + 1}`,
      position: { left: m.x, top: 472, width: 40, height: 40 },
      fill: index === 3 ? C.orange : C.navy,
      line: { style: "solid", fill: C.white, width: 2 },
    });
    addText(slide, `career-year-${index + 1}`, m.year, { left: m.x - 28, top: 435, width: 96, height: 32 }, { fontSize: 18, bold: true, color: index === 3 ? C.orange : C.navy, alignment: "center" });
    addText(slide, `career-label-${index + 1}`, m.label, { left: m.x - 58, top: 515, width: 160, height: 60 }, { fontSize: 16, color: C.dark, alignment: "center" });
  });

  slide.charts.add("bar", {
    position: { left: 520, top: 172, width: 620, height: 245 },
    title: "团队专业构成（不含本人）",
    titleTextStyle: { fontSize: 19, bold: true, fill: C.navy },
    categories: ["传统PLC电控", "视觉／AI／机器人"],
    series: [{ name: "人数", values: [10, 8], fill: C.cyan }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 55, varyColors: true },
    hasLegend: false,
    xAxis: { visible: false, min: 0, max: 12, majorGridlines: null },
    yAxis: { textStyle: { fill: C.dark, fontSize: 16 }, line: { style: "solid", fill: C.light, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.navy, fontSize: 17, bold: true } },
    chartFill: C.white,
    chartLine: { style: "solid", fill: C.white, width: 0 },
    plotAreaFill: C.white,
    plotAreaLine: { style: "solid", fill: C.white, width: 0 },
  });
  setNotes(
    slide,
    "【建议用时：35秒】\n我2011年毕业后从事现场设备维修，2015年加入LFAF从事电控，2021年起担任代理课长。目前团队含我19人，其中传统PLC 10人，视觉、AI和机器人8人。我的工作已经从单一程序开发，扩展到方案审核、资源配置、进度品质、人才培养和跨部门协同。我的角色目标，是通过标准化、人才培养和资源协同，保证项目按期交付。",
    ["用户确认：2011年毕业后从事现场设备维修；2015年入职；2021年代理课长；团队含本人19人。"],
  );
}

// Slide 4: standardization performance with native bar chart and real-photo placeholder.
{
  const slide = presentation.slides.getItem(3);
  setText(presentation.resolve("sh/1cj2d8b6"), "绩效达成（一）｜标准化提升开发效率", { fontSize: 48, bold: true, color: C.navy });
  const body = presentation.resolve("sh/0ba143al");
  body.delete();
  addText(
    slide,
    "altis-section-card",
    "",
    { left: 88, top: 166, width: 385, height: 190 },
    {},
    { geometry: "roundRect", fill: C.pale, line: { style: "solid", fill: C.light, width: 1 }, borderRadius: "rounded-lg" },
  );
  addText(slide, "altis-section-title", "01  Altis项目：形成PLC模块化", { left: 100, top: 176, width: 360, height: 34 }, { fontSize: 18, bold: true, color: C.navy });
  addText(
    slide,
    "altis-section-body",
    "9站整线，主导架构与主要功能块\n2人完成一般需4–5人的开发\n复制3条，共4条量产线\n模块复用：7天 → 2天",
    { left: 100, top: 214, width: 360, height: 132 },
    { fontSize: 16.5, color: C.dark },
  );
  addText(
    slide,
    "vm-section-card",
    "",
    { left: 88, top: 371, width: 385, height: 190 },
    {},
    { geometry: "roundRect", fill: C.white, line: { style: "solid", fill: C.cyan, width: 1.5 }, borderRadius: "rounded-lg" },
  );
  addText(slide, "vm-section-title", "02  VM程序：形成视觉标准化", { left: 100, top: 381, width: 360, height: 34 }, { fontSize: 18, bold: true, color: C.navy });
  addText(
    slide,
    "vm-section-body",
    "整合5种相机架设模式\n导入约50台设备\n平均配置：2天 → 0.5天\n相同架设约3小时",
    { left: 100, top: 419, width: 360, height: 132 },
    { fontSize: 16.5, color: C.dark },
  );
  slide.charts.add("bar", {
    position: { left: 500, top: 170, width: 430, height: 260 },
    title: "改善前 vs 改善后（天）",
    titleTextStyle: { fontSize: 18, bold: true, fill: C.navy },
    categories: ["PLC程序开发", "视觉现场调试"],
    series: [
      { name: "改善前", values: [7, 2], fill: C.gray, valuesFormatCode: "0.0" },
      { name: "改善后", values: [2, 0.5], fill: C.orange, valuesFormatCode: "0.0" },
    ],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 50, overlap: 0 },
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { fontSize: 14, fill: C.dark } },
    xAxis: { visible: true, textStyle: { fill: C.dark, fontSize: 13 }, line: { style: "solid", fill: C.light, width: 1 }, majorGridlines: null },
    yAxis: { visible: true, min: 0, max: 8, majorUnit: 2, textStyle: { fill: C.mid, fontSize: 12 }, line: { style: "solid", fill: C.light, width: 1 }, majorGridlines: { style: "solid", fill: C.light, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.dark, fontSize: 14, bold: true } },
    chartFill: C.white,
    chartLine: { style: "solid", fill: C.white, width: 0 },
    plotAreaFill: C.white,
    plotAreaLine: { style: "solid", fill: C.white, width: 0 },
  });
  addPhotoPlaceholder(slide, "altis-photo-placeholder", "Altis 9站整线或工站全景", { left: 952, top: 180, width: 240, height: 245 });
  addMetric(slide, "plc-reduction", "71%", "PLC开发时间缩短", { left: 505, top: 455, width: 210, height: 106 });
  addMetric(slide, "vision-reduction", "75%", "视觉调试工时减少", { left: 730, top: 455, width: 210, height: 106 }, C.cyan);
  addMetric(slide, "production-lines", "4条", "Altis量产线已投产", { left: 955, top: 455, width: 237, height: 106 }, C.navy);
  setNotes(
    slide,
    "【建议用时：55秒】\n这一项成果分为两个部分。第一部分，是通过Altis项目形成PLC模块化。Altis是一条9站整线，我主导程序架构和主要功能块，由我和另外1名电控完成通常需要4到5人的开发。首线约1个月完成开发和除错，后续小幅修改复制3条，共4条量产。功能块在后续项目持续复用，使PLC开发由7天降到2天。第二部分，是通过VM通用视觉对位程序形成视觉标准化。2024年我开发这套程序，整合5种相机模式，约50台设备导入，平均配置时间由2天降到半天，相同架设约3小时。",
    ["用户确认的Altis投入、周期和复制数量；altis自动线_总线工位功能动作步骤_20240424.xlsx。", "用户确认的VM视觉程序开发时间、5种相机模式和约50台设备导入数据。"],
  );
}

// Slide 5: team and AIDC performance.
{
  const slide = presentation.slides.getItem(4);
  setText(presentation.resolve("sh/dgbulwnm"), "绩效达成（二）｜从0建立团队能力", { fontSize: 48, bold: true, color: C.navy });
  const body = presentation.resolve("sh/cf2tcr61");
  setText(
    body,
    "从0建立8人视觉／AI／机器人团队\n参与招聘，多数为外聘应届生\n入门带教＋自主研究＋每周内训复盘\n目前4人可开发，4人侧重应用调试\nAIDC：培训、标注审核、模型优化\n持续维护各厂部设备与经验复用",
    { fontSize: 18, color: C.dark },
    { left: 88, top: 165, width: 390, height: 405 },
  );
  slide.charts.add("bar", {
    position: { left: 500, top: 170, width: 350, height: 230 },
    title: "8人团队能力分布",
    titleTextStyle: { fontSize: 18, bold: true, fill: C.navy },
    categories: ["具开发能力", "应用／调试"],
    series: [{ name: "人数", values: [4, 4], fill: C.cyan }],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 45, varyColors: true },
    hasLegend: false,
    xAxis: { visible: true, textStyle: { fill: C.dark, fontSize: 14 }, line: { style: "solid", fill: C.light, width: 1 } },
    yAxis: { visible: true, min: 0, max: 5, majorUnit: 1, tickLabelPosition: "none", majorGridlines: { style: "solid", fill: C.light, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.navy, fontSize: 16, bold: true } },
    chartFill: C.white,
    chartLine: { style: "solid", fill: C.white, width: 0 },
    plotAreaFill: C.white,
    plotAreaLine: { style: "solid", fill: C.white, width: 0 },
  });
  addPhotoPlaceholder(slide, "aidc-photo-placeholder", "AIDC设备或检测现场", { left: 875, top: 175, width: 317, height: 225 });
  addMetric(slide, "aidc-count", "39台", "AIDC跨厂部署", { left: 500, top: 435, width: 210, height: 120 });
  addMetric(slide, "aidc-pieces", "1,270万+", "累计实际检测", { left: 725, top: 435, width: 225, height: 120 }, C.cyan);
  addMetric(slide, "aidc-labor", "1–2人", "单台依项目节省", { left: 965, top: 435, width: 227, height: 120 }, C.navy);
  setNotes(
    slide,
    "【建议用时：35秒】\n第二个成果是团队建设和AIDC跨厂复制。我参与招聘，从零建立8人视觉、AI和机器人团队，多数是应届生。通过入门带教、自主研究和每周复盘，目前4人具备开发能力，其余人员侧重应用和调试。团队支撑AIDC跨厂部署39台，累计实际检测超过1,270万件，并持续负责现场培训、标注审核、模型优化和各厂部经验复用。",
    ["用户确认的团队组建、能力分布、培养方式及AIDC部署数据。"],
  );
}

// Slide 6: AI engineering roadmap.
{
  const slide = presentation.slides.getItem(5);
  setText(presentation.resolve("sh/yhg7epsj"), "未来工作规划｜AI驱动技术承接", { fontSize: 48, bold: true, color: C.navy });
  const body = presentation.resolve("sh/zi98nu94");
  body.delete();
  addText(
    slide,
    "future-summary",
    "目标不是单纯缩短开发时间，而是把资深工程师经验转成可调用、可测试、可追溯的组织资产。",
    { left: 150, top: 145, width: 980, height: 58 },
    { fontSize: 20, bold: true, color: C.dark, alignment: "center" },
  );
  slide.shapes.add({
    geometry: "line",
    name: "roadmap-connector",
    position: { left: 260, top: 270, width: 650, height: 0 },
    line: { style: "solid", fill: C.cyan, width: 5 },
    fill: "none",
  });
  addStage(slide, 245, 1, "0–6个月", "资料与模块标准化", "AI整理既有资料\n补齐说明、案例、测试与版本");
  addStage(slide, 575, 2, "6–12个月", "建立AI可调用模块库", "AI组合程序\n人员负责导入、测试与验证");
  addStage(slide, 905, 3, "1–2年", "完成整套程序试点", "先PLC，再扩展至\nRobot／CCD／PC");
  addText(
    slide,
    "roadmap-boundary",
    "安全边界：当前AI仅达到“可导入、可编译”；量产前必须完成功能、异常与安全验证。",
    { left: 150, top: 515, width: 980, height: 52 },
    { fontSize: 18, bold: true, color: C.orange, alignment: "center" },
    { fill: C.pale, line: { style: "solid", fill: C.light, width: 1 }, geometry: "roundRect", borderRadius: "rounded-lg" },
  );
  setNotes(
    slide,
    "【建议用时：50秒】\n未来一到两年，我会推动AI驱动的程序工程化。目标不只是缩短开发时间，而是降低经验门槛，减少对少数资深人员的依赖。前六个月先让AI整理资料，补齐模块说明、测试和版本规范；一年内建立AI可调用的模块库，由AI组合程序、人员测试验证；之后再试点整套PLC，并逐步扩展到机器人、CCD和PC。当前AI只做到可导入、可编译，量产前仍必须完成系统和安全验证。",
    ["用户确认的AI规划、当前验证边界和1—2年阶段目标。"],
  );
}

// Slide 7: personal development, expanded.
{
  const slide = presentation.slides.getItem(6);
  const title = slide.placeholders.getItem("title");
  const body = slide.elements.items.find((item) => item.name === "Content Placeholder 2");
  setText(title, "个人发展｜提升汇报与推动能力", { fontSize: 48, bold: true, color: C.navy });
  body.delete();
  addText(
    slide,
    "personal-summary",
    "个人短板不是技术能力，而是向上汇报和跨部门推动不够结构化。改善目标是让信息更清楚、风险更早暴露、事项能持续闭环。",
    { left: 115, top: 145, width: 1050, height: 62 },
    { fontSize: 19, bold: true, color: C.dark, alignment: "center" },
  );
  const actions = [
    {
      x: 100,
      no: "01",
      title: "向上汇报",
      text: "固定使用\n结论—事实—风险—支持—行动\n让主管快速判断与决策",
      check: "产出：项目状态一页报",
    },
    {
      x: 445,
      no: "02",
      title: "跨部门推动",
      text: "启动前明确目标、责任人与节点\n过程中形成问题清单和会议结论\n对未完成事项持续追踪",
      check: "产出：责任人＋完成日闭环",
    },
    {
      x: 790,
      no: "03",
      title: "管理复盘",
      text: "每周检讨进度、风险与资源\n重大项目结束后复盘\n把经验沉淀为标准",
      check: "产出：周检讨＋项目复盘",
    },
  ];
  actions.forEach((action, index) => {
    const card = slide.shapes.add({
      geometry: "roundRect",
      name: `personal-action-${index + 1}`,
      position: { left: action.x, top: 235, width: 310, height: 285 },
      fill: index === 0 ? "#FFF7ED" : C.pale,
      line: { style: "solid", fill: index === 0 ? C.orange : C.light, width: 2 },
      borderRadius: "rounded-lg",
    });
    card.text.set([[
      { run: `${action.no}  ${action.title}`, textStyle: { fontSize: "23px", bold: true, color: index === 0 ? C.orange : C.navy, typeface: "Microsoft JhengHei" } },
      { run: `\n\n${action.text}`, textStyle: { fontSize: "17px", color: C.dark, typeface: "Microsoft JhengHei" } },
      { run: `\n\n${action.check}`, textStyle: { fontSize: "16px", bold: true, color: C.cyan, typeface: "Microsoft JhengHei" } },
    ]]);
    card.text.insets = { left: 18, right: 18, top: 16, bottom: 16 };
    card.text.alignment = "left";
    card.text.verticalAlignment = "top";
  });
  setNotes(
    slide,
    "【建议用时：25秒】\n个人发展方面，我最需要改善的是向上汇报和跨部门推动。我会固定使用“结论、事实、风险、所需支持、下一步”的汇报结构；项目开始前明确目标、责任人和节点，过程中用问题清单和会议结论持续追踪；同时通过每周检讨和项目复盘，让事项形成闭环。",
    ["用户确认的个人沟通短板与改进行动。"],
  );
}

// Slide 8: organization development, expanded.
{
  const slide = presentation.slides.getItem(7);
  const title = slide.placeholders.getItem("title");
  const body = slide.elements.items.find((item) => item.name === "Content Placeholder 2");
  setText(title, "组织发展｜建立可承接的人才梯队", { fontSize: 48, bold: true, color: C.navy });
  body.delete();
  addText(
    slide,
    "organization-summary",
    "核心问题：模块说明、测试案例和版本责任仍不完整，新人对少数骨干依赖较大。",
    { left: 130, top: 145, width: 1020, height: 55 },
    { fontSize: 20, bold: true, color: C.orange, alignment: "center" },
  );
  // Role flow connectors first.
  slide.shapes.add({ geometry: "line", name: "org-arrow-1", position: { left: 355, top: 320, width: 105, height: 0 }, line: { style: "solid", fill: C.cyan, width: 4, endArrowType: "triangle" }, fill: "none" });
  slide.shapes.add({ geometry: "line", name: "org-arrow-2", position: { left: 705, top: 320, width: 105, height: 0 }, line: { style: "solid", fill: C.cyan, width: 4, endArrowType: "triangle" }, fill: "none" });
  const roles = [
    { x: 100, title: "需求／系统设计", text: "理解制程与现场需求\n定义接口、边界和验收条件" },
    { x: 455, title: "核心模块负责人", text: "维护模块、说明、测试案例\n承担版本与技术方向责任" },
    { x: 810, title: "测试验证／交付", text: "导入、调试、异常验证\n形成现场记录与反馈闭环" },
  ];
  roles.forEach((role, index) => {
    const box = slide.shapes.add({
      geometry: "roundRect",
      name: `org-role-${index + 1}`,
      position: { left: role.x, top: 240, width: 300, height: 175 },
      fill: index === 1 ? "#EAF5FA" : C.pale,
      line: { style: "solid", fill: index === 1 ? C.cyan : C.light, width: 2 },
      borderRadius: "rounded-lg",
    });
    box.text.set([[
      { run: role.title, textStyle: { fontSize: "22px", bold: true, color: C.navy, typeface: "Microsoft JhengHei" } },
      { run: `\n\n${role.text}`, textStyle: { fontSize: "17px", color: C.dark, typeface: "Microsoft JhengHei" } },
    ]]);
    box.text.alignment = "center";
    box.text.verticalAlignment = "middle";
    box.text.insets = { left: 12, right: 12, top: 14, bottom: 14 };
  });
  addText(
    slide,
    "org-mechanism",
    "承接机制：标准库同步维护说明／案例／测试／版本负责人  ｜  人才机制：入门带教＋自主研究＋每周内训＋项目复盘",
    { left: 100, top: 455, width: 1010, height: 82 },
    { fontSize: 18, bold: true, color: C.dark, alignment: "center" },
    { fill: C.pale, line: { style: "solid", fill: C.light, width: 1 }, geometry: "roundRect", borderRadius: "rounded-lg" },
  );
  setNotes(
    slide,
    "【建议用时：25秒】\n组织发展方面，当前最大问题是技术承接薄弱，模块说明和测试案例还不够完善。未来团队会强化需求与系统设计、核心模块负责人、测试验证与交付三类角色。每个模块同步建立说明、案例、测试和版本责任人，并延续入门带教、每周内训和项目复盘，逐步降低对少数技术骨干的依赖。",
    ["用户确认的技术承接问题、未来岗位分工与培养机制。"],
  );
}

// Slide 9: close.
setNotes(
  presentation.slides.getItem(8),
  "【建议用时：10秒】\n我转管理职，不是离开技术，而是希望把技术转成标准、人才和组织能力。我的管理承诺，是从解决单一技术问题，转为持续提升团队整体交付能力。以上是我的报告，谢谢各位主管，请指教。",
  ["用户确认的转管理职理由与管理承诺。"],
);

// Export final renders, layout JSON and PPTX.
for (let index = 0; index < presentation.slides.items.length; index += 1) {
  const slide = presentation.slides.items[index];
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(QA, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1.5 }));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(QA, `${stem}.layout.json`), await layout.text(), "utf8");
}
await writeBlob(path.join(QA, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 1 }));

const finalInspect = await presentation.inspect({
  kind: "slide,textbox,shape,chart,notes,layout",
  include: "id,slide,name,title,textPreview,textChars,textLines,bbox,bboxUnit,chartType,isPlaceholder,placeholders",
  maxChars: 200000,
});
await fs.writeFile(path.join(QA, "final-inspect.ndjson"), finalInspect.ndjson, "utf8");

const pptx = await PresentationFile.exportPptx(presentation);
const finalOut = OUT.replace(/\.pptx$/i, "_R5.pptx");
await pptx.save(finalOut);
console.log(finalOut);
