import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import { buildSlide02 } from "./grid/slide-02.mjs";
import { buildSlide06 } from "./grid/slide-06.mjs";
import { buildSlide08 } from "./grid/slide-08.mjs";
import { buildSlide16 } from "./grid/slide-16.mjs";
import { buildSlide17 } from "./grid/slide-17.mjs";
import { buildSlide19 } from "./grid/slide-19.mjs";
import { buildSlide26 } from "./grid/slide-26.mjs";

const ROOT = "C:/Users/lfaf-test/Documents/报告编写";
const ASSETS = `${ROOT}/ppt_assets`;
const OUTPUT = `${ROOT}/LFAF小助手_AI大赛成果报告.pptx`;
const PREVIEW = `${ROOT}/ppt_build/preview`;
const FONT = "Microsoft YaHei";
const INK = "#111827";
const BLUE = "#3D8DFF";
const CYAN = "#6DCBF4";
const MUTED = "#536171";

function rich(text, size = 24, bold = false, color = INK, options = {}) {
  return {
    runs: [{ run: text, textStyle: { fontSize: `${size}px`, typeface: FONT, color, bold } }],
    spaceAfter: options.spaceAfter ?? 300,
    paragraphStyle: { lineSpacingPercent: options.lineSpacingPercent ?? 112000 },
  };
}

function pair(title, body) {
  return {
    titleHere: rich(title, 27, true, INK, { spaceAfter: 650 }),
    loremIpsumDolorSitAmetConsecteturAdipiscing: rich(body, 20, false, MUTED, { lineSpacingPercent: 118000 }),
  };
}

function addNotes(slide, talkTrack, sources = []) {
  const sourceBlock = sources.length
    ? `\n\n[Sources]\n${sources.map((s) => `- ${s}`).join("\n")}\n[/Sources]`
    : "\n\n[Sources]\n- 用户提供的项目信息与成果报告初稿（2026-08-01）\n[/Sources]";
  slide.speakerNotes.textFrame.setText(`${talkTrack}${sourceBlock}`);
  slide.speakerNotes.setVisible(true);
}

async function bytes(path) {
  const data = await fs.readFile(path);
  return data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);
}

function addImage(slide, blob, alt, position, crop = undefined) {
  return slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    fit: "cover",
    geometry: "roundRect",
    borderRadius: "rounded-xl",
    position,
    ...(crop ? { crop } : {}),
  });
}

function addAccent(slide, left = 41.33, top = 145, width = 130) {
  slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height: 7 },
    fill: BLUE,
    line: { style: "solid", fill: BLUE, width: 0 },
  });
}

function addFooterLabel(slide, text) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left: 41.33, top: 665, width: 700, height: 24 },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = { fontSize: 14, typeface: FONT, color: "#7B8794" };
}

async function main() {
  await fs.mkdir(PREVIEW, { recursive: true });
  const painImage = await bytes(`${ASSETS}/pain_folder_maze.png`);
  const alarmImage = await bytes(`${ASSETS}/alarm_ai_search.png`);
  const futureImage = await bytes(`${ASSETS}/future_report_generation.png`);

  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // 1. Cover — Codex Grid slide 02
  {
    const slide = buildSlide02(presentation, {
      title: rich("AI大赛参赛成果｜LFAF × IIC", 24, true, BLUE),
      title2: rich("非标自动化知识应用", 22, false, MUTED),
      title3: rich("LFAF小助手\n让历史专案资料\n找得到、用得上", 66, true, INK, { lineSpacingPercent: 95000 }),
    });
    slide.background.fill = "#FFFFFF";
    slide.shapes.add({ geometry: "rect", position: { left: 41.33, top: 655, width: 1197, height: 8 }, fill: BLUE, line: { style: "solid", fill: BLUE, width: 0 } });
    addNotes(slide, "开场直接点出项目价值：我们没有改变资料归档方式，而是用AI改变工程师访问历史资料的方式。介绍团队与协作背景。参赛部门LFAF，项目负责人杨敏锐，成员里戈宁、宋佳骥；LFAF提出需求，IIC负责架构与小程序开发。");
  }

  // 2. Pain point — Codex Grid slide 08
  {
    const slide = buildSlide08(presentation, {
      title: rich("公共盘查找如大海捞针", 48, true),
      body1: pair("年份 → 月份 → 专案", "不知道资料路径时，只能凭记忆逐层打开文件夹。\n再逐一查看 Excel、PPT 等文件。\n\n结果：查找耗时、依赖经验、知识难复用。"),
      footer1: rich("02", 14, false, MUTED),
    });
    addImage(slide, painImage, "工程师面对大量分层历史文件进行查找", { left: 658.17, top: 41.62, width: 581.6, height: 588.14 }, { left: 0.04, top: 0.02, right: 0.04, bottom: 0.02 });
    addAccent(slide);
    addNotes(slide, "说明公共盘原有结构按年份、月份、专案建立，归档清楚，但不适合从报警代码或异常现象反向查找。强调问题不是资料不存在，而是资料找不到、用不上。", ["用户提供的业务痛点（2026-08-01）", "AI生成配图：ppt_assets/pain_folder_maze.png；由OpenAI内置图像生成工具制作"]);
  }

  // 3. AI workflow — Codex Grid slide 17
  {
    const slide = buildSlide17(presentation, {
      title: rich("AI把“记住路径”改造成“描述问题”", 48, true),
      label1: rich("01 资料进入", 21, true, BLUE),
      label2: rich("02 工程师提问", 21, true, BLUE),
      label3: rich("03 AI联想与匹配", 21, true, BLUE),
      body1: pair("多格式入库", "上传Excel、PPT等历史专案资料，形成统一知识入口。"),
      body2: pair("自然表达", "输入报警代码、设备名称、异常现象或相关提示词。"),
      body3: pair("返回资料线索", "AI缩小检索范围；工程师查看原始资料并作专业确认。"),
      footer1: rich("03", 14, false, MUTED),
    });
    addAccent(slide);
    addNotes(slide, "这一页回答比赛最关心的问题：AI发生在哪个流程、发挥什么作用。AI连接工程师的自然表达和历史资料内容，承担资料导航与关联匹配；最终技术判断仍由工程师完成。");
  }

  // 4. Use case — Codex Grid slide 08
  {
    const slide = buildSlide08(presentation, {
      title: rich("报警代码查询快速落地", 48, true),
      body1: pair("输入报警代码", "过去：先猜专案，再翻电气资料和调试记录。\n\n现在：从报警代码直接发起查询，由AI联想相关历史资料，工程师再确认处理方案。"),
      footer1: rich("04", 14, false, MUTED),
    });
    addImage(slide, alarmImage, "工程师通过AI小助手查询报警代码E-104并关联历史文件", { left: 658.17, top: 41.62, width: 581.6, height: 588.14 }, { left: 0.12, top: 0.02, right: 0.03, bottom: 0.02 });
    addAccent(slide);
    addNotes(slide, "用报警代码作为演示主线。建议现场用一个真实报警代码录屏或演示：输入代码、展示联想结果、打开原始资料。不要把AI描述成自动决定故障方案。", ["用户提供的高频场景（2026-08-01）", "AI生成配图：ppt_assets/alarm_ai_search.png；由OpenAI内置图像生成工具制作"]);
  }

  // 5. Delivered capabilities — Codex Grid slide 06
  {
    const slide = buildSlide06(presentation, {
      title: rich("基础能力已经完成，项目具备实际使用入口", 48, true),
      body1: pair("多格式资料入库", "支持Excel、PPT等资料上传，为部门知识库持续扩充提供基础。"),
      body2: pair("提示词联想", "根据报警代码、设备名或关键词，缩小资料查找范围。"),
      body3: pair("小程序统一入口", "整体架构与小程序已完成，将资料查询嵌入工程师日常工作。"),
      footer1: rich("05", 14, false, MUTED),
    });
    addAccent(slide);
    addNotes(slide, "区分已实现与未来能力：当前已经完成架构、小程序、多格式上传和提示词联想。自动总结与报告生成尚属于后续规划，不能在成果页中当作已实现功能。");
  }

  // 6. Value estimate — Codex Grid slide 19
  {
    const slide = buildSlide19(presentation, {
      title: rich("情境测算显示：查询时间有望明显缩短", 48, true),
      body1: {
        topic: rich("测算口径｜非实测", 24, true, BLUE, { spaceAfter: 500 }),
        loremIpsumDolorSitAmetConsecteturAdipiscing: rich("人工15分钟/次，小助手2分钟/次；按部门日均10次查询、每年220个工作日估算。", 21, false, MUTED),
      },
      stat1: rich("13 分钟", 58, true, INK),
      stat2: rich("86.7%", 58, true, BLUE),
      stat3: rich("477 小时", 58, true, INK),
      body2: rich("单次预计节省", 20, false, MUTED),
      body3: rich("查询时间缩短", 20, false, MUTED),
      body4: rich("年度潜在节省", 20, false, MUTED),
      footer1: rich("06", 14, false, MUTED),
    });
    addAccent(slide);
    addFooterLabel(slide, "建议赛前用20–30个典型任务开展人工/AI对照测试，并以实测数据替换本页测算。 ");
    addNotes(slide, "明确告诉评委：这是基于假设的情境测算，不是当前实测结果。公式为：日均查询次数×单次节省13分钟×220天÷60。若完成赛前对照测试，应立即用真实数据替换。", ["成果报告中的情境测算：人工15分钟/次、小助手2分钟/次、日均10次、220个工作日（待实测验证）"]);
  }

  // 7. Innovation — Codex Grid slide 16
  {
    const slide = buildSlide16(presentation, {
      title: rich("创新不在“聊天”，而在重构资料使用方式", 48, true),
      body1: pair("问题驱动", "从报警和异常出发，而非从目录出发。"),
      body2: pair("真实流程", "直接服务工程资料查询与异常处理。"),
      body3: pair("多格式连接", "汇集Excel、PPT等分散资料。"),
      body4: pair("统一入口", "降低文件名和路径记忆门槛。"),
      body5: pair("高频切入", "先落地报警代码查询。"),
      body6: pair("经验复用", "未参与原专案者也能找资料。"),
      body7: pair("人机协同", "AI导航，工程师审核与判断。"),
      body8: pair("持续扩展", "从检索走向总结与生成。"),
      footer1: rich("07", 14, false, MUTED),
    });
    addAccent(slide);
    addNotes(slide, "把创新性落在业务模式上：从路径驱动转为问题驱动，从个人记忆转为部门知识入口，从单一搜索转为可升级的知识应用链路。");
  }

  // 8. Roadmap — Codex Grid slide 08
  {
    const slide = buildSlide08(presentation, {
      title: rich("下一步：AI自动生成报告", 48, true),
      body1: pair("检索 → 总结 → 生成", "① 自动提炼单个专案摘要\n② 汇总报警、原因与历史处理方式\n③ 跨文件归纳技术信息\n④ 按部门模板生成报告初稿\n\n工程师负责审核确认。"),
      footer1: rich("08", 14, false, MUTED),
    });
    addImage(slide, futureImage, "多格式工程资料经过AI知识处理后形成结构化报告", { left: 658.17, top: 41.62, width: 581.6, height: 588.14 }, { left: 0.02, top: 0.02, right: 0.02, bottom: 0.02 });
    addAccent(slide);
    addNotes(slide, "后续升级分三层：先总结单个项目，再跨文件归纳，最后结合固定模板生成报告初稿。强调工程师审核，避免给人完全自动生成并直接采用的印象。", ["用户提供的后续规划（2026-08-01）", "AI生成配图：ppt_assets/future_report_generation.png；由OpenAI内置图像生成工具制作"]);
  }

  // 9. Team collaboration — Codex Grid slide 17
  {
    const slide = buildSlide17(presentation, {
      title: rich("业务与技术协同，让AI真正进入工程现场", 48, true),
      label1: rich("LFAF", 21, true, BLUE),
      label2: rich("IIC", 21, true, BLUE),
      label3: rich("联合验证", 21, true, BLUE),
      body1: pair("定义真实需求", "识别痛点、提供资料、确定报警代码等使用场景。"),
      body2: pair("搭建技术能力", "完成整体架构设计与小程序开发。"),
      body3: pair("持续迭代", "用真实任务测试效果，扩充资料并优化功能。"),
      footer1: rich("09", 14, false, MUTED),
    });
    addAccent(slide);
    addFooterLabel(slide, "项目负责人：杨敏锐｜项目成员：里戈宁、宋佳骥");
    addNotes(slide, "说明双方分工。LFAF的贡献是提出真实业务需求、提供资料与场景并开展验证；IIC承担整体架构和小程序开发。团队成员姓名请在正式提交前再次核对。");
  }

  // 10. Close — Codex Grid slide 26
  {
    const slide = buildSlide26(presentation, {
      title: rich("LFAF小助手", 24, true, BLUE),
      title2: rich("让历史资料成为\n可复用的工程知识", 68, true, INK, { lineSpacingPercent: 98000 }),
      title3: {
        loremIpsumDetails: rich("真实痛点", 25, true, INK),
        loremIpsumDetails2: rich("已完成基础能力", 25, true, INK),
        loremIpsumDetails3: rich("可持续升级与复制", 25, true, INK),
      },
    });
    slide.shapes.add({ geometry: "rect", position: { left: 864, top: 0, width: 416, height: 720 }, fill: "#EAF5FB", line: { style: "solid", fill: "#EAF5FB", width: 0 } });
    slide.shapes.add({ geometry: "ellipse", position: { left: 950, top: 185, width: 180, height: 180 }, fill: BLUE, line: { style: "solid", fill: BLUE, width: 0 } });
    const ai = slide.shapes.add({ geometry: "textbox", position: { left: 985, top: 232, width: 110, height: 70 }, fill: "none", line: { style: "solid", fill: "none", width: 0 } });
    ai.text = "AI";
    ai.text.style = { fontSize: 54, bold: true, typeface: FONT, color: "#FFFFFF", alignment: "center" };
    addNotes(slide, "结尾回到开场：LFAF小助手让部门资料从静态归档转化为可查询、可理解、可复用的知识资产。当前从检索切入，未来扩展总结与报告生成，并具备向其他资料密集型部门复制的潜力。");
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1.5 });
    await fs.writeFile(`${PREVIEW}/${stem}.png`, new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(`${PREVIEW}/${stem}.layout.json`, await layout.text());
  }

  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(`${PREVIEW}/deck-montage.webp`, new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUTPUT);
  console.log(JSON.stringify({ output: OUTPUT, slides: presentation.slides.items.length, preview: PREVIEW }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
