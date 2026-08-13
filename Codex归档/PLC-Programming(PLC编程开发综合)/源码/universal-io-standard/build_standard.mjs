import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const wb=Workbook.create();
const outDir="C:/Users/lfaf-test/Documents/PLC-Programming(PLC编程开发综合)/outputs/universal_io_standard_20260720";
const C={navy:"#17365D",blue:"#D9EAF7",green:"#E2F0D9",yellow:"#FFF2CC",red:"#F4CCCC",gray:"#E7E6E6",white:"#FFFFFF",line:"#B4C6E7"};
function letter(n){let s="";while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26)}return s}
function base(name,title,note,headers,rows=30){const sh=wb.worksheets.add(name);sh.showGridLines=false;const z=letter(headers.length);sh.getRange(`A1:${z}1`).merge();sh.getRange("A1").values=[[title]];sh.getRange("A1").format={fill:C.navy,font:{name:"Microsoft YaHei",size:16,bold:true,color:C.white},rowHeight:30};sh.getRange(`A2:${z}2`).merge();sh.getRange("A2").values=[[note]];sh.getRange("A2").format={fill:C.blue,font:{name:"Microsoft YaHei",size:10,italic:true},wrapText:true,rowHeight:32};sh.getRange(`A4:${z}4`).values=[headers];sh.getRange(`A4:${z}4`).format={fill:C.navy,font:{name:"Microsoft YaHei",size:10,bold:true,color:C.white},wrapText:true,horizontalAlignment:"center",rowHeight:28,borders:{preset:"all",style:"thin",color:C.line}};sh.getRange(`A5:${z}${rows}`).format={font:{name:"Microsoft YaHei",size:10},wrapText:true,verticalAlignment:"center",borders:{preset:"all",style:"thin",color:"#D9E2F3"}};sh.freezePanes.freezeRows(4);sh.freezePanes.freezeColumns(Math.min(2,headers.length));return sh}
function widths(sh,a){a.forEach((w,i)=>sh.getRangeByIndexes(0,i,1,1).format.columnWidth=w)}
function put(sh,data,last){if(data.length)sh.getRange(`A5:${last}${4+data.length}`).values=data}

const overview=wb.worksheets.add("规范总览");overview.showGridLines=false;
overview.getRange("A1:H1").merge();overview.getRange("A1").values=[["AS228T 通用 I/O 与 D 地址分配标准（送审版 v0.4）"]];overview.getRange("A1").format={fill:C.navy,font:{name:"Microsoft YaHei",size:18,bold:true,color:C.white},rowHeight:36};
overview.getRange("A3:B14").values=[
 ["适用范围","以后所有 AS228T / ISPSoft 项目"],["固定规则1","D10.0～D19.15 永久为系统状态"],["固定规则2","D20.0～D59.15 永久为 HMI 操作请求"],["固定规则3","D60～D99 永久为 HMI 反馈、选择和显示公共区"],["固定规则4","D100～D199 永久为伺服参数缓存，禁止其它用途"],["20轴容量","运行区每轴20字；参数区每轴40字，固定支持轴1～20"],["机器人容量","机器人1～10，每台固定100字"],["地址所有权","每个地址只有一个生产者/写入者；同一D字不得同时按位和整字由不同逻辑写入"],["HMI原则","HMI只写请求地址和D100～D139工作缓存，不直接写Y、轴输出、永久参数或机器人状态区"],["保持原则","运行命令、实时状态和D100～D199缓存不保持；永久参数、配方和示教点进入保持候选区"],["CANopen自动地址","D24000～D29999为HWCONFIG/CANopen自动映射及系统预留，禁止手工分配"],["发布状态","送审版；审核通过后才能进入skill和新项目模板"]
];overview.getRange("A3:A14").format={fill:C.navy,font:{bold:true,color:C.white},borders:{preset:"all",style:"thin",color:C.line}};overview.getRange("B3:B14").format={fill:C.green,wrapText:true,borders:{preset:"all",style:"thin",color:C.line}};
overview.getRange("A15:H15").merge();overview.getRange("A15").values=[["必须遵守"]];overview.getRange("A15").format={fill:C.navy,font:{bold:true,color:C.white}};
overview.getRange("A16:H22").values=[
 ["1","新功能只能使用所属分区的 Reserved/预留位，不得借用其它分区","","","","","",""] ,
 ["2","D位地址统一写成 D字.位，例如 D20.0；位号固定0～15","","","","","",""] ,
 ["3","PLC→外部和外部→PLC使用不同字；网络命令采用请求/确认或命令序号/回显","","","","","",""] ,
 ["4","报警主文本统一“区域/设备：客观异常状态”；处置建议独立保存","","","","","",""] ,
 ["5","安全门、急停、STO和安全链只能在普通PLC中监视，不以本表替代安全控制","","","","","",""] ,
 ["6","保持区以实际HWCONFIG为准；D20000～D23999只是手册默认保持候选区","","","","","",""] ,
 ["7","每个项目复制本模板后，只能补充符号和说明，不修改固定区段定义","","","","","",""]
];overview.getRange("A16:H22").format={fill:C.yellow,wrapText:true,borders:{preset:"all",style:"thin",color:C.line}};overview.getRange("A24:B28").values=[["审核状态","待审核"],["审核人",""],["审核日期",""],["意见",""],["批准成为公司标准","否"]];overview.getRange("A24:A28").format={fill:C.gray,font:{bold:true},borders:{preset:"all",style:"thin",color:C.line}};overview.getRange("B24:B28").format={fill:C.yellow,borders:{preset:"all",style:"thin",color:C.line}};overview.getRange("B24").dataValidation={rule:{type:"list",values:["待审核","有条件通过","通过","退回修改"]}};overview.getRange("B28").dataValidation={rule:{type:"list",values:["否","是"]}};widths(overview,[24,74,12,12,12,12,12,12]);

const ranges=[
 ["公共保留","D0","D9",10,"系统版本、项目编号、心跳、标准版本","否","固定"],
 ["系统状态","D10.0","D19.15",10,"机器模式、运行、就绪、故障、通信、安全状态监视","否","用户指定/锁定"],
 ["HMI操作请求","D20.0","D59.15",40,"模式、启停、复位、手动、示教、维护操作请求","否","用户指定/锁定"],
 ["HMI反馈与选择","D60","D99",40,"命令确认、拒绝原因、选择值、权限、当前页面/对象","否","固定"],
 ["伺服参数缓存","D100","D199",100,"当前轴工作缓存、影子/回滚缓存及缓存控制；禁止其它用途","否","用户指定/锁定"],
 ["物理DI映射","D200.0","D263.15",64,"最多1024点DI镜像；含伺服正/反极限及执行器反馈","否","固定"],
 ["物理DO请求","D264.0","D327.15",64,"最多1024点DO逻辑请求；Y仅由输出映射写入","否","固定"],
 ["互锁/许可","D328.0","D399.15",72,"设备许可、工艺互锁、禁止条件","否","固定"],
 ["报警Active","D400.0","D499.15",100,"当前报警条件，1600位","否","固定"],
 ["报警Latched","D500.0","D599.15",100,"报警事件锁存，1600位","否","固定"],
 ["报警请求/摘要","D600","D699",100,"Ack、Reset、受控屏蔽、等级汇总、报警代码","否","固定"],
 ["顺控/步骤","D700","D799",100,"步骤号、状态机、暂停/恢复上下文","否","固定"],
 ["工位/线体握手","D800","D899",100,"工位允许、完成、取走、上下站握手","否","固定"],
 ["公共预留","D900","D999",100,"公共功能扩展","否","不得跨区借用"],
 ["20轴运行区","D1000","D1399",400,"20轴×20字运行接口","否","固定"],
 ["轴诊断/组控制","D1400","D1599",200,"轴组、同步、公共诊断和HMI缓存","否","固定"],
 ["运动预留","D1600","D1999",400,"未来运动功能","否","预留"],
 ["机器人接口","D2000","D2999",1000,"机器人1～10×100字","否","固定"],
 ["通信映像","D3000","D3999",1000,"CANopen、EtherNet/IP、离散接口及诊断","否","固定"],
 ["设备/工位模块","D4000","D5999",2000,"工位1～20×100字或设备模块","否","固定"],
 ["线体/站间通信","D6000","D6999",1000,"上站、下站、MES前置握手","否","固定"],
 ["视觉/检测","D7000","D7999",1000,"CCD、测量、结果和拍照握手","否","固定"],
 ["数据/OEE","D8000","D8999",1000,"计数、周期、运行时间、数据上传缓存","按字段","固定"],
 ["项目工作区","D9000","D19999",11000,"项目特有工作数据；必须登记子分区","否","受控分配"],
 ["20轴参数区","D20000","D20799",800,"20轴×40字参数","项目确认","固定"],
 ["设备参数区","D20800","D20999",200,"设备设置、权限、工艺公共参数","项目确认","固定"],
 ["点位/配方区","D21000","D22999",2000,"示教点、配方、产品参数","项目确认","固定"],
 ["保持预留区","D23000","D23999",1000,"后续需保持参数","项目确认","预留"],
 ["CANopen输入自动映像","D24000","D24999",1000,"HWCONFIG自动分配：驱动TxPDO→PLC输入列表","否","自动/禁止手工"],
 ["CANopen输出自动映像","D25000","D25999",1000,"HWCONFIG自动分配：PLC输出列表→驱动RxPDO","否","自动/禁止手工"],
 ["系统自动映像预留","D26000","D29999",4000,"CANopen/HWCONFIG及系统自动分配扩展","按系统","禁止手工"]
];
const alloc=base("总地址分区","通用 D 地址总分区","绿色为锁定标准，黄色为受控预留，红色为系统自动区。以后项目不得改变起止范围。",["区块","起始","结束","字数","用途","保持","状态","责任模块","备注"],42);const allocRows=ranges.map(r=>[...r,r[6].includes("手工")?"HWCONFIG/CANopen":"标准库",""]);put(alloc,allocRows,"I");widths(alloc,[24,15,15,12,52,16,20,22,34]);allocRows.forEach((r,i)=>{const status=r[6];alloc.getRange(`A${5+i}:I${5+i}`).format.fill=status.includes("禁止手工")?C.red:(status.includes("预留")||status.includes("受控"))?C.yellow:C.green});

const state=base("系统状态D10-D19","系统状态固定字位","D10～D19只能由PLC状态管理模块写入，HMI、机器人和通信只能读取。未分配位必须保持Reserved。",["地址","标准符号","中文定义","生产者","消费者","失效值","保持","状态"],50);
const stateDefs=[
 ["D10.0","SYS_Manual","手动模式"],["D10.1","SYS_Auto","自动模式"],["D10.2","SYS_Running","运行中"],["D10.3","SYS_Standby","待机中"],["D10.4","SYS_Paused","暂停中"],["D10.5","SYS_Fault","故障中"],["D10.6","SYS_Ready","设备准备好"],["D10.7","SYS_Homed","回原点完成"],["D10.8","SYS_CycleActive","生产循环中"],["D10.9","SYS_CycleComplete","当前循环完成"],["D10.10","SYS_AlarmActive","存在活动报警"],["D10.11","SYS_EStopMon","急停状态监视"],["D10.12","SYS_SafetyReadyMon","安全系统就绪监视"],["D10.13","SYS_CommOK","公共通信正常"],["D10.14","SYS_Maintenance","维护模式"],["D10.15","SYS_InitDone","初始化完成"],
 ["D11.0","SYS_Starting","启动处理中"],["D11.1","SYS_Stopping","停止处理中"],["D11.2","SYS_Resetting","复位处理中"],["D11.3","SYS_Homing","回原点处理中"],["D11.4","SYS_WaitMaterial","等待物料"],["D11.5","SYS_WaitRobot","等待机器人"],["D11.6","SYS_WaitUpstream","等待上站"],["D11.7","SYS_WaitDownstream","等待下站"],["D11.8","SYS_SingleStep","单步模式"],["D11.9","SYS_DryRun","空运行/循环测试"],["D11.10","SYS_BypassActive","存在受控屏蔽"],["D11.11","SYS_RecipeLoaded","配方已加载"],["D11.12","SYS_Changeover","换型处理中"],["D11.13","SYS_RemoteEnable","远程操作允许"],["D11.14","SYS_DataValid","公共数据有效"],["D11.15","Reserved","预留"],
 ["D12.0～D15.15","SYS_StationState","工位1～64状态摘要","PLC状态管理","HMI/顺控","FALSE","否","固定"],["D16.0～D17.15","SYS_CommState","通信节点状态摘要","通信管理","HMI/顺控","FALSE","否","固定"],["D18.0～D19.15","Reserved","系统状态扩展预留","PLC状态管理","HMI","FALSE","否","预留"]
];
const stateRows=stateDefs.map(r=>r.length===3?[...r,"PLC状态管理","HMI/顺控/外部","FALSE","否",r[1]==="Reserved"?"预留":"固定"]:r);put(state,stateRows,"H");widths(state,[18,28,30,20,22,14,12,14]);state.getRange(`A5:H${4+stateRows.length}`).format.fill=C.green;

const hmi=base("HMI操作D20-D59","HMI 操作请求固定分配","所有位均为请求。PLC检查模式、权限、互锁和设备状态后执行；不得从HMI直接写Y或运动输出。",["字范围","功能分组","典型位定义","生产者","消费者","动作方式","超时/释放","状态"],50);
const hmiRows=[
 ["D20.0～D20.15","模式与整机控制","手动/自动选择、启动、停止、暂停、恢复、回零、初始化","HMI","PLC命令管理","请求/确认","PLC捕获后清除或保持至确认","固定"],
 ["D21.0～D21.15","生产循环","单循环、连续、单步、空运行、换型、恢复生产","HMI","顺控管理","请求/确认","超时撤销","固定"],
 ["D22.0～D22.15","报警与数据","报警确认、故障复位、计数清零、历史清除请求","HMI","报警/数据管理","边沿请求","权限确认后执行","固定"],
 ["D23.0～D23.15","配方与点位","加载、保存、插入、删除、设零、应用参数","HMI","参数/点位管理","请求/确认","写操作需权限和结果反馈","固定"],
 ["D24.0～D24.15","公共手动","夹具开关、气源、照明、蜂鸣、辅助设备请求","HMI","手动命令管理","保持或点动","掉线进入定义的安全状态","固定"],
 ["D25.0～D25.15","维护与诊断","诊断启动、测试请求、记录导出、受控调试","HMI","维护模块","请求/确认","工程师权限+自动超时","固定"],
 ["D26.0～D29.15","公共选择位","工位、设备、机器人、轴、动作类别选择标志","HMI","选择管理","保持","选择变化需一致性校验","固定"],
 ["D30.0～D39.15","工位手动请求","工位1～10或设备组手动动作请求","HMI","设备模块","按住/请求确认","松开、切页、掉线停止","固定"],
 ["D40.0～D49.15","轴/机器人手动请求","对D80选择的轴/机器人执行JOG、回零、复位、运行","HMI","轴/机器人管理","按住/请求确认","JOG松开或掉线立即停止","固定"],
 ["D50.0～D59.15","项目公共扩展","工位11～20或项目公共操作","HMI","设备模块","按项目登记","不得改变本范围用途","预留"]
];put(hmi,hmiRows,"H");widths(hmi,[20,22,52,16,22,20,34,14]);hmi.getRange("A5:H13").format.fill=C.green;hmi.getRange("A14:H14").format.fill=C.yellow;

const alarm=base("报警标准","报警地址与标准语言","Active、Latched、Ack、Reset和Suppress必须分开。安全相关文字只是状态监视，不替代安全功能。",["地址/区段","用途","写入者","标准语言/规则","保持","权限","备注"],35);
const alarmRows=[
 ["D400.0～D499.15","活动报警Active","报警管理","条件存在时TRUE，条件消失时FALSE","否","PLC","1600位"],
 ["D500.0～D599.15","锁存报警Latched","报警管理","报警发生后保持，按复位规则清除","否","PLC","与Active同序号映射"],
 ["D600.0～D619.15","报警确认请求Ack","HMI","人员确认请求，不等于故障消失","否","操作员","可按组或单条"],
 ["D620.0～D639.15","报警复位请求Reset","HMI","PLC验证触发条件消失后复位","否","操作员/工程师","不得直接清报警位"],
 ["D640.0～D659.15","受控屏蔽请求Suppress","HMI/权限管理","需要权限、原因、期限、记录和显著提示","项目确认","工程师","安全功能不得软件屏蔽"],
 ["D660～D679","报警汇总","报警管理","按等级、区域、设备汇总","否","PLC","HMI只读"],
 ["D680～D699","报警代码/索引","报警管理","当前、首发、最后、最高等级报警代码","按字段","PLC","时间戳可在上位机记录"],
 ["语言模板","主文本","HMI/PLC标准","“区域/设备：客观异常状态”","-","-","示例：1号轴：回原点超时"],
 ["操作指引","独立字段","HMI标准","说明确认条件和处理步骤，不写模糊的“请检查”","-","-","不在主报警文本中堆步骤"],
 ["禁止措辞","不允许","审核规则","设备坏了、通讯有问题、传感器异常、请检查一下","-","-","必须指出对象和状态"]
];put(alarm,alarmRows,"G");widths(alarm,[24,22,20,54,16,18,42]);alarm.getRange("A5:G14").format.fill=C.green;

const axis=base("20轴标准","20 轴固定地址","轴运行区不保持；参数区位于保持候选区。轴号永久为1～20，禁止按项目重新排序。",["轴号","运行起始","运行结束","参数起始","参数结束","运行公式","参数公式","状态"],24);
const axisRows=[];for(let a=1;a<=20;a++){const rb=1000+(a-1)*20,pb=20000+(a-1)*40;axisRows.push([a,`D${rb}`,`D${rb+19}`,`D${pb}`,`D${pb+39}`,`1000+(轴号-1)×20`,`20000+(轴号-1)×40`,"固定"])}put(axis,axisRows,"H");widths(axis,[10,16,16,16,16,26,28,14]);axis.getRange("A5:H24").format.fill=C.green;

const cache=base("伺服缓存D100-D199","伺服参数缓存固定分配 D100～D199","D100～D139为当前选中轴工作缓存，D140～D179为影子/回滚缓存，两者与D20000起的每轴40字永久参数块同偏移。D180～D189为缓存控制；D190～D199仅作伺服缓存扩展。",["地址","偏移","数据类型","标准符号","参数/单位","写入者","保持","校验与说明"],64);
const servoParamDefs=[
 [0,"DWORD","PositiveSoftLimit","正向软件极限/位置单位","HMI授权/参数管理","必须大于NegativeSoftLimit；物理正限位使用DI"],
 [2,"DWORD","NegativeSoftLimit","反向软件极限/位置单位","HMI授权/参数管理","必须小于PositiveSoftLimit；物理反限位使用DI"],
 [4,"UDWORD","PulsesPerRev","每圈脉冲数/pulse·rev⁻¹","HMI授权/参数管理","必须>0；脉冲轴必填，CANopen轴按工程单位换算"],
 [6,"UDWORD","Acceleration","加速度/工程单位·s⁻²","HMI授权/参数管理","必须>0且不超过驱动和机构允许值"],
 [8,"UDWORD","Deceleration","减速度/工程单位·s⁻²","HMI授权/参数管理","必须>0且不超过驱动和机构允许值"],
 [10,"UDWORD","ManualLowSpeed","手动低速/工程单位·s⁻¹","HMI授权/参数管理","0≤值≤MaxSpeed"],
 [12,"UDWORD","ManualMidSpeed","手动中速/工程单位·s⁻¹","HMI授权/参数管理","ManualLowSpeed≤值≤ManualHighSpeed"],
 [14,"UDWORD","ManualHighSpeed","手动高速/工程单位·s⁻¹","HMI授权/参数管理","值≤MaxSpeed"],
 [16,"UDWORD","AutoSpeed","自动速度/工程单位·s⁻¹","HMI授权/参数管理","值≤MaxSpeed"],
 [18,"UDWORD","HomeSpeed","回原速度/工程单位·s⁻¹","HMI授权/参数管理","值≤MaxSpeed；方向由ConfigFlags定义"],
 [20,"UDWORD","PositionTolerance","到位容差/位置单位","HMI授权/参数管理","必须≥0"],
 [22,"DINT","HomeOffset","原点偏移/位置单位","HMI授权/参数管理","可正可负；应用后重新确认软限位"],
 [24,"UDWORD","GearNumerator","电子齿轮分子","HMI授权/参数管理","必须>0"],
 [26,"UDWORD","GearDenominator","电子齿轮分母","HMI授权/参数管理","必须>0，禁止为0"],
 [28,"UDWORD","DecelPoint","减速点/位置单位","HMI授权/参数管理","按绝对值或剩余距离解释，由ConfigFlags定义"],
 [30,"UDWORD","SlowProcessSpeed","工艺慢速/工程单位·s⁻¹","HMI授权/参数管理","值≤MaxSpeed"],
 [32,"UDWORD","MaxSpeed","最大允许速度/工程单位·s⁻¹","工程师/参数管理","不得超过驱动、丝杆、皮带或机构额定值"],
 [34,"UDWORD","JogDistance","点动定距/位置单位","HMI授权/参数管理","0表示连续点动；>0表示定距点动"],
 [36,"WORD/BIT","ConfigFlags","启用/方向/单位/限位配置","参数管理","按位定义并版本化；不得与整字多写入者共用"],
 [37,"WORD","AxisType","轴类型","参数管理","0未用/1脉冲/2 CANopen 301/3 CANopen 402"],
 [38,"WORD","ParameterVersion","参数结构版本","参数管理","用于兼容迁移；本版建议4"],
 [39,"WORD","Checksum","参数校验码","参数管理","覆盖偏移+0～+38；算法需在项目中固定"]
];
const cacheRows=[];
for(const [o,t,n,u,w,note] of servoParamDefs){const end=(t==="DWORD"||t==="UDWORD"||t==="DINT")?o+1:o;cacheRows.push([end>o?`D${100+o}～D${100+end}`:`D${100+o}`,`+${o}${end>o?`～+${end}`:""}`,t,`AXC_${n}`,u,w,"否",note])}
for(const [o,t,n,u,w,note] of servoParamDefs){const end=(t==="DWORD"||t==="UDWORD"||t==="DINT")?o+1:o;cacheRows.push([end>o?`D${140+o}～D${140+end}`:`D${140+o}`,`影子+${o}${end>o?`～+${end}`:""}`,t,`AXS_${n}`,`${u}（回滚副本）`,`PLC参数管理`,"否",`加载工作缓存前复制；${note}`])}
cacheRows.push(
 ["D180","控制+0","WORD","AXC_SelectedAxisNo","选中轴号1～20","HMI","否","0=未选择；禁止超出1～20"],
 ["D181","控制+1","WORD/BIT","AXC_RequestWord","加载/校验/应用/保存/回滚/复制/默认值请求","HMI","否",".0 Load .1 Validate .2 Apply .3 Save .4 Rollback .5 CopyAxis .6 Default；仅HMI写"],
 ["D182","控制+2","WORD/BIT","AXC_StatusWord","已加载/有效/已修改/应用中/完成/拒绝/保存完成/回滚完成/校验和/范围/权限","PLC参数管理","否",".0～.10对应状态；仅PLC写，禁止HMI写"],
 ["D183","控制+3","WORD","AXC_ValidationErrorCode","参数校验错误码","PLC参数管理","否","0=无错误；非0对应首个拒绝原因"],
 ["D184","控制+4","WORD","AXC_SourceAxisNo","复制来源轴号","HMI","否","CopyAxis请求时1～20，且可禁止复制到同轴"],
 ["D185","控制+5","WORD","AXC_ChangeCounter","缓存变更计数","PLC参数管理","否","检测HMI分批写入和并发变更"],
 ["D186","控制+6","WORD","AXC_CacheVersion","缓存结构版本","PLC参数管理","否","应与ParameterVersion兼容"],
 ["D187～D189","控制+7～+9","WORD[3]","AXC_Reserved","伺服缓存控制扩展","-","否","保持Reserved"],
 ["D190～D199","预留","WORD[10]","AXC_ServoReserved","伺服参数缓存扩展","-","否","只能用于伺服缓存；禁止DI/DO、报警或通信占用"]
);
put(cache,cacheRows,"H");widths(cache,[20,18,16,28,40,24,12,62]);cache.getRange(`A5:H${4+cacheRows.length}`).format.fill=C.green;cache.getRange(`A${5+servoParamDefs.length}:H${4+servoParamDefs.length*2}`).format.fill=C.blue;cache.getRange(`A${5+servoParamDefs.length*2}:H${4+cacheRows.length}`).format.fill=C.yellow;

const axisField=base("轴块字段","每轴运行20字与参数40字字段","所有轴使用相同偏移。CANopen和脉冲轴都映射到本逻辑接口；协议私有数据留在通信映像区。",["区域","偏移","类型","标准字段","方向/生产者","保持","说明"],55);
const runFields=[
 ["运行","+0","WORD/BIT","CommandWord","PLC轴管理","否","Enable/ServoOn/Reset/Home/Move/Jog/Stop等请求"],
 ["运行","+1","WORD/BIT","StatusWord","驱动/轴管理","否","Online/Ready/ServoOn/Homed/Busy/InPosition/Alarm等"],
 ["运行","+2","WORD/BIT","AlarmWord","报警管理","否","驱动、通信、回零、定位、限位、参数、互锁报警"],
 ["运行","+3","WORD/BIT","InterlockWord","轴管理","否","允许运动、正/反向许可、回零许可"],
 ["运行","+4","WORD","AlarmCode","驱动/报警管理","否","0=无报警"],
 ["运行","+5","WORD","ModeAndQuality","轴/通信管理","否","轴模式、协议类型、数据质量"],
 ["运行","+6～+7","DWORD","TargetPosition","PLC轴管理","否","运行目标位置"],
 ["运行","+8～+9","DWORD","ActualPosition","驱动/计数器","否","实时位置"],
 ["运行","+10～+11","DWORD","TargetSpeed","PLC轴管理","否","运行目标速度"],
 ["运行","+12～+13","DWORD","ActualSpeed","驱动/计算模块","否","实时速度"],
 ["运行","+14","WORD","CommandSeq","PLC轴管理","否","新命令递增"],
 ["运行","+15","WORD","CommandSeqEcho","驱动/接口管理","否","处理完成后回显"],
 ["运行","+16","WORD","CurrentStep","轴状态机","否","当前动作步骤"],
 ["运行","+17","WORD","DiagnosticCode","轴管理","否","诊断子码"],
 ["运行","+18～+19","WORD[2]","Reserved","-","否","运行扩展预留"]
];
const paramFields=servoParamDefs.map(([o,t,n,u,w,note])=>["参数",(t==="DWORD"||t==="UDWORD"||t==="DINT")?`+${o}～+${o+1}`:`+${o}`,t,n,"参数管理/HMI授权","项目确认",`${u}；${note}`]);
put(axisField,[...runFields,...paramFields],"G");widths(axisField,[14,16,16,28,24,16,48]);axisField.getRange(`A5:G${4+runFields.length+paramFields.length}`).format.fill=C.green;

const robot=base("机器人标准","机器人1～10固定接口","每台100字；前50字PLC生产、后50字机器人生产，禁止双向共写。EIP或离散I/O只改变映射层，不改变逻辑地址。",["机器人","块起始","块结束","PLC→Robot","Robot→PLC","用途","状态"],14);
const robotRows=[];for(let r=1;r<=10;r++){const b=2000+(r-1)*100;robotRows.push([r,`D${b}`,`D${b+99}`,`D${b}～D${b+49}`,`D${b+50}～D${b+99}`,"命令/程序/数据 | 在线/就绪/忙/完成/报警/回显","固定"])}put(robot,robotRows,"G");widths(robot,[12,16,16,24,24,56,14]);robot.getRange("A5:G14").format.fill=C.green;

const comm=base("通信与物理IO","通信和物理 I/O 映射规则","协议原始映像与逻辑接口分离。CANopen采用CiA 301；CiA 402仅在设备EDS/手册支持时使用。",["地址范围","固定用途","方向","生产者","消费者","超时/失效","备注"],28);
const commRows=[
 ["D200.0～D263.15","物理DI镜像","现场→PLC","IO_MAP","设备/顺控","断线值按电气设计","X仅在映射层出现；执行器实际反馈也必须回到本区"],
 ["D200.0～D201.3","轴1～20正向物理限位","现场→PLC","IO_MAP","轴管理","断线按触发处理","轴n地址：D[200+INT((n-1)/16)].[(n-1) MOD 16]"],
 ["D202.0～D203.3","轴1～20反向物理限位","现场→PLC","IO_MAP","轴管理","断线按触发处理","轴n地址：D[202+INT((n-1)/16)].[(n-1) MOD 16]"],
 ["D204.0～D205.3","轴1～20原点传感器","现场→PLC","IO_MAP","轴管理","断线按未到位处理","轴n地址：D[204+INT((n-1)/16)].[(n-1) MOD 16]"],
 ["D206.0～D263.15","其它物理DI及执行器反馈","现场→PLC","IO_MAP","设备/顺控/HMI","按设备失效定义","不得用DO命令位代替实际反馈"],
 ["D264.0～D327.15","物理DO逻辑请求","PLC→现场","设备模块","IO_MAP","PLC STOP进入定义状态","Y只由IO_MAP写入；实际反馈从D200～D263返回"],
 ["D3000～D3199","CANopen原始映像","双向分区","CANopen管理","逻辑接口","Heartbeat超时置无效","NMT/PDO/SDO/EMCY"],
 ["D3200～D3399","EIP PLC输出Assembly","PLC→外部","PLC接口","外部设备","连接超时清命令","记录Assembly、长度、RPI、字序"],
 ["D3400～D3599","EIP PLC输入Assembly","外部→PLC","外部设备","PLC接口","连接超时状态无效","先校验再使用"],
 ["D3600～D3799","离散机器人/I/O映像","双向分区","IO_MAP","机器人接口","断线为FALSE或定义值","逻辑地址仍使用机器人标准块"],
 ["D3800～D3999","通信诊断/预留","只读为主","通信管理","HMI/诊断","保留最后错误和计数","不得放控制命令"],
 ["D24000～D24999","CANopen输入列表自动映像","驱动TxPDO→PLC","HWCONFIG/CANopen","PLC逻辑映射","重配后地址可能变化","禁止手工变量占用；以当前输入列表为准"],
 ["D25000～D25999","CANopen输出列表自动映像","PLC→驱动RxPDO","HWCONFIG/CANopen","驱动","重配后地址可能变化","禁止手工变量占用；以当前输出列表为准"],
 ["D26000～D29999","系统自动映像预留","系统决定","HWCONFIG/固件","系统","不得假设空闲","禁止手工分配"]
];put(comm,commRows,"G");widths(comm,[24,34,20,24,24,32,58]);comm.getRange(`A5:G${4+commRows.length-3}`).format.fill=C.green;comm.getRange(`A${5+commRows.length-3}:G${4+commRows.length}`).format.fill=C.red;

const eds=base("EDS与自动映射","SV630C EDS 与当前自动映射记录","EDS定义CANopen对象和PDO能力；PLC的D地址由ISPSoft/HWCONFIG按节点和PDO配置生成，不应写入公司固定逻辑地址。",["项目","内容","工程结论","来源"],30);
const edsRows=[
 ["EDS文件","SV630C_LFAF_ip.EDS；EDSVersion 4.0；FileVersion 3；2018-06-27","作为当前SV630C设备描述文件管理版本","EDS [FileInfo]"],
 ["厂商/产品","Shenzhen Inovance Technology；SV630C_LFAF_ip","不是台达私有驱动对象，但由台达HWCONFIG导入配置","EDS [DeviceInfo]"],
 ["PDO数量","4个RxPDO、4个TxPDO","映射内容和长度可配置；变更后D地址列表可能重新生成","EDS DeviceInfo"],
 ["CiA402对象","6040/6041/603F/6060/6061/607A/6064/60FF等","逻辑层使用标准轴接口；协议层按EDS映射","EDS对象字典"],
 ["默认RxPDO1","6040h、60C1:01h、6060h、6098h","仅是EDS初值；项目实际输出列表优先","EDS 1600h"],
 ["默认TxPDO1","6041h、603Fh、6077h、6061h等","EDS中6061h出现两次，实际使用前核对当前映射","EDS 1A00h"],
 ["当前节点4输入","D24048～D24055；TxPDO Statusword/Error/Torque/Mode/Position/Velocity等","当前配置可见8个D字；不是永久地址公式","用户截图"],
 ["当前节点4输出","D25048～D25055；RxPDO Controlword/Mode/Homing/Target position/Profile等","由HWCONFIG自动分配，不复制为固定协议地址","用户截图"],
 ["当前节点5","输入从D24056开始；输出从D25056开始","当前配置连续排列；修改PDO后重新核对","用户截图"],
 ["_L/_H含义","同一个D字的低/高字节；16位对象占1个D，32位对象占连续2个D","禁止把_L/_H误认为两个完整D字","截图/数据类型"],
 ["程序使用方式","D240xx/D250xx自动映像→CANopen映射POU→D1000～D1399标准轴运行区","业务顺控不直接依赖自动地址","本标准"],
 ["变更门禁","更换EDS、节点号、PDO对象或顺序后重新导出输入/输出列表并做交叉引用","未复核前禁止下载运行设备","本标准"]
];put(eds,edsRows,"D");widths(eds,[24,60,60,28]);eds.getRange("A5:D16").format.fill=C.blue;

const review=base("审核清单","标准发布前审核","审核通过后再写入skill；此后项目只能填预留位和符号，不得改变固定区段。",["序号","审核项","通过标准","结论","意见"],26);
const reviewRows=[
 [1,"系统状态区","确认D10.0～D19.15永久锁定为状态","待审核",""],[2,"HMI操作区","确认D20.0～D59.15永久锁定为操作请求","待审核",""],[3,"HMI反馈区","确认D60～D99用于反馈、选择和公共显示","待审核",""],[4,"伺服缓存锁定","确认D100～D199只用于伺服参数缓存，任何其它变量不得占用","待审核",""],[5,"缓存字段","确认D100～D139工作缓存、D140～D179影子缓存、D180～D189控制、D190～D199伺服预留","待审核",""],[6,"字段同偏移","确认缓存+0～+39与D20000起每轴40字永久参数块完全一致","待审核",""],[7,"限位与速度","确认正/反软限位、每圈脉冲、加减速度、手动三级速度、自动速度等具体地址","待审核",""],[8,"物理轴输入","确认轴1～20正限位D200.0起、反限位D202.0起、原点D204.0起","待审核",""],[9,"报警分区","确认D400 Active、D500 Latched、D600～D699请求/摘要","待审核",""],[10,"20轴容量","确认运行20字/轴、参数40字/轴满足项目","待审核",""],[11,"机器人容量","确认最多10台、100字/台及收发半区","待审核",""],[12,"通信映像","确认CANopen/EIP/离散映像区及方向","待审核",""],[13,"物理I/O","确认X/Y只在IO_MAP层使用，执行器反馈从DI区返回","待审核",""],[14,"保持范围","确认D20000～D23999实际HWCONFIG策略","待审核",""],[15,"屏蔽治理","屏蔽有权限、超时、记录、显著提示；不替代安全回路","待审核",""],[16,"命名规则","统一SYS/HMI/ALM/AX/AXC/AXS/RBT/DI/DO前缀","待审核",""],[17,"CANopen自动地址","D24000～D29999禁止手工使用；PDO变更后重新核对自动列表","待审核",""],[18,"EDS版本治理","EDS文件、节点号、PDO映射和输入/输出列表已归档","待审核",""],[19,"版本治理","标准升级需版本号、变更记录和兼容说明","待审核",""]
];put(review,reviewRows,"E");widths(review,[10,30,70,16,42]);review.getRange(`A5:E${4+reviewRows.length}`).format.fill=C.yellow;review.getRange(`D5:D${4+reviewRows.length}`).dataValidation={rule:{type:"list",values:["待审核","通过","需修改","不适用"]}};

for(const name of ["规范总览","总地址分区","系统状态D10-D19","HMI操作D20-D59","报警标准","20轴标准","伺服缓存D100-D199","轴块字段","机器人标准","通信与物理IO","EDS与自动映射","审核清单"]){wb.worksheets.getItem(name).getUsedRange().format.autofitRows()}

await fs.mkdir(outDir,{recursive:true});const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(`${outDir}/AS228T_通用IO地址分配标准_送审版_v0.4.xlsx`);
const renders={"规范总览":"A1:H28","总地址分区":"A1:I36","系统状态D10-D19":"A1:H40","HMI操作D20-D59":"A1:H16","报警标准":"A1:G16","20轴标准":"A1:H24","伺服缓存D100-D199":"A1:H60","轴块字段":"A1:G42","机器人标准":"A1:G14","通信与物理IO":"A1:G20","EDS与自动映射":"A1:D18","审核清单":"A1:E24"};
for(const [name,range] of Object.entries(renders)){const png=await wb.render({sheetName:name,range,scale:1,format:"png"});await fs.writeFile(`${outDir}/${name}.png`,new Uint8Array(await png.arrayBuffer()))}
const wordNo=v=>{const m=String(v).match(/^D(\d+)/);return m?Number(m[1]):NaN};
const numericRanges=ranges.map(r=>({name:r[0],start:wordNo(r[1]),end:wordNo(r[2])})).filter(r=>Number.isFinite(r.start)&&Number.isFinite(r.end)).sort((a,b)=>a.start-b.start);
const overlaps=[];for(let i=1;i<numericRanges.length;i++)if(numericRanges[i].start<=numericRanges[i-1].end)overlaps.push([numericRanges[i-1].name,numericRanges[i].name]);
const servoOffsets=servoParamDefs.flatMap(([o,t])=>(t==="DWORD"||t==="UDWORD"||t==="DINT")?[o,o+1]:[o]).sort((a,b)=>a-b);
const servoOffsetsComplete=servoOffsets.length===40&&servoOffsets.every((v,i)=>v===i);
await fs.writeFile(`${outDir}/qa.txt`,JSON.stringify({sheetCount:12,rangeCount:ranges.length,numericRangeOverlaps:overlaps,axis20:{runtime:"D1000-D1399",parameters:"D20000-D20799",parameterWordsPerAxis:40},locked:{state:"D10.0-D19.15",hmi:"D20.0-D59.15",servoCache:"D100-D199",physicalDI:"D200.0-D263.15",physicalDO:"D264.0-D327.15",canopenAutoInput:"D24000-D24999",canopenAutoOutput:"D25000-D25999",systemAutoReserved:"D26000-D29999"},servoCache:{working:"D100-D139",shadow:"D140-D179",control:"D180-D189",reserved:"D190-D199",offsets:servoOffsets,offsetsComplete:servoOffsetsComplete,fieldOffsetsMatchPermanent:servoOffsetsComplete}},null,2));
console.log(JSON.stringify({output:`${outDir}/AS228T_通用IO地址分配标准_送审版_v0.4.xlsx`,overlaps}));
