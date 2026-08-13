import fs from 'node:fs/promises';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const input='C:/Users/lfaf-test/Documents/报告编写/outputs/视觉无序抓取_电气技术汇报_完整评审稿_R004.pptx';
const output='C:/Users/lfaf-test/Documents/报告编写/outputs/视觉无序抓取_电气技术汇报_封面文案修正版_R006.pptx';
const work='C:/Users/lfaf-test/Documents/报告编写/outputs/cyber-ppt-work/artifact-edit';

const p=await PresentationFile.importPptx(await FileBlob.load(input));
const s=p.slides.items[0];
const target=s.shapes.items.find(sh=>sh.toSnapshot?.().text?.includes('本周电气技术汇报'));
if(!target) throw new Error('未找到封面三行说明文字');

await fs.writeFile(`${work}/before-cover.png`,new Uint8Array(await (await p.export({slide:s,format:'png',scale:1.5})).arrayBuffer()));

target.text.replace('本周电气技术汇报','汇报主题：视觉无序抓取技术应用');
target.text.replace('4 类方案已投入生产运行','量产成果：4类抓取方案已投入生产运行');
target.text.replace('下一步：并联机械手自主开发','下一步计划：推进并联机械手自主开发');

await fs.writeFile(`${work}/after-cover.png`,new Uint8Array(await (await p.export({slide:s,format:'png',scale:1.5})).arrayBuffer()));
await fs.writeFile(`${work}/after-cover.layout.json`,await (await s.export({format:'layout'})).text());
const out=await PresentationFile.exportPptx(p);
await out.save(output);
console.log(output);
