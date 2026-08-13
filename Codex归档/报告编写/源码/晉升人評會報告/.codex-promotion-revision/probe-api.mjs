import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const source = "C:\\Users\\lfaf-test\\Documents\\报告编写\\晉升人評會報告\\宋佳骥_晉升人評會報告.pptx";
const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
const slide = presentation.slides.getItem(3);
const body = slide.elements.items.find((item) => item.name === "Content Placeholder 2");
console.log("slide keys", Object.keys(slide));
console.log("body keys", Object.keys(body));
console.log("body proto", Object.getOwnPropertyNames(Object.getPrototypeOf(body)));
console.log("text keys", Object.keys(body.text));
console.log("text proto", Object.getOwnPropertyNames(Object.getPrototypeOf(body.text)));
console.log("position", body.position, "frame", body.frame);
console.log((await presentation.help("*", { search: "shape position move delete remove zOrder charts speakerNotes", include: ["index", "notes"], maxChars: 12000 })).ndjson);
