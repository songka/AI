import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/lfaf-test/Documents/报告编写/AI规划/_cyberppt_work/v2";
const ICONS = path.join(ROOT, "assets/icons-png");
const C = { bg:"#F7F6F0", navy:"#12355B", navy2:"#0A2D5E", ink:"#101820", body:"#303030", muted:"#6F7275", line:"#C9CDD1", pale:"#E9EDF2", pale2:"#F0F2F3", white:"#FFFFFF", orange:"#C45A1A", orangePale:"#FFF3EA" };

async function writeBlob(p, blob){ await fs.mkdir(path.dirname(p),{recursive:true}); await fs.writeFile(p,new Uint8Array(await blob.arrayBuffer())); }
async function iconBytes(name){ const b=await fs.readFile(path.join(ICONS,`${name}.png`)); return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength); }
function box(slide,name,x,y,w,h,fill="none",line="none",lw=0,round=false){ return slide.shapes.add({geometry:round?"roundRect":"rect",name,position:{left:x,top:y,width:w,height:h},fill,line:{style:"solid",fill:line,width:lw},...(round?{borderRadius:"rounded-xl"}:{})}); }
function text(slide,name,txt,x,y,w,h,size,color=C.body,bold=false,align="left",font="Microsoft YaHei"){
  const s=box(slide,name,x,y,w,h); s.text=txt; s.text.style={fontFamily:font,fontSize:size,color,bold,alignment:align}; return s;
}
function line(slide,name,x1,y1,x2,y2,color=C.navy,lw=1.5,dash=false){ return slide.shapes.add({geometry:"line",name,position:{left:x1,top:y1,width:Math.max(.5,x2-x1),height:Math.max(.5,y2-y1)},fill:"none",line:{style:dash?"dash":"solid",fill:color,width:lw}}); }
function ellipse(slide,name,x,y,w,h,fill="none",stroke=C.navy,lw=1){ return slide.shapes.add({geometry:"ellipse",name,position:{left:x,top:y,width:w,height:h},fill,line:{style:"solid",fill:stroke,width:lw}}); }
async function icon(slide,name,iconName,x,y,w,h){ slide.images.add({blob:await iconBytes(iconName),contentType:"image/png",alt:name,fit:"contain",position:{left:x,top:y,width:w,height:h}}); }
function triangle(slide,name,x,y,w,h){ return slide.shapes.add({geometry:"triangle",name,position:{left:x,top:y,width:w,height:h},rotation:90,fill:C.navy,line:{style:"solid",fill:C.navy,width:1}}); }
function header(slide,left,right,page){ text(slide,"header-left",left,30,20,470,20,13,C.navy); text(slide,"header-right",right,790,20,458,20,13,C.muted,false,"right"); box(slide,"header-rule",30,44,1218,1.2,C.navy); box(slide,"footer-rule",30,681,1218,1.2,C.navy); text(slide,"footer",`来源：内部规划与项目实践   |   仅供内部汇报使用`,30,689,430,18,11,C.muted); box(slide,"page-badge",1184,686,62,24,C.navy2,C.navy2,1,true); text(slide,"page-no",String(page).padStart(2,"0"),1184,686,62,24,12,C.white,true,"center","Arial"); }
function titleBlock(slide,titleText,subtitleText){ box(slide,"title-bar",48,72,8,48,C.navy2); text(slide,"page-title",titleText,72,65,1160,54,36,C.ink,true); if(subtitleText) text(slide,"page-subtitle",subtitleText,72,119,1120,30,18,C.muted); }
function soWhat(slide,txt,y=620){ box(slide,"so-what",38,y,1204,48,C.pale,C.line,1,true); box(slide,"so-label",38,y,150,48,C.navy2,C.navy2,1,true); text(slide,"so-label-text","SO WHAT",55,y+9,110,28,20,C.white,true,"center","Arial"); text(slide,"so-text",txt,210,y+8,1000,30,21,C.navy2,true); }

async function makeSlide2(slide){
  header(slide,"目录页","内部 AI 框架与 Skill 建设专题汇报",2); titleBlock(slide,"本次汇报聚焦三个问题","");
  const xs=[52,438,824]; const nums=["01","02","03"]; const qs=["如何构建内部\n可用的 AI 框架","需要开发\n哪五大类 Skill","为什么网络下载的\nSkill 必须改写"]; const icons=["settings","brain","folders"];
  for(let i=0;i<3;i++){ text(slide,`num-${i}`,nums[i],xs[i],222,105,76,52,C.navy2,true,"center","Arial"); line(slide,`v-${i}`,xs[i]+116,220,xs[i]+116,515,C.line,1,true); text(slide,`q-${i}`,qs[i],xs[i]+145,224,225,90,23,C.navy2,true); ellipse(slide,`icon-ring-${i}`,xs[i]+150,335,118,118,"none",C.navy,1.5); await icon(slide,`dir-icon-${i}`,icons[i],xs[i]+178,363,62,62); }
  line(slide,"progress",165,532,1094,532,C.navy,2); for(const x of [160,550,940]) ellipse(slide,`progress-${x}`,x,525,14,14,C.navy,C.navy,1); triangle(slide,"arrow-1",532,523,18,18); triangle(slide,"arrow-2",922,523,18,18);
  text(slide,"progress-label","框架   →   能力   →   改写落地",390,570,500,34,26,C.navy2,true,"center");
}

async function makeSlide3(slide){
  header(slide,"方案蓝图  |  轻量共享第一阶段","版本 1.0  |  2026年7月",3); titleBlock(slide,"先用公共 DeepSeek + SMB Skill 公共槽搭建轻量框架","Skill Hub 尚未建立，SMB 是第一阶段的共享、发布和版本载体");
  text(slide,"admin-title","管理员：发布与治理",678,151,300,26,18,C.navy2,true,"center"); box(slide,"admin-band",656,180,415,70,C.pale2,C.line,1,true);
  const admin=["发布\n新版本","权限\n读/写/执行","版本\n变更记录","备份\n定期快照","回滚\n快速恢复"]; for(let i=0;i<5;i++){ ellipse(slide,`adm-${i}`,680+i*77,190,30,30,C.white,C.navy,1); text(slide,`adm-t-${i}`,admin[i],666+i*79,220,62,28,11,C.body,false,"center"); }
  text(slide,"pc-title","个人电脑（使用者）",45,188,260,24,18,C.navy2,true,"center");
  for(let i=0;i<3;i++){ box(slide,`pc-card-${i}`,35,228+i*92,245,72,C.pale,C.line,1,true); await icon(slide,`pc-${i}`,"device-laptop",48,236+i*92,67,50); text(slide,`pc-t-${i}`,`个人 PC ${i+1}\nopencode / Claude Code`,125,240+i*92,145,48,16,C.navy2,true); line(slide,`pc-link-${i}`,280,264+i*92,395,264+i*92,C.navy,2); triangle(slide,`pc-arr-${i}`,382,256+i*92,16,16); }
  box(slide,"deepseek-card",405,228,190,256,C.pale,C.line,1,true); await icon(slide,"deepseek-icon","brain",462,262,76,76); text(slide,"deepseek","DeepSeek",430,343,140,32,22,C.navy2,true,"center","Arial"); text(slide,"deepseek-desc","公共电脑\n统一模型能力\n访问日志与审计",438,382,125,78,15,C.body,false,"center"); line(slide,"model-smb",595,354,650,354,C.navy,2); triangle(slide,"model-smb-arr",638,346,16,16);
  box(slide,"smb-card",650,270,365,242,C.pale,C.navy,1.2,true); text(slide,"smb-title","SMB Skill 公共槽（共享文件库 / 网络存储）",672,284,320,30,18,C.navy2,true,"center"); await icon(slide,"smb-icon","folders",676,330,70,70); const rows=[["Skill","可复用能力单元与知识"],["公司规则","编码、工程、安全规范"],["模板","项目、文档、配置模板"],["示例","最佳实践与使用示例"]]; for(let i=0;i<4;i++){ box(slide,`smb-row-${i}`,760,328+i*42,230,38,C.white,C.line,1,true); text(slide,`smb-r1-${i}`,rows[i][0],772,336+i*42,70,22,15,C.navy2,true); text(slide,`smb-r2-${i}`,rows[i][1],842,336+i*42,138,22,13,C.body); }
  box(slide,"hub",1055,250,185,270,"none","#8CA1B5",1.5,true); text(slide,"hub-title","后续：平台化 Skill Hub\n（尚未建设）",1070,275,155,58,19,C.navy2,true,"center"); await icon(slide,"hub-icon","share-3",1115,348,64,64); text(slide,"hub-list","集中检索与发现\n能力评价与评分\n自动化发布流程\n依赖与兼容管理",1080,428,140,82,14,C.body); line(slide,"hub-link",1015,382,1055,382,C.navy,1.5,true);
  soWhat(slide,"先低成本解决大家都能用同一套 Skill，再考虑平台化。",610);
}

async function makeSlide4(slide){
  header(slide,"AI 赋能工业工程","五类 Skill 建设",4); titleBlock(slide,"首批建设五大类 Skill，覆盖工程开发与日常办公核心场景","Skill 不是通用问答，而是把公司做法变成可重复调用的能力");
  const xs=[45,285,525,765,1005]; const names=["PLC Skill","Robot Skill","PC 程序 Skill","视觉程序 Skill","办公类 Skill"]; const icons=["cpu","robot","device-laptop","settings","folders"]; const desc=["台达 AS228T\n全局变量 / 局部变量 / ST","那智 / Fanuc / 川崎\n按品牌分别专精","标准框架 / 通信\n日志 / 异常 / 测试","相机与算法平台\nPLC / PC 二次开发","报告 / 表格 / PPT\n会议纪要 / 知识检索"]; const bullets=[["工程规范与模板","常用功能块/算法","变量与数据管理"],["品牌专属指令","运动与路径规划","I/O 与通信集成"],["工程框架与结构","通信与协议封装","单元与集成测试"],["相机采集配置","算法与工具链封装","结果通信与联动"],["报告与文档模板","数据整理与分析","知识检索与沉淀"]];
  for(let i=0;i<5;i++){ ellipse(slide,`skill-ring-${i}`,xs[i]+62,170,78,78,"none",C.navy,1.5); await icon(slide,`skill-icon-${i}`,icons[i],xs[i]+81,189,40,40); ellipse(slide,`skill-num-${i}`,xs[i]+84,239,34,34,C.navy2,C.navy2,1); text(slide,`skill-no-${i}`,`0${i+1}`,xs[i]+84,246,34,18,12,C.white,true,"center","Arial"); text(slide,`skill-name-${i}`,names[i],xs[i],282,205,28,18,C.navy2,true,"center"); text(slide,`skill-desc-${i}`,desc[i],xs[i]+7,318,192,58,15,C.body,false,"center"); line(slide,`skill-sep-${i}`,xs[i]+18,382,xs[i]+187,382,C.line,1,true); text(slide,`skill-bullets-${i}`,`• ${bullets[i][0]}\n• ${bullets[i][1]}\n• ${bullets[i][2]}`,xs[i]+15,397,180,80,14,C.body); line(slide,`skill-down-${i}`,xs[i]+102,483,xs[i]+102,520,C.navy,2); }
  box(slide,"smb-base",180,518,920,78,C.pale,C.navy,1.2,true); await icon(slide,"base-icon","folders",202,532,48,48); text(slide,"base-title","SMB 公共槽",265,528,155,28,20,C.navy2,true); text(slide,"base-desc","统一存储、版本管理、权限控制、复用分发",265,558,305,24,14,C.body); const packs=["references\n参考资料","templates\n模板库","examples\n示例库","evals\n评测验证"]; for(let i=0;i<4;i++){ line(slide,`pack-sep-${i}`,590+i*125,528,590+i*125,584,C.line,1); text(slide,`pack-${i}`,packs[i],600+i*125,535,110,42,13,C.navy2,true,"center"); }
  soWhat(slide,"把公司的做法沉淀为可复用、可迭代、可度量的能力。",610);
}

async function makeSlide5(slide){
  header(slide,"SMB Skill 体系建设蓝图","标准化 · 可复用 · 可验收 · 可进化",5); titleBlock(slide,"每类 Skill 都必须有负责人、公司规则、示例和验收标准","");
  const roles=["领域 Owner","Skill 编写人","验收人","SMB 管理员","使用者反馈"]; const sub=["定义场景与边界","沉淀规则模板流程","真实项目验收","发布/权限/版本","反馈错误与新场景"]; const xs=[55,285,515,745,975];
  for(let i=0;i<5;i++){ ellipse(slide,`role-${i}`,xs[i]+45,170,82,82,C.pale,C.navy,1.5); text(slide,`role-no-${i}`,String(i+1),xs[i]+70,194,32,32,23,C.navy2,true,"center","Arial"); text(slide,`role-name-${i}`,roles[i],xs[i],270,172,28,18,C.navy2,true,"center"); text(slide,`role-sub-${i}`,sub[i],xs[i],303,172,44,14,C.body,false,"center"); if(i<4){ line(slide,`role-line-${i}`,xs[i]+133,210,xs[i]+222,210,C.navy,2); triangle(slide,`role-arr-${i}`,xs[i]+207,202,16,16); } }
  line(slide,"feedback-line",1058,354,1058,390,C.navy,2); line(slide,"feedback-back",1058,390,105,390,C.navy,2); line(slide,"feedback-up",105,354,105.5,390,C.navy,2); text(slide,"feedback-label","持续反馈与迭代",520,376,160,24,16,C.navy2,true,"center");
  text(slide,"package-title","最小交付包（目录结构）",42,414,300,28,20,C.navy2,true); const packs=["SKILL.md\n概述、边界、输入输出、公司规则","references\n技术资料、标准、厂商手册","templates / examples\n提示模板、配置、代码与案例","evals\n评测用例、标准与验收报告"]; for(let i=0;i<4;i++){ box(slide,`pkg-${i}`,42+i*240,452,225,115,i%2?C.pale2:C.pale,C.line,1,true); text(slide,`pkg-t-${i}`,packs[i],56+i*240,468,195,82,14,C.body,i===0); }
  box(slide,"gate",1015,430,225,154,C.orangePale,C.orange,1,true); text(slide,"gate-title","进入 SMB 的准入门",1027,444,200,28,18,C.orange,true,"center"); text(slide,"gate-list","✓ 规则已批准\n✓ 样例齐全\n✓ 真实项目验收\n✓ 版本与回滚就绪",1032,478,190,90,14,C.body);
  soWhat(slide,"没有负责人和真实项目验收的 Skill，不进入 SMB 公共槽。",610);
}

async function makeSlide6(slide){
  header(slide,"PLC Skill 治理与转化方法论","从素材库到生产力：可控 · 可用 · 可复用",6); titleBlock(slide,"网络下载的 PLC Skill 只能作为素材库，不能直接作为公司生产 Skill","");
  box(slide,"evidence",30,140,1218,80,C.pale,C.navy,1,true); box(slide,"evi-label",30,140,150,80,C.navy2,C.navy2,1,true); text(slide,"evi-title","证据总览\n网络下载包",45,155,120,50,18,C.white,true,"center"); const vals=[["111","个文件"],["110","个 Markdown"],["10","个厂商目录"],["3","台达文件"],["0","AS228T 专属"]]; for(let i=0;i<5;i++){ if(i>0) line(slide,`evi-sep-${i}`,180+i*205,153,180+i*205,207,C.line,1); text(slide,`evi-v-${i}`,vals[i][0],195+i*205,151,88,38,34,C.navy2,true,"center","Arial"); text(slide,`evi-l-${i}`,vals[i][1],190+i*205,188,110,22,14,C.body,false,"center"); }
  box(slide,"wide",30,242,410,330,C.pale2,C.line,1,true); box(slide,"wide-head",30,242,410,38,C.navy2,C.navy2,1,true); text(slide,"wide-title","网络通用包：宽而杂",45,249,380,24,19,C.white,true,"center"); await icon(slide,"wide-icon","folders",58,304,70,70); text(slide,"wide-text","多厂商并存、内容分散、规则冲突\n\n常见问题\n• 厂商语法与指令集差异大\n• 工具链不一致：ISPSoft / GX Works2 等\n• 命名、地址、结构、注释风格各异\n• 直接使用风险高",145,302,270,230,15,C.body);
  box(slide,"actions",465,242,330,330,C.white,C.line,1,true); text(slide,"act-title","将“素材”转化为“公司生产 Skill”",480,255,300,28,18,C.navy2,true,"center"); const acts=[["1  保留","章节框架、模板、检查表、通用方法"],["2  删除","非目标厂商、冲突规则、陈旧重复内容"],["3  重写","AS228T / ISPSoft / 公司工程标准"]]; for(let i=0;i<3;i++){ ellipse(slide,`act-c-${i}`,490,306+i*82,44,44,i===2?C.orangePale:C.pale,C.navy,1); text(slide,`act-n-${i}`,String(i+1),490,317+i*82,44,22,18,i===2?C.orange:C.navy2,true,"center","Arial"); text(slide,`act-h-${i}`,acts[i][0],548,300+i*82,210,26,18,C.navy2,true); text(slide,`act-d-${i}`,acts[i][1],548,330+i*82,220,38,13,C.body); }
  box(slide,"narrow",820,242,428,330,C.pale,C.navy,1.2,true); box(slide,"narrow-head",820,242,428,38,C.navy2,C.navy2,1,true); text(slide,"narrow-title","公司专精 Skill：窄而深",835,249,398,24,19,C.white,true,"center"); text(slide,"target","目标：台达 AS228T（ISPSoft）",850,296,360,30,20,C.navy2,true,"center"); text(slide,"cap-list","✓ 指令集与功能特性\n✓ 项目结构与程序框架\n✓ 地址规范与命名标准\n✓ 设备通信与扩展规范\n✓ 常用功能与模板库\n✓ 调试、诊断和验收标准",860,342,330,158,15,C.body); box(slide,"risk",850,510,370,48,C.orangePale,C.orange,1,true); text(slide,"risk-text","缺口：公司地址、命名、程序框架和安全规则待补齐",865,521,340,26,13,C.orange,true,"center");
  soWhat(slide,"网络 Skill 可复用结构，但厂商、型号和公司规则必须重新校准。",610);
}

async function makeSlide7(slide){
  header(slide,"收束页","将网络 PLC Skill 改写为只服务台达 AS228T 的公司专精 Skill",7); titleBlock(slide,"将网络 PLC Skill 改写为只服务台达 AS228T 的公司专精 Skill","");
  const steps=["网络 Skill","裁剪 / 重写","注入公司规则","AS228T 三件套","真实工程验收","发布至 SMB"]; const icons=["folders","settings","settings","cpu","brain","share-3"]; const xs=[45,250,455,660,865,1070]; for(let i=0;i<6;i++){ ellipse(slide,`step-icon-ring-${i}`,xs[i]+50,145,68,68,"none",C.navy,1.5); await icon(slide,`step-icon-${i}`,icons[i],xs[i]+68,163,34,34); ellipse(slide,`step-no-${i}`,xs[i]+5,202,34,34,C.navy2,C.navy2,1); text(slide,`step-n-${i}`,`0${i+1}`,xs[i]+5,210,34,18,11,C.white,true,"center","Arial"); text(slide,`step-t-${i}`,steps[i],xs[i]+42,210,140,24,17,C.navy2,true,"center"); if(i<5){ line(slide,`step-line-${i}`,xs[i]+180,214,xs[i]+202,214,C.navy,2); triangle(slide,`step-arr-${i}`,xs[i]+190,206,16,16); } }
  const cardX=[35,242,449,656,863,1070]; const heads=["网络 Skill 内容","裁剪 / 重写范围","公司规则注入","AS228T 三件套","质量检查清单","发布至 SMB"]; const bodies=["• 通用网络配置\n• 多品牌 PLC 适配\n• 通信协议封装\n• 通用功能块库","• 仅保留 AS228T 相关\n• 精简通信与功能模块\n• 移除非必要兼容层\n• 统一工程结构与命名","地址分配\n变量命名\n程序框架\n报警 / 互锁 / 复位","全局变量（GVL）\n局部变量（LVAR）\nST 程序（ST Code）\n工程模板与示例库","地址冲突检查\n命名规范检查\n变量引用检查\n输出单写与回归测试","资产目录与版本\n权限控制\n使用指引\n反馈闭环与持续改进"];
  for(let i=0;i<6;i++){ box(slide,`card-${i}`,cardX[i],268,188,242,i===3?C.pale:C.white,i===3?C.navy:C.line,i===3?1.5:1,true); box(slide,`card-head-${i}`,cardX[i],268,188,38,i===3?C.navy2:C.pale,C.line,1,true); text(slide,`card-title-${i}`,heads[i],cardX[i]+8,276,172,22,16,i===3?C.white:C.navy2,true,"center"); text(slide,`card-body-${i}`,bodies[i],cardX[i]+16,325,156,150,14,C.body); if(i<5){ triangle(slide,`card-arr-${i}`,cardX[i]+192,375,16,20); } }
  box(slide,"support",35,530,1205,72,C.orangePale,C.orange,1,true); text(slide,"support-label","老板支持请求",55,550,160,28,21,C.orange,true); text(slide,"support-1","① 指定 PLC Owner 与验收人",235,548,285,30,16,C.body,true); text(slide,"support-2","② 提供公司规则与真实工程样例",535,548,330,30,16,C.body,true); text(slide,"support-3","③ 批准 SMB 权限与版本管理方式",875,548,340,30,16,C.body,true);
  box(slide,"conclusion",35,615,1205,52,C.navy2,C.navy2,1,true); text(slide,"conclusion-label","最终结论",60,626,150,30,20,C.white,true); text(slide,"conclusion-text","先把一个 PLC Skill 做深做实，再复制到其他四类 Skill。",235,624,965,32,25,C.white,true,"center");
}

const makers={2:makeSlide2,3:makeSlide3,4:makeSlide4,5:makeSlide5,6:makeSlide6,7:makeSlide7};
async function main(){
  for(const n of [2,3,4,5,6,7]){
    const out=path.join(ROOT,"pages",`slide-${String(n).padStart(2,"0")}`); await fs.mkdir(path.join(out,"render"),{recursive:true}); await fs.mkdir(path.join(out,"qa"),{recursive:true});
    const deck=Presentation.create({slideSize:{width:1280,height:720}}); const slide=deck.slides.add(); slide.background.fill=C.bg; await makers[n](slide);
    const preview=await deck.export({slide,format:"png",scale:2}); await writeBlob(path.join(out,"render",`slide-${String(n).padStart(2,"0")}.png`),preview);
    const layout=await slide.export({format:"layout"}); await fs.writeFile(path.join(out,"render",`slide-${String(n).padStart(2,"0")}.layout.json`),await layout.text());
    const pptx=await PresentationFile.exportPptx(deck); await pptx.save(path.join(out,`slide-${String(n).padStart(2,"0")}.pptx`));
  }
}
main().catch(async err=>{ await fs.writeFile(path.join(ROOT,"pages","build-pages-error.txt"),String(err?.stack||err),"utf8").catch(()=>{}); console.error(err); process.exitCode=1; });
