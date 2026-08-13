import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const source = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\宋佳骥_晉升人評會報告.pptx";
const outDir = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\.codex-promotion-revision\\manual-inspect";

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

await fs.mkdir(outDir, { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
const snapshot = await presentation.inspect({
  kind: "deck,slide,textbox,shape,image,table,chart,notes,layout",
  include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,rows,cols,chartType,alt,isPlaceholder,placeholders",
  maxChars: 200000,
});
await fs.writeFile(path.join(outDir, "source-inspect.ndjson"), snapshot.ndjson, "utf8");

for (let index = 0; index < presentation.slides.items.length; index += 1) {
  const slide = presentation.slides.items[index];
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(outDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1.5 }));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(outDir, `${stem}.layout.json`), await layout.text(), "utf8");
}
await writeBlob(path.join(outDir, "source-montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 1 }));

const structure = {
  slideCount: presentation.slides.items.length,
  masters: presentation.masters.items.map((master) => ({
    id: master.id,
    name: master.name,
    placeholders: master.placeholders.summary(),
    elementCount: master.elements?.items?.length ?? master.elements?.length ?? 0,
  })),
  layouts: presentation.layouts.items.map((layout) => ({
    id: layout.id,
    name: layout.name,
    parentLayoutId: layout.parentLayoutId,
    placeholders: layout.placeholders.summary(),
  })),
};
await fs.writeFile(path.join(outDir, "structure.json"), JSON.stringify(structure, null, 2), "utf8");
console.log(JSON.stringify(structure, null, 2));
