import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const sourcePath = "C:/Users/lfaf-test/Documents/PLC-Programming(PLC编程开发综合)/2.csv";
const outputDir = "C:/Users/lfaf-test/Documents/PLC-Programming(PLC编程开发综合)/outputs/global_vars_20axis_20260720";
const bytes = await fs.readFile(sourcePath);
const csvText = new TextDecoder("gbk").decode(bytes);
const imported = await Workbook.fromCSV(csvText, { sheetName: "导入" });
const rawValues = imported.worksheets.getItem("导入").getUsedRange().values;
const headers = rawValues[0].map(v => String(v ?? ""));
const body = rawValues.slice(1).filter(r => [r[1], r[2], r[3]].some(v => String(v ?? "").trim() !== ""));
const rows = body.map((r, idx) => ({
  line: idx + 2,
  cls: String(r[0] ?? ""), id: String(r[1] ?? ""), address: String(r[2] ?? ""),
  type: String(r[3] ?? ""), initial: String(r[4] ?? ""), comment: String(r[5] ?? "")
}));

function category(id, address) {
  if (/^X/i.test(address) || /^EXIN_/.test(id)) return "物理DI";
  if (/^Y/i.test(address) || /^EXOUT_/.test(id)) return "物理DO";
  if (/^ALM_/.test(id)) return "报警";
  if (/^HMI_/.test(id)) return "HMI";
  if (/伺服|轴|JOG|寸动|目标位置|当前位置|回原点速度/.test(id)) return "轴/运动";
  if (/robot|机械手|^UO_|^UI_/i.test(id)) return "机器人";
  if (/通讯|^read|^write/i.test(id)) return "通信";
  if (/^STATE_|^STOP_|^WT_/.test(id)) return "系统状态";
  return "工艺/内部";
}

function typeBits(type) {
  let m = type.match(/^ARRAY\s*\[(\d+)\]\s*OF\s*(BOOL|WORD|DWORD)/i);
  if (m) return Number(m[1]) * ({ BOOL: 1, WORD: 16, DWORD: 32 })[m[2].toUpperCase()];
  if (/^BOOL$/i.test(type)) return 1;
  if (/^WORD$/i.test(type)) return 16;
  if (/^DWORD$/i.test(type)) return 32;
  m = type.match(/^STRING\((\d+)\)/i);
  if (m) return (Math.ceil(Number(m[1]) / 2) + 1) * 16;
  return 0;
}

function dStart(address) {
  const m = address.match(/^D(\d+)(?:\.(\d+))?$/i);
  if (!m) return null;
  return Number(m[1]) * 16 + Number(m[2] ?? 0);
}

const occupancy = new Map();
rows.forEach((r, i) => {
  const start = dStart(r.address), len = typeBits(r.type);
  if (start === null || !len) return;
  for (let bit = start; bit < start + len; bit++) {
    if (!occupancy.has(bit)) occupancy.set(bit, []);
    occupancy.get(bit).push(i);
  }
});
const pairMap = new Map();
for (const [bit, ids] of occupancy) {
  if (ids.length < 2) continue;
  for (let a = 0; a < ids.length; a++) for (let b = a + 1; b < ids.length; b++) {
    const key = `${Math.min(ids[a], ids[b])}|${Math.max(ids[a], ids[b])}`;
    if (!pairMap.has(key)) pairMap.set(key, { a: Math.min(ids[a], ids[b]), b: Math.max(ids[a], ids[b]), bits: [] });
    pairMap.get(key).bits.push(bit);
  }
}
const overlaps = [...pairMap.values()].map(p => {
  const min = Math.min(...p.bits), max = Math.max(...p.bits);
  const fmt = n => `D${Math.floor(n / 16)}.${n % 16}`;
  return { ...p, range: min === max ? fmt(min) : `${fmt(min)}～${fmt(max)}` };
});

function issue(r) {
  const out = [];
  if (!r.address) out.push("未固定地址");
  if (!r.comment) out.push("缺少注释");
  if (/ARRAY\s*\[(10|16)\]/i.test(r.type) && /伺服|轴|JOG|寸动|位置|速度|公差|脉冲|极限|加速度|减速度/.test(r.id)) out.push("轴容量不足20");
  if (/屏蔽|最高速率/.test(r.id)) out.push("旁路/权限风险");
  if (/当前位置/.test(r.id) && /^D20\d{3}/.test(r.address)) out.push("实时值位于保持候选区");
  return out.join("；");
}

const wb = Workbook.create();
const C = { navy:"#17365D", blue:"#D9EAF7", yellow:"#FFF2CC", red:"#F4CCCC", green:"#E2F0D9", gray:"#E7E6E6", white:"#FFFFFF", line:"#B4C6E7" };
function colLetter(n) { let s=""; while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);} return s; }
function sheetBase(name,title,note,heads,totalRows=30){
  const sh=wb.worksheets.add(name); sh.showGridLines=false; const last=colLetter(heads.length);
  sh.getRange(`A1:${last}1`).merge(); sh.getRange("A1").values=[[title]]; sh.getRange("A1").format={fill:C.navy,font:{name:"Microsoft YaHei",size:16,bold:true,color:C.white},rowHeight:30,verticalAlignment:"center"};
  sh.getRange(`A2:${last}2`).merge(); sh.getRange("A2").values=[[note]]; sh.getRange("A2").format={fill:C.blue,font:{name:"Microsoft YaHei",size:10,italic:true},wrapText:true,rowHeight:32};
  sh.getRange(`A4:${last}4`).values=[heads]; sh.getRange(`A4:${last}4`).format={fill:C.navy,font:{name:"Microsoft YaHei",size:10,bold:true,color:C.white},wrapText:true,rowHeight:28,horizontalAlignment:"center",borders:{preset:"all",style:"thin",color:C.line}};
  sh.freezePanes.freezeRows(4); sh.freezePanes.freezeColumns(Math.min(2,heads.length));
  if(totalRows>4) sh.getRange(`A5:${last}${totalRows}`).format={font:{name:"Microsoft YaHei",size:10},wrapText:true,verticalAlignment:"center",borders:{preset:"all",style:"thin",color:"#D9E2F3"}};
  return sh;
}
function setWidths(sh, widths){widths.forEach((w,i)=>sh.getRangeByIndexes(0,i,1,1).format.columnWidth=w);}
function writeRows(sh, data, lastCol){ if(data.length) sh.getRange(`A5:${lastCol}${4+data.length}`).values=data; }

const summary=wb.worksheets.add("总结"); summary.showGridLines=false;
summary.getRange("A1:H1").merge(); summary.getRange("A1").values=[["AS228T 全局变量总结与 20 轴优化（送审版）"]]; summary.getRange("A1").format={fill:C.navy,font:{name:"Microsoft YaHei",size:18,bold:true,color:C.white},rowHeight:36};
summary.getRange("A3:B10").values=[["来源","2.csv（现有程序全局变量）"],["有效变量",""],["固定地址变量",""],["无固定地址变量",""],["缺少注释",""],["轴容量不足20",""],["地址占用重叠对",""],["结论","轴参数区不能原地扩展，建议整体迁移"]];
summary.getRange("A3:A10").format={fill:C.navy,font:{bold:true,color:C.white},borders:{preset:"all",style:"thin",color:C.line}};
summary.getRange("B3:B10").format={fill:C.blue,wrapText:true,borders:{preset:"all",style:"thin",color:C.line}};
summary.getRange("A12:H12").merge(); summary.getRange("A12").values=[["核心优化决定"]]; summary.getRange("A12").format={fill:C.navy,font:{bold:true,color:C.white}};
summary.getRange("A13:H19").values=[
  ["1","保留现有非轴变量地址，降低整体改造风险","","","","","",""] ,
  ["2","现有 10 轴 DWORD 参数数组每组占 20 字，扩到 20 轴需 40 字，会覆盖下一数组；统一迁移到 D23000～D23799","","","","","",""] ,
  ["3","轴实时命令、状态、报警和位置迁移到非保持运行区 D3000～D3399；配置参数放 D23000～D23799 保持候选区","","","","","",""] ,
  ["4","按参数建立 ARRAY[20]，兼容当前程序风格；轴号统一 1～20，数组索引规则须在程序内固定为 0～19 或 1～20","","","","","",""] ,
  ["5","HMI 屏蔽、安全门屏蔽、最高速率等变量必须增加权限、超时自动撤销、操作记录和显著状态提示","","","","","",""] ,
  ["6","报警从当前散列位优化为每轴报警字+报警代码，同时保留标准 HMI 报警文本","","","","","",""] ,
  ["7","本文件是迁移方案，不可直接替换在线项目；先编译、交叉引用、离线仿真，再分阶段切换","","","","","",""]
];
summary.getRange("A13:H19").format={fill:C.yellow,wrapText:true,borders:{preset:"all",style:"thin",color:C.line}}; summary.getRange("A13:A19").format.font={bold:true};
summary.getRange("A21:H25").merge(); summary.getRange("A21").values=[["20 轴建议容量：运行区每轴折算约 20 字，合计预留 400 字；参数区每个 DWORD 参数 40 字，18 组共 720 字，再加类型/启用/模式及预留。D23000～D23799 共 800 字可容纳当前建议，D23800～D23999 保留后续扩展。\n\n保持属性以实际 ISPSoft/HWCONFIG 为准；D20000～D23999 仅是手册默认保持区，不代表当前项目配置。"]]; summary.getRange("A21").format={fill:C.gray,wrapText:true,rowHeight:88,borders:{preset:"outside",style:"thin",color:C.line}};
setWidths(summary,[10,28,14,14,14,14,14,14]);

const original=sheetBase("原始变量","现有全局变量整理","保留 2.csv 原值；“类别”和“检查结果”为分析列。红色检查项需优先审核。",[...headers,"类别","检查结果","建议动作","固定地址标志","缺注释标志","轴不足20标志"],4+rows.length);
const originalData=rows.map(r=>{const chk=issue(r);return[r.cls,r.id,r.address,r.type,r.initial,r.comment,category(r.id,r.address),chk,chk.includes("轴容量不足20")?"迁移到20轴区":(!r.comment?"补注释":"保留/核实"),r.address?1:0,r.comment?0:1,chk.includes("轴容量不足20")?1:0]});
writeRows(original,originalData,"L"); setWidths(original,[10,32,16,24,14,44,14,32,18,12,12,14]);
original.getRange(`A5:L${4+rows.length}`).format.fill=C.blue;
original.getRange(`H5:H${4+rows.length}`).conditionalFormats.add("containsText",{text:"轴容量不足20",format:{fill:C.red,font:{color:"#9C0006",bold:true}}});
original.getRange(`H5:H${4+rows.length}`).conditionalFormats.add("containsText",{text:"旁路/权限风险",format:{fill:C.red,font:{color:"#9C0006",bold:true}}});

const ov=sheetBase("地址重叠","现有 D 地址重叠检查","按 BOOL/WORD/DWORD/数组占用位展开检查。重叠可能是有意别名，也可能是整字覆盖位地址，必须逐项确认写入者。",["序号","变量A","地址A","类型A","变量B","地址B","类型B","重叠范围","风险判断","处理建议"],Math.max(20,4+overlaps.length));
const ovData=overlaps.map((p,i)=>{const a=rows[p.a],b=rows[p.b];const wordMix=(!/^BOOL$/i.test(a.type)||!/^BOOL$/i.test(b.type));return[i+1,a.id,a.address,a.type,b.id,b.address,b.type,p.range,wordMix?"整字/数组覆盖风险":"同位重复","确认唯一写入者；必要时拆分地址"]});
writeRows(ov,ovData,"J"); setWidths(ov,[10,30,15,22,30,15,22,24,20,34]); if(ovData.length) ov.getRange(`A5:J${4+ovData.length}`).format.fill=C.red;

const issues=sheetBase("优化问题","现状问题与优先级","问题按迁移风险排序；不把“无固定地址”一概当错误，内部变量可由编译器分配。",["优先级","问题","证据/数量","影响","建议"],[].length+15);
const axisShort=rows.filter(r=>/ARRAY\s*\[(10|16)\]/i.test(r.type)&&/伺服|轴|JOG|寸动|位置|速度|公差|脉冲|极限|加速度|减速度/.test(r.id)).length;
const issueRows=[
  ["P1","10轴数组无法原地扩到20轴",`${axisShort} 项轴相关数组为10或16长度；D20020起的DWORD数组相邻仅隔20字`,"扩容会覆盖下一变量","整体迁移到D23000起的新参数区"],
  ["P1","潜在地址重叠",`${overlaps.length} 对按位展开后重叠`,"整字写入可能覆盖D字位","逐项确认生产者；禁止不同POU混写"],
  ["P1","安全门/报警屏蔽由HMI直接保持","存在安全门屏蔽、机器人报警屏蔽等变量","误操作或重启后持续旁路","权限+超时撤销+记录；不得替代安全回路"],
  ["P2","实时位置位于默认保持候选区","HMI_当前位置=D20240", "运行值与参数混区，掉电语义不清","迁移到D3120运行区，不保持"],
  ["P2","轴报警按1～10手工散列","D411～D412仅覆盖10轴", "扩到20轴需大量手工位且易漏","每轴一报警字D3040～D3059+报警码"],
  ["P2","注释覆盖率低",`${rows.filter(r=>!r.comment).length}/${rows.length} 条无注释`,"难以确认方向、单位、保持和写入者","至少补方向、单位、生产者、失效值"],
  ["P3","命名规则混合", "中文、英文、read/write、DI/DO、EXIN/EXOUT并存", "搜索与维护成本高","新变量统一AXIS/RBT/HMI/ALM前缀，旧变量分阶段迁移"],
  ["P3","132个内部变量未固定地址",`${rows.filter(r=>!r.address).length} 条`,"不一定错误，但外部HMI/通信不可依赖","仅接口变量固定D；纯内部变量可保留符号地址"]
]; writeRows(issues,issueRows,"E"); setWidths(issues,[12,32,30,34,48]); issues.getRange("A5:E7").format.fill=C.red; issues.getRange("A8:E12").format.fill=C.yellow;

const plan=sheetBase("20轴规划","20 轴地址总规划","采用“参数数组+运行字块”混合方式：便于HMI批量访问，也能按轴快速监控。",["区域","起始","结束","字数","保持建议","用途","生产者","消费者","备注"],18);
const planRows=[
  ["轴运行接口","D3000","D3399",400,"否","20轴命令/状态/报警/位置/速度/序号/质量","AXIS_MGR/通信分向","HMI/顺控/驱动","掉线置无效，不保持"],
  ["轴运行预留","D3400","D3499",100,"否","后续运行字段和诊断","AXIS_MGR","HMI/诊断","暂不分配"],
  ["轴参数","D23000","D23799",800,"项目确认","20轴速度、限位、加减速、比例、偏移等","参数管理/HMI授权","AXIS_MGR","默认保持候选区内"],
  ["轴参数预留","D23800","D23999",200,"项目确认","后续轴参数/版本迁移","参数管理","AXIS_MGR","禁止放运行命令和实时状态"],
  ["现有点位区","D21000","D22999",2000,"项目确认","现有100点×20字","现有程序/HMI","运动程序","保持现状，不与新轴参数重叠"]
]; writeRows(plan,planRows,"I"); setWidths(plan,[18,14,14,12,16,34,22,22,36]); plan.getRange("A5:I9").format.fill=C.blue;

const axisMap=sheetBase("每轴地址","20 轴运行地址索引","轴号1～20；地址按参数数组展开。命令/状态/报警字使用各轴对应D字的位0～15。",["轴号","命令字D","状态字D","报警字D","报警代码","目标位置DWORD","当前位置DWORD","目标速度DWORD","实际速度DWORD","命令序号","序号回显","质量字","参数索引"],24);
const axisRows=[]; for(let a=1;a<=20;a++){const i=a-1;axisRows.push([a,`D${3000+i}`,`D${3020+i}`,`D${3040+i}`,`D${3060+i}`,`D${3080+i*2}:D${3081+i*2}`,`D${3120+i*2}:D${3121+i*2}`,`D${3160+i*2}:D${3161+i*2}`,`D${3200+i*2}:D${3201+i*2}`,`D${3240+i}`,`D${3260+i}`,`D${3280+i}`,i]);}
writeRows(axisMap,axisRows,"M"); setWidths(axisMap,[10,14,14,14,14,20,20,20,20,14,14,14,12]); axisMap.getRange("A5:M24").format.fill=C.blue;

const bitDef=sheetBase("轴位定义","轴命令、状态与报警位定义","同一D字由一个生产者管理。通信写入状态字时，PLC只能读取其D位；PLC生成命令字时，外部设备只能读取。",["字类型","位","标准符号后缀","中文含义","生产者","失效值","说明"],45);
const cmd=[[0,"EnableReq","接口使能"],[1,"ServoOnReq","伺服使能请求"],[2,"ResetReq","复位请求"],[3,"HomeReq","回原点请求"],[4,"MoveAbsReq","绝对定位请求"],[5,"MoveRelReq","相对定位请求"],[6,"JogPosReq","正向点动请求"],[7,"JogNegReq","反向点动请求"],[8,"StopReq","停止请求"],[9,"PauseReq","暂停请求"],[10,"ResumeReq","恢复请求"],[11,"SetZeroReq","设零请求"],[12,"AlarmAckReq","报警确认请求"]];
const sts=[[0,"Online","在线"],[1,"Ready","就绪"],[2,"ServoOn","伺服已使能"],[3,"Homed","原点已建立"],[4,"Busy","动作中"],[5,"InPosition","位置到达"],[6,"Jogging","点动中"],[7,"Alarm","报警"],[8,"PosLimit","正限位"],[9,"NegLimit","负限位"],[10,"Stopped","已停止"],[11,"CmdAccepted","命令已接受"],[12,"CommOK","通信正常"]];
const alm=[[0,"DriveAlarm","驱动报警"],[1,"CommTimeout","通信超时"],[2,"HomeTimeout","回原点超时"],[3,"MoveTimeout","定位超时"],[4,"PosLimitAlarm","正限位报警"],[5,"NegLimitAlarm","负限位报警"],[6,"FeedbackError","反馈异常"],[7,"ParameterInvalid","参数无效"],[8,"InterlockMissing","互锁不满足"],[9,"UnexpectedMotion","非预期运动"],[10,"ServoNotReady","伺服未就绪"]];
const bits=[]; cmd.forEach(x=>bits.push(["命令字",x[0],x[1],x[2],"PLC轴管理","FALSE","请求保持至确认或超时"])); sts.forEach(x=>bits.push(["状态字",x[0],x[1],x[2],"驱动/轴管理","FALSE","超时后质量无效"])); alm.forEach(x=>bits.push(["报警字",x[0],x[1],x[2],"报警管理","按风险","Active与Latched另行管理"]));
writeRows(bitDef,bits,"G"); setWidths(bitDef,[14,10,24,24,20,14,38]); bitDef.getRange(`A5:G${4+bits.length}`).format.fill=C.blue;

const paramDefs=[
 ["AXIS_手动JOG低速","D23000","手动低速","mm/s或pulse/s"],["AXIS_手动JOG中速","D23040","手动中速","mm/s或pulse/s"],["AXIS_手动JOG高速","D23080","手动高速","mm/s或pulse/s"],["AXIS_回原点速度","D23120","回零速度","mm/s或pulse/s"],
 ["AXIS_生产运行速度","D23160","自动运行速度","mm/s或pulse/s"],["AXIS_正向软件限位","D23200","正向软件限位","工程单位"],["AXIS_反向软件限位","D23240","反向软件限位","工程单位"],["AXIS_加速度","D23280","加速度","工程单位/s²"],
 ["AXIS_减速度","D23320","减速度","工程单位/s²"],["AXIS_到位公差","D23360","位置到达公差","工程单位"],["AXIS_每转脉冲数","D23400","编码/脉冲比例","pulse/rev"],["AXIS_减速点","D23440","减速切换位置","工程单位"],
 ["AXIS_慢速过程速度","D23480","慢速工艺速度","工程单位/s"],["AXIS_点动距离","D23520","寸动距离","工程单位"],["AXIS_回零偏移","D23560","原点偏移","工程单位"],["AXIS_电子齿轮分子","D23600","电子齿轮分子","count"],
 ["AXIS_电子齿轮分母","D23640","电子齿轮分母","count"],["AXIS_最大速度","D23680","允许最大速度","工程单位/s"]
];
const gvlRows=[];
paramDefs.forEach(p=>gvlRows.push(["VAR",p[0],p[1],"ARRAY [20] OF DWORD","",`${p[2]}；轴索引0～19；单位=${p[3]}`,"参数管理/HMI授权","项目确认"]));
gvlRows.push(["VAR","AXIS_报警代码","D3060","ARRAY [20] OF WORD","","轴报警代码；0=无报警","报警管理","否"]);
for(const [id,addr,desc] of [["AXIS_目标位置","D3080","运行目标位置"],["AXIS_当前位置","D3120","实时反馈位置"],["AXIS_目标速度","D3160","运行目标速度"],["AXIS_实际速度","D3200","实时反馈速度"]]) gvlRows.push(["VAR",id,addr,"ARRAY [20] OF DWORD","",`${desc}；轴索引0～19`,`AXIS_MGR/驱动分向`,"否"]);
for(const [id,addr,desc] of [["AXIS_命令序号","D3240","命令序号"],["AXIS_命令序号回显","D3260","命令处理回显"],["AXIS_质量字","D3280","在线/超时/数据有效"]]) gvlRows.push(["VAR",id,addr,"ARRAY [20] OF WORD","",`${desc}；轴索引0～19`,`AXIS_MGR/驱动分向`,"否"]);
for(let a=1;a<=20;a++){
  const ax=String(a).padStart(2,"0"), cmdD=3000+a-1, stsD=3020+a-1, almD=3040+a-1;
  cmd.forEach(x=>gvlRows.push(["VAR",`AX${ax}_${x[1]}`,`D${cmdD}.${x[0]}`,"BOOL","",x[2],"AXIS_MGR","否"]));
  sts.forEach(x=>gvlRows.push(["VAR",`AX${ax}_${x[1]}`,`D${stsD}.${x[0]}`,"BOOL","",x[2],"驱动/通信","否"]));
  alm.forEach(x=>gvlRows.push(["VAR",`AX${ax}_${x[1]}`,`D${almD}.${x[0]}`,"BOOL","",x[2],"报警管理","否"]));
}
const gvl=sheetBase("20轴GVL","20 轴优化变量定义（替换段）","仅替换现有轴相关变量，不要与旧轴变量同时导入。方向、单位、数组下标和保持区须经项目审核。",["Class","Identifiers","Address","Type","Initial Value","Comment","生产者/写入者","保持"],4+gvlRows.length);
writeRows(gvl,gvlRows,"H"); setWidths(gvl,[10,30,16,24,14,48,22,14]); gvl.getRange(`A5:H${4+gvlRows.length}`).format.fill=C.yellow;
gvl.getRange(`C5:C${4+gvlRows.length}`).conditionalFormats.add("duplicateValues",{format:{fill:C.red,font:{color:"#9C0006",bold:true}}});

const migration=sheetBase("迁移清单","现有轴变量迁移建议","先建立新变量和转换层，再逐个POU/HMI画面替换，最后删除旧变量。",["旧变量","旧地址","旧类型","新变量/结构","新地址","新类型","迁移动作","风险"],120);
const mig=[];
const known=new Map(paramDefs.map(p=>[p[0].replace("AXIS_","HMI_"),p]));
known.set("HMI_正向极限位设置",["AXIS_正向软件限位","D23200"]); known.set("HMI_反向极限位设置",["AXIS_反向软件限位","D23240"]); known.set("HMI_伺服加速度",["AXIS_加速度","D23280"]); known.set("HMI_伺服减速度",["AXIS_减速度","D23320"]); known.set("HMI_跑点公差",["AXIS_到位公差","D23360"]); known.set("HMI_减速点高度",["AXIS_减速点","D23440"]); known.set("HMI_寸动量",["AXIS_点动距离","D23520"]);
for(const r of rows){
  if(known.has(r.id)){const p=known.get(r.id);mig.push([r.id,r.address,r.type,p[0],p[1],"ARRAY [20] OF DWORD","复制旧0～9轴参数，10～19轴用受控默认值","高"]);}
}
mig.push(["HMI_当前位置","D20240","ARRAY [10] OF DWORD","AXIS_当前位置","D3120","ARRAY [20] OF DWORD","改为非保持实时区；HMI标签同步修改","高"]);
mig.push(["HMI_目标位置","D20260","ARRAY [10] OF DWORD","AXIS_目标位置","D3080","ARRAY [20] OF DWORD","确认目标位置是否为运行值或示教值；示教值应另存点位区","高"]);
mig.push(["HMI_轴JOG加","D39.0","ARRAY [10] OF BOOL","AX01～AX20_JogPosReq","D3000.6～D3019.6","20个BOOL","HMI逐轴改绑；按住有效，松开/掉线停止","高"]);
mig.push(["HMI_轴JOG减","D40.0","ARRAY [10] OF BOOL","AX01～AX20_JogNegReq","D3000.7～D3019.7","20个BOOL","HMI逐轴改绑；按住有效，松开/掉线停止","高"]);
for(let a=1;a<=10;a++){
  const oldBase=411*16+(a-1)*3; const oldFmt=n=>`D${Math.floor(n/16)}.${n%16}`;
  mig.push([`ALM_伺服${a}故障`,oldFmt(oldBase),"BOOL",`AX${String(a).padStart(2,"0")}_DriveAlarm`,`D${3039+a}.0`,"BOOL","报警逻辑改绑；补轴11～20","中"]);
  mig.push([`ALM_伺服${a}超反向极限`,oldFmt(oldBase+1),"BOOL",`AX${String(a).padStart(2,"0")}_NegLimitAlarm`,`D${3039+a}.5`,"BOOL","报警逻辑改绑；补轴11～20","中"]);
  mig.push([`ALM_伺服${a}超正向极限`,oldFmt(oldBase+2),"BOOL",`AX${String(a).padStart(2,"0")}_PosLimitAlarm`,`D${3039+a}.4`,"BOOL","报警逻辑改绑；补轴11～20","中"]);
}
writeRows(migration,mig,"H"); setWidths(migration,[30,18,24,34,22,24,48,12]); migration.getRange(`A5:H${4+mig.length}`).format.fill=C.yellow; migration.getRange(`H5:H${4+mig.length}`).dataValidation={rule:{type:"list",values:["高","中","低"]}};

const review=sheetBase("审核清单","实施前审核清单","每项通过后才能进入正式GVL和HMI改造。",["序号","审核项","通过标准","责任角色","结论","备注"],24);
const reviewRows=[
 [1,"数组下标","确认ISPSoft项目统一使用0～19或1～20，禁止混用","PLC","待审核",""],[2,"D地址冲突","与HWCONFIG、通信表、点位区、保持区无冲突","PLC","待审核",""],[3,"保持区","D23000～D23999实际配置为所需保持属性","PLC","待审核",""],[4,"轴类型","20轴逐一标注CANopen/脉冲、驱动型号、比例、单位","电气/PLC","待审核",""],[5,"命令所有权","每个命令位只有AXIS_MGR写入；HMI仅发请求","PLC/HMI","待审核",""],[6,"状态所有权","通信/驱动写状态，PLC不得反写","PLC","待审核",""],[7,"点动失效","松开、切画面、HMI掉线、PLC STOP均验证停止行为","PLC/HMI/调试","待审核",""],[8,"参数迁移","旧轴1～10参数逐项核对；轴11～20使用受控默认值","PLC/工艺","待审核",""],[9,"报警语言","20轴报警文本使用“轴号：客观异常状态”并有独立处置建议","PLC/HMI","待审核",""],[10,"屏蔽治理","安全门/报警屏蔽有权限、时限、记录和显著提示","安全/PLC/HMI","待审核",""],[11,"交叉引用","旧变量所有读写点、HMI标签和通信映射已迁移","PLC/HMI","待审核",""],[12,"验证","编译、离线测试、断网、掉电、重连、限位、报警复位通过","项目组","待审核",""]
]; writeRows(review,reviewRows,"F"); setWidths(review,[10,32,56,20,16,38]); review.getRange("A5:F16").format.fill=C.yellow; review.getRange("E5:E16").dataValidation={rule:{type:"list",values:["待审核","通过","需修改","不适用"]}};

for(const name of ["总结","原始变量","地址重叠","优化问题","20轴规划","每轴地址","轴位定义","20轴GVL","迁移清单","审核清单"]){
  const sh=wb.worksheets.getItem(name); sh.getUsedRange().format.autofitRows();
}

const sourceEnd = 4 + rows.length;
summary.getRange("B4").formulas=[[`=COUNTA('原始变量'!$B$5:$B$${sourceEnd})`]];
summary.getRange("B5").formulas=[[`=SUM('原始变量'!$J$5:$J$${sourceEnd})`]];
summary.getRange("B6").formulas=[["=B4-B5"]];
summary.getRange("B7").formulas=[[`=SUM('原始变量'!$K$5:$K$${sourceEnd})`]];
summary.getRange("B8").formulas=[[`=SUM('原始变量'!$L$5:$L$${sourceEnd})`]];
summary.getRange("B9").formulas=[["=COUNTA('地址重叠'!$A$5:$A$300)"]];

await fs.mkdir(outputDir,{recursive:true});
const xlsx=await SpreadsheetFile.exportXlsx(wb); await xlsx.save(`${outputDir}/AS228T_全局变量优化_20轴_送审版.xlsx`);
const renderSpecs={"总结":"A1:H25","原始变量":"A1:L35","地址重叠":"A1:J35","优化问题":"A1:E12","20轴规划":"A1:I12","每轴地址":"A1:M24","轴位定义":"A1:G42","20轴GVL":"A1:H35","迁移清单":"A1:H40","审核清单":"A1:F18"};
for(const [name,range] of Object.entries(renderSpecs)){const png=await wb.render({sheetName:name,range,scale:1,format:"png"});await fs.writeFile(`${outputDir}/${name}.png`,new Uint8Array(await png.arrayBuffer()));}
await fs.writeFile(`${outputDir}/qa.txt`,JSON.stringify({summaryValues:summary.getRange("A3:B10").values,summaryFormulas:summary.getRange("A3:B10").formulas,rows:rows.length,overlapPairs:overlaps.length,axisShort},null,2));
console.log(JSON.stringify({rows:rows.length,overlapPairs:overlaps.length,axisShort,output:`${outputDir}/AS228T_全局变量优化_20轴_送审版.xlsx`}));
