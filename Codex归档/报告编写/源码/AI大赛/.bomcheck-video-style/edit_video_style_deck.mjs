import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspace = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\.bomcheck-video-style";
const source = path.join(workspace, "source.pptx");
const output = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\AI大赛_BOMCheck项目汇报-视频同款第一人称版.pptx";
const qaDir = path.join(workspace, "final");

const copy = {
  "sh/547294r6": "我用 AI 把 BOM 审核经验\n做成了可交付工具",
  "sh/k3yl0zql": "BOMCheck 落地实践｜我怎么做 · 做成什么 · 如何复用",
  "sh/7qp4be9c": "我怎么用 AI",
  "sh/65g3298r": "我如何证明",
  "sh/ts7md4r2": "我做成什么",

  "sh/t8byxkn2": "这 10 分钟，我想讲清楚五件事",
  "sh/9072xkry": "AI 怎么参与、成果是什么、证据在哪里、如何落地、怎么扩展",
  "sh/b29kza94": "我把 AI 用在哪里",
  "sh/a10jqpsj": "理解需求、翻译规则、生成实现、测试修复、部署交付",
  "sh/w3i1sfa9": "我最终做成什么",
  "sh/r65knqtk": "可执行规则、桌面与 Web 工具、资料入口和部署能力",
  "sh/ove9o7yd": "我用什么证明",
  "sh/9wnqhczy": "真实新旧截图、现场问题、修复过程和交付记录",
  "sh/nu58f2hs": "我怎么让它落地",
  "sh/wjy9sry9": "共享盘、打包、窗口适配和交接文档全部走通",
  "sh/ahwrqhgj": "我怎么继续扩展",
  "sh/bip8jmho": "规则、资料入口和业务场景都可以继续复用",

  "sh/d0jax03i": "我把 AI 放进了开发闭环",
  "sh/298ryl4v": "AI 帮我理解、生成和修复；BOMCheck 运行时仍按确定性规则执行",

  "sh/1cj2d8b6": "我让 AI 参与了五个关键流程",
  "sh/0ba143al": "它负责理解、生成、推理和修复，我负责业务判断和最终验收",
  "sh/rm1k7yt4": "我描述需求\n自然语言→任务",
  "sh/ql8jytsj": "我确认规则\n经验→逻辑",
  "sh/doj29oba": "AI生成实现\nPython/Flask/Tk",
  "sh/sna103ap": "我用样本验证\n日志→补丁",
  "sh/3ihk3et8": "AI协助交付\n部署/文档",

  "sh/x4vedgvm": "我没有把业务判断交给 AI",
  "sh/dgbulwnm": "我负责规则、样本和验收；AI 负责工程化、快速迭代和问题定位",
  "sh/cf2tcr61": "AI 帮我理解\n需求文件与对话",
  "sh/z2tcnm5s": "AI 帮我生成\n代码、界面与测试",
  "sh/yhkbe1o7": "我来提供\n样本、规则与反馈",
  "sh/l4bupwny": "我来确认\n结果与现场验收",
  "sh/032tgr6d": "AI 贯穿：理解、生成、修复",
  "sh/n6dcr65o": "我保留业务责任；运行时仍按可解释、可复查的确定性规则执行。",

  "sh/zi98nu94": "我最终沉淀了哪些成果",
  "sh/87ipkzal": "我把个人审核经验，转成了规则、软件、交付物和团队能力",

  "sh/ydkbm5sv": "我面对的，不是没数据，而是经验没有被工具化",
  "sh/cb2tkvap": "Excel 和 ERP 都有数据，但判断分散在人脑、文件和现场习惯里",
  "sh/kzmdova1": "我已经有：Excel + 人工判断",
  "sh/l0vuh0rm": "我还缺：统一规则 + 清晰结果 + 团队复用",

  "sh/m5gvmhwn": "我把六类高频工作做进了软件",
  "sh/18byd4zy": "原来靠口头经验和零散文件，现在可以执行、查询并直接交付",
  "sh/id0fu50z": "我的转化路径：业务经验 → 可执行规则 → 软件功能 → 团队复用",

  "sh/0b65obm9": "我用三处变化证明它不是概念",
  "sh/nex4jq5k": "接下来不讲抽象口号，我直接用新旧界面展示规则、交互和工作台的变化",

  "sh/zelojyl8": "我先把专家经验翻译成可执行规则",
  "sh/xc3mho32": "规则不再只在我脑中，而是进入检查流程、状态提示和结果输出",
  "sh/m1cnetkj": "以前：流程能跑\n判断还是靠人",
  "sh/s7yt4b21": "现在：规则、状态、结果\n集中到同一工作台",

  "sh/n69grmpw": "我再把现场操作习惯写进产品",
  "sh/xcryxg7y": "我没有要求同事适应系统语法，而是让系统适应同事的搜索和复制方式",
  "sh/61kzalof": "以前：我要记住 % 通配符",
  "sh/ofqtgnyt": "现在：我直接输入关键词",
  "sh/9gza9sze": "我可以拖选、多行复制",

  "sh/ra943il8": "我把零散脚本收拢成日常工作台",
  "sh/1gbm9s3a": "执行、查询、配置状态和结果处理，都集中在我每天使用的桌面入口",
  "sh/wvupgz6t": "我可以在审核、查询间快速切换",
  "sh/xw3q94ne": "我一眼就能看清结果状态",
  "sh/atc7epon": "我可以拖选并多行复制",

  "sh/q50nydsj": "我把扩展能力拆成四个可配置层",
  "sh/bq9orito": "增加新业务时，我优先增加规则、资料映射和入口配置，不重写整套系统",

  "sh/wbydknq1": "我怎么把它真正落到现场",
  "sh/jepwf2pc": "功能只是第一步，我还处理了共享盘、启动速度、窗口适配和交接文档",

  "sh/547mhg3m": "我把共享盘启动，从 1 分钟降到快速启动",
  "sh/k3y5ov21": "我借助 AI 定位企业环境问题，而不只是生成业务功能",
  "sh/76p4jqls": "我找到原因\nonefile 在网络盘读取、解包",
  "sh/65gnqlk7": "我调整方案\n小启动器先缓存到本地",
  "sh/t87ml0ji": "我保留同步\n配置和数据仍走共享盘",

  "sh/2pcfa5oz": "我借助本地 Codex 打通了最后一公里",
  "sh/8z2h8bq1": "我让 AI 直接看窗口、点界面、修体验、做验证，直到可以打包交付",
  "sh/9kby1g7m": "我发现窗口显示不全",
  "sh/ytkf2h8j": "我补上滚动并收敛尺寸",
  "sh/zutgvm94": "我发现列表要手动刷新",
  "sh/kv2h4rqp": "我改成打开后自动加载",
  "sh/lwbyxwra": "我发现复制不直观",
  "sh/ip4zel83": "我改成鼠标拖选 + Ctrl+C",
  "sh/3qdg7qpo": "我发现配置界面拥挤",
  "sh/fm1gzq5o": "我把子界面重新分组",
  "sh/e1sf65o3": "最后我完成打包交付",
  "sh/1ojy10ne": "桌面版 / Web 版 exe",

  "sh/gbedwfmx": "我把这次实践沉淀成一套方法",
  "sh/rm5czq50": "我留下的不只是 BOMCheck，还有一套能复用的内部工具开发方法",

  "sh/fapkr6pw": "我留下了四类可持续资产",
  "sh/wrelszu9": "除了软件，我还沉淀了业务规则、产品能力和部署方法",
  "sh/hsn2l4bu": "业务成果\n我把审核经验\n变成标准规则",
  "sh/itw3upcf": "产品成果\n我做出桌面 / Web\n形成日常工作台",
  "sh/je5knut0": "交付成果\n我补齐启动器 / 文档\n支持共享盘发布",
  "sh/4felwzu5": "组织价值\n我把个人经验\n变成团队能力",
  "sh/5gnmp4bq": "我的转化路径：经验 → 规则 → 软件 → 交付 → 团队可复用能力",

  "sh/oj21o7qt": "下一次，我会继续沿用这六步",
  "sh/9gb6xgbi": "对我来说，这套方法比某一个单独功能更值得复用",
  "sh/vitozqt8": "我先写清业务规则",
  "sh/xkbq10be": "我提供真实样本",
  "sh/jmd83atk": "我先做最小闭环",
  "sh/cri1gnql": "我用现场问题迭代",
  "sh/qpgjex8f": "我处理部署细节",
  "sh/0vi1k7qx": "我沉淀规则与文档",
  "sh/1gridcr2": "我定标准，AI 帮我快速工程化、验证和交付。",

  "sh/4nu1krqh": "我用 AI 做成的，不只是一套软件",
  "sh/qpwjmh8n": "我把 AI 用进真实开发闭环\n留下规则、产品、交付和可复制方法"
};

const notes = {
  "nt/y90nupkv": "大家好，今天我想用十分钟，复盘一下我是怎么把 AI 真正用进 BOMCheck 项目的。这里我不准备只讲概念。我会讲清楚 AI 在哪些环节帮到了我，我最后做成了什么，以及这些成果为什么能继续复用。",
  "nt/hwbqtkby": "整份汇报我会围绕五件事展开。第一，我把 AI 用在哪里；第二，我做成了什么；第三，我拿什么证明；第四，我怎么处理现场落地；最后，这套方法还能不能扩展。大家带着这五个问题往下看就可以。",
  "nt/ofy9wn61": "先说结论：我没有把 AI 放进系统里替我做最终审核。我是把 AI 放进开发闭环，让它帮我理解需求、翻译规则、生成代码、定位问题和整理交付。真正运行时，BOMCheck 仍然执行我确认过的确定性业务规则。",
  "nt/jyx0ra1s": "具体来说，我先用自然语言把需求说清楚，再把现场经验和审核规则交给 AI 帮我拆成逻辑。接着，它协助生成和重构 Python、Flask 以及桌面界面代码。我再拿真实 BOM 和日志验证，发现问题就继续让它定位、修复，最后连共享盘部署和文档也一起补齐。",
  "nt/i107q5of": "这里我想特别强调边界。我负责提供真实样本、业务规则和反馈，也负责最后验收；AI 负责把这些内容快速工程化。这样做不是让 AI 替我判断，而是让我的判断变成一套可以执行、解释和复查的工具。",
  "nt/x8f69ofe": "接下来看看成果。我最开始只有个人经验、Excel 和一些零散资料。项目做完以后，这些内容被我转成了四类东西：可以执行的规则、可以日常使用的软件、可以发布的交付物，以及团队以后还能继续复用的方法。",
  "nt/gnmp4jqx": "项目一开始并不是没有数据。Excel 和 ERP 里都有数据，真正的问题是规则散在人的脑子里、文件里和现场习惯里。旧版流程虽然能跑，但很多判断还是要靠熟练员工自己补上，所以同一个问题很难稳定复制给团队。",
  "nt/fu1gfa1s": "我后来把六类高频工作逐步做进了软件，包括批量检查、简繁体和多工作表兼容、失效料号替换、组合料号绑定、资料查询，以及结果统计和交付。做到这里，成果就不再是一份方案，而是每天可以直接使用的功能。",
  "nt/udsvah03": "下面我不再用抽象文字证明创新，而是直接看真实界面。我选择三组变化：第一，规则有没有进入执行过程；第二，系统有没有适应现场操作；第三，原来的零散脚本有没有真正变成一个日常工作台。",
  "nt/m90b6t0r": "第一处变化，是我把专家经验写成了可执行规则。旧版只是让流程跑起来，很多判断仍然留给使用者。新版把规则、状态和结果放到同一工作台里。对我来说，这才叫把经验变成产品，而不是把 Excel 换一个外壳。",
  "nt/jetc3ut0": "第二处变化，是我把同事真实的操作习惯写进产品。以前查询要记百分号通配符，现在直接输入关键词就可以；查到结果以后，还能拖选和多行复制。这个改变看起来不大，但它直接决定同事愿不愿意每天使用。",
  "nt/8f2psfyx": "第三处变化，是我把执行、查询、配置状态和结果处理放进同一个桌面入口。做审核时，我可以快速切到查询；看结果时，状态也更明确。这一页后续在视频中会配合真实操作画面，让评审看到它确实可以工作，而不是只有静态截图。",
  "nt/hgzapcr6": "我也考虑了后续扩展。现在系统可以拆成四层：规则层、数据层、资料层和场景层。以后增加新规则、新专案或者新的资料入口时，我会优先增加配置和映射，而不是把整个系统推倒重写。",
  "nt/6lsnupw7": "功能做出来，不等于项目落地。我在现场还碰到了共享盘启动慢、窗口显示不完整、列表需要手动刷新、复制不顺手，以及交接资料不齐这些问题。它们看起来不像核心算法，却会直接决定同事能不能真正使用。",
  "nt/vaxsvy10": "共享盘启动就是一个典型例子。本地启动大约几秒，放到网络盘以后可能超过一分钟。我借助 AI 定位到 onefile 的网络读取和解包问题，最后改成小启动器先缓存到本地，同时让配置和业务数据继续从共享盘同步。",
  "nt/gny5sjyp": "本地 Codex 还让我把最后一公里纳入 AI 闭环。我可以让它直接看窗口、点界面、验证滚动和尺寸，再处理自动加载、复制方式和子界面布局。每改完一轮，我都能马上验证，直到桌面版和 Web 版都可以打包交付。",
  "nt/14bup87q": "做到这里，我真正想复制的已经不只是 BOMCheck 这套软件，而是这次开发方法。只要我能写清规则、提供样本、快速做出最小闭环，再用现场问题持续迭代，这条路线就可以迁移到其他内部工具。",
  "nt/y5wne50z": "最后盘点一下，我留下了四类资产。第一是标准化业务规则；第二是桌面版和 Web 版产品；第三是启动器、文档和共享盘发布能力；第四是团队可以复用的方法。也就是说，我把个人经验逐步变成了组织能力。",
  "nt/nid43ytk": "如果再做一个类似项目，我会继续沿用这六步：先写清业务规则，提供真实样本，先做最小闭环，再用现场问题迭代，然后处理部署细节，最后沉淀规则和文档。业务标准仍然由我来定义，AI 负责加快工程化、验证和交付。",
  "nt/zyxsni5k": "最后用一句话总结：我用 AI 做成的，不只是一套 BOMCheck 软件。我把自己的审核经验，转成了可执行规则、可使用产品、可交付能力和可复制的方法。这也是我认为这个项目最有价值、最值得继续扩展的地方。"
};

const titleIds = new Set([
  "sh/547294r6","sh/t8byxkn2","sh/d0jax03i","sh/1cj2d8b6","sh/x4vedgvm",
  "sh/zi98nu94","sh/ydkbm5sv","sh/m5gvmhwn","sh/0b65obm9","sh/zelojyl8",
  "sh/n69grmpw","sh/ra943il8","sh/q50nydsj","sh/wbydknq1","sh/547mhg3m",
  "sh/2pcfa5oz","sh/gbedwfmx","sh/fapkr6pw","sh/oj21o7qt","sh/4nu1krqh"
]);
const chapterIds = new Set(["sh/cza94vmx","sh/yhg7epsj","sh/1cfmhgne","sh/xc7eds76","sh/1c7e50ni"]);
const footerPattern = /^BOMCheck AI 落地实践$|^\d{2}$/;
const yellowShapes = new Set(["sh/ts7md4r2","sh/id0fu50z","sh/5gnmp4bq","sh/1gridcr2"]);
const pinkShapes = new Set(["sh/7qp4be9c","sh/65g3298r"]);
const numberPills = new Set(["sh/ozy1ofad","sh/x4r21kru","sh/q5wjelsz","sh/mtwrmxg7","sh/xk7qlczu"]);
const flowCards = new Set(["sh/rm1k7yt4","sh/ql8jytsj","sh/doj29oba","sh/sna103ap","sh/3ihk3et8"]);
const sectionSlides = new Set([3,6,9,14,17]);

async function saveBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(qaDir, { recursive: true });
  const presentation = await PresentationFile.importPptx(await FileBlob.load(source));

  for (const [id, value] of Object.entries(copy)) {
    presentation.resolve(id).text = value;
  }
  for (const [id, value] of Object.entries(notes)) {
    const target = presentation.resolve(id);
    target.setText(value);
    target.setVisible(true);
  }

  const snapshot = await presentation.inspect({
    kind: "slide,textbox,shape,image,notes,layout",
    include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,isPlaceholder,alt,placeholders",
    maxChars: 240000
  });
  const records = snapshot.ndjson.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));

  for (const [index, slide] of presentation.slides.items.entries()) {
    slide.background.fill = sectionSlides.has(index + 1) ? "#FFF0FC" : "#FFFFFF";
  }

  for (const rec of records) {
    if (!rec.id?.startsWith("sh/")) continue;
    const target = presentation.resolve(rec.id);
    const bbox = rec.bbox ?? [0,0,0,0];
    const [, top, width, height] = bbox;
    const isFooter = typeof rec.text === "string" && footerPattern.test(rec.text.trim());
    const isRounded = /圓角|圆角|round/i.test(rec.name ?? "");

    if (typeof rec.text === "string" && rec.text.length) {
      target.text.style = {
        typeface: "Microsoft YaHei",
        color: isFooter ? "#777777" : "#111111"
      };
      if (titleIds.has(rec.id)) {
        target.text.style = { typeface: "Microsoft YaHei", color: "#111111", bold: true };
      }
      if (chapterIds.has(rec.id)) {
        target.text.style = { typeface: "Microsoft YaHei", color: "#E54CCF", bold: true };
      }
    }

    if (isRounded && !isFooter) {
      target.fill = "#FFFFFF";
      target.line = { style: "solid", fill: "#191919", width: 1.5 };
      target.borderRadius = 14;
      target.shadow = "4px 5px 0px #E85AD7/35";
    }

    if (yellowShapes.has(rec.id)) {
      target.fill = "#FFE56B";
      target.line = { style: "solid", fill: "#191919", width: 1.2 };
      target.shadow = "3px 4px 0px #E85AD7/25";
    } else if (pinkShapes.has(rec.id)) {
      target.fill = "#F8D7F5";
      target.line = { style: "solid", fill: "#191919", width: 1.2 };
    } else if (numberPills.has(rec.id)) {
      target.fill = "#F8D7F5";
      target.line = { style: "solid", fill: "#191919", width: 1.2 };
      target.text.style = { typeface: "Microsoft YaHei", color: "#111111", bold: true };
    }

    if ((!rec.text || rec.text.length === 0) && width >= 1200 && height >= 680) {
      target.fill = sectionSlides.has(rec.slide) ? "#FFF0FC" : "#FFFFFF";
      target.line = { style: "solid", fill: "none", width: 0 };
    } else if ((!rec.text || rec.text.length === 0) && height <= 24 && width > 80) {
      target.fill = "#E85AD7";
      target.line = { style: "solid", fill: "#E85AD7", width: 1 };
    }

    if (isFooter && top > 640) {
      target.text.style = { typeface: "Microsoft YaHei", color: "#777777", fontSize: 13 };
    }
    if (flowCards.has(rec.id)) {
      target.text.style = {
        typeface: "Microsoft YaHei",
        color: "#111111",
        bold: true,
        fontSize: 16,
        alignment: "center",
        verticalAlignment: "middle"
      };
    }
  }

  const finalInspect = await presentation.inspect({
    kind: "slide,textbox,shape,image,notes,layout",
    include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,isPlaceholder,alt,placeholders",
    maxChars: 240000
  });
  await fs.writeFile(path.join(qaDir, "inspect.ndjson"), finalInspect.ndjson, "utf8");

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await saveBlob(path.join(qaDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text(), "utf8");
  }
  await saveBlob(path.join(qaDir, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 0.7 }));

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(output);
  console.log(JSON.stringify({ output, slides: presentation.slides.items.length, textEdits: Object.keys(copy).length, noteEdits: Object.keys(notes).length }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
