import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "C:/Users/lfaf-test/Documents/测试/outputs/04-Skill实际案例与文件结构解析.pptx";
const PREVIEW = "C:/Users/lfaf-test/Documents/测试/work/presentations/skill-training/tmp/preview/04-examples";
const W = 1280;
const H = 720;
const c = { ink: "#111111", muted: "#555555", panel: "#EFEFEF", rule: "#B8BCC4", orange: "#FF6B35", green: "#059669", blue: "#2563EB" };

function deck() { return Presentation.create({ slideSize: { width: W, height: H } }); }
function shape(slide, x, y, w, h, fill = "#FFFFFF", line = c.rule) {
  return slide.shapes.add({ geometry: "rect", position: { left: x, top: y, width: w, height: h }, fill, line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 } });
}
function txt(slide, value, x, y, w, h, o = {}) {
  const s = slide.shapes.add({ geometry: "textbox", position: { left: x, top: y, width: w, height: h }, fill: "none", line: { style: "solid", fill: "none", width: 0 } });
  s.text = value;
  s.text.style = { fontSize: o.size ?? 22, bold: o.bold ?? false, color: o.color ?? c.ink, alignment: o.align ?? "left", fontFace: "Microsoft YaHei" };
}
function foot(slide, n) {
  txt(slide, "课程四｜实际案例与文件结构解析", 54, 30, 430, 26, { size: 15, bold: true, color: c.muted });
  txt(slide, String(n).padStart(2, "0"), 1184, 674, 42, 24, { size: 14, color: c.muted, align: "right" });
}
function title(slide, v, sub) {
  shape(slide, 54, 42, 1172, 6, c.ink, "none");
  txt(slide, "课程四｜实际案例与文件结构解析", 54, 96, 520, 32, { size: 20, bold: true, color: c.orange });
  txt(slide, v, 54, 170, 860, 138, { size: 54, bold: true });
  txt(slide, sub, 54, 385, 760, 70, { size: 26, color: c.muted });
  shape(slide, 900, 170, 250, 250, c.panel, "none");
  shape(slide, 940, 215, 250, 250, "#FFFFFF", c.ink);
  txt(slide, "SKILL.md", 970, 300, 200, 54, { size: 38, bold: true, align: "center" });
  txt(slide, "结构 + 内容", 970, 370, 200, 30, { size: 18, color: c.muted, align: "center" });
}
function bullets(slide, titleText, items, n) {
  foot(slide, n);
  txt(slide, titleText, 54, 78, 1050, 58, { size: 40, bold: true });
  items.forEach((it, i) => {
    const y = 176 + i * 92;
    txt(slide, `0${i + 1}`, 54, y + 3, 60, 34, { size: 26, bold: true, color: c.orange });
    txt(slide, it.head, 140, y, 360, 34, { size: 24, bold: true });
    txt(slide, it.body, 520, y + 2, 620, 42, { size: 20, color: c.muted });
    shape(slide, 140, y + 62, 920, 1, c.rule, "none");
  });
}
function columns(slide, titleText, cols, n) {
  foot(slide, n);
  txt(slide, titleText, 54, 78, 1050, 58, { size: 40, bold: true });
  cols.forEach((col, i) => {
    const x = 54 + i * 292;
    shape(slide, x, 190, 260, 350, i % 2 ? "#F8F8F8" : "#FFFFFF", c.rule);
    shape(slide, x, 190, 260, 8, col.color ?? c.orange, "none");
    txt(slide, col.head, x + 20, 222, 220, 46, { size: 23, bold: true });
    txt(slide, col.body, x + 20, 292, 220, 170, { size: 18, color: c.muted });
    txt(slide, col.foot, x + 20, 480, 220, 30, { size: 16, bold: true, color: col.color ?? c.orange });
  });
}
function codeSlide(slide, n, titleText, left, right) {
  foot(slide, n);
  txt(slide, titleText, 54, 76, 1050, 58, { size: 39, bold: true });
  shape(slide, 54, 166, 520, 430, "#111111", "#111111");
  txt(slide, left, 78, 190, 472, 370, { size: 18, color: "#FFFFFF" });
  shape(slide, 620, 166, 560, 430, "#F3F3F3", "none");
  txt(slide, right, 650, 198, 500, 350, { size: 22, color: c.ink });
}
function table(slide, titleText, rows, n) {
  foot(slide, n);
  txt(slide, titleText, 54, 78, 1050, 58, { size: 40, bold: true });
  const widths = [250, 290, 310, 300], x0 = 54, y0 = 172;
  ["文件/目录", "作用", "什么时候读取", "课堂讲法"].forEach((h, i) => {
    const x = x0 + widths.slice(0, i).reduce((a, b) => a + b, 0);
    shape(slide, x, y0, widths[i], 52, c.ink, c.ink);
    txt(slide, h, x + 14, y0 + 14, widths[i] - 28, 24, { size: 17, bold: true, color: "#FFFFFF" });
  });
  rows.forEach((r, ri) => {
    const y = y0 + 52 + ri * 76;
    r.forEach((cell, ci) => {
      const x = x0 + widths.slice(0, ci).reduce((a, b) => a + b, 0);
      shape(slide, x, y, widths[ci], 76, ri % 2 ? "#FAFAFA" : "#FFFFFF", c.rule);
      txt(slide, cell, x + 14, y + 12, widths[ci] - 28, 48, { size: 16, color: ci === 0 ? c.ink : c.muted, bold: ci === 0 });
    });
  });
}

async function main() {
  const p = deck();
  let s = p.slides.add(); title(s, "从建立 Skill 到解析文件结构", "用 4 个非标自动化部门样例做课堂演示");
  s = p.slides.add(); bullets(s, "实际建立 Skill 的六步", [
    { head: "选任务", body: "选择高频、稳定、有验收标准的工作。" },
    { head: "定边界", body: "写清什么时候用、什么时候不能用。" },
    { head: "建目录", body: "创建 skill-name/SKILL.md 和可选资源目录。" },
    { head: "写流程", body: "把岗位经验拆成输入、步骤、输出和验收。" },
    { head: "放资源", body: "模板进 assets，规则进 references，确定性处理进 scripts。" },
    { head: "验证迭代", body: "用真实提示词和真实样例测试触发与结果。" },
  ], 2);
  s = p.slides.add(); columns(s, "本次补充的四个可打开示例", [
    { head: "scheme-review", body: "根据 URS、工艺流程和会议记录生成方案评审问题清单。", foot: "适合方案工程师/PM", color: c.orange },
    { head: "io-table-review", body: "检查 IO 表重复地址、空字段、命名和安全互锁风险。", foot: "适合电控工程师", color: c.blue },
    { head: "project-doc-archive", body: "整理项目资料目录、缺失文件和待办跟进清单。", foot: "适合文职/PMO", color: c.green },
    { head: "validation-doc-check", body: "检查验证资料、URS 追溯、签名日期和偏差闭环。", foot: "适合质量/生物管", color: c.orange },
  ], 3);
  s = p.slides.add(); table(s, "一个 Skill 文件夹通常这样拆", [
    ["SKILL.md", "核心说明和执行流程", "Skill 被触发后", "像岗位 SOP 的首页"],
    ["agents/openai.yaml", "界面名称、默认提示、隐式触发策略", "系统/UI 使用", "像技能名片"],
    ["references/", "详细规则、术语、检查标准", "任务需要细节时", "像部门制度和检查表"],
    ["assets/", "模板、样表、格式文件", "生成输出或复制模板时", "像标准表单"],
    ["scripts/", "确定性检查或批处理", "有文件可自动检查时", "像小工具"],
  ], 4);
  s = p.slides.add(); codeSlide(s, 5, "SKILL.md 的 frontmatter 决定 Skill 会不会被叫醒",
`---
name: io-table-review
description: Use when checking automation IO tables,
point lists, PLC tag exports...
---

# IO Table Review

Use this skill to review IO table quality before
electrical design review or PLC software handoff.`,
`name:
必须简短、唯一、只用小写字母数字和短横线。

description:
最重要。要写清触发场景、任务边界、输入类型和禁用场景。

正文:
只有触发后才会读取，所以不要把触发条件只写在正文里。`);
  s = p.slides.add(); codeSlide(s, 6, "SKILL.md 正文要写“做事顺序”，不要写空泛原则",
`## Workflow

1. If the user provides a CSV IO table, run
   scripts/check_io_table.py first.
2. Read references/io-rules.md.
3. Inspect by station, device, signal type,
   address, tag name, and description.
4. Group findings into duplicates, missing fields,
   naming issues, signal mismatches...
5. Output a review table.
6. End with a readiness status.`,
`课堂解析:
这段让 AI 先做确定性检查，再做工程判断。

好的正文有三个特点:
1. 顺序清楚
2. 输入输出清楚
3. 验收状态清楚`);
  s = p.slides.add(); table(s, "示例一：scheme-review 的文件内容", [
    ["SKILL.md", "定义方案评审任务和输出表格", "收到 URS/工艺流程/会议纪要", "先问清项目边界"],
    ["references/review-rules.md", "列过程、机构、电控、软件、交付风险", "生成评审清单前", "把老工程师经验写进去"],
    ["assets/review-checklist-template.csv", "固定输出字段", "要生成表格时", "让结果能直接进 Excel"],
  ], 7);
  s = p.slides.add(); table(s, "示例二：io-table-review 为什么加 scripts", [
    ["scripts/check_io_table.py", "查空字段、重复地址、重复 tag", "有 CSV IO 表时", "确定性问题交给脚本"],
    ["references/io-rules.md", "命名、信号类型和安全问题规则", "做工程判断时", "经验判断交给参考规则"],
    ["assets/sample-io-table.csv", "课堂演示用样例 IO 表", "上课演示时", "现场跑给大家看"],
  ], 8);
  s = p.slides.add(); codeSlide(s, 9, "IO 表脚本演示结果",
`输入样例:
ST10 CYL-01 DI I0.0 ST10_CYL01_EXTENDED
ST10 CYL-01 DI I0.0 ST10_CYL01_EXTENDED_DUP
ST20 Door   DI I1.0 [blank tag]

脚本输出:
missing_field,row 5:tag
duplicate_address,I0.0,Rows [3, 4] share the same address.`,
`解析:
脚本不理解项目方案，但能稳定抓重复和空字段。

Skill 再把脚本结果转成工程语言:
影响、优先级、责任人、建议动作。`);
  s = p.slides.add(); table(s, "示例三：project-doc-archive 的文件内容", [
    ["SKILL.md", "组织资料、缺失清单和行动跟踪", "收到会议纪要/项目资料", "先统一归档口径"],
    ["references/archive-rules.md", "项目阶段和必备文件清单", "判断资料缺失时", "让文职工作有标准"],
    ["assets/archive-structure-template.txt", "标准文件夹结构", "生成目录建议时", "减少每个项目重新想"],
  ], 10);
  s = p.slides.add(); table(s, "示例四：validation-doc-check 的文件内容", [
    ["SKILL.md", "验证包预检查流程和边界", "收到 URS/FAT/SAT/测试记录", "只做预检查，不做最终放行"],
    ["references/validation-rules.md", "完整性、签名、版本、追溯规则", "检查质量缺口时", "把质量关注点显性化"],
    ["assets/validation-issue-template.csv", "问题严重度和整改字段", "输出问题清单时", "便于复核和跟进"],
  ], 11);
  s = p.slides.add(); bullets(s, "课堂最后可以这样带练习", [
    { head: "打开文件树", body: "先看每个 Skill 只有少量必要文件，没有 README 和杂项。" },
    { head: "读 description", body: "让学员判断什么请求会触发，什么请求不该触发。" },
    { head: "读 Workflow", body: "看 AI 被要求先做什么、再做什么、最后交什么。" },
    { head: "读 references", body: "说明为什么细规则不都塞进 SKILL.md。" },
    { head: "跑脚本", body: "用 sample-io-table.csv 展示确定性检查的价值。" },
    { head: "改一个字段", body: "让学员现场添加一个本部门真实检查项。" },
  ], 12);
  s = p.slides.add(); bullets(s, "判断一个 Skill 是否合格", [
    { head: "能触发", body: "description 覆盖真实说法，不会过宽或过窄。" },
    { head: "能执行", body: "Workflow 是动作，不是口号。" },
    { head: "能复核", body: "输出字段稳定，能看见依据和假设。" },
    { head: "有边界", body: "清楚哪些事情必须人工确认。" },
    { head: "能迭代", body: "真实项目反馈可以写回 references 或 SKILL.md。" },
  ], 13);

  await fs.mkdir(PREVIEW, { recursive: true });
  for (const [i, slide] of p.slides.items.entries()) {
    const png = await p.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(PREVIEW, `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
  }
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
