import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const ROOT = process.cwd().replaceAll("\\", "/");
const PACKAGE = `${ROOT}/outputs/${"\u0041\u0049\u002d\u0053\u006b\u0069\u006c\u006c\u57f9\u8bad\u6700\u7ec8\u4ea4\u4ed8\u5305"}`;
const ASSET_DIR = `${PACKAGE}/assets`;
const PPT_DIR = `${PACKAGE}/ppt`;
const PREVIEW = `${ROOT}/work/presentations/skill-training/tmp/preview/final-cartoon-package`;
const SRC_IMAGE = "C:/Users/lfaf-test/.codex/generated_images/019f257b-fd9e-77b3-bac4-6d1ffd199e4e/ig_0637a9c637050a05016a4b3b1440708191a063ba6f7bb64eb4.png";
const CARTOON = `${ASSET_DIR}/cartoon-ai-classroom.png`;

const expectedPrefixes = ["07-", "08-", "09-", "10-", "11-", "12-", "13-"];
const revised = "\u4fee\u8ba2\u7248";
const lively = "\u6d3b\u6cfc\u7248";
const chineseVersion = "\u4e2d\u6587\u5316\u7248";
const notes = "\u5e26\u8bb2\u5e08\u5907\u6ce8";

async function ensureCleanDir(dir) {
  await fs.rm(dir, { recursive: true, force: true });
  await fs.mkdir(dir, { recursive: true });
}

async function findFinalDecks() {
  const files = await fs.readdir(`${ROOT}/outputs`);
  return expectedPrefixes.map((prefix) => {
    const matches = files
      .filter((name) => name.startsWith(prefix) && name.endsWith(".pptx") && name.includes(notes))
      .filter((name) => {
        if (prefix === "13-") return name.includes(chineseVersion);
        return name.includes(revised);
      })
      .sort();
    if (matches.length === 0) {
      throw new Error(`Missing deck for prefix ${prefix}`);
    }
    const srcName = matches[matches.length - 1];
    const outName = srcName.includes(revised)
      ? srcName.replace(revised, lively)
      : srcName.replace(notes, `${lively}-${notes}`);
    return [srcName, outName];
  });
}

async function imageBytes(file) {
  const bytes = await fs.readFile(file);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function addCartoonToDeck(srcName, outName) {
  const ppt = await PresentationFile.importPptx(await FileBlob.load(`${ROOT}/outputs/${srcName}`));
  const cartoon = await imageBytes(CARTOON);
  const first = ppt.slides.items[0];
  first.images.add({
    blob: cartoon,
    contentType: "image/png",
    alt: "\u0041\u0049\u8bfe\u7a0b\u5361\u901a\u8bfe\u5802\u573a\u666f",
    fit: "cover",
    position: { left: 955, top: 82, width: 220, height: 176 },
  });
  const out = await PresentationFile.exportPptx(ppt);
  await out.save(`${PPT_DIR}/${outName}`);

  const png = await ppt.export({ slide: first, format: "png", scale: 1 });
  await fs.writeFile(`${PREVIEW}/${outName.replace(/\.pptx$/, "")}-cover.png`, new Uint8Array(await png.arrayBuffer()));
}

async function copyDir(src, dest) {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });
  for (const entry of entries) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      await copyDir(s, d);
    } else {
      await fs.copyFile(s, d);
    }
  }
}

async function main() {
  await ensureCleanDir(PACKAGE);
  await fs.mkdir(ASSET_DIR, { recursive: true });
  await fs.mkdir(PPT_DIR, { recursive: true });
  await ensureCleanDir(PREVIEW);
  await fs.copyFile(SRC_IMAGE, CARTOON);

  const decks = await findFinalDecks();
  for (const [src, out] of decks) {
    await addCartoonToDeck(src, out);
  }

  await copyDir(`${ROOT}/outputs/skill-examples-cn`, `${PACKAGE}/skill-examples-cn`);
  await copyDir(`${ROOT}/outputs/ai-practice-cases/io-table-demo-cn`, `${PACKAGE}/practice-cases/io-table-demo-cn`);
  console.log(`Built ${decks.length} decks in ${PACKAGE}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
