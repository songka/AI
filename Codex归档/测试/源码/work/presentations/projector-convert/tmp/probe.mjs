import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const p = await PresentationFile.importPptx(await FileBlob.load("C:/Users/lfaf-test/Documents/测试/outputs/AI-Skill培训最终交付包/ppt/07-新版01-AI名词比喻与关系-活泼版-带讲师备注.pptx"));
console.log("keys", Object.keys(p));
console.log("slideSize", p.slideSize, p.size);
console.log("slides", p.slides.items.length);
console.log("slide keys", Object.keys(p.slides.items[0]));
console.log("proto keys", Object.keys(p.toProto()));
console.log(JSON.stringify(p.toProto()).slice(0, 1000));
