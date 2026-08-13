import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const deck = await PresentationFile.importPptx(await FileBlob.load('./source.pptx'));
const chain = (obj) => {
  const out=[]; let cur=obj;
  for(let i=0;cur&&i<4;i++,cur=Object.getPrototypeOf(cur)) out.push(Object.getOwnPropertyNames(cur));
  return out;
};
console.log('slides', JSON.stringify(chain(deck.slides)));
console.log('slide', JSON.stringify(chain(deck.slides.items[0])));
console.log('notes', JSON.stringify(chain(deck.slides.items[0].notes)));
console.log('removeFn', deck.slides.remove.toString());
console.log('deleteFn', deck.slides.items[0].delete.toString());
console.log('moveToFn', deck.slides.items[0].moveTo.toString());
console.log('speakerNotes', deck.slides.items[0].speakerNotes);
console.log('speakerNotesProto', JSON.stringify(chain(deck.slides.items[0].speakerNotes)));
