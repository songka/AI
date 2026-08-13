import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const sourcePptx = "C:/Users/lfaf-test/Documents/报告编写/.tmp_promotion_deck/template-starter.pptx";
const outputPptx = "C:/Users/lfaf-test/Documents/报告编写/晉升人評會報告/5- PBG 晉升報告範本-楊敏銳R03(1)_優化版.pptx";
const previewDir = "C:/Users/lfaf-test/Documents/报告编写/.tmp_promotion_deck/final-preview";
const layoutDir = "C:/Users/lfaf-test/Documents/报告编写/.tmp_promotion_deck/final-layout";

const COLORS = {
  navy: "#00457A",
  blue: "#1479B8",
  cyan: "#2FA8D4",
  ink: "#17324A",
  gray: "#455867",
  pale1: "#EEF8FC",
  pale2: "#E5F5FA",
  pale3: "#DDF0F7",
  line: "#8FC9DE",
  white: "#FFFFFF",
};

const FONT = "Microsoft JhengHei";

function slidesOf(presentation) {
  if (Array.isArray(presentation.slides?.items)) return presentation.slides.items;
  return Array.from(
    { length: presentation.slides.count },
    (_, index) => presentation.slides.getItem(index),
  );
}

function setCardText(shape, icon, stage, title, lines, fill, accent) {
  shape.fill = fill;
  shape.line = { style: "solid", fill: COLORS.line, width: 1.4 };
  shape.text.set([
    {
      runs: [{
        run: icon,
        textStyle: { fontSize: "48pt", color: accent, typeface: "Segoe UI Emoji" },
      }],
      paragraphStyle: { alignment: "left" },
      spaceAfter: 4,
    },
    {
      runs: [{
        run: stage,
        textStyle: { fontSize: "28pt", bold: true, color: accent, typeface: FONT },
      }],
      paragraphStyle: { alignment: "left" },
      spaceAfter: 8,
    },
    {
      runs: [{
        run: title,
        textStyle: { fontSize: "24pt", bold: true, color: COLORS.navy, typeface: FONT },
      }],
      paragraphStyle: { alignment: "left" },
      spaceAfter: 18,
    },
    ...lines.map((line, index) => ({
      runs: [{
        run: line,
        textStyle: {
          fontSize: "16pt",
          bold: index === lines.length - 1,
          color: index === lines.length - 1 ? COLORS.navy : COLORS.gray,
          typeface: FONT,
        },
      }],
      paragraphStyle: { alignment: "left" },
      spaceAfter: index === lines.length - 1 ? 0 : 12,
    })),
  ]);
  shape.text.style = {
    fontSize: 21.33,
    typeface: FONT,
    color: COLORS.ink,
    verticalAlignment: "middle",
    insets: { top: 28, right: 26, bottom: 28, left: 26 },
  };
}

function setTitle(shape, text) {
  shape.text = text;
  shape.position = { left: 88, top: 38.33, width: 720, height: 62.03 };
  shape.text.style = {
    fontSize: 48,
    bold: true,
    color: COLORS.navy,
    typeface: "Helvetica",
    alignment: "left",
    verticalAlignment: "middle",
  };
}

async function saveBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePptx));
  const slides = slidesOf(presentation);
  const titleLayout = presentation.layouts.items.find((layout) => layout.name === "Title Slide");
  titleLayout.shapes.items.find((shape) => shape.name === "Text Placeholder 21").text = "楊敏銳";
  titleLayout.shapes.items.find((shape) => shape.name === "Text Placeholder 23").text = "2026.07.28";

  // 第 10 頁：三階段技術升級路徑。
  setTitle(presentation.resolve("sh/xc3mho32"), "未來工作規劃");

  const s10Card1 = presentation.resolve("sh/1cru1g3y");
  s10Card1.position = { left: 88, top: 169.94, width: 312.8, height: 435.6 };
  setCardText(
    s10Card1,
    "🏭",
    "01",
    "裝配技術專精",
    [
      "行動｜研究各類設備裝配",
      "沉澱｜歸納方法與驗證",
      "價值｜提升複雜設備交付力",
    ],
    COLORS.pale1,
    COLORS.blue,
  );

  const s10Card2 = presentation.resolve("sh/e9gb61k7");
  s10Card2.position = { left: 437.73, top: 169.94, width: 343.47, height: 435.6 };
  s10Card2.fill = COLORS.pale2;
  s10Card2.line = { style: "solid", fill: COLORS.line, width: 1.4 };

  const s10Icon2 = presentation.resolve("im/nidcv6po");
  s10Icon2.frame = { left: 594, top: 205, width: 92, height: 80 };

  const s10Title2 = presentation.resolve("sh/ozitcv29");
  s10Title2.position = { left: 496, top: 302, width: 288, height: 62 };
  s10Title2.text.set([
    [{
      run: "02  標準沉澱",
      textStyle: { fontSize: "24pt", bold: true, color: COLORS.navy, typeface: FONT },
    }],
  ]);
  s10Title2.text.style = { alignment: "left", verticalAlignment: "middle", typeface: FONT };

  const s10Body2 = presentation.resolve("sh/p0ru503u");
  s10Body2.position = { left: 496, top: 370, width: 288, height: 202 };
  s10Body2.text.set([
    { runs: [{ run: "行動｜深化製程標準", textStyle: { fontSize: "16pt", color: COLORS.gray, typeface: FONT } }], spaceAfter: 12 },
    { runs: [{ run: "制度｜統一作業規範", textStyle: { fontSize: "16pt", color: COLORS.gray, typeface: FONT } }], spaceAfter: 12 },
    { runs: [{ run: "價值｜降低人為差異", textStyle: { fontSize: "16pt", bold: true, color: COLORS.navy, typeface: FONT } }] },
  ]);
  s10Body2.text.style = {
    fontSize: 21.33,
    typeface: FONT,
    alignment: "left",
    verticalAlignment: "top",
    insets: { top: 8, right: 0, bottom: 0, left: 0 },
  };

  const s10Card3 = presentation.resolve("sh/xwnupgvy");
  s10Card3.position = { left: 818.13, top: 169.94, width: 354.27, height: 435.35 };
  setCardText(
    s10Card3,
    "🤖",
    "03",
    "數位提效（AI 化）",
    [
      "辦公｜Routing、工時 KEY IN",
      "服務｜LFAF 售後管理小程式",
      "價值｜客戶聲音形成改善閉環",
    ],
    COLORS.pale3,
    COLORS.cyan,
  );

  // 第 11 頁：人才與組織升級路徑。
  setTitle(presentation.resolve("sh/xcryxg7y"), "人才與組織發展");

  const s11Card1 = presentation.resolve("sh/xgnehwri");
  s11Card1.position = { left: 88, top: 160, width: 340, height: 444 };
  setCardText(
    s11Card1,
    "👥",
    "01",
    "人才多能",
    [
      "建立技能矩陣，掌握能力缺口",
      "培養電工、鉗工、調試多技能",
      "成果｜形成可彈性調度的多能工梯隊",
    ],
    COLORS.pale1,
    COLORS.blue,
  );

  const s11Card2 = presentation.resolve("sh/fmlw729k");
  s11Card2.position = { left: 470, top: 160, width: 340, height: 444 };
  setCardText(
    s11Card2,
    "🧰",
    "02",
    "售後整合",
    [
      "培養售後人員的 PLC 與電控能力",
      "逐步承接現場調試工作",
      "成果｜提升響應速度，釋放電控人力",
    ],
    COLORS.pale2,
    COLORS.blue,
  );

  const s11Card3 = presentation.resolve("sh/jutoj2lk");
  s11Card3.position = { left: 852, top: 160, width: 340, height: 444 };
  setCardText(
    s11Card3,
    "🤖",
    "03",
    "自動化生產",
    [
      "推進「機器組裝機器」",
      "將設備組裝方法導入精益生產",
      "成果｜建立可複製的自動化裝配模式",
    ],
    COLORS.pale3,
    COLORS.cyan,
  );

  const notes = [
    "本頁重點：以一句話交代報告目的與個人定位。\n建議講法：各位評審好，我是楊敏銳，現任 LFAF 精益彈性自動化中心製造部門主管。本次報告將用成果、能力與未來規劃三部分，說明我為何已具備承擔更高職責的準備。",
    "本頁重點：先建立聽眾預期，報告依序回答「我是誰、做成什麼、下一步怎麼做」。\n建議講法：前半段快速交代個人經歷與核心能力；中段用專案、團隊及標準化成果證明績效；最後聚焦未來工作與組織發展規劃。",
    "本頁重點：從品質到製造管理，呈現能力範圍持續擴大。\n建議講法：2009 年從品質工程起步，2018 年進入漢揚 LFAF 品質部門，2023 年轉任 LFAF 製造部門主管。職務雖不同，但核心始終是對結果負責並推動團隊與業務發展。",
    "本頁重點：四項優勢共同支撐「能交付、能學習、能帶人、能解題」。\n建議講法：先講執行力與學習力，說明自己如何把任務拆解並快速補足機構、電控知識；再講教導力與問題解決能力，強調能把個人經驗轉化成團隊能力與可複製方法。",
    "本頁重點：用多個重大專案證明跨線別、跨設備的交付能力。\n建議講法：不要逐張念照片，選兩到三個代表案例，說明專案規模、我的責任與交付結果；最後總結，重點不是完成單一設備，而是建立穩定交付多專案的團隊能力。",
    "本頁重點：從零搭建 6 人調試售後團隊，完成職能分工與流程建立。\n建議講法：先講為什麼要組隊，再講三個結果：對外 24 小時內響應、對內釋放電控人力、建立調試期到保固外的統一流程。強調這是組織能力的形成，不只是人員增加。",
    "本頁重點：以配盤佈局與線材顏色標準化，降低差異並提高可維護性。\n建議講法：左側講「佈局標準」，右側照片指出元件排列與線色規範。評審最需要聽到的是：標準化讓新人更容易執行，也讓後續排查與維修更有效率。",
    "本頁重點：把標籤、線纜與取出臂佈線做成可辨識、可維護的標準。\n建議講法：依序指出三組照片對應的改善：標籤清楚、線束一致、快換設計。最後收斂到一點：把個人經驗轉為目視化規範，才能穩定複製品質。",
    "本頁重點：非生產物料由被動補貨改為有標準、有清單、可預警。\n建議講法：用「改善前—改善後—效益」三段說明。改善前容易缺料與臨時採購；改善後建立標準庫存與清單；效益是降低停等、縮短取料時間並減少不必要成本。",
    "本頁重點：未來技術路線分三步，先做深、再做穩、最後做快。\n建議講法：第一步深化不同設備的裝配技術；第二步把方法沉澱為標準，降低人為差異；第三步用 AI 與數位工具改善辦公、售後與客戶回饋閉環。三步不是平行專案，而是由能力到制度再到效率的升級。",
    "本頁重點：組織發展分三條路徑，讓人才、服務與生產能力同步升級。\n建議講法：人才端建立技能矩陣與多能工梯隊；售後端補強 PLC 與電控能力，逐步承接調試；生產端推進「機器組裝機器」與精益方法。最終目標是更快響應、更少依賴單點人才、形成可複製的組織能力。",
    "本頁重點：用一句話收束晉升價值並邀請提問。\n建議講法：我的核心價值，是把個人技術經驗轉化為團隊、標準與持續改善機制。未來我會以更高層級的責任，持續提升交付、人才與數位化能力。謝謝各位，歡迎提問。",
  ];

  slides.forEach((slide, index) => {
    slide.speakerNotes.textFrame.setText(notes[index]);
    slide.speakerNotes.setVisible(true);
  });

  await fs.mkdir(previewDir, { recursive: true });
  await fs.mkdir(layoutDir, { recursive: true });
  for (let index = 0; index < slides.length; index += 1) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await saveBlob(
      `${previewDir}/${stem}.png`,
      await presentation.export({ slide: slides[index], format: "png", scale: 1 }),
    );
    const layout = await slides[index].export({ format: "layout" });
    await fs.writeFile(`${layoutDir}/${stem}.layout.json`, await layout.text(), "utf8");
  }
  await saveBlob(
    "C:/Users/lfaf-test/Documents/报告编写/.tmp_promotion_deck/final-montage.webp",
    await presentation.export({ format: "webp", montage: true, scale: 1 }),
  );

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPptx);
  console.log(outputPptx);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
