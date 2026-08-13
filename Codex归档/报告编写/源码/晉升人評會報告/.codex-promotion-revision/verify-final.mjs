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

const source = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\宋佳骥_晉升人評會報告_口播稿優化版.pptx";
const outDir = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\.codex-promotion-revision\\reimport-qa";

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

await fs.mkdir(outDir, { recursive: true });
const finalSource = source.replace(/\.pptx$/i, "_R5.pptx");
const presentation = await PresentationFile.importPptx(await FileBlob.load(finalSource));
const snapshot = await presentation.inspect({
  kind: "deck,slide,textbox,shape,chart,notes,layout",
  include: "id,slide,name,title,textPreview,textChars,textLines,bbox,bboxUnit,chartType,isPlaceholder,placeholders",
  maxChars: 200000,
});
await fs.writeFile(path.join(outDir, "reimport-inspect.ndjson"), snapshot.ndjson, "utf8");

for (let index = 0; index < presentation.slides.items.length; index += 1) {
  const slide = presentation.slides.items[index];
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(outDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1.5 }));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(outDir, `${stem}.layout.json`), await layout.text(), "utf8");
}
console.log(JSON.stringify({ slideCount: presentation.slides.items.length, output: finalSource }));
