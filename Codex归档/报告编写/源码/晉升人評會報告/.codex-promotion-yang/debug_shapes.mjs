import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const deck = await PresentationFile.importPptx(
  await FileBlob.load("C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\.codex-promotion-yang\\template-starter.pptx"),
);

for (let slideIndex = 0; slideIndex < 2; slideIndex += 1) {
  console.log(`SLIDE ${slideIndex + 1}`);
  for (const [index, shape] of deck.slides.items[slideIndex].shapes.items.entries()) {
    console.log(index, shape.name, typeof shape.text, Object.keys(shape.text ?? {}).slice(0, 8), String(shape.text ?? "").slice(0, 80));
  }
}
