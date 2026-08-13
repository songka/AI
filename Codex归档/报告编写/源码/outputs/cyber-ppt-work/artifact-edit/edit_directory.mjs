import fs from 'node:fs/promises';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const input = 'C:/Users/lfaf-test/Documents/报告编写/outputs/视觉无序抓取_电气技术汇报_完整评审稿_R004.pptx';
const output = 'C:/Users/lfaf-test/Documents/报告编写/outputs/视觉无序抓取_电气技术汇报_目录优化_R005.pptx';
const work = 'C:/Users/lfaf-test/Documents/报告编写/outputs/cyber-ppt-work/artifact-edit';

const photoPaths = [
  'C:/Users/lfaf-test/Documents/报告编写/自建三轴铁件产品.jpg',
  'C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/visual-random-pick-weekly/tmp/assets/four-axis-thumb.png',
  'C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/visual-random-pick-weekly/tmp/assets/conveyor-thumb.png',
  'C:/Users/lfaf-test/Documents/报告编写/outputs/视觉无序抓取_素材/自建三轴_屏蔽机器人.png',
];

const p = await PresentationFile.importPptx(await FileBlob.load(input));
const s = p.slides.items[1];
await fs.writeFile(`${work}/before-slide2.png`, new Uint8Array(await (await p.export({slide:s,format:'png',scale:1.5})).arrayBuffer()));

// Preserve only the inherited company title/chrome/footer objects.
const keepShapes = new Set(['sh/9072xkry','sh/ozy1ofad','sh/b29kza94','sh/a10jqpsj','sh/x4r21kru']);
const title = s.shapes.items.find(sh=>sh.toSnapshot?.().aid==='sh/9072xkry');
for (const sh of [...s.shapes.items]) if (!keepShapes.has(sh.toSnapshot?.().aid)) sh.delete();
const logo = s.images.items[0];
for (const im of [...s.images.items]) if (im !== logo) s.images.deleteById(im.id);

title.text.replace('四类方案均已量产，视觉逻辑可复用，但高速平台仍依赖外购','目录｜从系统逻辑到量产应用，再到自主化计划');

const navy = '#00457A';
const blue = '#0B5B92';
const pale = '#EEF5F9';
const line = '#B7CAD8';
const gray = '#5E6872';
const orange = '#ED7D31';
const font = 'Microsoft JhengHei';

function rect(name,left,top,width,height,fillColor='white',lineColor=line,lineWidth=1){
  return s.shapes.add({geometry:'rect',name,position:{left,top,width,height},fill:fillColor,line:{style:'solid',fill:lineColor,width:lineWidth}});
}
function text(name,value,left,top,width,height,size=18,color=navy,bold=false,alignment='left'){
  const t=s.shapes.add({geometry:'textbox',name,position:{left,top,width,height},fill:'none',line:{style:'solid',fill:'none',width:0}});
  t.text=value;
  t.text.style={fontSize:size,typeface:font,color,bold,alignment};
  return t;
}
async function addPhoto(path,left,top,width,height,alt){
  const b=await fs.readFile(path);
  s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:path.toLowerCase().endsWith('.png')?'image/png':'image/jpeg',alt,fit:'cover',position:{left,top,width,height},geometry:'rect'});
}

text('directory-lead','汇报路径',52,112,120,25,14,blue,true);
text('directory-summary','通用视觉逻辑已在4类量产方案复用；汇报最后聚焦自制蜘蛛手的成本、排程与验证。',170,110,875,28,14,gray,false);

const rows=[
  {n:'01',title:'系统架构与视觉流程',desc:'两条控制路径｜拍照、补料、匹配、叠料判断与补偿闭环',pages:'P03–04'},
  {n:'02',title:'四类量产应用',desc:'K7自建轴｜K21四轴｜K41并联机械手｜四轴随线取放',pages:'P05–08'},
  {n:'03',title:'方案选型与成本对比',desc:'按节拍、精度、行程与材料成本选择适合的平台',pages:'P09'},
  {n:'04',title:'自制蜘蛛手推进计划',desc:'首台预计材料 ¥33,862｜10月底完成调试与量产验证',pages:'P10'},
];

for(let i=0;i<rows.length;i++){
  const y=146+i*121;
  const r=rows[i];
  rect(`directory-row-${i+1}`,48,y,1165,103,'#FFFFFF',line,1);
  rect(`directory-num-bg-${i+1}`,48,y,82,103,i===3?orange:navy,i===3?orange:navy,0);
  text(`directory-num-${i+1}`,r.n,48,y+27,82,40,28,'#FFFFFF',true,'center');
  text(`directory-title-${i+1}`,r.title,158,y+16,455,33,21,navy,true);
  text(`directory-desc-${i+1}`,r.desc,158,y+55,665,28,14,gray,false);
  text(`directory-pages-${i+1}`,r.pages,818,y+37,118,28,16,i===3?orange:blue,true,'center');
  await addPhoto(photoPaths[i],952,y+10,249,83,`目录章节${i+1}真实设备照片`);
}

await fs.writeFile(`${work}/after-slide2.png`, new Uint8Array(await (await p.export({slide:s,format:'png',scale:1.5})).arrayBuffer()));
await fs.writeFile(`${work}/after-slide2.layout.json`, await (await s.export({format:'layout'})).text());
const out = await PresentationFile.exportPptx(p);
await out.save(output);
console.log(output);
