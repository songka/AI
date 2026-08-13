import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const wb = Workbook.create();
const outputDir = "C:/Users/lfaf-test/Documents/PLC-Programming(PLC编程开发综合)/outputs/io_table_review_20260720";
const navy = "#17365D", blue = "#D9EAF7", yellow = "#FFF2CC", gray = "#E7E6E6";
const green = "#E2F0D9", red = "#F4CCCC", white = "#FFFFFF", line = "#B4C6E7";

function setup(name, title, note, headers, rows, totalRows = 44) {
  const sh = wb.worksheets.add(name);
  sh.showGridLines = false;
  const lastCol = String.fromCharCode(64 + headers.length);
  sh.getRange(`A1:${lastCol}1`).merge();
  sh.getRange("A1").values = [[title]];
  sh.getRange("A1").format = { fill: navy, font: { color: white, bold: true, size: 16 }, rowHeight: 30, verticalAlignment: "center" };
  sh.getRange(`A2:${lastCol}2`).merge();
  sh.getRange("A2").values = [[note]];
  sh.getRange("A2").format = { fill: blue, font: { color: "#1F1F1F", italic: true }, wrapText: true, rowHeight: 34, verticalAlignment: "center" };
  sh.getRange(`A4:${lastCol}4`).values = [headers];
  sh.getRange(`A4:${lastCol}4`).format = { fill: navy, font: { color: white, bold: true }, wrapText: true, rowHeight: 30, borders: { preset: "all", style: "thin", color: line }, horizontalAlignment: "center", verticalAlignment: "center" };
  if (rows.length) sh.getRange(`A5:${lastCol}${4 + rows.length}`).values = rows;
  if (4 + rows.length < totalRows) sh.getRange(`A${5 + rows.length}:${lastCol}${totalRows}`).format.fill = yellow;
  sh.getRange(`A5:${lastCol}${totalRows}`).format = { ...sh.getRange(`A5:${lastCol}${totalRows}`).format, borders: { preset: "all", style: "thin", color: "#D9E2F3" }, wrapText: true, verticalAlignment: "center" };
  if (rows.length) sh.getRange(`A5:${lastCol}${4 + rows.length}`).format.fill = blue;
  sh.freezePanes.freezeRows(4);
  sh.freezePanes.freezeColumns(2);
  sh.getRange(`A1:${lastCol}${totalRows}`).format.font = { name: "Microsoft YaHei", size: 10 };
  sh.getRange("A1").format.font = { name: "Microsoft YaHei", size: 16, bold: true, color: white };
  sh.getRange(`A4:${lastCol}4`).format.font = { name: "Microsoft YaHei", size: 10, bold: true, color: white };
  return { sh, lastCol, totalRows };
}

function widths(sh, vals) {
  vals.forEach((w, i) => sh.getRangeByIndexes(0, i, 1, 1).format.columnWidth = w);
}

const cover = wb.worksheets.add("审核说明");
cover.showGridLines = false;
cover.getRange("A1:H1").merge(); cover.getRange("A1").values = [["AS228T 标准 I/O 表（送审版）"]];
cover.getRange("A1").format = { fill: navy, font: { name: "Microsoft YaHei", color: white, bold: true, size: 20 }, rowHeight: 38, verticalAlignment: "center" };
cover.getRange("A3:B12").values = [
  ["项目状态","送审草案，不可直接用于现场下载"],["适用平台","Delta AS228T / AS228T-A + ISPSoft"],["版本","DRAFT 0.1 / 2026-07-20"],["审核重点","地址分区、生产者/消费者、机器人握手、报警语言、HMI 手动权限"],
  ["D 位写法","AS 系列支持 D0.0～D29999.15；一个字只有一个写入方"],["物理输出","HMI、机器人和通信不得直接拥有 Y；统一由 PLC 输出映射层写入"],
  ["CANopen","采用通用 CiA 301；CiA 402 对象仅在设备 EDS/手册支持时使用"],["机器人","EtherNet/IP 或离散 I/O；请求保持至确认，或使用命令序号+回显"],
  ["保持原则","命令/状态/报警实时位不保持；配方/校准参数才进入经确认的保持区"],["安全边界","普通 PLC 报警和 SafetyOK 状态不替代急停、门锁、STO 或安全 PLC"]
];
cover.getRange("A3:A12").format = { fill: navy, font: { color: white, bold: true }, borders: { preset: "all", style: "thin", color: line } };
cover.getRange("B3:B12").format = { fill: blue, wrapText: true, borders: { preset: "all", style: "thin", color: line } };
cover.getRange("A14:H14").merge(); cover.getRange("A14").values = [["审核结论填写"]]; cover.getRange("A14").format = { fill: navy, font: { color: white, bold: true } };
cover.getRange("A15:B19").values = [["审核状态","待审核"],["审核人",""],["审核日期",""],["意见",""],["是否允许进入 skill 2.2.0","否"]];
cover.getRange("A15:A19").format = { fill: gray, font: { bold: true }, borders: { preset: "all", style: "thin", color: line } };
cover.getRange("B15:B19").format = { fill: yellow, borders: { preset: "all", style: "thin", color: line }, wrapText: true };
cover.getRange("B15").dataValidation = { rule: { type: "list", values: ["待审核","有条件通过","通过","退回修改"] } };
cover.getRange("B19").dataValidation = { rule: { type: "list", values: ["否","是"] } };
cover.getRange("A21:H26").merge(); cover.getRange("A21").values = [["官方依据：\n1) Delta AS Series Programming Manual 2024-09-20（D 字位设备范围）\n2) Delta ISPSoft User Manual（HWCONFIG、符号与通信映射）\n3) CiA 301 / CiA 402 官方资料（CANopen）\n4) ODVA EtherNet/IP Technology Overview（Producer/Consumer 与连接超时）\n\n注意：本表中的 D 区是项目建议分区，不是 CPU 自动分配；必须与实际 HWCONFIG、现有程序、通信表和保持区核对。"]];
cover.getRange("A21").format = { fill: "#F2F2F2", wrapText: true, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: line }, rowHeight: 110 };
widths(cover,[18,78,12,12,12,12,12,12]);

let s = setup("地址分区","建议 D 地址分区","蓝色为示例，黄色为待填写。分区发布前必须与实际项目做冲突检查。",["区块","起始","结束","用途","生产者/唯一写入者","主要消费者","保持","状态","审核备注"],[
  ["SYS","D0","D99","系统公共命令、状态、模式、心跳","PLC_SYS","HMI/各模块","否","建议","D0～D9 优先保留公共字"],
  ["IO_MAP","D100","D499","物理 I/O 映射与设备接口","IO_MAP","设备模块/HMI","否","建议","Y 仅由输出映射写入"],
  ["HMI","D500","D999","HMI 请求、反馈、手动、设定值","HMI/PLC分向","PLC/HMI","否","建议","请求与反馈分字"],
  ["ALM","D1000","D1999","报警 Active/Latched/Ack/代码","ALARM_MGR","HMI/顺控","否","建议","四类状态分区"],
  ["ROBOT","D2000","D2999","机器人命令、状态、程序和数据","PLC/Robot分向","PLC/Robot","否","建议","EIP 与离散 I/O共用逻辑层"],
  ["AXIS","D3000","D3999","CANopen、脉冲轴命令/状态/工艺量","AXIS_MGR","HMI/顺控","否","建议","每轴预留连续块"],
  ["COM","D4000","D4999","EIP及其它通信收发映像","通信驱动/PLC分向","接口层","否","建议","接收先校验再使用"],
  ["EQUIP","D5000","D9999","设备模块和扩展预留","各设备模块","HMI/顺控","否","预留","按设备分块"],
  ["RETAIN","D20000","D20999","配方、校准和需保持参数候选","参数管理","控制模块/HMI","项目确认","建议","不得放运行命令/状态"]
],20); widths(s.sh,[14,12,12,30,24,22,12,12,34]);
s.sh.getRange("G5:G20").dataValidation = { rule: { type: "list", values: ["否","是","项目确认"] } };
s.sh.getRange("H5:H20").dataValidation = { rule: { type: "list", values: ["建议","已确认","预留","停用"] } };

s = setup("物理IO","物理 I/O 点表","X/Y 仅用于映射层。常态、有效电平、安全失效状态必须按电气图与现场确认。",["IO_ID","物理地址","符号","DI/DO","模块/槽/通道","端子","信号类型","常态/有效电平","失效安全状态","滤波/去抖ms","设备/来源","唯一写入者","图纸号","状态","重复检查"],[
  ["DI-001","X0.0","PB_Start","DI","CPU/0/0","TB-X1","24VDC","常开/高有效","FALSE",20,"启动按钮","现场输入","E-001","示例",""],
  ["DI-002","X0.1","Rbt_Ready_DI","DI","CPU/0/1","TB-X2","24VDC","高有效","FALSE",20,"机器人","现场输入","E-010","示例",""],
  ["DO-001","Y0.0","Tower_Green","DO","CPU/0/0","TB-Y1","晶体管输出","高有效","OFF",0,"三色灯","IO_MAP","E-020","示例",""]
],44); widths(s.sh,[12,13,24,10,18,12,16,18,18,14,20,18,14,12,14]);
s.sh.getRange("D5:D44").dataValidation = { rule: { type: "list", values: ["DI","DO"] } };
s.sh.getRange("N5:N44").dataValidation = { rule: { type: "list", values: ["待定义","示例","已确认","停用"] } };
s.sh.getRange("O5").formulas = [["=IF(B5=\"\",\"\",IF(COUNTIF($B$5:$B$44,B5)>1,\"地址重复\",\"\"))"]]; s.sh.getRange("O5:O44").fillDown();
s.sh.getRange("B5:B44").conditionalFormats.add("duplicateValues",{format:{fill:red,font:{color:"#9C0006",bold:true}}});

s = setup("机器人接口","机器人接口表","PLC 视角定义方向。网络命令使用请求/确认或序号回显；禁止把单扫描脉冲作为可靠跨网络命令。",["接口ID","D地址","符号","方向(PLC视角)","EIP/离散IO","生产者","消费者","含义","更新/握手","超时ms","失效值","数据类型","保持","状态","重复检查"],[
  ["RBT-CMD-00","D2000.0","Rbt_Enable","PLC→Robot","EIP或DO","PLC_ROBOT","Robot","机器人接口使能","电平保持",500,"FALSE","BOOL","否","示例",""],
  ["RBT-CMD-01","D2000.1","Rbt_StartReq","PLC→Robot","EIP或DO","PLC_ROBOT","Robot","启动请求","保持至StartAck",500,"FALSE","BOOL","否","示例",""],
  ["RBT-CMD-02","D2000.2","Rbt_ResetReq","PLC→Robot","EIP或DO","PLC_ROBOT","Robot","复位请求","保持至ResetAck",1000,"FALSE","BOOL","否","示例",""],
  ["RBT-STS-00","D2010.0","Rbt_Online","Robot→PLC","EIP或DI","Robot","PLC_ROBOT","通信在线","周期状态",500,"FALSE","BOOL","否","示例",""],
  ["RBT-STS-01","D2010.1","Rbt_Ready","Robot→PLC","EIP或DI","Robot","PLC_ROBOT","机器人就绪","周期状态",500,"FALSE","BOOL","否","示例",""],
  ["RBT-STS-02","D2010.2","Rbt_StartAck","Robot→PLC","EIP或DI","Robot","PLC_ROBOT","启动确认","请求确认",500,"FALSE","BOOL","否","示例",""],
  ["RBT-STS-03","D2010.3","Rbt_Busy","Robot→PLC","EIP或DI","Robot","PLC_ROBOT","程序执行中","周期状态",500,"FALSE","BOOL","否","示例",""],
  ["RBT-STS-04","D2010.4","Rbt_Complete","Robot→PLC","EIP或DI","Robot","PLC_ROBOT","循环完成","确认保持",500,"FALSE","BOOL","否","示例",""],
  ["RBT-STS-05","D2010.5","Rbt_Alarm","Robot→PLC","EIP或DI","Robot","PLC_ROBOT","机器人报警","周期状态",500,"TRUE","BOOL","否","示例",""],
  ["RBT-DATA-01","D2020","Rbt_ProgramNo","PLC→Robot","EIP","PLC_ROBOT","Robot","程序号","CmdSeq更新前锁定",500,"0","UINT16","否","示例",""],
  ["RBT-DATA-02","D2021","Rbt_CmdSeq","PLC→Robot","EIP","PLC_ROBOT","Robot","命令序号","每条新命令+1",500,"保持上次","UINT16","否","示例",""],
  ["RBT-DATA-03","D2031","Rbt_CmdSeqEcho","Robot→PLC","EIP","Robot","PLC_ROBOT","命令序号回显","处理后回显",500,"不匹配","UINT16","否","示例",""]
],48); widths(s.sh,[15,14,24,18,14,18,18,26,20,12,15,14,10,12,14]);
s.sh.getRange("D5:D48").dataValidation = { rule: { type: "list", values: ["PLC→Robot","Robot→PLC"] } };
s.sh.getRange("M5:M48").dataValidation = { rule: { type: "list", values: ["否","是"] } };
s.sh.getRange("N5:N48").dataValidation = { rule: { type: "list", values: ["待定义","示例","已确认","停用"] } };
s.sh.getRange("O5").formulas = [["=IF(B5=\"\",\"\",IF(COUNTIF($B$5:$B$48,B5)>1,\"地址重复\",\"\"))"]]; s.sh.getRange("O5:O48").fillDown();
s.sh.getRange("B5:B48").conditionalFormats.add("duplicateValues",{format:{fill:red,font:{color:"#9C0006",bold:true}}});

s = setup("轴_CANopen","轴与 CANopen 接口","CANopen 使用 CiA 301；只有设备 EDS/手册确认支持 CiA 402 时才采用标准驱动对象。脉冲轴对象索引列填 N/A。",["轴/节点","D地址","符号","方式","方向","对象Index","PDO/SDO","类型","字序/符号","比例","单位","更新/超时","生产者","消费者","失效处理","状态"],[
  ["Axis01/Node1","D3000.0","Ax1_EnableReq","CANopen CiA402","PLC→Drive","6040h bit","RPDO","BOOL","bit","1","-","10ms/300ms","AXIS_MGR","Drive","撤销使能请求","示例"],
  ["Axis01/Node1","D3010.0","Ax1_Ready","CANopen CiA402","Drive→PLC","6041h bit","TPDO","BOOL","bit","1","-","10ms/300ms","Drive","AXIS_MGR","FALSE并报警","示例"],
  ["Axis01/Node1","D3020:D3021","Ax1_TargetPos","CANopen CiA402","PLC→Drive","607Ah","RPDO","INT32","低字在前/有符号","0.001","mm","命令时/300ms","AXIS_MGR","Drive","禁止新启动","示例"],
  ["Axis01/Node1","D3030:D3031","Ax1_ActualPos","CANopen CiA402","Drive→PLC","6064h","TPDO","INT32","低字在前/有符号","0.001","mm","10ms/300ms","Drive","AXIS_MGR/HMI","质量无效","示例"],
  ["Axis02","D3100.0","Ax2_JogPosReq","脉冲+方向","HMI→PLC","N/A","N/A","BOOL","bit","1","-","保持/立即停止","HMI","AXIS_MGR","松开或断线即停","示例"],
  ["Axis02","D3110.0","Ax2_InPosition","脉冲+方向","Drive→PLC","N/A","DI","BOOL","bit","1","-","周期/100ms","Drive DI","AXIS_MGR","FALSE并禁止完成","示例"]
],44); widths(s.sh,[16,16,24,18,16,15,12,12,18,10,10,18,18,18,24,12]);
s.sh.getRange("D5:D44").dataValidation = { rule: { type: "list", values: ["CANopen CiA301","CANopen CiA402","脉冲+方向","脉冲串"] } };
s.sh.getRange("P5:P44").dataValidation = { rule: { type: "list", values: ["待定义","示例","已确认","停用"] } };
s.sh.getRange("B5:B44").conditionalFormats.add("duplicateValues",{format:{fill:red,font:{color:"#9C0006",bold:true}}});

s = setup("报警地址","报警地址与逻辑","Active=当前条件；Latched=事件记忆；Ack=人员确认；ResetReq=复位请求。四者不得共用同一位。",["报警ID","设备/区域","Active地址","Latched地址","Ack地址","级别","触发条件","延时ms","复位条件","联锁/响应","唯一写入者","HMI主文本","状态","重复检查"],[
  ["ALM-RBT-001","机器人1","D1000.0","D1100.0","D1200.0","2-停机","Rbt_Online=FALSE",500,"通信恢复且复位请求","停止发新命令","ALARM_MGR","机器人1：通信超时","示例",""],
  ["ALM-RBT-002","机器人1","D1000.1","D1100.1","D1200.1","2-停机","Rbt_Alarm=TRUE",100,"机器人报警清除且复位请求","终止当前循环","ALARM_MGR","机器人1：控制器报警","示例",""],
  ["ALM-AX1-001","1号轴","D1001.0","D1101.0","D1201.0","2-停机","Ax1_DriveAlarm=TRUE",50,"驱动报警清除且复位请求","轴停止/禁止启动","ALARM_MGR","1号轴：伺服报警","示例",""],
  ["ALM-AX1-002","1号轴","D1001.1","D1101.1","D1201.1","3-暂停","回零超过设定时间",0,"条件消失且复位请求","暂停顺控","ALARM_MGR","1号轴：回原点超时","示例",""],
  ["ALM-SYS-001","整机","D1002.0","D1102.0","D1202.0","1-安全链监视","安全链状态断开",0,"安全系统恢复且复位请求","普通PLC停止请求","ALARM_MGR","整机：安全链未就绪","示例",""]
],44); widths(s.sh,[16,16,15,15,14,16,28,12,28,24,18,28,12,14]);
s.sh.getRange("F5:F44").dataValidation = { rule: { type: "list", values: ["1-安全链监视","2-停机","3-暂停","4-提示"] } };
s.sh.getRange("M5:M44").dataValidation = { rule: { type: "list", values: ["待定义","示例","已确认","停用"] } };
s.sh.getRange("N5").formulas = [["=IF(C5=\"\",\"\",IF(COUNTIF($C$5:$C$44,C5)>1,\"Active重复\",\"\"))"]]; s.sh.getRange("N5:N44").fillDown();
s.sh.getRange("C5:E44").conditionalFormats.add("duplicateValues",{format:{fill:red,font:{color:"#9C0006",bold:true}}});

s = setup("报警语言","标准报警语言","主文本采用“区域/设备：客观异常状态”。操作指引独立成列，禁止用模糊、责备或只写寄存器号的语言。",["类别","推荐主文本模板","推荐示例","避免使用","操作指引模板","维护信息示例","级别建议","备注"],[
  ["通信","{设备}：通信超时","机器人1：通信超时","通讯故障/连接有问题","确认设备上电与网络连接；恢复后按复位","超时500 ms，连接质量位=FALSE","2-停机","指明设备和超时"],
  ["设备报警","{设备}：控制器报警","机器人1：控制器报警","机器人坏了","查看设备报警代码；排除原因后按复位","外部报警码见诊断页","2-停机","外部代码另列"],
  ["运动","{轴}：回原点超时","1号轴：回原点超时","回零失败","确认运动区域安全；检查原点/限位信号和机械阻挡","超时30 s，当前步骤=HOME_SEARCH","2或3","说明动作与状态"],
  ["限位","{轴}：正限位已触发","1号轴：正限位已触发","限位异常","停止正向操作；确认安全后仅允许反向退出","DI=X0.4，触发位置=…","2-停机","不写“请检查限位”"],
  ["反馈","{设备}：启动反馈超时","输送机1：启动反馈超时","电机没转","确认急停/门锁状态；检查接触器与运行反馈","启动命令后2 s无反馈","2-停机","区分命令和反馈"],
  ["互锁","{设备}：启动条件不满足","机器人1：启动条件不满足","不能启动","查看未满足条件列表，条件恢复后重新启动","缺失：自动模式/安全链/工件到位","3-暂停","最好配合原因列表"],
  ["物料","{工位}：物料未到位","上料位：物料未到位","缺料","补充物料并确认传感器状态","等待10 s，传感器=OFF","3-暂停","避免误判为传感器坏"],
  ["气压","{区域}：气压低","整机：气压低","气源故障","确认供气阀开启且压力达到设定值","当前0.42 MPa，下限0.50 MPa","2或3","显示当前值与阈值"],
  ["参数","{参数}：超出允许范围","轴1速度：超出允许范围","参数错误","输入允许范围内数值后重新确认","当前1200，允许0～1000 mm/s","4-提示","显示值、范围和单位"],
  ["安全状态监视","{区域}：安全链未就绪","整机：安全链未就绪","安全故障","按现场安全程序确认急停、门锁和安全控制器状态","普通PLC仅显示安全状态","1-安全链监视","不宣称普通PLC执行安全功能"]
],24); widths(s.sh,[18,28,30,24,48,38,18,34]);

s = setup("HMI手动","HMI 手动交互地址","HMI 写入的是请求，不是物理输出。点动必须定义按住、松开、画面退出和通信中断行为。",["功能ID","请求地址","反馈地址","符号","控件类型","允许模式","权限","PLC互锁","确认/反馈","超时/释放行为","生产者","消费者","保持","状态","重复检查"],[
  ["MAN-AX2-JP","D500.0","D510.0","Ax2_JogPosReq","按住点动","手动/维护","操作员","安全链就绪;无报警;未到正限位","Ax2_Jogging","松开/掉线立即停止","HMI","AXIS_MGR","否","示例",""],
  ["MAN-AX2-JN","D500.1","D510.1","Ax2_JogNegReq","按住点动","手动/维护","操作员","安全链就绪;无报警;未到负限位","Ax2_Jogging","松开/掉线立即停止","HMI","AXIS_MGR","否","示例",""],
  ["MAN-RBT-RST","D501.0","D511.0","Rbt_ResetReq_HMI","瞬时按钮","手动/自动","工程师","机器人在线;报警存在","Rbt_ResetAck","PLC边沿捕获;2s超时","HMI","PLC_ROBOT","否","示例",""],
  ["MAN-ALM-ACK","D502.0","D512.0","Alarm_AckAllReq","瞬时按钮","任意","操作员","无","Alarm_AckDone","PLC边沿捕获","HMI","ALARM_MGR","否","示例",""]
],44); widths(s.sh,[16,15,15,24,18,16,14,32,20,28,16,18,10,12,14]);
s.sh.getRange("M5:M44").dataValidation = { rule: { type: "list", values: ["否","是"] } };
s.sh.getRange("N5:N44").dataValidation = { rule: { type: "list", values: ["待定义","示例","已确认","停用"] } };
s.sh.getRange("O5").formulas = [["=IF(B5=\"\",\"\",IF(COUNTIF($B$5:$B$44,B5)>1,\"请求地址重复\",\"\"))"]]; s.sh.getRange("O5:O44").fillDown();
s.sh.getRange("B5:B44").conditionalFormats.add("duplicateValues",{format:{fill:red,font:{color:"#9C0006",bold:true}}});

s = setup("通信数据","通信数据与 EIP Assembly","收发区分开；接收数据在在线、超时、范围、序号检查通过后才能进入控制逻辑。",["接口ID","协议","连接/节点","方向(PLC视角)","本地D地址","外部地址/对象","长度word","类型","字节/字序","比例/单位","周期/RPI","超时","质量/在线位","失效值","生产者","消费者","状态"],[
  ["EIP-RBT-CMD","EtherNet/IP","Robot1 Conn1","PLC→Robot","D2000:D2029","Output Assembly待定",30,"UINT16[]","按机器人手册","混合","20ms",500,"D2040.0","清命令位","PLC_ROBOT","Robot","示例"],
  ["EIP-RBT-STS","EtherNet/IP","Robot1 Conn1","Robot→PLC","D2030:D2059","Input Assembly待定",30,"UINT16[]","按机器人手册","混合","20ms",500,"D2040.0","状态无效","Robot","PLC_ROBOT","示例"],
  ["CO-AX1-PDO","CANopen","Node1","Drive→PLC","D3030:D3039","TPDO映射见EDS",10,"MIXED","低字在前待确认","混合","10ms",300,"D3040.0","轴状态无效","Drive","AXIS_MGR","示例"]
],44); widths(s.sh,[16,16,18,18,18,24,12,14,18,16,14,12,16,18,18,18,12]);
s.sh.getRange("B5:B44").dataValidation = { rule: { type: "list", values: ["EtherNet/IP","CANopen","离散I/O","Modbus TCP","Socket"] } };
s.sh.getRange("D5:D44").dataValidation = { rule: { type: "list", values: ["PLC→外部","外部→PLC","PLC→Robot","Robot→PLC","Drive→PLC","PLC→Drive"] } };
s.sh.getRange("Q5:Q44").dataValidation = { rule: { type: "list", values: ["待定义","示例","已确认","停用"] } };

const dict = setup("字典","字段字典与审核清单","统一方向、状态和失效定义；审核通过后再复制到正式项目。",["主题","允许值/规则","审核问题","结论"],[
  ["地址所有权","每个地址一个生产者/写入者","是否存在 HMI、通信、POU 同写一个地址？","待审核"],
  ["D字位","D列.0～D列.15；位字不得被其他逻辑整字写入","是否检查了 MOV/通信表/配方整字覆盖？","待审核"],
  ["方向","统一按 PLC 视角","PLC→外部与外部→PLC 是否分区？","待审核"],
  ["保持","运行命令/状态默认不保持","是否有命令因断电保持导致自动恢复？","待审核"],
  ["机器人握手","请求保持至确认，或命令序号+回显","是否测试丢包、重复包、掉线和重连？","待审核"],
  ["CANopen","CiA301；CiA402仅限设备支持","EDS、PDO、Heartbeat、EMCY 是否记录？","待审核"],
  ["HMI手动","请求经 PLC 模式/权限/互锁校验","是否存在 HMI 直写 Y 或轴控制字？","待审核"],
  ["报警语言","设备：客观异常；操作指引另列","是否有模糊措辞、责备用语或只有寄存器号？","待审核"],
  ["安全边界","安全状态仅监视，不替代安全功能","是否错误地把普通 PLC 报警当安全回路？","待审核"]
],20); widths(dict.sh,[22,46,50,16]); dict.sh.getRange("D5:D20").dataValidation = { rule: { type: "list", values: ["待审核","通过","需修改","不适用"] } };

for (const name of ["审核说明","地址分区","物理IO","机器人接口","轴_CANopen","报警地址","报警语言","HMI手动","通信数据","字典"]) {
  const sh = wb.worksheets.getItem(name);
  const used = sh.getUsedRange();
  used.format.autofitRows();
}

await fs.mkdir(outputDir, { recursive: true });
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(`${outputDir}/AS228T_标准IO表_送审版_v0.1.xlsx`);
for (const name of ["审核说明","地址分区","物理IO","机器人接口","轴_CANopen","报警地址","报警语言","HMI手动","通信数据","字典"]) {
  const png = await wb.render({ sheetName: name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(`${outputDir}/${name}.png`, new Uint8Array(await png.arrayBuffer()));
}
const check = await wb.inspect({ kind: "sheet,formula", maxChars: 5000, tableMaxRows: 8, tableMaxCols: 8 });
console.log(check.ndjson ?? check);
