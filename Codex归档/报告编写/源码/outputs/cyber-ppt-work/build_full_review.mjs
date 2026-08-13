import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const pptxgen = require('C:/Users/lfaf-test/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/pptxgenjs@4.0.1/node_modules/pptxgenjs/dist/pptxgen.cjs.js');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'MPT Electrical Engineering';
pptx.subject = '视觉无序抓取技术应用汇报';
pptx.title = '视觉无序抓取技术应用汇报';
pptx.company = 'MPT Solution';
pptx.lang = 'zh-CN';
pptx.theme = {
  headFontFace: 'Microsoft JhengHei',
  bodyFontFace: 'Microsoft JhengHei',
  lang: 'zh-CN'
};

const C = {
  navy: '00457A',
  navy2: '0B4E7F',
  cyan: '2FA8D7',
  blue: '4472C4',
  pale: 'EAF3F9',
  pale2: 'F5F8FA',
  gray: '8C8C8C',
  gray2: 'D9DEE3',
  gray3: 'EEF1F3',
  text: '243342',
  orange: 'ED7D31',
  green: '2E8B57',
  white: 'FFFFFF',
  amber: 'FFF2CC',
  red: 'C84545'
};

const P = {
  coverBg: 'C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/visual-random-pick-cyber-final/tmp/template-inspect/assets/ppt/media/image3.png',
  logo: 'C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/visual-random-pick-cyber-final/tmp/template-inspect/assets/ppt/media/image.png',
  self: 'C:/Users/lfaf-test/Documents/报告编写/outputs/视觉无序抓取_素材/自建三轴_屏蔽机器人.png',
  selfProduct: 'C:/Users/lfaf-test/Documents/报告编写/自建三轴铁件产品.jpg',
  four: 'C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/visual-random-pick-weekly/tmp/assets/four-axis-thumb.png',
  fourProduct: 'C:/Users/lfaf-test/Documents/报告编写/四轴lens产品.jpg',
  conveyor: 'C:/Users/lfaf-test/AppData/Local/Temp/codex-presentations/visual-random-pick-weekly/tmp/assets/conveyor-thumb.png'
};

function addText(slide, text, x, y, w, h, opt={}) {
  slide.addText(text, {
    x,y,w,h, margin:0,
    fontFace: opt.fontFace || 'Microsoft JhengHei',
    fontSize: opt.fontSize || 12,
    color: opt.color || C.text,
    bold: opt.bold || false,
    align: opt.align || 'left',
    valign: opt.valign || 'mid',
    breakLine: false,
    fit: 'shrink',
    ...opt
  });
}

function addContentChrome(slide, title, page) {
  slide.background = { color: C.white };
  addText(slide, title, 0.72, 0.27, 11.65, 0.55, {fontSize:26, bold:true, color:C.navy, valign:'mid'});
  slide.addShape(pptx.ShapeType.line, {x:0.72,y:0.98,w:10.9,h:0,line:{color:C.navy,width:1.1}});
  slide.addShape(pptx.ShapeType.rect, {x:0,y:6.82,w:13.333,h:0.68,line:{color:'D1D1D1',transparency:100},fill:{color:'D9D9D9'}});
  addText(slide, String(page), 0.38, 7.08, 0.28, 0.17, {fontSize:7.5,color:C.navy});
  addText(slide, 'Copyright © 2021 MPT Solution and / or any of its affiliates. All Rights Reserved. CONFIDENTIAL.', 1.0, 7.05, 7.3, 0.2, {fontFace:'Arial',fontSize:6.7,color:C.navy});
  slide.addImage({path:P.logo,x:12.34,y:6.96,w:0.66,h:0.42,transparency:0});
}

function addPanel(slide,x,y,w,h,title='') {
  slide.addShape(pptx.ShapeType.roundRect,{x,y,w,h,rectRadius:0.05,line:{color:'B9C9D6',width:0.8},fill:{color:C.white}});
  if(title){
    slide.addShape(pptx.ShapeType.rect,{x,y,w,h:0.32,line:{color:C.navy,transparency:100},fill:{color:C.navy}});
    addText(slide,title,x+0.12,y+0.03,w-0.24,0.25,{fontSize:11,bold:true,color:C.white});
  }
}

function addKpi(slide,x,y,w,label,value,color=C.navy) {
  slide.addShape(pptx.ShapeType.roundRect,{x,y,w,h:0.72,rectRadius:0.05,line:{color:'C2D0DC',width:0.7},fill:{color:'F9FBFC'}});
  addText(slide,label,x+0.1,y+0.08,w-0.2,0.18,{fontSize:8.5,bold:true,color:C.text,align:'center'});
  addText(slide,value,x+0.08,y+0.29,w-0.16,0.32,{fontSize:18,bold:true,color,align:'center'});
}

function addSoWhat(slide,text,y=6.18) {
  slide.addShape(pptx.ShapeType.roundRect,{x:0.72,y,w:11.9,h:0.48,rectRadius:0.04,line:{color:'AFC7D9',width:0.7},fill:{color:'EAF3F9'}});
  addText(slide,'SO WHAT：'+text,0.96,y+0.07,11.35,0.32,{fontSize:12,bold:true,color:C.navy});
}

// 1 Cover
{
  const s=pptx.addSlide();
  s.addImage({path:P.coverBg,x:0,y:0,w:13.333,h:7.5});
  addText(s,'VISION',1.73,1.35,2.45,0.72,{fontFace:'Arial',fontSize:36,bold:true,color:C.white,align:'center'});
  addText(s,'视觉无序抓取技术应用汇报',6.0,0.55,6.15,0.58,{fontSize:27,bold:true,color:C.navy});
  addText(s,'Ø  本周电气技术汇报\n\nØ  4 类方案已投入生产运行\n\nØ  下一步：并联机械手自主开发',5.88,1.78,5.9,2.2,{fontSize:20,color:'505050',breakLine:true,valign:'top'});
  addText(s,'Copyright © 2021 MPT Solution and / or any of its affiliates. All Rights Reserved.',6.15,7.16,5.2,0.13,{fontFace:'Arial',fontSize:5.7,color:'D0D0D0'});
}

// 2 Executive summary with real equipment images
{
  const s=pptx.addSlide(); addContentChrome(s,'四类方案均已量产，视觉逻辑可复用，但高速平台仍依赖外购',2);
  const cards=[
    {x:0.38,y:1.22,title:'1  自建三轴+旋转轴',img:P.self,app:'K7铁件',ct:'6s',acc:'±1mm',cost:'¥33,170'},
    {x:4.72,y:1.22,title:'2  四轴机械手',img:P.four,app:'K21 Lens上料',ct:'6s',acc:'±1mm',cost:'¥49,000'},
    {x:0.38,y:3.96,title:'3  并联机械手',img:null,app:'K41脚垫测试',ct:'4s',acc:'±1mm',cost:'外购'},
    {x:4.72,y:3.96,title:'4  四轴随线取放',img:P.conveyor,app:'K21-H-MODEL',ct:'2.2s',acc:'±2mm',cost:'¥64,000'}
  ];
  for(const c of cards){
    addPanel(s,c.x,c.y,4.15,2.48,c.title);
    if(c.img) s.addImage({path:c.img,x:c.x+0.05,y:c.y+0.36,w:2.78,h:2.04,sizing:{type:'cover'}});
    else {
      s.addShape(pptx.ShapeType.rect,{x:c.x+0.05,y:c.y+0.36,w:2.78,h:2.04,line:{color:'C9CED2',dash:'dash'},fill:{color:'F2F2F2'}});
      addText(s,'现场照片待补\n设备已投入生产',c.x+0.35,c.y+1.04,2.18,0.55,{fontSize:14,bold:true,color:C.gray,align:'center',breakLine:true});
    }
    addText(s,'应用',c.x+2.98,c.y+0.43,0.48,0.18,{fontSize:8,bold:true,color:C.navy}); addText(s,c.app,c.x+2.98,c.y+0.63,1.0,0.24,{fontSize:8.5});
    addText(s,'CT',c.x+2.98,c.y+1.02,0.45,0.18,{fontSize:8,bold:true,color:C.navy}); addText(s,c.ct,c.x+3.45,c.y+0.99,0.5,0.24,{fontSize:11,bold:true,color:C.orange});
    addText(s,'精度',c.x+2.98,c.y+1.39,0.5,0.18,{fontSize:8,bold:true,color:C.navy}); addText(s,c.acc,c.x+3.45,c.y+1.36,0.55,0.24,{fontSize:10,bold:true,color:C.navy});
    addText(s,'材料成本',c.x+2.98,c.y+1.77,0.78,0.18,{fontSize:8,bold:true,color:C.navy}); addText(s,c.cost,c.x+2.98,c.y+1.98,1.05,0.24,{fontSize:10.5,bold:true,color:C.orange});
  }
  addPanel(s,9.05,1.22,3.55,5.18,'管理结论');
  const insights=['视觉流程已跨四种平台复用','四类设备均已投入生产','下一项能力建设：自制并联机械手','随线与标准抓取工况不同，CT不直接横比'];
  insights.forEach((t,i)=>{s.addShape(pptx.ShapeType.ellipse,{x:9.28,y:1.82+i*0.78,w:0.34,h:0.34,line:{color:C.navy},fill:{color:C.navy}}); addText(s,String(i+1),9.28,1.84+i*0.78,0.34,0.26,{fontSize:9,bold:true,color:C.white,align:'center'}); addText(s,t,9.76,1.77+i*0.78,2.45,0.48,{fontSize:11,bold:true,color:C.navy,breakLine:true});});
  s.addShape(pptx.ShapeType.roundRect,{x:9.27,y:5.24,w:3.05,h:0.88,rectRadius:0.04,line:{color:'AFC7D9'},fill:{color:'EAF3F9'}});
  addText(s,'SO WHAT',9.55,5.35,2.48,0.22,{fontSize:11,bold:true,color:C.navy,align:'center'});
  addText(s,'成果已从单点设备上升为\n可复用的视觉抓取能力',9.48,5.58,2.65,0.42,{fontSize:11,bold:true,color:C.navy,align:'center',breakLine:true});
}

// 3 Architecture
{
  const s=pptx.addSlide(); addContentChrome(s,'一套视觉程序通过两条控制路径适配自建轴和机器人',3);
  const arrow=(x,y,w,h=0)=>s.addShape(pptx.ShapeType.line,{x,y,w,h,line:{color:C.navy,width:1.35,beginArrowType:'none',endArrowType:'triangle'}});
  addPanel(s,0.55,1.25,9.75,2.2,'路径1：自建轴路径');
  // connectors first
  arrow(1.90,2.08,0.65); arrow(3.70,2.08,0.72); arrow(5.62,2.08,0.88); arrow(8.08,2.08,0.68);
  const nodes1=[['视觉相机',0.78,1.12],['视觉PC',2.55,1.15],['PLC',4.42,1.20],['自建三轴+旋转轴',6.50,1.58],['机械定位',8.76,1.18]];
  nodes1.forEach(([t,x,nw],i)=>{s.addShape(i===0?pptx.ShapeType.roundRect:pptx.ShapeType.rect,{x,y:1.68,w:nw,h:0.78,line:{color:C.navy,width:1.1},fill:{color:i===2?'EAF3F9':'FFFFFF'}});addText(s,t,x,1.91,nw,0.25,{fontSize:9.5,bold:true,color:C.navy,align:'center'});});
  addText(s,'网线',1.94,1.72,0.56,0.18,{fontSize:8,color:C.navy,align:'center'}); addText(s,'Modbus/TCP',3.72,1.72,0.68,0.18,{fontSize:7.7,color:C.navy,align:'center'}); addText(s,'CANopen',5.70,1.72,0.72,0.18,{fontSize:8,color:C.navy,align:'center'});
  s.addShape(pptx.ShapeType.roundRect,{x:1.05,y:2.68,w:1.45,h:0.44,rectRadius:0.03,line:{color:'A8C1D3'},fill:{color:'F8FAFB'}}); addText(s,'柔性振动盘',1.15,2.79,1.25,0.2,{fontSize:9,bold:true,color:C.navy,align:'center'});
  s.addShape(pptx.ShapeType.line,{x:2.5,y:2.9,w:2.52,h:0,line:{color:C.navy,width:1.2,endArrowType:'triangle'}}); addText(s,'I/O',3.42,2.70,0.58,0.18,{fontSize:8,color:C.navy,align:'center'});
  addPanel(s,0.55,3.68,9.75,2.12,'路径2：机器人路径');
  arrow(2.60,4.74,1.02); arrow(5.02,4.74,1.10); arrow(7.47,4.74,0.86);
  const nodes2=[['视觉PC',1.25,1.35],['Robot控制器',3.62,1.40],['四轴机械手',6.12,1.35],['并联机械手',8.33,1.35]];
  nodes2.forEach(([t,x,nw])=>{s.addShape(pptx.ShapeType.roundRect,{x,y:4.36,w:nw,h:0.78,line:{color:C.navy,width:1.1},fill:{color:'FFFFFF'}});addText(s,t,x,4.6,nw,0.25,{fontSize:10,bold:true,color:C.navy,align:'center'});});
  addText(s,'TCP/IP',2.70,4.34,0.82,0.2,{fontSize:8,color:C.navy,align:'center'}); addText(s,'同一接口适配不同机器人',6.93,5.28,2.05,0.2,{fontSize:8,color:C.gray,align:'center'});
  addPanel(s,10.52,1.25,2.1,4.55,'职责分工');
  addText(s,'视觉PC\n拍照・识别・补偿\n\nPLC\n自建轴流程与运动控制\n\nRobot\nPC直接反馈视觉坐标',10.72,1.75,1.7,3.55,{fontSize:9.5,bold:true,color:C.navy,align:'center',breakLine:true,valign:'top'});
  addSoWhat(s,'更换运动平台时，主要调整接口与运动参数，不重复开发视觉逻辑。',6.18);
}

// 4 Vision flow
{
  const s=pptx.addSlide(); addContentChrome(s,'三个判断分支把缺料、空盘和叠料纳入自动闭环',4);
  const box=(txt,x,y,w=1.2,h=0.48,fill='F4F8FB')=>{s.addShape(pptx.ShapeType.roundRect,{x,y,w,h,rectRadius:0.03,line:{color:C.blue,width:0.9},fill:{color:fill}});addText(s,txt,x+0.05,y+0.08,w-0.1,h-0.14,{fontSize:9.5,bold:true,color:C.text,align:'center',breakLine:true});};
  const dia=(txt,x,y,w=1.15,h=0.7)=>{s.addShape(pptx.ShapeType.diamond,{x,y,w,h,line:{color:C.navy,width:1.1},fill:{color:'FFFFFF'}});addText(s,txt,x+0.17,y+0.18,w-0.34,h-0.32,{fontSize:8.8,bold:true,color:C.text,align:'center',breakLine:true});};
  const ar=(x,y,w,h=0,end=true)=>s.addShape(pptx.ShapeType.line,{x,y,w,h,line:{color:C.navy,width:1.15,endArrowType:end?'triangle':'none'}});
  const ln=(x,y,w,h=0)=>ar(x,y,w,h,false);
  const back=(x,y,w)=>s.addShape(pptx.ShapeType.line,{x,y,w,h:0,line:{color:C.navy,width:1.15,beginArrowType:'triangle'}});
  // 主流程：拍照 → 判断缺料 → 匹配 → 判断找到 → 定位 → 判断叠料 → 补偿 → 反馈
  ar(1.35,1.75,0.30); ar(2.85,1.75,0.30); ar(4.35,1.75,0.28);
  ar(5.17,2.10,0,0.50); ar(5.17,3.08,0,0.34); ar(5.17,4.10,0,0.34); ar(6.00,4.76,0.52); ar(7.72,4.76,0.50); ar(9.42,4.76,0.42); ar(10.98,4.76,0.34);
  box('收到拍照信号',0.45,1.51,0.9); box('拍照取像',1.65,1.51); box('Blob分析',3.15,1.51); dia('需要补料？',4.62,1.39,1.1,0.72);
  box('特征匹配',4.56,2.60,1.22); dia('找到产品？',4.60,3.42,1.14,0.72); box('产品定位',4.56,4.44,1.44,0.62); dia('周围有\n其他产品？',6.52,4.35,1.20,0.82);
  box('视觉补偿计算',8.22,4.48,1.20,0.56); box('反馈补偿值',9.84,4.48,1.14,0.56); box('结束',11.32,4.48,0.62,0.56,'DDEFD8');
  addText(s,'否',5.28,2.24,0.34,0.18,{fontSize:8,bold:true,color:C.navy}); addText(s,'否',7.82,4.48,0.28,0.18,{fontSize:8,bold:true,color:C.navy}); addText(s,'是',5.28,4.16,0.28,0.18,{fontSize:8,bold:true,color:C.navy});
  // 缺料分支：补料 + 振动后回到拍照取像
  ar(5.72,1.75,0.42); ar(7.32,1.75,0.36);
  box('补料动作',6.14,1.51,1.18,0.48,'FFF2CC'); box('振动',7.68,1.51,0.84,0.48,'FFF2CC'); addText(s,'是',5.82,1.50,0.28,0.18,{fontSize:8,bold:true,color:C.navy});
  ln(8.10,1.99,0,0.40); back(2.25,2.39,5.85); ln(2.25,1.99,0,0.40); addText(s,'重新拍照',2.38,2.15,0.78,0.18,{fontSize:8,color:C.navy});
  // 未找到分支：振动后回到拍照取像
  ar(5.74,3.78,0.55); box('振动',6.29,3.54,0.90,0.48,'FFF2CC'); addText(s,'否',5.84,3.53,0.28,0.18,{fontSize:8,bold:true,color:C.navy});
  ln(6.74,3.12,0,0.42); back(2.25,3.12,4.49); ln(2.25,1.99,0,1.13); addText(s,'振动后重新拍照',2.48,2.89,1.14,0.18,{fontSize:8,color:C.navy});
  // 叠料分支：有其他产品则排除当前目标并返回特征匹配；无叠料进入补偿计算
  ar(7.12,5.17,0,0.23); box('排除当前目标',6.45,5.40,1.35,0.48,'FFF2CC'); addText(s,'是',7.22,5.18,0.28,0.18,{fontSize:8,bold:true,color:C.navy});
  ln(7.12,5.88,0,0.16); ln(4.15,6.04,2.97,0); ln(4.15,2.84,0,3.20); ar(4.15,2.84,0.41); addText(s,'返回特征匹配',4.28,5.80,1.02,0.18,{fontSize:8,color:C.navy});
  addPanel(s,9.65,1.35,2.95,2.7,'异常分支与处理策略');
  const rows=[['缺料','补料+振动','重新拍照'],['空盘/未找到','振动','重新拍照'],['叠料风险','排除目标','重新匹配']];
  ['条件','动作','返回'].forEach((t,i)=>addText(s,t,9.78+i*0.88,1.78,0.82,0.24,{fontSize:8.5,bold:true,color:C.navy,align:'center'}));
  rows.forEach((r,ri)=>r.forEach((t,i)=>{s.addShape(pptx.ShapeType.rect,{x:9.74+i*0.88,y:2.06+ri*0.54,w:0.88,h:0.54,line:{color:'C6D2DB',width:0.5},fill:{color:ri%2?'F6F8F9':'FFFFFF'}});addText(s,t,9.78+i*0.88,2.16+ri*0.54,0.8,0.3,{fontSize:7.8,align:'center',breakLine:true});}));
  addSoWhat(s,'异常自动回流，减少人工干预并避免叠料误抓。');
  addText(s,'注：重试次数、超时及报警阈值待现场参数化。',8.55,6.52,3.85,0.17,{fontSize:7,color:C.gray,align:'right'});
}

function addCaseSlide({page,title,img,product,app,status,ct,acc,cost,communication,advantage,constraint,soWhat,comparison}){
  const s=pptx.addSlide(); addContentChrome(s,title,page);
  s.addImage({path:img,x:0.48,y:1.28,w:6.45,h:4.55,sizing:{type:'cover'}});
  if(product) s.addImage({path:product,x:0.55,y:4.55,w:2.85,h:1.05,sizing:{type:'cover'}});
  addKpi(s,7.18,1.28,1.55,'CT',ct,C.orange); addKpi(s,8.88,1.28,1.55,'精度',acc,C.green); addKpi(s,10.58,1.28,2.02,'材料成本',cost,C.orange);
  addPanel(s,7.18,2.22,5.42,2.8);
  const lines=[['应用',app+'｜'+status],['通信',communication],['优势',advantage],['约束',constraint]];
  lines.forEach((r,i)=>{addText(s,r[0]+'：',7.45,2.48+i*0.58,0.7,0.26,{fontSize:10,bold:true,color:C.navy});addText(s,r[1],8.18,2.48+i*0.58,4.05,0.3,{fontSize:10,breakLine:true});});
  if(comparison){s.addShape(pptx.ShapeType.roundRect,{x:7.18,y:5.17,w:2.65,h:0.56,rectRadius:0.04,line:{color:C.navy},fill:{color:C.navy}});addText(s,comparison,7.34,5.29,2.33,0.25,{fontSize:10,bold:true,color:C.white,align:'center'});}
  addSoWhat(s,soWhat,6.1);
  addText(s,'口径：仅材料成本，不含人工、软件开发、调试、预备金与维护。',7.15,6.57,5.35,0.15,{fontSize:6.8,color:C.gray,align:'right'});
}

addCaseSlide({page:5,title:'K7自建方案以6s／±1mm满足量产，并保留成本和调整优势',img:P.self,product:P.selfProduct,app:'K7铁件',status:'已投入生产运行',ct:'6s',acc:'±1mm',cost:'¥33,170',communication:'视觉PC—Modbus/TCP—PLC—CANopen—自建轴',advantage:'结构自行搭建，调整灵活、材料成本低',constraint:'精度主要受视觉视野影响',soWhat:'在现有标准设备上追加自建模组，以较低投入满足当前量产节拍。'});

addCaseSlide({page:6,title:'K21四轴以相同CT和精度换取更大的跨区域行程',img:P.four,product:P.fourProduct,app:'K21 Altis线 Lens上料',status:'已投入生产运行',ct:'6s',acc:'±1mm',cost:'¥49,000',communication:'视觉PC与机器人采用 TCP/IP',advantage:'行程大，适合跨区域取放',constraint:'精度主要受视觉视野影响',comparison:'比自建方案高 ¥15,830',soWhat:'当行程优先级高于材料成本时，标准四轴更稳妥。'});

// 7 Parallel / self-build
{
  const s=pptx.addSlide(); addContentChrome(s,'K41并联将标准抓取CT降至4s，但核心机构仍为外购',7);
  s.addShape(pptx.ShapeType.rect,{x:0.55,y:1.32,w:4.15,h:4.72,line:{color:'C8CDD2',dash:'dash'},fill:{color:'F2F2F2'}}); addText(s,'并联机械手现场照片待补',1.1,3.35,3.05,0.42,{fontSize:15,bold:true,color:C.gray,align:'center'});
  addKpi(s,4.95,1.32,1.75,'CT','4s',C.orange); addKpi(s,6.9,1.32,1.75,'精度','±1mm',C.green); addKpi(s,8.85,1.32,2.0,'当前机构','外购',C.navy);
  addText(s,'量产实测',11.05,1.54,1.15,0.25,{fontSize:10,bold:true,color:C.white,align:'center',fill:{color:C.navy}});
  addPanel(s,4.95,2.25,5.05,2.3);
  const facts=['应用：K41 KDB10-B件脚垫测试｜已投入生产运行','通信：视觉PC与机器人采用 TCP/IP','优势：速度快，标准抓取方案中CT最短','约束：核心运动机构仍依赖外购'];
  facts.forEach((t,i)=>addText(s,t,5.25,2.5+i*0.48,4.45,0.28,{fontSize:10,bold:i===0,color:i===0?C.navy:C.text}));
  s.addShape(pptx.ShapeType.roundRect,{x:10.22,y:2.25,w:2.4,h:2.3,rectRadius:0.04,line:{color:C.navy},fill:{color:C.navy}}); addText(s,'自制蜘蛛手',10.5,2.55,1.85,0.32,{fontSize:14,bold:true,color:C.white,align:'center'}); addText(s,'臂展 300mm\n\n首台预计材料\n¥33,862',10.54,3.04,1.75,1.05,{fontSize:13,bold:true,color:C.white,align:'center',breakLine:true});
  addPanel(s,4.95,4.78,7.67,0.98); addText(s,'已验证（外购）',5.35,4.95,2.05,0.22,{fontSize:10,bold:true,color:C.navy,align:'center'}); addText(s,'4s／±1mm',5.35,5.24,2.05,0.28,{fontSize:15,bold:true,color:C.orange,align:'center'}); addText(s,'待验证（自制）',9.25,4.95,2.05,0.22,{fontSize:10,bold:true,color:C.navy,align:'center'}); addText(s,'CT、精度、稳定性',8.65,5.24,3.2,0.28,{fontSize:12,bold:true,color:C.navy,align:'center'});
  addSoWhat(s,'现阶段用外购机构保节拍，同时推进自制方案补齐成本与自主性。');
}

// 8 Conveyor
{
  const s=pptx.addSlide(); addContentChrome(s,'随线取放在不停线条件下实现2.2s，但精度受皮带偏差约束',8);
  s.addImage({path:P.conveyor,x:0.45,y:1.28,w:5.65,h:4.48,sizing:{type:'cover'}}); s.addShape(pptx.ShapeType.rect,{x:0.45,y:5.42,w:5.65,h:0.34,line:{color:C.navy,transparency:100},fill:{color:C.navy}}); addText(s,'K21-H-MODEL 印刷下料｜已投入生产运行',0.62,5.48,5.3,0.2,{fontSize:10,bold:true,color:C.white,align:'center'});
  addKpi(s,6.3,1.28,1.75,'CT','2.2s',C.orange); addKpi(s,8.25,1.28,1.75,'精度','±2mm',C.navy); addKpi(s,10.2,1.28,2.25,'材料成本','¥64,000',C.orange);
  const steps=[['皮带连续运行',6.35],['视觉定位+跟踪补偿',8.4],['四轴随线取放',10.55]]; steps.forEach(([t,x],i)=>{s.addShape(pptx.ShapeType.roundRect,{x,y:2.25,w:1.75,h:0.78,rectRadius:0.04,line:{color:'B7CAD8'},fill:{color:'F8FAFB'}});addText(s,t,x+0.1,2.48,1.55,0.28,{fontSize:10,bold:true,color:C.navy,align:'center'});if(i<2)s.addShape(pptx.ShapeType.line,{x:x+1.78,y:2.64,w:0.25,h:0,line:{color:C.navy,width:1.2,endArrowType:'triangle'}});});
  addPanel(s,6.3,3.25,2.55,2.15); addText(s,'通信：视觉PC与机器人采用 TCP/IP\n\n优势：不停线取放，节拍最快\n\n约束：精度主要受皮带线偏差影响',6.55,3.52,2.05,1.55,{fontSize:9.5,bold:true,color:C.navy,breakLine:true,valign:'top'});
  addPanel(s,9.05,3.25,3.4,2.15,'方案对比（精度维度）'); addText(s,'标准抓取｜停稳后拍照｜±1mm\n\n随线取放｜运动中跟踪｜±2mm',9.35,3.78,2.85,0.92,{fontSize:10,bold:true,color:C.navy,breakLine:true}); addText(s,'工况不同，2.2s不可与标准抓取CT直接横向比较。',9.28,4.82,2.95,0.34,{fontSize:8.3,bold:true,color:C.orange,align:'center'});
  addSoWhat(s,'适合连续输送场景；若精度优先，应先降低皮带偏差。');
}

// 9 Selection matrix
{
  const s=pptx.addSlide(); addContentChrome(s,'选型应先看场景约束，再在节拍、精度、行程和成本之间取舍',9);
  const cols=[0.65,3.6,5.55,7.0,8.4,10.0,12.55];
  const headers=['方案','材料成本（元）','CT','精度','行程／臂展','主要优势'];
  headers.forEach((t,i)=>{s.addShape(pptx.ShapeType.rect,{x:cols[i],y:1.22,w:cols[i+1]-cols[i]-0.02,h:0.38,line:{color:C.navy},fill:{color:C.navy}});addText(s,t,cols[i]+0.05,1.28,cols[i+1]-cols[i]-0.12,0.24,{fontSize:9.5,bold:true,color:C.white,align:'center'});});
  const rows=[
    ['自建三轴+旋转轴','¥33,170','6s','±1mm','—','低成本、调整灵活'],
    ['标准四轴','¥49,000','6s','±1mm','行程大','行程大'],
    ['外购并联机械手','未知','4s','±1mm','—','速度快、机构外购'],
    ['自制蜘蛛手','预计 ¥33,862','待验证','待验证','300mm','自主化目标'],
    ['随线取放','¥64,000','2.2s','±2mm','—','连续输送、受皮带偏差影响']
  ];
  rows.forEach((r,ri)=>r.forEach((t,i)=>{s.addShape(pptx.ShapeType.rect,{x:cols[i],y:1.62+ri*0.58,w:cols[i+1]-cols[i]-0.02,h:0.58,line:{color:'BCCAD5',width:0.5},fill:{color:ri%2?'F7F9FA':'FFFFFF'}});addText(s,t,cols[i]+0.06,1.72+ri*0.58,cols[i+1]-cols[i]-0.14,0.32,{fontSize:i===0||i===5?9:9.5,bold:i===1||i===2,color:i===2?C.orange:C.text,align:i===0||i===5?'left':'center',breakLine:true});}));
  const diffs=[['自制蜘蛛手比四轴低','¥15,138'],['自制蜘蛛手比随线低','¥30,138'],['四轴比自建三轴高','¥15,830']]; diffs.forEach((d,i)=>{s.addShape(pptx.ShapeType.roundRect,{x:0.65+i*4.0,y:4.72,w:3.68,h:0.48,rectRadius:0.04,line:{color:'A8C1D3'},fill:{color:'F8FAFB'}});addText(s,d[0]+'  '+d[1],0.82+i*4.0,4.82,3.34,0.22,{fontSize:10,bold:true,color:C.navy,align:'center'});});
  addPanel(s,0.65,5.38,11.9,0.62,'场景推荐'); addText(s,'成本/灵活性→自建轴    大行程→标准四轴    高速标准抓取→并联    连续输送→随线取放    核心自主化→自制蜘蛛手（验证后）',1.0,5.71,11.2,0.22,{fontSize:9.5,bold:true,color:C.navy,align:'center'});
  addSoWhat(s,'没有单一最优方案，优先按工况筛选，再比较成本。',6.08);
  addText(s,'注：材料成本口径可能不同；均不含人工、软件开发、调试、预备金与维护。',7.1,6.56,5.35,0.14,{fontSize:6.7,color:C.gray,align:'right'});
}

// 10 Gantt
{
  const s=pptx.addSlide(); addContentChrome(s,'自制蜘蛛手按设计、物料、组装和调试四阶段推进至10月底',10);
  s.addShape(pptx.ShapeType.roundRect,{x:9.0,y:1.18,w:3.3,h:0.72,rectRadius:0.04,line:{color:C.navy},fill:{color:C.navy}}); addText(s,'自制蜘蛛手首台｜臂展300mm｜预计材料 ¥33,862',9.28,1.36,2.75,0.3,{fontSize:10.5,bold:true,color:C.white,align:'center'});
  const months=[['7月',0.65,3.2],['8月',3.85,3.2],['9月',7.05,3.2],['10月',10.25,2.25]]; months.forEach(m=>{s.addShape(pptx.ShapeType.rect,{x:m[1],y:2.08,w:m[2],h:0.32,line:{color:C.navy},fill:{color:C.navy}});addText(s,m[0],m[1],2.12,m[2],0.22,{fontSize:10,bold:true,color:C.white,align:'center'});});
  for(let i=0;i<16;i++){s.addShape(pptx.ShapeType.line,{x:0.65+i*0.75,y:2.45,w:0,h:2.62,line:{color:'D9E0E5',width:0.4,dash:'dash'}});}
  const phases=[
    {name:'设计  7/2–7/20｜臂展300mm',x:0.78,y:2.72,w:2.45,c:'4472C4'},
    {name:'物料  7/21–8/15｜柔性振动盘/蜘蛛手/触控一体机',x:3.0,y:3.37,w:3.35,c:'70AD47'},
    {name:'组装  8/16–8/30',x:6.15,y:4.02,w:1.85,c:'ED7D31'},
    {name:'调试  8/31–10/30',x:8.0,y:4.67,w:4.25,c:'7030A0'}
  ];
  phases.forEach(p=>{s.addShape(pptx.ShapeType.roundRect,{x:p.x,y:p.y,w:p.w,h:0.42,rectRadius:0.04,line:{color:p.c},fill:{color:p.c}});addText(s,p.name,p.x+0.12,p.y+0.09,p.w-0.24,0.24,{fontSize:8.8,bold:true,color:C.white,align:'center'});});
  const ms=[['设计冻结',3.0,'4472C4'],['物料齐套',4.75,'70AD47'],['机械完成',8.0,'ED7D31'],['量产验证',12.25,'7030A0']]; ms.forEach(m=>{s.addShape(pptx.ShapeType.ellipse,{x:m[1]-0.06,y:5.2,w:0.12,h:0.12,line:{color:m[2]},fill:{color:m[2]}});addText(s,m[0],m[1]-0.48,5.35,0.96,0.22,{fontSize:8,bold:true,color:m[2],align:'center'});});
  addPanel(s,0.65,5.68,6.0,0.72); addText(s,'待验证指标：CT｜精度｜连续运行稳定性\n建议交付：参数记录、异常清单、量产验证报告',0.95,5.86,5.4,0.38,{fontSize:9.5,bold:true,color:C.navy,breakLine:true});
  addPanel(s,6.85,5.68,5.7,0.72); addText(s,'风险：物料齐套影响组装起点；调试覆盖视觉、运动控制与稳定性验证',7.15,5.88,5.1,0.3,{fontSize:9.5,bold:true,color:C.navy,breakLine:true});
  addSoWhat(s,'10月底前完成调试，并形成是否具备替代外购机构的量产证据。',6.42);
}

const out='C:/Users/lfaf-test/Documents/报告编写/outputs/视觉无序抓取_电气技术汇报_完整评审稿_R004.pptx';
await pptx.writeFile({fileName:out});
console.log(out);
