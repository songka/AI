import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspace = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\.bomcheck-judge";
const source = path.join(workspace, "source.pptx");
const output = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\AI大赛_BOMCheck项目汇报-评审重点版.pptx";
const qaDir = path.join(workspace, "final");

const edits = {
  "sh/547294r6": "AI 参与率约 80% 的\nBOMCheck 落地实践",
  "sh/k3yl0zql": "AI 大赛项目汇报｜综合价值 · 创新性 · 可拓展性",
  "sh/7qp4be9c": "AI 贯穿 8/10 环节",
  "sh/65g3298r": "真实截图",
  "sh/ts7md4r2": "现场交付",

  "sh/t8byxkn2": "评审先看这五个结论",
  "sh/9072xkry": "AI 占比有口径，项目价值有证据，创新和拓展都有落点",
  "sh/b29kza94": "AI 参与率约 80%",
  "sh/a10jqpsj": "10 个关键环节中，AI 深度参与 8 个",
  "sh/w3i1sfa9": "价值形成业务闭环",
  "sh/r65knqtk": "审核、查询、资料、交付形成闭环",
  "sh/ove9o7yd": "创新在业务工程化",
  "sh/9wnqhczy": "把专家经验和操作习惯写进工具",
  "sh/nu58f2hs": "真实落地已经验证",
  "sh/wjy9sry9": "共享盘、打包、窗口、文档都走通",
  "sh/ahwrqhgj": "方法可以继续扩展",
  "sh/bip8jmho": "规则、资料和场景均可复用",

  "sh/d0jax03i": "AI 在项目里做了多少",
  "sh/298ryl4v": "过程记录显示：10 个关键环节中，8 个有 AI 深度参与",

  "sh/1cj2d8b6": "按关键环节统计，AI 参与率约 80%",
  "sh/0ba143al": "口径是“AI 深度参与的环节数”，不是代码行数或替代率",
  "sh/rm1k7yt4": "需求结构化\n方案设计",
  "sh/ql8jytsj": "代码实现\n规则实现",
  "sh/doj29oba": "UI 优化\n交互改进",
  "sh/sna103ap": "测试修复\n部署打包",
  "sh/3ihk3et8": "文档交付\n经验沉淀",

  "sh/x4vedgvm": "AI 占比高，但业务责任没有交给 AI",
  "sh/dgbulwnm": "人负责判断，AI 负责把判断快速做成、试出来、交付出去",
  "sh/cf2tcr61": "人输入\n真实需求与样本",
  "sh/z2tcnm5s": "人主导\n业务规则与边界",
  "sh/yhkbe1o7": "AI 主导\n实现、优化与修复",
  "sh/l4bupwny": "人验收\n结果与现场责任",
  "sh/032tgr6d": "AI 深度参与：8 / 10 个关键环节",
  "sh/n6dcr65o": "业务判断 100% 由人负责；AI 的高占比体现在工程实现和迭代速度。",

  "sh/zi98nu94": "项目的综合价值",
  "sh/87ipkzal": "少漏检、少查找、少重复操作，最后形成可交付工具",

  "sh/ydkbm5sv": "最初不是缺数据，而是审核经验没有被工具化",
  "sh/cb2tkvap": "Excel 和 ERP 都有数据，但规则分散在人脑、文件和现场习惯里",
  "sh/kzmdova1": "已有：Excel + 人工判断",
  "sh/l0vuh0rm": "缺少：统一规则 + 清晰结果 + 团队复用",

  "sh/m5gvmhwn": "综合价值覆盖六类高频工作",
  "sh/18byd4zy": "不是只快一个按钮，而是把审核、查询、资料和交付串起来",
  "sh/g72x4zyd": "批量 BOM 检查",
  "sh/ri9g7uhw": "简繁体与多表兼容",
  "sh/6h0fypgb": "失效料号替换",
  "sh/tkby9kzm": "组合料号绑定",
  "sh/sjix0zy1": "关键词查询与资料入口",
  "sh/je9g3ahk": "结果统计与交付",
  "sh/id0fu50z": "综合价值：个人经验 → 标准规则 → 团队可重复使用",

  "sh/0b65obm9": "创新性在哪里",
  "sh/nex4jq5k": "创新不在模型本身，而在把业务经验、操作习惯和部署条件一起工程化",

  "sh/zelojyl8": "创新 1：把专家经验翻译成可执行规则",
  "sh/xc3mho32": "规则不再只在人脑里，而是进入检查流程、状态提示和结果输出",
  "sh/m1cnetkj": "旧版：流程能跑\n判断仍靠使用者",
  "sh/s7yt4b21": "新版：规则、状态、结果\n放进同一工作台",

  "sh/n69grmpw": "创新 2：把现场操作习惯写进产品",
  "sh/xcryxg7y": "不要求员工记系统语法，而是让系统适应员工的搜索与复制方式",
  "sh/61kzalof": "以前：要记住 % 通配符",
  "sh/ofqtgnyt": "现在：直接输入关键词",
  "sh/9gza9sze": "结果可拖选、多行复制",

  "sh/ra943il8": "创新 3：从脚本升级为日常工作台",
  "sh/1gbm9s3a": "执行、查询、配置状态和结果处理，都集中在同一个桌面入口",
  "sh/a543mx4r": "网络与配置状态",
  "sh/wvupgz6t": "审核、查询快速切换",
  "sh/xw3q94ne": "结果状态明确",
  "sh/atc7epon": "拖选与多行复制",

  "sh/q50nydsj": "可拓展性来自四个可配置层",
  "sh/bq9orito": "新增业务不必重写系统，优先增加规则、资料映射和入口配置",
  "sh/o3i5w3ad": "规则层\n失效 / 绑定 / 重要料",
  "sh/p4r6p8by": "数据层\n料号 / 描述 / 简繁体",
  "sh/21gnuts7": "资料层\n图片 / 说明书 / 路径",
  "sh/32ponyts": "场景层\nUA 专案与后续项目",

  "sh/wbydknq1": "为什么它能真正落地",
  "sh/jepwf2pc": "除了功能，还解决共享盘、启动速度、窗口适配和交接文档",

  "sh/547mhg3m": "共享盘启动从 1 分钟，变成本地缓存快速启动",
  "sh/k3y5ov21": "AI 不只写功能，也参与定位企业环境中的部署问题",
  "sh/76p4jqls": "原因\nonefile 在网络盘读取、解包",
  "sh/65gnqlk7": "方案\n小启动器先缓存到本地",
  "sh/t87ml0ji": "保持\n配置和数据仍走共享盘",

  "sh/2pcfa5oz": "Windows 本地 Codex 把最后一公里也纳入 AI 闭环",
  "sh/8z2h8bq1": "可以直接看窗口、点界面、修体验、做验证，直到能打包交付",

  "sh/gbedwfmx": "如何复制和扩展",
  "sh/rm5czq50": "沉淀下来的不只是 BOMCheck，而是一套内部工具开发方法",

  "sh/fapkr6pw": "最终交付是一套可扩展的 BOM 辅助平台",
  "sh/wrelszu9": "当前覆盖审核、查询、资料和部署，后续可继续增加规则与场景",
  "sh/hsn2l4bu": "规则能力\n失效替换\n组合绑定",
  "sh/itw3upcf": "查询能力\n关键词搜索\n拖选复制",
  "sh/je5knut0": "资料能力\n图片 / 说明书\n专案入口",
  "sh/4felwzu5": "交付能力\n共享盘发布\n本地缓存启动",
  "sh/5gnmp4bq": "同一方法可扩展到工程资料校验、配置检查和台账核对。",

  "sh/oj21o7qt": "扩展到其他场景，沿用这 6 步即可",
  "sh/9gb6xgbi": "这套方法比单一功能更值得复用",
  "sh/vitozqt8": "写清业务规则",
  "sh/xkbq10be": "提供真实样本",
  "sh/jmd83atk": "先做最小闭环",
  "sh/cri1gnql": "用现场问题迭代",
  "sh/qpgjex8f": "处理部署细节",
  "sh/0vi1k7qx": "沉淀规则与文档",
  "sh/1gridcr2": "业务定义标准，AI 负责快速工程化、验证和交付。",

  "sh/4nu1krqh": "评审结论：AI 占比高，价值不止于写代码",
  "sh/qpwjmh8n": "AI 深度参与约 80% 关键环节\n同时形成综合价值、业务创新和可扩展能力"
};

const notes = {
  "nt/y90nupkv": "这版汇报先回应评审最关心的问题：AI 到底参与了多少。按项目关键环节覆盖率统计，AI 深度参与约 80%。但我也会明确说明，业务规则和最终验收仍由人负责。后面再用真实截图证明项目的综合价值、创新性和可拓展性。",
  "nt/hwbqtkby": "评审可以先记住五个结论：AI 参与率约 80%；价值不是单点提效，而是形成业务闭环；创新来自把专家经验工程化；项目已经经过真实部署；规则和方法还能继续扩展。",
  "nt/ofy9wn61": "先解释 AI 参与率的口径。我没有用一个很难验证的代码行数，而是把项目拆成 10 个关键环节，看 AI 在多少环节里承担了结构化、实现、优化或交付工作。",
  "nt/jyx0ra1s": "10 个关键环节里，AI 深度参与了 8 个：需求结构化、方案设计、代码和规则实现、UI 优化、测试修复、部署打包以及文档交付。因此按环节覆盖率估算约为 80%。这个数字是过程参与率，不是替代率。",
  "nt/i107q5of": "这里要特别说明人机分工。业务人员提供真实需求、样本和判断边界，并对现场结果负责；AI 主要负责把这些判断快速工程化、不断修复和形成交付物。所以 AI 占比高，但业务责任没有外包。",
  "nt/x8f69ofe": "说完占比，再看项目值不值得做。它的价值不是多一个界面，而是减少漏检、查找和重复操作，并把个人经验变成团队可以稳定使用的工具。",
  "nt/gnmp4jqx": "项目最初并不是没有 Excel 或 ERP，而是审核规则分散在人脑、文件和现场习惯中。旧版截图证明主流程可以跑，但还没有形成清晰、统一、可复用的工作方式。",
  "nt/fu1gfa1s": "综合价值覆盖六类高频工作：批量检查、文件兼容、失效替换、组合绑定、查询资料和结果交付。重点不是某个按钮节省几秒，而是整条审核链路更一致、更容易复用。",
  "nt/udsvah03": "第三部分讲创新。这里不强调模型有多新，而是强调我们把业务经验、员工操作习惯和企业部署条件一起做进了产品，这才是这个项目真正的创新落点。",
  "nt/m90b6t0r": "第一类创新，是把专家经验变成可执行规则。旧版只是让流程能跑，新版把规则、状态和结果放进同一工作台，让判断过程更加标准化，也让普通使用者更容易理解。",
  "nt/jetc3ut0": "第二类创新，是让系统适应人的操作习惯。员工不需要记住 ERP 的百分号通配符，直接输入关键词即可；查到结果后还可以拖选和多行复制。创新体现在业务体验，而不是堆功能。",
  "nt/8f2psfyx": "第三类创新，是从一次性脚本升级成日常工作台。执行、查询、配置状态和结果处理集中在一个入口，软件才真正具备长期使用和交付的基础。",
  "nt/hgzapcr6": "可拓展性来自四层配置：规则层、数据层、资料层和场景层。后续增加新规则、新专案或新资料入口时，优先增加配置和映射，不需要把系统全部推倒重来。",
  "nt/6lsnupw7": "下面用真实部署问题证明它不是演示稿。能不能在共享盘启动、窗口能不能显示完整、是否能打包和交接，决定了工具能不能真的被同事使用。",
  "nt/vaxsvy10": "共享盘启动从本地 5 秒变成超过 1 分钟，是典型企业环境问题。AI 协助定位 onefile 网络读取和解包，并实现小启动器加本地缓存；配置和业务数据仍然保留在共享盘。",
  "nt/gny5sjyp": "Windows 本地 Codex 让 AI 可以直接参与最后一公里：看窗口、点界面、修滚动和尺寸、处理自动加载、优化复制，再完成桌面版和 Web 版打包。AI 的作用覆盖到交付，而不只停在代码生成。",
  "nt/14bup87q": "最后看可复制和可扩展。项目真正留下来的，一部分是软件，另一部分是做内部工具的方法：怎么给样本、怎么迭代、怎么验证和怎么交付。",
  "nt/y5wne50z": "当前平台已经具备规则、查询、资料和交付四类能力。以后可以继续扩展工程资料校验、配置检查、台账核对等场景，复用相同的数据处理、规则配置和交付方式。",
  "nt/nid43ytk": "扩展其他场景时可以沿用六步：写清规则、给真实样本、做最小闭环、现场迭代、处理部署、沉淀文档。业务人员定义标准，AI 负责快速工程化、验证和交付。",
  "nt/zyxsni5k": "最后总结：AI 深度参与约 80% 的关键环节，但它的价值不只是替我们写代码。它帮助项目同时形成了综合业务价值、可验证的创新点，以及可以继续复制的扩展能力。"
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
  for (const [id, value] of Object.entries(notes)) {
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
  console.log(JSON.stringify({ output, slides: presentation.slides.items.length, edits: Object.keys(edits).length, notes: Object.keys(notes).length }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
