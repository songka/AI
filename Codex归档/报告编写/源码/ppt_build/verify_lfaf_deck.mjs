import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const input = "C:/Users/lfaf-test/Documents/报告编写/LFAF小助手_AI大赛成果报告.pptx";
const outDir = "C:/Users/lfaf-test/Documents/报告编写/ppt_build/reimport_check";

async function main() {
  await fs.mkdir(outDir, { recursive: true });
  const deck = await PresentationFile.importPptx(await FileBlob.load(input));
  for (const [index, slide] of deck.slides.items.entries()) {
    const png = await deck.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(`${outDir}/slide-${String(index + 1).padStart(2, "0")}.png`, new Uint8Array(await png.arrayBuffer()));
  }
  const inspection = await deck.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 3000 });
  await fs.writeFile(`${outDir}/inspect.ndjson`, inspection.ndjson, "utf8");
  console.log(JSON.stringify({ slides: deck.slides.items.length, reimported: true }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
