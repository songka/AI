import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = process.cwd().replaceAll("\\", "/");
const OUT = `${ROOT}/outputs/13-真实案例实操拆解-中文化版-带讲师备注.pptx`;
const PREVIEW = `${ROOT}/work/presentations/skill-training/tmp/preview/13-practical-case-cn`;
const W = 1280;
const H = 720;

const c = {
  ink: "#111111",
  muted: "#555555",
  panel: "#F3F4F6",
  line: "#C7CCD4",
  red: "#DC2626",
  green: "#059669",
  blue: "#2563EB",
  orange: "#F97316",
  purple: "#7C3AED",
};

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
    fontSize: opts.size ?? 21,
    bold: opts.bold ?? false,
    color: opts.color ?? c.ink,
    alignment: opts.align ?? "left",
  };
  return shape;
}

function box(slide, x, y, w, h, fill = c.panel, line = c.line) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
  });
}

function notes(slide, lines) {
  slide.speakerNotes.textFrame.setText(Array.isArray(lines) ? lines : [lines]);
  slide.speakerNotes.setVisible(true);
}

function footer(slide, n) {
  text(slide, "中文实操案例 / IO 表检查", 56, 30, 560, 24, { size: 15, bold: true, color: c.muted });
  text(slide, String(n).padStart(2, "0"), W - 94, H - 46, 40, 20, { size: 14, color: c.muted, align: "right" });
}

function title(slide, n, heading, sub = "") {
  slide.background.fill = "#FFFFFF";
  footer(slide, n);
  text(slide, heading, 58, 82, 1040, 64, { size: 40, bold: true });
  if (sub) text(slide, sub, 60, 152, 1040, 42, { size: 21, color: c.muted });
}

function cover(slide) {
  slide.background.fill = "#FFFFFF";
  box(slide, 58, 92, 10, 492, c.orange, c.orange);
  text(slide, "第 13 份 / 中文化实训课件", 92, 96, 620, 26, { size: 18, bold: true, color: c.muted });
  text(slide, "用中文材料讲清一个错误例子和一个正确例子", 92, 168, 960, 116, { size: 46, bold: true });
  text(slide, "以 IO 表检查为例，文件、提示词、技能（Skill）、规则、工具输出和预期结果尽量使用中文。", 94, 314, 940, 42, { size: 23, color: c.muted });
  box(slide, 96, 470, 1040, 84, "#F7F7F7", c.line);
  text(slide, "课堂目标：学员能按中文材料跑一遍，并指出哪一部分是大语言模型（LLM）、智能体（Agent）、技能（Skill）、工具、知识库、记忆（Memory）。", 120, 490, 980, 40, { size: 18, bold: true });
  notes(slide, [
    "讲师提示：这版替代前一版英文示例。保留 DI、DO、PLC、CSV 这类行业常用缩写即可。",
    "开场可以说：我们先不背名词，先跑一个中文例子。",
  ]);
}

function codeBlock(slide, x, y, w, h, heading, body, color = c.blue) {
  box(slide, x, y, w, h, "#F7F7F7", c.line);
  text(slide, heading, x + 18, y + 16, w - 36, 24, { size: 20, bold: true, color });
  text(slide, body, x + 18, y + 54, w - 36, h - 74, { size: 16, color: c.ink });
}

function twoCols(slide, n, heading, sub, left, right, note) {
  title(slide, n, heading, sub);
  box(slide, 70, 228, 520, 360, left.fill ?? "#FFF5F5", c.line);
  box(slide, 690, 228, 520, 360, right.fill ?? "#F0FDF4", c.line);
  text(slide, left.head, 100, 258, 450, 32, { size: 28, bold: true, color: left.color ?? c.red });
  text(slide, left.body, 100, 316, 440, 220, { size: 19 });
  text(slide, right.head, 720, 258, 450, 32, { size: 28, bold: true, color: right.color ?? c.green });
  text(slide, right.body, 720, 316, 440, 220, { size: 19 });
  notes(slide, note);
}

function rows(slide, n, heading, sub, data, note) {
  title(slide, n, heading, sub);
  const x = 56, y = 218;
  const widths = [220, 300, 305, 291];
  const heads = ["部分", "实际文件/动作", "它负责什么", "不能做什么"];
  let cx = x;
  for (let i = 0; i < heads.length; i++) {
    box(slide, cx, y, widths[i], 44, "#E5E7EB", c.line);
    text(slide, heads[i], cx + 10, y + 12, widths[i] - 20, 18, { size: 15, bold: true, align: "center" });
    cx += widths[i];
  }
  let cy = y + 44;
  for (const row of data) {
    cx = x;
    for (let i = 0; i < row.length; i++) {
      box(slide, cx, cy, widths[i], 62, i === 0 ? "#FFFFFF" : "#F7F7F7", c.line);
      text(slide, row[i], cx + 10, cy + 9, widths[i] - 20, 44, { size: i === 0 ? 15 : 13, bold: i === 0 });
      cx += widths[i];
    }
    cy += 62;
  }
  notes(slide, note);
}

async function build() {
  const p = Presentation.create({ slideSize: { width: W, height: H } });

  let s = p.slides.add();
  cover(s);

  s = p.slides.add();
  title(s, 2, "这套中文实操包可以直接打开使用", "所有文件都在 outputs/ai-practice-cases/io-table-demo-cn 目录下。");
  codeBlock(s, 70, 230, 520, 320, "课堂要打开的中文文件", [
    "input/IO表样例.csv",
    "prompts/错误提示词.txt",
    "prompts/正确提示词.txt",
    "skill/SKILL.md",
    "skill/references/IO检查规则.md",
    "tool-output/工具检查结果.csv",
    "expected-output/工程预审结果.csv",
    "concept-map.txt",
  ].join("\n"), c.blue);
  codeBlock(s, 670, 230, 500, 320, "课堂要运行的中文脚本", [
    "python outputs/ai-practice-cases/io-table-demo-cn/tools/检查IO表.py outputs/ai-practice-cases/io-table-demo-cn/input/IO表样例.csv",
    "",
    "说明：命令里的 python、CSV 是工具环境和文件格式名称，保留即可。",
  ].join("\n"), c.green);
  notes(s, [
    "讲师提示：先打开 README.txt，再打开 IO 表样例.csv。",
    "如果现场不方便运行脚本，可以直接打开 tool-output/工具检查结果.csv。",
  ]);

  s = p.slides.add();
  twoCols(s, 3, "错误例子：一句话让 AI 猜，结果不可控", "这个错误例子已经改成中文，学员能直接看懂问题。", {
    head: "错误输入",
    body: "帮我看一下这个 IO 表有没有问题，给我一个结论。\n\n问题：没有检查项、没有输出格式、没有证据要求，也没有人工确认边界。",
    color: c.red,
    fill: "#FFF5F5",
  }, {
    head: "可能输出",
    body: "这个 IO 表整体基本可用，建议检查重复地址和空字段。\n\n问题：结论太粗，不能指导电控工程师改表，也不能给质量或管理复核。",
    color: c.orange,
    fill: "#FFF7ED",
  }, [
    "讲师提示：让学员回答：这个输出能不能直接作为项目评审依据？答案通常是不能。",
    "这页的重点不是提示词写得短，而是缺少结构。",
  ]);

  s = p.slides.add();
  title(s, 4, "中文 IO 表样例里故意放了真实常见问题", "先让学员自己找，再用工具检查。");
  codeBlock(s, 70, 230, 550, 330, "IO表样例.csv 关键内容", [
    "第 2 行：工位10 气缸01 DI I0.0 伸出到位",
    "第 3 行：工位10 气缸01 DI I0.0 伸出到位重复",
    "第 5 行：工位10 气缸01 DO Q0.1 变量名为空",
    "第 10 行：工位20 扫码枪01 DI I1.2 扫码完成",
    "第 11 行：工位20 扫码枪01 DI I1.2 扫码完成",
    "第 12 行：工位20 报警复位按钮 DI 地址为空",
  ].join("\n"), c.blue);
  codeBlock(s, 690, 230, 480, 330, "这里埋了哪些问题", [
    "I0.0 地址重复",
    "第 5 行变量名为空",
    "I1.2 地址重复",
    "扫码完成变量名重复",
    "第 12 行地址为空",
    "安全门、急停、报警复位需要人工确认完整性",
  ].join("\n"), c.red);
  notes(s, [
    "讲师提示：这里要让学员看到例子是“项目味”的，不是抽象玩具数据。",
    "DI、DO、PLC 这些保留缩写，因为现场本来就这样叫。",
  ]);

  s = p.slides.add();
  title(s, 5, "中文工具脚本能直接跑出确定性问题", "工具负责找证据，不负责替工程师做最终判断。");
  codeBlock(s, 70, 220, 1080, 350, "运行结果：工具检查结果.csv", [
    "问题类型,证据,备注",
    "必填字段为空,第 5 行：变量名,这个字段不能为空。",
    "必填字段为空,第 12 行：地址,这个字段不能为空。",
    "地址重复,I0.0,第 [2, 3] 行使用了同一个地址。",
    "地址重复,I1.2,第 [10, 11] 行使用了同一个地址。",
    "变量名重复,工位20_扫码枪01_扫码完成,第 [10, 11] 行使用了同一个变量名。",
  ].join("\n"), c.green);
  text(s, "这一页对应：模型上下文协议（MCP）/工具。它像检测仪器，给出证据，不替人签字。", 76, 596, 1000, 28, { size: 20, bold: true, color: c.green });
  notes(s, [
    "讲师提示：把工具讲成“确定性检查”。它稳定，但不懂项目背景。",
    "模型上下文协议（MCP）可以理解为让 AI 接入这类工具的一种标准方式。",
  ]);

  s = p.slides.add();
  title(s, 6, "正确例子把技能、规则、工具结果都放进来", "正确提示词不是更长，而是把工作边界说清楚。");
  codeBlock(s, 70, 220, 520, 360, "正确提示词.txt 摘要", [
    "输入：",
    "1. IO 表：IO表样例.csv",
    "2. 工具检查结果：工具检查结果.csv",
    "3. 检查规则：IO检查规则.md",
    "",
    "任务：",
    "先列确定问题，再补充需工程师确认的问题。",
    "不允许编造输入中没有的地址、变量名、设备或工位。",
  ].join("\n"), c.blue);
  codeBlock(s, 670, 220, 500, 360, "输出字段", [
    "问题类型",
    "证据",
    "影响",
    "建议处理",
    "责任岗位",
    "是否需要人工确认",
    "",
    "边界：安全门、急停、复位、互锁、动作顺序必须由电控工程师确认。",
  ].join("\n"), c.orange);
  notes(s, [
    "讲师提示：这一页让学员明白，正确提示词把输入、规则、输出和边界都讲清楚。",
    "这里可以对照打开 prompts/正确提示词.txt。",
  ]);

  s = p.slides.add();
  title(s, 7, "技能（Skill）和知识库在文件里分得很清楚", "左边是怎么做，右边是依据是什么。");
  codeBlock(s, 70, 220, 520, 360, "skill/SKILL.md", [
    "先用工具检查确定性问题。",
    "再按规则检查工程风险。",
    "输出时区分：",
    "  工具已经确定的问题",
    "  需要工程师确认的问题",
    "不得把猜测写成事实。",
    "最后给出是否建议进入下一步。",
  ].join("\n"), c.orange);
  codeBlock(s, 670, 220, 500, 360, "skill/references/IO检查规则.md", [
    "安全门、急停、复位、报警信号必须描述清楚。",
    "气缸通常需要伸出、缩回、到位或原点信号。",
    "视觉、扫码设备应有完成、合格、不合格、异常或超时逻辑。",
    "涉及安全和互锁必须人工确认。",
  ].join("\n"), c.purple);
  notes(s, [
    "讲师提示：技能（Skill）是流程，知识库是资料依据。",
    "这页是名词落地的关键页。",
  ]);

  s = p.slides.add();
  title(s, 8, "正确输出要能指导下一步处理", "工程输出必须包含证据、影响、建议、责任岗位和人工确认。");
  codeBlock(s, 70, 220, 1080, 366, "工程预审结果.csv 摘要", [
    "确定问题：变量名为空 | 第 5 行变量名为空 | 后续 PLC 程序、报警、调试记录无法稳定引用 | 补充变量名 | 电控 | 是",
    "确定问题：地址为空 | 第 12 行地址为空 | 报警复位按钮无法映射到 PLC 输入点 | 补充实际输入地址 | 电控 | 是",
    "确定问题：地址重复 | I0.0 出现在第 2 行和第 3 行 | PLC 地址冲突 | 更正其中一个地址 | 电控 | 是",
    "需确认：安全相关信号完整性 | 有安全门关闭和急停正常，但未看到安全复位说明 | 可能影响安全逻辑 | 电控确认 | 电控/安全评审 | 是",
    "需确认：扫码异常处理 | 仅看到扫码完成，未看到扫码不合格或超时 | 异常流程可能无法识别 | 增加异常信号确认 | 电控/软件 | 是",
  ].join("\n"), c.green);
  notes(s, [
    "讲师提示：让学员判断：哪些是工具确定的问题，哪些是工程师确认的问题。",
    "强调：好的 AI 输出不是漂亮文字，而是能进入工作流。",
  ]);

  s = p.slides.add();
  rows(s, 9, "这个中文例子里，每个 AI 名词都有实际位置", "学员应该能指着文件说清楚每部分是什么。", [
    ["大语言模型（LLM）", "读取提示词、工具结果、检查规则", "转成工程语言和预审表", "不确认安全设计"],
    ["技能（Skill）", "skill/SKILL.md", "规定检查顺序、格式、边界", "不保存项目资料"],
    ["智能体（Agent）", "按 README 步骤推进", "读表、调工具、查规则、生成输出", "不越权、不自动下发"],
    ["模型上下文协议（MCP）/工具", "tools/检查IO表.py", "找空字段、重复地址、重复变量名", "不理解安全逻辑"],
    ["知识库", "IO检查规则.md", "提供检查依据和人工确认点", "不自动执行流程"],
    ["记忆（Memory）", "本例不强制使用", "可记部门输出偏好", "不记客户机密"],
    ["工作流（Workflow）", "README.txt 的课堂顺序", "串起输入、工具、规则、输出和复核", "不跳过人工确认"],
  ], [
    "讲师提示：这页回应“分析那个是哪部分”。让学员打开 concept-map.txt 对照。",
    "如果学员只能背定义，还不算掌握；能指出文件和动作，才算能落地。",
  ]);

  s = p.slides.add();
  title(s, 10, "课堂验收看这三件事", "练习结束不是看有没有生成文字，而是看能不能复核、能不能用于工作。");
  codeBlock(s, 70, 230, 330, 320, "学员要做", [
    "打开中文 IO 表。",
    "肉眼找问题。",
    "运行中文检查脚本。",
    "用正确提示词生成预审表。",
    "标出每一部分属于哪个概念。",
  ].join("\n"), c.blue);
  codeBlock(s, 475, 230, 330, 320, "讲师要看", [
    "是否列证据。",
    "是否区分确定问题和需确认问题。",
    "是否输出责任岗位。",
    "是否标注人工确认点。",
    "是否避免编造信息。",
  ].join("\n"), c.green);
  codeBlock(s, 880, 230, 330, 320, "最终交付", [
    "一份工程预审表。",
    "一份概念拆解表。",
    "一条岗位改进建议：",
    "哪个任务适合做成技能（Skill）或工作流（Workflow）。",
  ].join("\n"), c.orange);
  notes(s, [
    "结尾提示：这份课件可以作为前面所有课件的练习前导入。",
    "课后让各岗位换自己的真实但脱敏文件，再照这个流程做一次。",
  ]);

  await fs.mkdir(PREVIEW, { recursive: true });
  for (const [i, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(PREVIEW, `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(PREVIEW, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
