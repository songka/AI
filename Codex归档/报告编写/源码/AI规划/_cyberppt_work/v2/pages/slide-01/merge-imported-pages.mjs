import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/lfaf-test/Documents/报告编写/AI规划/_cyberppt_work/v2";
const FINAL = "C:/Users/lfaf-test/Documents/报告编写/AI规划/内部AI框架与五类Skill建设规划_老板汇报精简版.pptx";
const RENDER = path.join(ROOT,"final-render");

function uniqueMerge(target, incoming){
  const seen=new Set(target.map((x,i)=>String(x?.id??x?.layoutId??x?.assetId??x?.name??i)));
  for(const x of incoming??[]){ const k=String(x?.id??x?.layoutId??x?.assetId??x?.name??JSON.stringify(x).slice(0,120)); if(!seen.has(k)){target.push(x);seen.add(k);} }
}
async function writeBlob(p,blob){ await fs.mkdir(path.dirname(p),{recursive:true}); await fs.writeFile(p,new Uint8Array(await blob.arrayBuffer())); }

const protos=[];
for(let n=1;n<=7;n++){
  const s=`slide-${String(n).padStart(2,"0")}`;
  const file=path.join(ROOT,"pages",s,`${s}.pptx`);
  const imported=await PresentationFile.importPptx(await FileBlob.load(file));
  protos.push(imported.toProto());
}

const merged=structuredClone(protos[0]);
merged.slides=[];
for(const key of ["layouts","charts","images","contentReferences","fonts","textStyles","people","threads"]) merged[key]=[];
for(const proto of protos){
  merged.slides.push(...proto.slides);
  for(const key of ["layouts","charts","images","contentReferences","fonts","textStyles","people","threads"]) uniqueMerge(merged[key],proto[key]);
}

const deck=Presentation.load(merged);
if(deck.slides.items.length!==7) throw new Error(`Expected 7 slides, got ${deck.slides.items.length}`);
await fs.mkdir(RENDER,{recursive:true});
for(const [i,slide] of deck.slides.items.entries()){
  const png=await deck.export({slide,format:"png",scale:1});
  await writeBlob(path.join(RENDER,`slide-${String(i+1).padStart(2,"0")}.png`),png);
}
const montage=await deck.export({format:"webp",montage:true,scale:1});
await writeBlob(path.join(RENDER,"montage.webp"),montage);
const pptx=await PresentationFile.exportPptx(deck);
await pptx.save(FINAL);
await fs.writeFile(path.join(ROOT,"final_merge_manifest.json"),JSON.stringify({method:"merge_imported_single_page_pptx",source_single_page_pptx:Array.from({length:7},(_,i)=>{const s=`slide-${String(i+1).padStart(2,"0")}`;return path.join(ROOT,"pages",s,`${s}.pptx`)}),regenerated_pages:false,merged_slide_count:7,output:FINAL},null,2),"utf8");
console.log(FINAL);
