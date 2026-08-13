import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspace = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\.bomcheck-tech";
const source = path.join(workspace, "source.pptx");
const output = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\AI大赛_BOMCheck项目汇报-AI技术与成果版.pptx";
const qaDir = path.join(workspace, "final");

const edits = {
  "sh/547294r6": "AI 技术驱动的\nBOMCheck 成果转化",
  "sh/k3yl0zql": "AI 大赛项目汇报｜技术应用 · 转化成果 · 视觉证据",
  "sh/7qp4be9c": "AI 贯穿开发闭环",
  "sh/65g3298r": "真实截图",
  "sh/ts7md4r2": "可交付成果",

  "sh/t8byxkn2": "这份报告回答三个核心问题",
  "sh/9072xkry": "AI在哪里发挥作用、最终转化成什么、证据如何展示",
  "sh/b29kza94": "AI 技术用在哪里",
  "sh/a10jqpsj": "需求理解、规则转译、实现、修复、交付",
  "sh/w3i1sfa9": "转化成什么成果",
  "sh/r65knqtk": "规则、软件、资料入口和部署能力",
  "sh/ove9o7yd": "如何证明成果",
  "sh/9wnqhczy": "真实新旧截图、现场问题和交付记录",

  "sh/d0jax03i": "AI 技术如何发挥作用",
  "sh/298ryl4v": "AI工作在开发闭环，BOMCheck运行时按确定性业务规则执行",

  "sh/1cj2d8b6": "AI 在五个开发流程持续发挥作用",
  "sh/0ba143al": "大语言模型用于理解、生成、推理和修复，不替代现场业务判断",
  "sh/rm1k7yt4": "需求理解\n自然语言 → 任务",
  "sh/ql8jytsj": "规则转译\n专家经验 → 逻辑",
  "sh/doj29oba": "代码生成\nPython / Flask / Tk",
  "sh/sna103ap": "测试修复\n样本 / 日志 → 补丁",
  "sh/3ihk3et8": "部署交付\nSMB诊断 / 文档",

  "sh/x4vedgvm": "AI 技术有明确作用，也有明确边界",
  "sh/dgbulwnm": "AI负责工程化和快速迭代，人负责业务规则、验收和最终责任",
  "sh/cf2tcr61": "AI 理解\n需求文件与对话",
  "sh/z2tcnm5s": "AI 生成\n代码、界面与测试",
  "sh/yhkbe1o7": "人提供\n样本、规则与反馈",
  "sh/l4bupwny": "人确认\n结果与现场验收",
  "sh/032tgr6d": "AI 贯穿：理解、生成、修复",
  "sh/n6dcr65o": "部署和文档也由AI协助；运行时仍按确定性规则执行。",

  "sh/zi98nu94": "转化成果与综合价值",
  "sh/87ipkzal": "把个人审核经验，转成规则、软件、交付物和团队能力",

  "sh/m5gvmhwn": "转化成果：六类高频工作已经进入软件",
  "sh/18byd4zy": "从口头经验和零散文件，转成可执行、可查询、可交付的功能",
  "sh/id0fu50z": "成果转化链：业务经验 → 可执行规则 → 软件功能 → 团队复用",

  "sh/0b65obm9": "创新与真实产品证据",
  "sh/nex4jq5k": "下面不只讲文字，直接用新旧截图展示规则、交互和工作台的变化",

  "sh/fapkr6pw": "转化成果：形成四类可持续资产",
  "sh/wrelszu9": "项目不只交付软件，还沉淀业务规则、产品能力和部署方法",
  "sh/hsn2l4bu": "业务成果\n审核经验\n转成标准规则",
  "sh/itw3upcf": "产品成果\n桌面 / Web\n形成工作台",
  "sh/je5knut0": "交付成果\n启动器 / 文档\n共享盘发布",
  "sh/4felwzu5": "组织价值\n个人经验\n变成团队能力",
  "sh/5gnmp4bq": "转化路径：经验 → 规则 → 软件 → 交付 → 团队可复用能力",

  "sh/4nu1krqh": "AI 技术最终转化成了可交付成果",
  "sh/qpwjmh8n": "AI 在开发流程中持续发挥作用\n最终沉淀为规则、软件、部署能力和团队价值"
};

const noteUpdates = {
  "nt/y90nupkv": "这份汇报按三个要求展开：第一，说明AI技术到底在哪个流程发挥作用；第二，说明最终转化成了什么成果和价值；第三，用真实软件截图展示，而不是只用文字描述。",
  "nt/hwbqtkby": "评审可以围绕三个问题看：AI用在哪里，转化成了什么，以及有什么可视化证据。后续还会补充真实部署和可扩展性。",
  "nt/ofy9wn61": "先讲AI技术应用。这里需要区分开发阶段和运行阶段：大语言模型主要参与需求理解、规则转译、代码实现、测试修复和交付；BOMCheck运行时执行确定性审核规则。",
  "nt/jyx0ra1s": "AI在五个开发流程中持续发挥作用。它把自然语言需求整理成任务，把专家经验转成代码逻辑，生成和重构Python、Flask与桌面界面代码，再根据真实样本和日志定位问题，最后协助处理共享盘部署和交付文档。",
  "nt/i107q5of": "AI技术不是黑箱替代业务。人提供样本、规则和反馈，并对结果负责；AI主要负责理解、生成、推理、修复和沉淀。运行时使用确定性规则，也让结果更容易解释和复查。",
  "nt/x8f69ofe": "接下来讲成果转化。这个项目把个人审核经验转成四类资产：可以执行的规则、可以使用的软件、可以发布的交付物，以及团队可以复用的方法。",
  "nt/fu1gfa1s": "六类高频工作已经进入软件，证明成果不是停留在方案层。批量检查、文件兼容、失效替换、组合绑定、查询资料和结果交付都形成了实际功能。",
  "nt/udsvah03": "第三部分直接看视觉证据。接下来的新旧截图分别展示规则如何进入执行流程、操作习惯如何进入查询页，以及单页脚本如何升级为日常工作台。",
  "nt/8f2psfyx": "这一页适合进行现场演示。如果后续准备一段30秒BOMCheck录屏，可以在这里切换播放：选择BOM、执行检查、查看结果、跳转查询。当前PPT先使用两张真实截图作为证据。",
  "nt/y5wne50z": "最终转化成果分成四类：业务规则被标准化；桌面版和Web版形成产品；启动器、共享盘发布和文档形成交付能力；个人经验变成团队可复用能力。",
  "nt/zyxsni5k": "最后总结：AI技术真实参与了开发闭环，并不是只在报告里出现。它最终转化成了可执行规则、可使用软件、可交付部署能力和可复制的团队价值。"
};

async function saveBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(qaDir, { recursive: true });
  const presentation = await PresentationFile.importPptx(await FileBlob.load(source));

  for (const [id, value] of Object.entries(edits)) {
    presentation.resolve(id).text = value;
  }
  for (const [id, value] of Object.entries(noteUpdates)) {
    const target = presentation.resolve(id);
    target.setText(value);
    target.setVisible(true);
  }

  const snapshot = await presentation.inspect({
    kind: "slide,textbox,shape,image,table,chart,notes,layout",
    include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,isPlaceholder,alt,placeholders",
    maxChars: 200000
  });
  await fs.writeFile(path.join(qaDir, "inspect.ndjson"), snapshot.ndjson, "utf8");

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await saveBlob(path.join(qaDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text(), "utf8");
  }
  await saveBlob(path.join(qaDir, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 0.7 }));

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(output);
  console.log(JSON.stringify({ output, slides: presentation.slides.items.length, edits: Object.keys(edits).length }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
