import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const workspace = path.dirname(fileURLToPath(import.meta.url));
const source = path.join(workspace, 'source.pptx');
const finalDir = path.dirname(workspace);

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function build({name, order, outputName, noteOverrides = {}}) {
  const deck = await PresentationFile.importPptx(await FileBlob.load(source));
  const originals = [...deck.slides.items];
  const wanted = order.map(n => originals[n - 1]);
  const keep = new Set(wanted);

  for (const slide of originals) {
    if (!keep.has(slide)) slide.delete();
  }
  for (const [index, slide] of wanted.entries()) slide.moveTo(index);
  for (const [indexText, note] of Object.entries(noteOverrides)) {
    deck.slides.items[Number(indexText)].speakerNotes.setText(note);
  }

  const outDir = path.join(workspace, `${name}-render`);
  if (!outDir.startsWith(workspace + path.sep)) throw new Error('Unsafe render cleanup path');
  await fs.rm(outDir, {recursive:true, force:true});
  await fs.mkdir(outDir, {recursive:true});
  for (const [i, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(i + 1).padStart(2, '0')}`;
    await writeBlob(path.join(outDir, `${stem}.png`), await deck.export({slide, format:'png', scale:1}));
    const layout = await slide.export({format:'layout'});
    await fs.writeFile(path.join(outDir, `${stem}.layout.json`), await layout.text(), 'utf8');
  }
  const inspection = await deck.inspect({kind:'slide,textbox,shape,image,notes,layout',maxChars:120000});
  await fs.writeFile(path.join(workspace, `${name}-inspect.ndjson`), inspection.ndjson, 'utf8');
  const pptx = await PresentationFile.exportPptx(deck);
  const finalPath = path.join(finalDir, outputName);
  await pptx.save(finalPath);
  console.log(`${name}: ${deck.slides.items.length} slides -> ${finalPath}`);
}

await build({
  name:'live',
  order:[1,5,2,18,13,20],
  outputName:'AI大赛_BOMCheck_现场讲解版-视频前后.pptx',
  noteOverrides:{
    2:'先把评审最关心的AI占比说清楚。按照开发任务复盘估算，AI参与的工程化工作量大约占百分之七十，而且覆盖需求理解、规则转译、代码实现、测试修复和部署交付五个关键环节，也就是五分之五的流程覆盖。这里的百分之七十是项目复盘估算，不是审计数据；业务规则确认和最终验收仍然由人负责。接下来，我用一支短片带大家看看，AI是怎样进入开发流程，以及BOMCheck最后是怎样落地的。现在请看视频。',
    3:'刚才大家看到的是BOMCheck从需求、规则到产品落地的过程。但衡量一个AI项目，不能只看软件能不能运行，更要看项目结束以后留下了什么。最后盘点一下，我留下了四类资产：标准化业务规则、桌面和Web产品、启动器与共享盘发布能力，以及团队可以复用的方法。它们对应两类预期价值：缩短料号查询时间、降低选料难度和错误率；同时降低BOM检查难度，通过前置检查减少ECR返工。'
  },
});

await build({
  name:'notebooklm',
  order:[1,2,3,4,5,7,8,10,12,15,16,13,18,19,20],
  outputName:'AI大赛_BOMCheck_NotebookLM视频素材版.pptx',
});
