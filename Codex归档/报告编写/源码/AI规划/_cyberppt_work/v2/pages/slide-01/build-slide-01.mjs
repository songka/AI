import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/lfaf-test/Documents/报告编写/AI规划/_cyberppt_work/v2";
const OUT = path.join(ROOT, "pages/slide-01");
const ICONS = path.join(ROOT, "assets/icons-png");

const C = {
  bg: "#F7F6F0",
  navy: "#12355B",
  navy2: "#0A2D5E",
  ink: "#101820",
  body: "#303030",
  muted: "#6F7275",
  line: "#C9CDD1",
  pale: "#E9EDF2",
  white: "#FFFFFF"
};

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function iconPngBytes(name) {
  const png = await fs.readFile(path.join(ICONS, `${name}.png`));
  return png.buffer.slice(png.byteOffset, png.byteOffset + png.byteLength);
}

function addBox(slide, name, x, y, w, h, fill = "none", lineFill = "none", lineWidth = 0, radius = false) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
    ...(radius ? { borderRadius: "rounded-xl" } : {})
  });
}

function addText(slide, name, text, x, y, w, h, size, color, bold = false, align = "left", font = "Microsoft YaHei") {
  const shape = addBox(slide, name, x, y, w, h);
  shape.text = text;
  shape.text.style = { fontFamily: font, fontSize: size, color, bold, alignment: align };
  return shape;
}

function addLine(slide, name, x1, y1, x2, y2, color = C.navy, width = 2, dashed = false) {
  return slide.shapes.add({
    geometry: "line",
    name,
    position: { left: x1, top: y1, width: Math.max(0.5, x2 - x1), height: Math.max(0.5, y2 - y1) },
    fill: "none",
    line: { style: dashed ? "dash" : "solid", fill: color, width }
  });
}

function addEllipse(slide, name, x, y, w, h, fill = "none", lineFill = C.navy, lineWidth = 1) {
  return slide.shapes.add({
    geometry: "ellipse",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth }
  });
}

async function addIcon(slide, name, icon, x, y, w, h) {
  slide.images.add({
    name,
    blob: await iconPngBytes(icon),
    contentType: "image/png",
    alt: name,
    fit: "contain",
    position: { left: x, top: y, width: w, height: h }
  });
}

async function main() {
  await fs.mkdir(path.join(OUT, "render"), { recursive: true });
  await fs.mkdir(path.join(OUT, "qa"), { recursive: true });

  const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  const slide = deck.slides.add();
  slide.background.fill = C.bg;

  // Header.
  addText(slide, "header-left", "AI 赋能工程能力   |   内部框架规划", 32, 25, 252, 19, 13, C.navy, false);
  addText(slide, "header-right", "先形成可用闭环，持续演进优化", 1055, 24, 198, 19, 11, C.navy, false, "right");
  addBox(slide, "header-rule", 32, 47, 1216, 1.5, C.navy);

  // Left title block.
  addText(slide, "page-title", "内部 AI 框架与五类\nSkill 建设规划", 67, 230, 548, 140, 55, C.navy2, true);
  addText(slide, "subtitle", "以 SMB 公共槽共享工程能力，\n先形成可用闭环，再逐步完善治理", 70, 404, 470, 64, 26, C.body, false);
  addBox(slide, "title-accent", 72, 497, 68, 4, C.navy);
  addText(slide, "report-date", "老板汇报版   |   2026年7月", 71, 531, 209, 22, 15, C.body, false);

  // Technical orbit and subtle engineering hints.
  addEllipse(slide, "orbit-outer", 737, 145, 395, 420, "none", "#A8BDD0", 1);
  addEllipse(slide, "orbit-mid", 844, 248, 203, 203, "none", "#A8BDD0", 1);
  addEllipse(slide, "orbit-inner", 862, 266, 167, 167, "none", C.navy, 1.2);
  addLine(slide, "orbit-v", 936, 136, 936.5, 578, "#D1D9DF", 1, true);
  addLine(slide, "orbit-h", 604, 349, 1180, 349.5, "#D1D9DF", 1, true);
  await addIcon(slide, "decor-robot", "robot", 1103, 116, 84, 84);
  await addIcon(slide, "decor-cpu", "cpu", 1131, 501, 76, 76);
  await addIcon(slide, "decor-settings", "settings", 1040, 535, 64, 64);

  // Three personal PC nodes.
  const pcs = [184, 301, 420];
  for (let i = 0; i < pcs.length; i++) {
    const y = pcs[i];
    addBox(slide, `pc-group-${i + 1}`, 656, [184, 301, 419][i], 113, 106);
    await addIcon(slide, `pc-icon-${i + 1}`, "device-laptop", 660, y, 92, 64);
    addText(slide, `pc-label-${i + 1}`, "个人 PC", 666, y + 65, 80, 18, 13, C.navy, false, "center");
    addEllipse(slide, `pc-node-${i + 1}`, 757, y + 48, 10, 10, C.navy, C.navy, 1);
  }

  // Right-angle PC connectors into DeepSeek.
  addBox(slide, "pc-connectors-group", 752, 230, 116, 247);
  addLine(slide, "pc1-h", 767, 237, 812, 237, C.navy, 1.5);
  addLine(slide, "pc1-v", 812, 237, 812.5, 331, C.navy, 1.5);
  addLine(slide, "pc1-join", 812, 331, 858, 331.5, C.navy, 1.5);
  addLine(slide, "pc2-h", 767, 349, 858, 349.5, C.navy, 1.5);
  addLine(slide, "pc3-h", 767, 473, 812, 473, C.navy, 1.5);
  addLine(slide, "pc3-v", 812, 367, 812.5, 473, C.navy, 1.5);
  addLine(slide, "pc3-join", 812, 367, 858, 367.5, C.navy, 1.5);
  for (const [n, yy] of [[1,331],[2,349],[3,367]]) addEllipse(slide, `join-${n}`, 854, yy - 4, 8, 8, C.navy, C.navy, 1);

  // DeepSeek native core with editable label.
  addBox(slide, "deepseek-group", 845, 282, 163, 163);
  addEllipse(slide, "deepseek-halo", 845, 282, 163, 163, "none", "#7D9AB5", 1);
  addEllipse(slide, "deepseek-core", 862, 299, 129, 129, C.bg, C.navy, 1.4);
  await addIcon(slide, "deepseek-brain", "brain", 895, 315, 62, 62);
  addText(slide, "deepseek-label", "DeepSeek", 862, 382, 129, 26, 18, C.navy2, true, "center", "Arial");
  addEllipse(slide, "deepseek-out-node", 986, 344, 10, 10, C.navy, C.navy, 1);

  // DeepSeek to SMB connection.
  addLine(slide, "deepseek-smb-line", 996, 349, 1051, 349.5, C.navy, 2);
  addEllipse(slide, "smb-line-node", 1036, 344, 10, 10, C.navy, C.navy, 1);

  // SMB Skill public share, native container + editable text.
  addBox(slide, "smb-group", 1051, 260, 190, 182);
  addBox(slide, "smb-shadow", 1051, 260, 190, 182, "#E7E9EA", "#BBC3C9", 1, true);
  await addIcon(slide, "smb-folders", "folders", 1079, 274, 136, 72);
  addBox(slide, "smb-label-panel", 1066, 346, 160, 76, C.bg, "#AAB6C0", 1, true);
  addText(slide, "smb-label", "SMB Skill\n公共槽", 1080, 358, 132, 52, 20, C.navy2, true, "center");
  addEllipse(slide, "share-circle", 1190, 394, 48, 48, C.bg, C.navy, 1);
  await addIcon(slide, "share-icon", "share-3", 1200, 404, 28, 28);

  // Invisible registration boundaries for grouped blueprint elements.
  addBox(slide, "orbit-group", 737, 145, 395, 420);
  addBox(slide, "robot-group", 1101, 111, 117, 107);
  addBox(slide, "plc-gears-group", 1036, 481, 178, 126);

  // Footer.
  addBox(slide, "footer-rule", 32, 662, 1216, 1.5, C.navy);
  addText(slide, "footer-source", "来源：内部规划与工程实践   |   仅供内部汇报使用", 34, 678, 283, 18, 11, C.muted, false);
  addBox(slide, "page-badge", 1175, 673, 67, 26, C.navy2, C.navy2, 1, true);
  addText(slide, "page-number", "01", 1175, 673, 67, 26, 12, C.white, true, "center", "Arial");

  const preview = await deck.export({ slide, format: "png", scale: 2 });
  await writeBlob(path.join(OUT, "render/slide-01-artifact.png"), preview);
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(OUT, "render/slide-01.layout.json"), await layout.text());
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(path.join(OUT, "slide-01.pptx"));
}

main().catch((err) => {
  fs.writeFile(path.join(OUT, "build-error.txt"), String(err?.stack || err), "utf8").catch(() => {});
  console.error(err);
  process.exitCode = 1;
});
