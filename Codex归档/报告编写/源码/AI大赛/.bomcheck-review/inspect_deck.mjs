import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspace = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\.bomcheck-review";
const source = path.join(workspace, "source.pptx");
const outDir = path.join(workspace, "inspect");

async function saveBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(outDir, { recursive: true });
  const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
  const snapshot = await presentation.inspect({
    kind: "deck,slide,textbox,shape,image,table,chart,notes,layout",
    include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,isPlaceholder,alt,placeholders",
    maxChars: 200000,
  });
  await fs.writeFile(path.join(outDir, "inspect.ndjson"), snapshot.ndjson, "utf8");

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await saveBlob(path.join(outDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(outDir, `${stem}.layout.json`), await layout.text(), "utf8");
  }

  await saveBlob(
    path.join(outDir, "montage.webp"),
    await presentation.export({ format: "webp", montage: true, scale: 0.7 }),
  );
  console.log(JSON.stringify({ slides: presentation.slides.items.length, outDir }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
