import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/lfaf-test/Documents/测试";
const SRC_DIR = `${ROOT}/outputs/AI-Skill培训最终交付包/ppt`;
const OUT_DIR = `${ROOT}/outputs/PPT-projector`;
const PREVIEW_DIR = `${ROOT}/work/presentations/projector-convert/tmp/preview`;

const SOURCE_W = 12192000;
const SOURCE_H = 6858000;
const TARGET_W = 9144000;
const TARGET_H = 6858000;
const X_SCALE = TARGET_W / SOURCE_W;

function scaleBbox(box) {
  if (!box) return;
  if (typeof box.xEmu === "number") box.xEmu = Math.round(box.xEmu * X_SCALE);
  if (typeof box.widthEmu === "number") box.widthEmu = Math.round(box.widthEmu * X_SCALE);
}

function scaleElement(element) {
  scaleBbox(element.bbox);
  if (Array.isArray(element.children)) {
    for (const child of element.children) scaleElement(child);
  }
}

function adaptProtoForProjector(proto) {
  for (const slide of proto.slides ?? []) {
    slide.widthEmu = TARGET_W;
    slide.heightEmu = TARGET_H;
    for (const element of slide.elements ?? []) scaleElement(element);
  }
  const cover = proto.slides?.[0];
  const coverCartoon = cover?.elements?.find((element) =>
    element.type === 7 && element.imageReference?.id === "/ppt/media/image.png" && element.bbox,
  );
  if (coverCartoon) {
    coverCartoon.bbox.xEmu = 7429500; // x=780px on 960x720 4:3 render
    coverCartoon.bbox.yEmu = 714375; // y=75px
    coverCartoon.bbox.widthEmu = 1333500; // width=140px
    coverCartoon.bbox.heightEmu = 1066800; // height=112px, keeps the image away from long titles
  }
  for (const layout of proto.layouts ?? []) {
    layout.widthEmu = TARGET_W;
    layout.heightEmu = TARGET_H;
    for (const element of layout.elements ?? []) scaleElement(element);
  }
  return proto;
}

async function writeBlob(file, blob) {
  await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer()));
}

async function convertDeck(srcName) {
  const presentation = await PresentationFile.importPptx(await FileBlob.load(`${SRC_DIR}/${srcName}`));
  const proto = adaptProtoForProjector(presentation.toProto());
  const projected = Presentation.load(proto);
  const outName = srcName.replace(".pptx", "-投影版-4比3.pptx");
  const outPath = `${OUT_DIR}/${outName}`;

  const exported = await PresentationFile.exportPptx(projected);
  await exported.save(outPath);

  const inspect = await projected.inspect({
    kind: "slide,textbox,shape,image,table,chart,notes,layout",
    maxChars: 120000,
  });
  await fs.writeFile(`${outPath}.inspect.ndjson`, inspect.ndjson);

  const stem = outName.replace(/\.pptx$/, "");
  const deckPreviewDir = `${PREVIEW_DIR}/${stem}`;
  await fs.mkdir(deckPreviewDir, { recursive: true });
  for (const [i, slide] of projected.slides.items.entries()) {
    const png = await projected.export({ slide, format: "png", scale: 1 });
    await writeBlob(`${deckPreviewDir}/slide-${String(i + 1).padStart(2, "0")}.png`, png);
  }
  const montage = await projected.export({ format: "webp", montage: true, scale: 0.45 });
  await writeBlob(`${PREVIEW_DIR}/${stem}-montage.webp`, montage);
  return outPath;
}

async function main() {
  await fs.rm(OUT_DIR, { recursive: true, force: true });
  await fs.rm(PREVIEW_DIR, { recursive: true, force: true });
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });

  const entries = (await fs.readdir(SRC_DIR))
    .filter((name) => name.endsWith(".pptx"))
    .sort();

  const outputs = [];
  for (const entry of entries) {
    outputs.push(await convertDeck(entry));
  }

  await fs.writeFile(
    `${OUT_DIR}/说明.txt`,
    [
      "PPT-projector 投影版说明",
      "",
      "用途：适配 1024x768 投影仪，页面比例改为 4:3。",
      "处理方式：基于最终活泼版 7 份 PPT 生成投影版，保留讲师备注、中文内容和卡通图片。",
      "显示建议：投影时选择“适合窗口/全屏放映”，不要再强制宽屏 16:9。",
      "",
      "文件：",
      ...outputs.map((file) => `- ${path.basename(file)}`),
      "",
    ].join("\r\n"),
    "utf8",
  );
  console.log(`Converted ${outputs.length} projector decks to ${OUT_DIR}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
