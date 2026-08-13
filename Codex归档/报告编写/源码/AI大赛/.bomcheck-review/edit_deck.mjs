import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspace = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\.bomcheck-review";
const source = path.join(workspace, "source.pptx");
const output = "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\AI大赛_BOMCheck项目复盘-JIAJI.SONG-口语化优化版.pptx";
const qaDir = path.join(workspace, "final");

const edits = {
  "sh/547294r6": "我用 AI 做了一套\n电控 BOM 审核工具",
  "sh/k3yl0zql": "BOMCheck 项目复盘｜从需求、迭代到现场交付",
  "sh/7qp4be9c": "真实需求",
  "sh/65g3298r": "真实截图",
  "sh/ts7md4r2": "真实踩坑",
  "sh/t8byxkn2": "今天主要讲五件事",
  "sh/9072xkry": "不讲模型原理，只讲这个工具是怎么一步步做出来、用起来的",
  "sh/b29kza94": "先说为什么要做",
  "sh/w3i1sfa9": "第一版怎么做出来",
  "sh/ove9o7yd": "从能跑到好用",
  "sh/nu58f2hs": "真正难的是交付",
  "sh/ahwrqhgj": "最后留下什么",
  "sh/d0jax03i": "先说为什么要做",
  "sh/298ryl4v": "ERP 有数据，但现场审核还有很多经验判断",
  "sh/1cj2d8b6": "真正耗时间的，是这些零散判断",
  "sh/0ba143al": "ERP 能查料号，但很多现场规则还得靠人记、靠人找",
  "sh/x4vedgvm": "我没有先让 AI 写代码，而是先把审核过程写清楚",
  "sh/dgbulwnm": "先讲清输入、规则和输出，再谈界面与功能",
  "sh/032tgr6d": "我最开始交给 AI 的：需求.txt",
  "sh/n6dcr65o": "不是一句“帮我做软件”，而是把每天怎么审核，一步一步写给它。",
  "sh/zi98nu94": "第一版怎么做出来",
  "sh/87ipkzal": "先把主流程跑通，再拿真实 BOM 一项项补规则",
  "sh/ydkbm5sv": "第一版先不求好看，先确认流程能跑通",
  "sh/cb2tkvap": "选 BOM、执行检查、看到结果，最小闭环先成立",
  "sh/kzmdova1": "当时已经能用",
  "sh/l0vuh0rm": "但还像开发工具，现场操作不够直观",
  "sh/m5gvmhwn": "功能不是一次想全的，是被真实样本逼出来的",
  "sh/18byd4zy": "每遇到一个问题，就补一条规则、做一次本地验证",
  "sh/id0fu50z": "我们的迭代方式：真实 BOM → 暴露问题 → AI 修改 → 本地验证",
  "sh/0b65obm9": "从能跑到好用",
  "sh/nex4jq5k": "界面不是换颜色，而是让同事少找、少点、少出错",
  "sh/zelojyl8": "同一张执行页，现场操作少绕了几步",
  "sh/xc3mho32": "旧版能执行；新版把状态、结果和下一步操作摆到了眼前",
  "sh/m1cnetkj": "旧版：入口简单\n但状态不够清楚",
  "sh/s7yt4b21": "新版：导航、状态和流程\n都放到同一页",
  "sh/n69grmpw": "查询页不再只是“能查到”，而是方便继续做事",
  "sh/xcryxg7y": "从看列表，到搜索、复制、带走结果",
  "sh/61kzalof": "以前：要记住 % 通配符",
  "sh/ofqtgnyt": "现在：直接输入关键词",
  "sh/9gza9sze": "查到后可直接拖选复制",
  "sh/ra943il8": "新版桌面端，已经能承担日常审核",
  "sh/1gbm9s3a": "审核和料号查询，放到了同一个工作台里",
  "sh/q50nydsj": "做着做着，它从审核工具变成了资料入口",
  "sh/bq9orito": "既然料号已经读进来了，就顺手把图片、说明书和专案资料接进来",
  "sh/wbydknq1": "真正难的是交付",
  "sh/jepwf2pc": "到了共享盘、打包和多人使用，问题才真正暴露",
  "sh/547mhg3m": "共享盘一跑，启动时间从 5 秒变成 1 分钟",
  "sh/k3y5ov21": "功能没有坏，但这种等待会直接影响现场使用",
  "sh/76p4jqls": "原因\nonefile 在网络盘读取、解包",
  "sh/65gnqlk7": "处理\n用小启动器先缓存到本地",
  "sh/t87ml0ji": "不变\n配置和数据仍走共享盘",
  "sh/2pcfa5oz": "Windows 本地 Codex 解决的是最后一公里",
  "sh/8z2h8bq1": "可以直接看窗口、点界面、改完马上验证，体验问题收敛得更快",
  "sh/gbedwfmx": "最后留下什么",
  "sh/rm5czq50": "除了工具，更重要的是一套可以复用的做法",
  "sh/fapkr6pw": "最后交付的，不只是一个检查按钮",
  "sh/wrelszu9": "桌面版为主，把审核、查询、资料和发布串在一起",
  "sh/5gnmp4bq": "它把我脑子里的审核经验，变成了同事可以反复使用的工具。",
  "sh/oj21o7qt": "如果再做一个内部工具，我会按这 6 步来",
  "sh/9gb6xgbi": "这套方法，比 BOMCheck 本身更值得复用",
  "sh/1gridcr2": "业务人员定规则，AI 帮我们更快做成、试出来、交付出去。",
  "sh/4nu1krqh": "AI 没有替我做业务判断",
  "sh/qpwjmh8n": "它帮我把这些判断\n做成了一个能执行、能复用、能交付的工具"
};

const notes = {
  "nt/y90nupkv": "大家好，我是电控主管，平时要审核不少电控 BOM。这个项目的起点很简单：我想把每天重复做、又容易漏掉的检查，做成一个同事也能直接用的工具。今天不讲 AI 概念，主要复盘这套工具怎么一步步落地。",
  "nt/hwbqtkby": "我按五段来讲。先说现场为什么需要它，再看第一版怎么跑起来；然后用新旧截图看它怎么变好用，接着讲共享盘和打包这些真正的交付问题，最后总结我会复用的做法。",
  "nt/ofy9wn61": "先从业务问题开始。ERP 里当然有数据，但审核 BOM 不只是查有没有这个料号，很多判断来自现场经验。下一页我把这些经验判断拆开给大家看。",
  "nt/jyx0ra1s": "实际审核时，麻烦往往不是一个大问题，而是很多小判断叠在一起：料多容易漏、停产料要替换、组合料要绑定、资料又分散。人当然能做，但量一上来，速度和一致性就很难保证。",
  "nt/i107q5of": "所以我第一步不是让 AI 直接写程序。我先把输入是什么、要按什么规则判断、最后输出什么，整理成一份需求文件。对 AI 来说，越像一份真实的工作说明，第一版就越接近我们要的东西。",
  "nt/x8f69ofe": "需求讲清楚以后，才进入开发。我的策略不是一开始把所有功能想全，而是先做一个能跑的最小闭环，再用真实 BOM 去找问题。",
  "nt/gnmp4jqx": "这就是最早的版本。它已经能选 Excel、执行检查、看到结果，所以流程是通的。但大家也能看出来，它更像开发人员自己用的工具，状态提示和下一步操作都不够直观。",
  "nt/fu1gfa1s": "后面的功能大多不是坐在会议室里想出来的，而是拿真实 BOM 一份份测出来的。数量列、多工作表、简繁体、失效替换、绑定料号，这些问题每出现一次，就补一条规则，再在本地重新验证。",
  "nt/udsvah03": "流程跑通以后，下一步才是好不好用。这里我不讲抽象的 UI 优化，直接看两组新旧截图：同样的功能，现场要少找、少点，而且知道自己现在做到哪一步。",
  "nt/m90b6t0r": "先看执行页。旧版的问题不是不能执行，而是执行前后状态不够清楚。新版把导航、配置状态、执行流程和结果放在同一个工作台里，用户不需要自己猜下一步。",
  "nt/jetc3ut0": "再看查询页。以前在 ERP 里查料号，要记住通配符的写法；新版直接输几个关键词就可以，查到以后还能拖选复制。这个改动不复杂，但很贴近同事平时的操作习惯。",
  "nt/8f2psfyx": "做到这里，新版桌面端已经不再是一个单页脚本。审核和查询在同一个入口里，网络配置、状态提示和复制操作也都补上了，已经可以承担日常反复使用。",
  "nt/hgzapcr6": "后来功能又自然往外长了一步。既然系统已经拿到了料号，就不只拿来检查；同事还希望顺手看到图片、说明书和专案资料，所以它慢慢变成了一个资料入口。",
  "nt/6lsnupw7": "功能做完只是前半段。真正放到公司环境里，才会遇到共享盘、打包、窗口尺寸和多人使用这些问题。下一页这个启动速度问题，就是最典型的一次。",
  "nt/vaxsvy10": "同一个 exe，本地大约 5 秒，从共享盘打开却要 1 分钟以上。原因是 onefile 需要在网络盘读取和解包。后来用一个很小的启动器先把主程序缓存到本地，配置和业务数据仍放在共享盘，兼顾了集中发布和启动速度。",
  "nt/gny5sjyp": "Windows 本地 Codex 出来以后，最大的变化不是多了多少代码，而是能直接看到窗口、点击界面、马上验证。窗口显示不全、列表要手动刷新、复制不顺手这些最后一公里的问题，收敛速度明显更快。",
  "nt/14bup87q": "到这里，项目本身基本讲完了。最后我想总结的不是功能清单，而是这次做完以后，我下次再做内部工具会怎么走。",
  "nt/y5wne50z": "最后交付的不是一个检查按钮，而是一整套辅助工作链：BOM 检查、料号查询、资料入口，以及共享盘上的发布和启动。核心价值是把个人经验固化下来，让同事可以稳定、重复地使用。",
  "nt/nid43ytk": "如果再做一个内部工具，我会按这六步：先写清流程，给真实样本，做最小闭环，用现场问题迭代，再处理部署，最后补齐文档和规则。业务判断仍然由我们负责，AI 的作用是把这些判断更快变成工具。",
  "nt/zyxsni5k": "所以我的结论是，AI 没有替我做电控审核，也没有替我承担业务责任。它真正帮到我的，是把脑子里的经验做成一个能执行、能复用、能交付的工具。这套方法也可以继续复制到其他工程管理场景。谢谢大家。"
};

async function saveBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(qaDir, { recursive: true });
  const presentation = await PresentationFile.importPptx(await FileBlob.load(source));

  for (const [id, value] of Object.entries(edits)) {
    const target = presentation.resolve(id);
    target.text = value;
  }
  for (const [id, value] of Object.entries(notes)) {
    const target = presentation.resolve(id);
    target.setText(value);
    target.setVisible(true);
  }

  const snapshot = await presentation.inspect({
    kind: "slide,textbox,shape,image,table,chart,notes,layout",
    include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,isPlaceholder,alt,placeholders",
    maxChars: 200000,
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
