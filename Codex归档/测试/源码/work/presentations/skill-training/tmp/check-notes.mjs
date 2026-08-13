import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const p = await PresentationFile.importPptx(
  await FileBlob.load("C:/Users/lfaf-test/Documents/测试/outputs/01-Skill入门认知-非标自动化部门-带讲师提示版.pptx"),
);

const result = await p.inspect({ kind: "slide,notes", maxChars: 6000 });
console.log(result.ndjson);
