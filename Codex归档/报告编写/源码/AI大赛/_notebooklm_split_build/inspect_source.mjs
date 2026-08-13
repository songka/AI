import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const source = fileURLToPath(new URL('./source.pptx', import.meta.url));
const outDir = fileURLToPath(new URL('./source-artifact-render/', import.meta.url));
await fs.mkdir(outDir, { recursive: true });
const deck = await PresentationFile.importPptx(await FileBlob.load(source));
const inspection = await deck.inspect({kind:'slide,textbox,shape,image,notes,layout',maxChars:200000});
await fs.writeFile(new URL('./source-inspect.ndjson', import.meta.url), inspection.ndjson, 'utf8');
for (const [i, slide] of deck.slides.items.entries()) {
  const png = await deck.export({slide, format:'png', scale:1});
  await fs.writeFile(`${outDir}slide-${String(i+1).padStart(2,'0')}.png`, new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({format:'layout'});
  await fs.writeFile(`${outDir}slide-${String(i+1).padStart(2,'0')}.layout.json`, await layout.text(), 'utf8');
}
const montage = await deck.export({format:'webp',montage:true,scale:1});
await fs.writeFile(new URL('./source-montage.webp', import.meta.url), new Uint8Array(await montage.arrayBuffer()));
console.log(`slides=${deck.slides.items.length}`);
console.log(deck.help('*',{search:'slides remove delete collection',include:['index','notes'],maxChars:5000}));
