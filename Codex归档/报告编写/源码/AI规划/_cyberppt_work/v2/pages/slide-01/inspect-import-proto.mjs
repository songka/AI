import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const p = await PresentationFile.importPptx(await FileBlob.load("../slide-02/slide-02.pptx"));
const proto = p.toProto();
console.log(JSON.stringify(Object.fromEntries(Object.entries(proto).map(([k,v])=>[k,{type:typeof v,array:Array.isArray(v),keys:v&&typeof v==='object'?Object.keys(v).slice(0,6):[],length:Array.isArray(v)?v.length:undefined}])),null,2));
