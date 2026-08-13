import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const work = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\.codex-promotion-yang";
const starter = path.join(work, "template-starter.pptx");
const output = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\楊敏銳_製造部主管晉升課長_會議優化版.pptx";
const previewDir = path.join(work, "final-previews");
const layoutDir = path.join(work, "final-layout");

await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(layoutDir, { recursive: true });

const deck = await PresentationFile.importPptx(await FileBlob.load(starter));
const slides = deck.slides.items;
const titleLayout = deck.layouts.items.find((layout) => layout.name === "Title Slide");
const inheritedDate = titleLayout?.shapes.items.find(
  (shape) => String(shape.text ?? "").trim() === "Date",
);
if (inheritedDate) inheritedDate.text = "2026.07.27";

const textShapes = slides.map((slide) =>
  slide.shapes.items.filter((shape) => String(shape.text ?? "").trim().length > 0),
);

function setText(slideIndex, textIndex, value) {
  const shape = textShapes[slideIndex][textIndex];
  if (!shape) {
    throw new Error(`Missing text shape at slide ${slideIndex + 1}, text index ${textIndex}.`);
  }
  shape.text = value;
}

function setTextStyle(slideIndex, textIndex, style) {
  textShapes[slideIndex][textIndex].text.style = style;
}

function setNotes(slide, text, sourceSlides) {
  slide.speakerNotes.setText(
    `${text}\n\n[Sources]\n- Internal source deck, source slide${sourceSlides.length > 1 ? "s" : ""} ${sourceSlides.join(", ")}.`,
  );
}

// Slide 1 — cover.
setText(0, 0, "2026 晉升報告");
setText(0, 1, "LFAF 精益彈性自動化中心");
setText(0, 2, "楊敏銳｜製造主管晉升課長");
setText(0, 3, "2026.07.27");
setNotes(
  slides[0],
  "各位主管好，我是楊敏銳。這次申請由製造主管晉升課長。接下來我將用工作成果說明：我不只完成現場任務，也已開始透過團隊、標準與機制，讓交付能力可以持續複製。",
  [1],
);

// Slide 2 — agenda.
setText(1, 0, "個人簡介");
setText(1, 1, "績效達成狀況");
setText(1, 2, "未來工作規劃");
setText(1, 3, "發展規劃／經營答辯");
setText(1, 4, "報告內容");
setNotes(
  slides[1],
  "報告分為四段：先說明我的經歷，再用專案、團隊與標準化成果證明管理能力，最後提出未來工作與組織發展規劃；經營管理能力在答辯環節進一步說明。",
  [2],
);

// Slide 3 — career timeline.
setText(2, 0, "個人簡介｜跨品質與製造管理");
setText(2, 1, "3");
setText(2, 2, "2023");
setText(2, 3, "主管 LFAF 製造部門，負責現場、計畫與團隊管理");
setText(2, 4, "2018");
setText(2, 5, "加入漢揚 LFAF，主管品質部門工作");
setText(2, 6, "15+ 年品質與製造經驗，具備從品質控制、現場製造到團隊交付的完整視角");
setText(2, 7, "任職履歷");
setText(2, 8, "2009");
setText(2, 9, "任職外部企業品質工程師");
setNotes(
  slides[2],
  "我從品質工程起步，2018年加入LFAF負責品質管理，2023年轉任製造主管。這段經歷讓我能同時從品質、進度、現場與人員四個面向看問題，也是我承接課長職責的基礎。",
  [3, 4],
);

// Slide 4 — project portfolio.
setText(3, 0, "績效達成｜重大專案交付");
setText(3, 1, "4");
setText(3, 2, "帶領團隊完成 6 類重大專案");
setTextStyle(3, 2, {
  fontSize: 30,
  typeface: "Microsoft JhengHei",
  color: "#0000FF",
  bold: true,
  alignment: "left",
});
setText(3, 3, "Altis 組裝線");
setText(3, 4, "B/D 件自動線");
setText(3, 5, "太魯閣組裝線");
setText(3, 6, "NIF 組裝線");
setText(3, 7, "打磨線");
setText(3, 8, "衝壓線");
setNotes(
  slides[3],
  "在績效成果上，我帶領製造團隊完成六類重大專案，涵蓋衝壓、打磨、自動組裝等不同場景。我的重點不是單一設備完成，而是把人員、進度與現場問題協調到位，確保專案順利投入生產。",
  [5],
);

// Slide 5 — service team.
setText(4, 0, "績效達成");
setText(4, 1, "5");
setText(4, 2, "6 人調試售後團隊");
setText(
  4,
  3,
  "組織｜6 人團隊，分離調試與售後職能\n效率｜對外 24H 響應；對內釋放電控人力\n機制｜統一調試期、保固期、保固外流程",
);
setTextStyle(4, 2, {
  fontSize: 34,
  typeface: "Microsoft JhengHei",
  color: "#0000FF",
  bold: true,
  alignment: "left",
});
setTextStyle(4, 3, {
  fontSize: 24,
  typeface: "Microsoft JhengHei",
  color: "#1F1F1F",
  bold: false,
  alignment: "left",
});
setNotes(
  slides[4],
  "為解決調試與售後互相牽制，我規劃並組建六人團隊，完成職能分離。對外做到二十四小時內響應；對內讓電控人員回到方案與程序。更重要的是，我把三個服務階段統一成流程，讓服務不再依賴個人。",
  [6],
);

// Slide 6 — standardization.
setText(5, 0, "績效達成");
setText(5, 1, "6");
setText(5, 2, "標準化落地");
setText(
  5,
  3,
  "配盤佈局｜強電、PLC、驅動器與端子臺依序配置\n線色標準｜依規範統一 380V、220V、24V 線色\n目視快換｜號碼管與標貼清楚識別，關鍵走線與快換統一",
);
setTextStyle(5, 2, {
  fontSize: 34,
  typeface: "Microsoft JhengHei",
  color: "#0000FF",
  bold: true,
  alignment: "left",
});
setTextStyle(5, 3, {
  fontSize: 22,
  typeface: "Microsoft JhengHei",
  color: "#1F1F1F",
  bold: false,
  alignment: "left",
});
setNotes(
  slides[5],
  "第二項改善是標準化。我把配盤佈局、線色、標識與關鍵走線整理成一致做法。這不只是畫面整齊，而是降低新人學習成本、方便排查維修，也讓不同人員交付的品質更一致。",
  [7, 8],
);

// Slide 7 — inventory prevention.
setText(6, 0, "績效達成");
setText(6, 1, "7");
setText(6, 2, "安全庫存預防管理");
setText(
  6,
  3,
  "改善前｜缺料才緊急採購或請廠商先送，流程不合規且延誤進度\n改善後｜建立清單、分區分格、每月底盤點，低於安全量即開 PR\n管理價值｜以制度降低缺料風險，穩定現場節奏",
);
setTextStyle(6, 2, {
  fontSize: 34,
  typeface: "Microsoft JhengHei",
  color: "#0000FF",
  bold: true,
  alignment: "left",
});
setTextStyle(6, 3, {
  fontSize: 22,
  typeface: "Microsoft JhengHei",
  color: "#1F1F1F",
  bold: false,
  alignment: "left",
});
setNotes(
  slides[6],
  "在零星物料上，過去常是缺料後才緊急處理。我建立清單、安全量與月底盤點機制，低於安全量立即請購。這項改善代表我的管理方式，正從處理問題轉向提前發現與預防問題。",
  [9],
);

// Slide 8 — future plan.
setText(7, 0, "未來工作規劃｜三條主線");
setText(7, 1, "8");
setText(7, 2, "團隊 × 技術 × 標準化");
setText(
  7,
  3,
  "團隊｜推進多能工訓練，落實 AB 角與帶教機制\n技術｜向前端延伸，掌握客戶需求與新製程動向\n標準｜持續推進 7S 與作業流程標準化\n\n目標｜提升人員彈性、問題預防與複製效率",
);
setNotes(
  slides[7],
  "未來我聚焦三條主線：第一，建立多能工與AB角，降低單點依賴；第二，向前端了解客戶與新製程，使製造更早介入；第三，持續推進7S與流程標準化。目標是讓團隊更有彈性、問題更早被看見、方法可以複製。",
  [10],
);

// Slide 9 — leadership path.
setText(8, 0, "個人及組織發展規劃");
setText(8, 1, "1");
setText(8, 2, "現場管理\n品質控制\n持續學習");
setText(8, 3, "技能提升");
setText(8, 4, "2");
setText(8, 5, "目標分解\n有效溝通\n風險決策");
setText(8, 6, "領導發展");
setText(8, 7, "3");
setText(8, 8, "協作機制\n衝突處理\n效率改善");
setText(8, 9, "團隊建設");
setText(8, 10, "4");
setText(8, 11, "多能工\nAB 角\n人才梯隊");
setText(8, 12, "人才培養");
setText(8, 13, "5");
setText(8, 14, "責任文化\n持續改善\n共同成長");
setText(8, 15, "文化建設");
setText(8, 16, "從自己完成，到帶領團隊持續完成");
setNotes(
  slides[8],
  "我對課長角色的理解，是從自己完成工作，轉為讓團隊持續完成。能力路徑分五層：先守住專業與現場，再做好目標、溝通與決策；接著建立協作機制、培養梯隊，最後形成責任與改善文化。",
  [11],
);

// Slide 10 — close.
setNotes(
  slides[9],
  "以上是我的晉升報告。我願意對團隊能力、交付結果與持續改善承擔更完整的責任，敬請各位主管指導。",
  [12],
);

for (let index = 0; index < slides.length; index += 1) {
  const number = String(index + 1).padStart(2, "0");
  const preview = await deck.export({ slide: slides[index], format: "png", scale: 1 });
  await fs.writeFile(path.join(previewDir, `slide-${number}.png`), Buffer.from(await preview.arrayBuffer()));
  const layout = await slides[index].export({ format: "layout" });
  await fs.writeFile(path.join(layoutDir, `slide-${number}.layout.json`), await layout.text(), "utf8");
}

const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(work, "final-montage.webp"), Buffer.from(await montage.arrayBuffer()));

const inspection = await deck.inspect({
  kind: "slide,textbox,shape,image,notes,layout",
  maxChars: 100000,
});
await fs.writeFile(path.join(work, "final-inspect.ndjson"), inspection.ndjson, "utf8");

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(output);

console.log(output);
