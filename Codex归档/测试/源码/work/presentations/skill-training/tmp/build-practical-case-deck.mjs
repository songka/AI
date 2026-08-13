import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = process.cwd().replaceAll("\\", "/");
const OUT = `${ROOT}/outputs/13-真实案例实操拆解-错误与正确-带讲师备注.pptx`;
const PREVIEW = `${ROOT}/work/presentations/skill-training/tmp/preview/13-practical-case`;
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
  text(slide, "真实案例实操拆解 / 错误与正确", 56, 30, 560, 24, { size: 15, bold: true, color: c.muted });
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
  text(slide, "第 13 份 / 可操作实训课件", 92, 96, 600, 26, { size: 18, bold: true, color: c.muted });
  text(slide, "两个真实例子：一个错误，一个正确", 92, 168, 920, 116, { size: 50, bold: true });
  text(slide, "以 IO 表检查为例，给出样例文件、操作步骤、命令、输出和概念拆解。", 94, 314, 900, 42, { size: 24, color: c.muted });
  box(slide, 96, 470, 1040, 84, "#F7F7F7", c.line);
  text(slide, "课堂目标：学员能亲手跑一遍，并指出哪一部分是大语言模型（LLM）、智能体（Agent）、技能（Skill）、工具、记忆（Memory）和知识库。", 120, 490, 980, 40, { size: 18, bold: true });
  notes(slide, [
    "讲师提示：这份课件放在任意练习前使用。先不讲抽象概念，直接带大家跑一个能操作的例子。",
    "强调：错误例子不是为了批评，而是让学员看到为什么“只会问一句”不等于会用 AI。",
  ]);
}

function twoCols(slide, n, heading, sub, left, right, note) {
  title(slide, n, heading, sub);
  box(slide, 70, 228, 520, 360, left.fill ?? "#FFF5F5", c.line);
  box(slide, 690, 228, 520, 360, right.fill ?? "#F0FDF4", c.line);
  text(slide, left.head, 100, 258, 450, 32, { size: 28, bold: true, color: left.color ?? c.red });
  text(slide, left.body, 100, 316, 440, 210, { size: 19 });
  text(slide, right.head, 720, 258, 450, 32, { size: 28, bold: true, color: right.color ?? c.green });
  text(slide, right.body, 720, 316, 440, 210, { size: 19 });
  notes(slide, note);
}

function codeBlock(slide, x, y, w, h, heading, body, color = c.blue) {
  box(slide, x, y, w, h, "#F7F7F7", c.line);
  text(slide, heading, x + 18, y + 16, w - 36, 24, { size: 20, bold: true, color });
  text(slide, body, x + 18, y + 54, w - 36, h - 74, { size: 16, color: c.ink });
}

function rows(slide, n, heading, sub, data, note) {
  title(slide, n, heading, sub);
  const x = 56, y = 218;
  const widths = [230, 300, 300, 286];
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
  title(s, 2, "这个实操包可以直接打开文件操作", "所有样例都在 outputs/ai-practice-cases/io-table-demo 目录下。");
  codeBlock(s, 70, 230, 520, 310, "课堂要打开的文件", [
    "input/sample-io-table.csv",
    "prompts/wrong-prompt.txt",
    "prompts/correct-prompt.txt",
    "skill/SKILL.md",
    "skill/references/io-rules.md",
    "tool-output/check-result.csv",
    "expected-output/engineering-review.csv",
    "concept-map.txt",
  ].join("\n"), c.blue);
  codeBlock(s, 670, 230, 500, 310, "课堂要运行的命令", "python outputs/skill-examples/io-table-review/scripts/check_io_table.py outputs/ai-practice-cases/io-table-demo/input/sample-io-table.csv", c.green);
  text(s, "讲法：先让学员看输入文件，再跑工具，再用正确提示词把工具结果转成工程评审表。", 74, 586, 980, 28, { size: 20, bold: true, color: c.orange });
  notes(s, [
    "讲师提示：这一页先告诉学员文件在哪里。不要只展示 PPT，最好现场打开 CSV 和提示词。",
    "如果现场没有 Python，就直接打开 tool-output/check-result.csv，说明这是工具运行结果。",
  ]);

  s = p.slides.add();
  twoCols(s, 3, "错误例子：只问一句，AI 很难稳定工作", "这个例子看起来省事，但没有输入边界、检查规则和输出格式。", {
    head: "错误输入",
    body: "帮我看一下这个 IO 表有没有问题，给我一个结论。\n\n文件：prompts/wrong-prompt.txt\n输入：sample-io-table.csv",
    color: c.red,
    fill: "#FFF5F5",
  }, {
    head: "可能输出",
    body: "这个 IO 表整体基本可用，但建议检查重复地址和空字段。\n\n问题：没有证据、没有行号、没有责任岗位，也没有人工确认边界。",
    color: c.orange,
    fill: "#FFF7ED",
  }, [
    "讲师提示：错误例子不要让学员只看结论，要问：如果你是电控工程师，你能凭这个输出改表吗？通常不能。",
    "重点：AI 不是不能帮忙，而是任务定义太粗。",
  ]);

  s = p.slides.add();
  rows(s, 4, "错误例子的概念分析", "它缺少的不是“模型能力”，而是缺少工程化结构。", [
    ["大语言模型（LLM）", "只收到一句模糊请求", "只能猜用户想检查什么", "不能凭空知道部门规则"],
    ["技能（Skill）", "没有使用 SKILL.md", "没有固定检查顺序", "不能保证每次一致"],
    ["工具", "没有运行脚本", "没有确定性检查证据", "不能定位空字段和重复地址"],
    ["知识库", "没有引用 io-rules.md", "没有部门规则依据", "不能判断哪些需人工确认"],
    ["智能体（Agent）", "没有拆步骤", "没有读取、检查、汇总流程", "不能形成任务闭环"],
  ], ["讲师提示：这一页要把“错在哪里”讲具体，不要只说提示词不好。"]);

  s = p.slides.add();
  title(s, 5, "正确例子：先把任务拆成可执行步骤", "正确做法不是把问题问长，而是把输入、规则、工具、输出和人工确认点放清楚。");
  codeBlock(s, 70, 230, 330, 330, "步骤 1：准备输入", "打开：\ninput/sample-io-table.csv\n\n看字段：\nstation\ndevice\nsignal_type\naddress\ntag\ndescription", c.blue);
  codeBlock(s, 475, 230, 330, 330, "步骤 2：运行工具", "运行命令：\npython ...check_io_table.py ...sample-io-table.csv\n\n得到：\ntool-output/check-result.csv", c.green);
  codeBlock(s, 880, 230, 330, 330, "步骤 3：生成工程评审", "使用：\nprompts/correct-prompt.txt\nskill/SKILL.md\nio-rules.md\n\n输出：\nengineering-review.csv", c.orange);
  notes(s, [
    "讲师提示：这一页从流程角度讲，不要陷入技术细节。",
    "如果学员问模型上下文协议（MCP），这里先说：本例用本地脚本代表工具；在平台里接工具时，可以通过模型上下文协议（MCP）暴露类似能力。",
  ]);

  s = p.slides.add();
  title(s, 6, "正确例子的输入文件是真实可检查的", "这不是口头例子，CSV 中故意放了几个真实项目常见问题。");
  codeBlock(s, 70, 230, 530, 330, "sample-io-table.csv 关键行", [
    "2: ST10,CYL-01,DI,I0.0,ST10_CYL01_EXTENDED,...",
    "3: ST10,CYL-01,DI,I0.0,ST10_CYL01_EXTENDED_DUP,...",
    "5: ST10,CYL-01,DO,Q0.1,,Cylinder 01 retract solenoid",
    "10: ST20,SCANNER-01,DI,I1.2,ST20_SCAN_DONE,...",
    "11: ST20,SCANNER-01,DI,I1.2,ST20_SCAN_DONE,...",
    "12: ST20,ALARM-RESET,DI,,ST20_ALARM_RESET,...",
  ].join("\n"), c.blue);
  codeBlock(s, 670, 230, 500, 330, "这里埋了哪些问题", [
    "I0.0 地址重复",
    "第 5 行 tag 缺失",
    "I1.2 地址重复",
    "ST20_SCAN_DONE tag 重复",
    "第 12 行 address 缺失",
    "安全门、急停、报警复位需要人工确认完整性",
  ].join("\n"), c.red);
  notes(s, [
    "讲师提示：这一页让学员先自己找。先问：你能肉眼看到几个问题？再用工具跑一遍。",
    "强调：工具擅长确定性问题，人擅长工程判断。",
  ]);

  s = p.slides.add();
  title(s, 7, "工具输出给出可复核证据", "工具不负责工程判断，但它能稳定找出确定性问题。");
  codeBlock(s, 70, 220, 1080, 350, "运行结果 check-result.csv", [
    "issue_type,evidence,note",
    "missing_field,row 5:tag,Required field is blank.",
    "missing_field,row 12:address,Required field is blank.",
    "duplicate_address,I0.0,Rows [2, 3] share the same address.",
    "duplicate_address,I1.2,Rows [10, 11] share the same address.",
    "duplicate_tag,ST20_SCAN_DONE,Rows [10, 11] share the same tag.",
  ].join("\n"), c.green);
  text(s, "这一页对应：模型上下文协议（MCP）/工具。它像“检测仪器”，给 AI 提供证据，不替 AI 做最终判断。", 76, 596, 1040, 28, { size: 20, bold: true, color: c.green });
  notes(s, [
    "讲师提示：把这页讲成“工具和模型分工”。工具确定重复和空字段，模型负责把结果转成工程语言。",
    "注意说清：本地脚本是工具示例，不等于模型上下文协议（MCP）本身；模型上下文协议（MCP）是连接工具的一种方式。",
  ]);

  s = p.slides.add();
  title(s, 8, "技能（Skill）把检查经验写成流程", "有了技能（Skill），AI 不再每次凭感觉回答。");
  codeBlock(s, 70, 220, 520, 360, "SKILL.md 关键内容", [
    "1. 先用工具检查 CSV 的确定性问题。",
    "2. 再按规则检查工程风险。",
    "3. 输出时区分：",
    "   - 工具已经确定的问题",
    "   - 需要工程师确认的问题",
    "4. 不得把猜测写成事实。",
    "5. 最后给出是否建议进入下一步。",
  ].join("\n"), c.orange);
  codeBlock(s, 670, 220, 500, 360, "io-rules.md 关键内容", [
    "安全门、急停、复位、报警相关信号必须描述清楚。",
    "气缸类设备通常需要伸出、缩回、到位或原点信号。",
    "视觉、扫码设备应有完成、OK/NG、异常或超时处理逻辑。",
    "涉及安全和互锁必须人工确认。",
  ].join("\n"), c.purple);
  notes(s, [
    "讲师提示：这里区分技能（Skill）和知识库：技能（Skill）是怎么做，知识库是依据是什么。",
    "让学员指出：左边是技能（Skill），右边是知识库。",
  ]);

  s = p.slides.add();
  title(s, 9, "正确提示词把输入、规则、工具结果和输出格式讲清楚", "这才是能实际操作的提示词（Prompt），不是一句“帮我看看”。");
  codeBlock(s, 70, 220, 1080, 370, "correct-prompt.txt 摘要", [
    "输入：IO 表 CSV、工具检查结果、检查规则。",
    "任务：",
    "1. 先读取工具检查结果，只把工具已经确定的问题列为“确定问题”。",
    "2. 再根据检查规则补充“需要工程师确认的问题”。",
    "3. 不允许编造未在输入中出现的地址、tag、设备或工位。",
    "4. 输出字段：问题类型、证据、影响、建议处理、责任岗位、是否需要人工确认。",
    "人工确认边界：安全门、急停、复位、互锁、设备动作顺序必须由电控工程师确认。",
  ].join("\n"), c.blue);
  notes(s, [
    "讲师提示：让学员对比 wrong-prompt.txt 和 correct-prompt.txt。",
    "重点：正确提示词（Prompt）不是越长越好，而是关键输入和边界要完整。",
  ]);

  s = p.slides.add();
  title(s, 10, "正确输出必须能指导下一步动作", "工程输出不能只说“有问题”，要能让岗位人员复核和处理。");
  codeBlock(s, 70, 220, 1080, 366, "engineering-review.csv 摘要", [
    "确定问题：地址重复 | I0.0 出现在第 2 行和第 3 行 | PLC 地址冲突 | 确认 CYL-01 伸出到位地址 | 电控 | 是",
    "确定问题：tag 缺失 | 第 5 行 tag 为空 | 后续程序和调试记录无法引用 | 补充符合命名规则 tag | 电控 | 是",
    "确定问题：地址缺失 | 第 12 行 address 为空 | 报警复位按钮无法映射输入点 | 补充实际输入地址 | 电控 | 是",
    "需确认：安全相关信号完整性 | 有安全门和急停，但未看到安全复位说明 | 可能影响安全逻辑 | 由电控确认 | 电控/安全评审 | 是",
    "需确认：扫码异常处理 | 仅看到 SCAN_DONE | 异常流程可能无法识别 | 确认 NG、超时、通信异常信号 | 电控/软件 | 是",
  ].join("\n"), c.green);
  notes(s, [
    "讲师提示：这页强调输出质量。好的 AI 输出应该包含证据、影响、建议、责任岗位、人工确认。",
    "让学员判断：哪些是工具确定的，哪些是工程师确认的。",
  ]);

  s = p.slides.add();
  rows(s, 11, "正确例子的概念拆解", "每个名词都能在这个案例里找到实际位置。", [
    ["大语言模型（LLM）", "读取提示词、工具结果、规则", "转成工程语言和评审表", "不直接确认安全设计"],
    ["技能（Skill）", "skill/SKILL.md", "规定检查顺序、格式、边界", "不保存项目资料"],
    ["智能体（Agent）", "按课堂顺序执行步骤", "读表、调工具、查规则、生成输出", "不越权、不自动下发"],
    ["模型上下文协议（MCP）/工具", "check_io_table.py", "找空字段、重复地址、重复 tag", "不理解安全逻辑"],
    ["知识库", "io-rules.md", "提供检查依据和人工确认点", "不自动执行流程"],
    ["记忆（Memory）", "本例不强制使用", "可记部门输出偏好", "不记客户机密"],
    ["工作流（Workflow）", "README.txt 的课堂顺序", "把输入、工具、规则、输出串起来", "不跳过人工审核"],
  ], ["讲师提示：这是用户要求的“分析那个是哪部分”。建议让学员拿 concept-map.txt 对照看。"]);

  s = p.slides.add();
  title(s, 12, "课堂实际练习按这张清单验收", "练习结束时，不只看有没有结果，要看是否能复核、能落地。");
  codeBlock(s, 70, 230, 330, 320, "学员要做", [
    "1. 打开 IO 表。",
    "2. 找出肉眼能看到的问题。",
    "3. 运行工具或查看工具输出。",
    "4. 使用正确提示词生成评审表。",
    "5. 标出每一部分属于哪个概念。",
  ].join("\n"), c.blue);
  codeBlock(s, 475, 230, 330, 320, "讲师要看", [
    "是否列证据。",
    "是否区分确定问题和需确认问题。",
    "是否输出责任岗位。",
    "是否标注人工确认点。",
    "是否没有编造输入中不存在的信息。",
  ].join("\n"), c.green);
  codeBlock(s, 880, 230, 330, 320, "最终交付", [
    "一份工程评审表。",
    "一份概念拆解表。",
    "一条改进建议：",
    "把本岗位哪个任务做成技能（Skill）或工作流（Workflow）。",
  ].join("\n"), c.orange);
  notes(s, [
    "结尾提示：把这个案例讲透，比再增加十页概念更有效。",
    "课后可以让各岗位换自己的真实但脱敏文件，照这个流程再做一次。",
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
