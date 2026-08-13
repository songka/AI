# CDHD2 EtherCAT 与 CANopen 参考手册

CDHD2 伺服驱动器  
修订版：1.0  
固件版本：2.15.x

> 译稿状态：当前已完成封面、版权页、第 1-8 章中文翻译；第 9-11 章为对象字典，已另行生成对象索引，详细条目可继续按对象号追加。  
> 源文件：`CDHD2_ECT_CAN_fw2.15.x_Rev.1.0.pdf`  
> 英文提取稿：`CDHD2_ECT_CAN_fw2.15.x_Rev.1.0_extracted_en.md`

## 修订历史

| 文档修订版 | 日期 | 备注 |
|---|---|---|
| 1.0 | 2017 年 12 月 | CDHD2 - 正式发布。固件 2.15.x |

## 版权声明

Copyright 2017 Servotronix Motion Control Ltd. 保留所有权利。未经 Servotronix 事先书面许可，不得以任何形式或通过任何方式复制或传播本作品的任何部分。

## 免责声明

本产品文档在发布时准确且可靠。Servotronix Motion Control Ltd. 保留在任何时间不经通知而更改本手册所述产品规格的权利。

## 商标

ServoStudio 和 sensAR 是 Servotronix Motion Control Ltd. 的商标。  
CANopen 和 CiA 是 CAN in Automation User's Group 的注册商标。  
EtherCAT 是 Beckhoff Automation GmbH 的注册商标。  
EnDat 是 Dr. Johannes Heidenhain GmbH 的注册商标。  
HIPERFACE 是 Sick Stegmann GmbH 的注册商标。  
BiSS-C 是 iC-Haus GmbH 的注册商标。  
Windows 是 Microsoft Corporation 的注册商标。

## 联系信息

Servotronix Motion Control Ltd.  
21C Yagia Kapayim Street  
Petach Tikva 49130, Israel  
电话：+972 (3) 927 3800  
传真：+972 (3) 922 8075  
网站：www.servotronix.com

## 技术支持

如果在产品安装和配置方面需要帮助，请联系 Servotronix 技术支持：tech.support@servotronix.com

## 术语表

| 英文术语 | 中文译法 |
|---|---|
| drive | 驱动器 |
| servo drive | 伺服驱动器 |
| fieldbus | 现场总线 |
| object dictionary | 对象字典 |
| node address | 节点地址 |
| termination resistor | 终端电阻 |
| command interface mode | 命令接口模式 |
| host controller | 主站控制器 |
| PLC controller | PLC 控制器 |
| operational state | Operational (OP) 状态 |
| pre-operational state | Pre-Operational (PREOP) 状态 |
| safe-operation state | Safe-Operation (SAFEOP) 状态 |
| initial state | Initial (INIT) 状态 |
| cyclic synchronous | 循环同步 |
| interpolation time | 插补时间 |
| PDO mapping | PDO 映射 |
| read/write access | 读/写访问 |
| read only | 只读 |

## 目录

1. 引言  
   1.1 关于本手册  
   1.2 手册格式 - 对象字典  
2. 现场总线接线与设置  
   2.1 现场总线接线 - 示例  
   2.2 节点地址  
   2.3 终端电阻开关  
   2.4 命令接口模式  
   2.5 CAN 总线位速率  
   2.6 插补时间（循环同步）  
3. 为 CDHD2 EtherCAT 配置 softMC 控制器  
4. 为 CDHD2 EtherCAT 配置 Beckhoff 控制器  
5. 为 CDHD2 CANopen 配置 Horner 控制器  
6. 为 CDHD2 EtherCAT 配置 Keba 控制器  
7. CANopen 操作  
8. 单位  
9. 通信段  
10. 制造商特定对象  
11. 标准伺服驱动器对象  

# 1 引言

## 1.1 关于本手册

驱动器功能通过各种命令和变量进行配置，这些命令和变量可通过串口或现场总线进行通信。

本手册说明 CDHD2 伺服驱动器中 CANopen 以及 EtherCAT 上 CANopen（CANopen over EtherCAT, CoE）通信的实现。

本手册无意替代 CANopen 规范，也不用于复述 CANopen 规范的全部内容。

本手册适用于已接受培训、能够操作本文档所述设备的熟练人员。

## 1.2 手册格式 - 对象字典

CAN 对象按以下格式呈现和说明：

### `nnnnh - 对象名称`

对象说明

| 字段 | 说明 |
|---|---|
| Index | `nnnn` |
| Description | VarCom 等效项（如适用）以及对象说明 |
| Object Code | `Variable` / `Array` / `Record` |
| Data Type | `INTEGER8` / `INTEGER16` / `INTEGER32` / `UNSIGNED8` / `UNSIGNED16` / `UNSIGNED32` / `REAL32` / `VISIBLE_STRING` |

### Variable 与 Record 对象的条目说明

| 字段 | 说明 |
|---|---|
| Access: Read/Write | 读写访问 |
| Access: Read Only | 只读 |
| Access: Constant | 只读访问，值为常量 |
| PDO Mapping | `Yes` / `No` |
| Default Value | 对象默认值 |
| Lower Limit | 对象最小值 |
| Upper Limit | 对象最大值 |
| Units | 当对象值具有计量单位含义时，在此指定单位 |

### Array 对象的条目说明

| 字段 | 说明 |
|---|---|
| Sub-Index | `nnn` |
| Description | 子索引说明 |
| Entry Category | `Optional` / `Mandatory` |
| Data Type | `Integer8` / `Integer16` / `Integer32` / `Unsigned8` / `Unsigned16` / `Unsigned32` / `Real32` / `Visible_String` |
| Access: Read/Write | 读写访问 |
| Access: Read Only | 只读 |
| Access: Constant | 只读访问，值为常量 |
| PDO Mapping | `Yes` / `No` |
| Default Value | 对象默认值 |
| Lower Limit | 对象最小值 |
| Upper Limit | 对象最大值 |
| Unit | 当对象值具有计量单位含义时，在此指定单位 |

# 2 现场总线接线与设置

## 2.1 现场总线接线 - 示例

### 2.1.1 CDHD2 - EtherCAT 配置 - softMC 7 控制器 - 示例

图 2-1：CDHD2 - EtherCAT 配置 - softMC 7 控制器 - 示例。

### 2.1.2 CDHD2 - EtherCAT 配置 - Beckhoff 控制器 - 示例

图 2-2：CDHD2 - EtherCAT 配置 - Beckhoff 控制器 - 示例。

图中包含：CDHD2 驱动器、EtherCAT、Beckhoff Ethernet 模块、Beckhoff PLC 或嵌入式 PC。

### 2.1.3 CDHD2 - CAN 配置 - softMC 7 控制器 - 示例

图 2-3：CDHD2 - CAN 配置 - softMC 7 控制器 - 示例。

### 2.1.4 CDHD2 - CAN 配置 - Beckhoff 控制器 - 示例

图 2-4：CDHD2 - CAN 配置 - Beckhoff 控制器 - 示例。

图中包含：CDHD2 驱动器、CAN、Beckhoff CAN 总线模块、Beckhoff PLC 或嵌入式 PC，以及 120 欧姆终端电阻。

## 2.2 节点地址

### 2.2.1 CANopen 网络中的节点地址

在 CANopen 网络中，必须为每个独立的 CANopen 设备分配唯一的节点地址（识别号）。

如果只有一台驱动器连接到主机计算机，则驱动器地址默认为 0，无需另行定义。

如果有两台或更多驱动器连接到网络，则不能使用地址 0。只有单台驱动器可以使用地址 0。

同一 CANopen 网络中的两台驱动器不能使用相同地址。

如果驱动器前面板带有旋转地址开关，请使用该开关设置驱动器通信地址。

如果驱动器没有旋转地址开关，请使用操作面板参数 `P000` 设置驱动器地址。也可以使用 VarCom 变量 `ADDR`。随后输入 `SAVE`，并对驱动器重新上电。

注意：新地址只有在执行 `SAVE` 并对驱动器重新上电后才会生效。

### 2.2.2 EtherCAT 网络中的节点地址

在 EtherCAT 网络中，不需要为设备专门分配物理节点地址（识别号）；EtherCAT 控制器会分配地址。

连接在 EtherCAT 网络中的两台或更多驱动器可以设置为相同物理地址；EtherCAT 控制器会自动设置从站 ID。

## 2.3 终端电阻开关

### 2.3.1 CANopen 网络中的终端电阻开关

CDHD2 的终端电阻开关位于驱动器顶部，靠近菊花链连接器（C8）。

图 2-5：接口 C8 上的终端电阻开关（T）。

使用小型螺丝刀或类似工具，将开关设到正确位置：

- 朝向 `T`（默认）：不使用 120 欧姆终端电阻。
- 远离 `T`：当该驱动器是链路中的最后一台驱动器时使用。此时驱动器在 CAN high 与 CAN low 之间提供 120 欧姆终端电阻。

注意：链路起点也需要 120 欧姆终端电阻，位置可在 CAN 总线模块上，或在 D9 到 RJ45 转接器上。

### 2.3.2 EtherCAT 网络中的终端电阻开关

EtherCAT 驱动器不需要终端电阻开关。

## 2.4 命令接口模式

某些参数（例如命令接口模式）在驱动器固件中由工厂定义，只能通过 ServoStudio 软件修改。请注意，ServoStudio 需要主机计算机与驱动器之间建立串行连接（USB 或 RS232）。

驱动器出厂配置为现场总线（CANopen/Ethernet）命令接口，该接口由驱动器参数 `COMMODE=1` 定义。

如有必要，可通过 ServoStudio Terminal 画面启用 CANopen/EtherCAT 命令接口模式。输入命令 `COMMODE 1`，然后执行串行命令 `SAVE`。

也可以在 ServoStudio Drive Information 画面中选择 Interface Mode。

| 模式 | 说明 | 参数 |
|---|---|---|
| EtherCAT/CANopen | `SERVO ON (ACTIVE)` 和运动命令通过 EtherCAT/CANopen 接口传输。不适用于 CDHD2 AP 型号。 | `COMMODE 1` |
| Serial/Pulse/Analog | `SERVO ON (ACTIVE)` 和运动命令通过串行、脉冲或模拟接口传输。 | `COMMODE 0` |

### 2.4.1 CANopen 网络中的通信

使用 CANopen 通信时，请确保所需的 EDS 文件已安装在 PLC 控制器或主机计算机中。可从 Servotronix 网站下载该文件，或联系技术支持获取。

使用任意 RJ45 电缆：

- 将主机连接到驱动器接口 C5。
- 将下一个节点连接到接口 C6。

在 CANopen 网络通信时，AF 型号上的接口 C5 与 C6 共用一个 LED，用于指示现场总线状态。

图 2-6：CANopen 型号顶部面板接口与 LED。

| 指示 | 状态说明 |
|---|---|
| 绿色常亮 | Operational (OP) 状态 |
| 绿色快速闪烁 | Pre-Operational (PREOP) 状态 |
| 绿色慢速闪烁 | Stopped 状态 |
| 红色闪烁 | 错误 |
| 不亮 | 驱动器未设置为 EtherCAT/CANopen 命令接口模式。参见“命令接口模式”。 |

### 2.4.2 EtherCAT 网络中的通信

使用 EtherCAT 通信时，请确保所需的 XML 文件已安装在 PLC 控制器或主机计算机中。可从 Servotronix 网站下载该文件，或联系技术支持获取。

使用任意 RJ45 电缆：

- 将主机连接到驱动器接口 C5。
- 将下一个节点连接到接口 C6。

连接器 C5 与 C6 分别作为发送端（Tx）和接收端（Rx）。

在 EtherCAT 网络通信时，EB 与 EC 型号上的接口 C5 和 C6 各有两个 LED，用于指示现场总线状态。

图 2-7：接口 C5 与 C6 上的 LED。

| 指示 | 状态说明 |
|---|---|
| 绿色闪烁 | 有通信活动 |
| 绿色不亮 | 无通信活动 |
| 橙色常亮 | Operational (OP) 状态 |
| 橙色慢速闪烁 | Safe-Operation (SAFEOP) 状态 |
| 橙色快速闪烁 | Pre-Operational (PREOP) 状态 |
| 橙色非常快速闪烁 | Bootstrap (BOOT) 状态 |
| 橙色不亮 | Initial (INIT) 状态 |

## 2.5 CAN 总线位速率

驱动器出厂配置的通信总线速率为 500 kbps，该值由驱动器参数 `CANBITRATE=3` 定义。

如有必要，可通过 ServoStudio Terminal 画面手动设置 `CANBITRATE` 的值。设置 `CANBITRATE` 后，必须执行串行命令 `SAVE`，然后对驱动器重新上电。

`CANBITRATE` 可设置为以下值之一：

- `1`：125 kbps
- `2`：250 kbps
- `3`：500 kbps（默认）
- `4`：1000 kbps（1 Mbit）

## 2.6 插补时间（循环同步）

驱动器参数 `FBITPRD` 和 `FBITIDX` 分别定义插补时间周期和时间指数，用于在循环同步工作模式下计算现场总线循环同步时间。

以下公式定义这些参数之间的关系：

```text
FBITPRD x 10^FBITIDX = 现场总线循环同步时间（秒）
```

可以通过对象 `60C2h` 的子索引 1 和 2 设置这些参数。

在 `INIT` 状态期间，主站控制器必须将这些索引值设置为与控制器等效的循环时间。

如有必要，可通过 ServoStudio Terminal 画面手动设置 `FBITPRD` 和 `FBITIDX` 的值。设置 `FBITPRD` 和 `FBITIDX` 后，必须执行串行命令 `SAVE`。

# 3 为 CDHD2 EtherCAT 配置 softMC 控制器

关于如何配置 softMC 控制器以配合 CDHD2 使用的信息，可参见 softMC 文档 wiki。

应按以下顺序访问并阅读文章：

1. `http://softmc.servotronix.com/wiki/Category:EtherCAT:EC_SETUP`
2. `http://softmc.servotronix.com/wiki/EtherCAT:EC_INSTALL_STX_CDHD`

登录 softMC wiki：

- 用户名：`softMC`
- 密码：`documentation`

如需安装和配置方面的其他帮助，请联系 Servotronix 技术支持。

# 4 为 CDHD2 EtherCAT 配置 Beckhoff 控制器

本章说明如何配置 Beckhoff 控制器，使其能够与 CDHD2 EC 型号进行通信和运行。

应用系统由以下部分组成：

- CDHD2 EC Ethernet 伺服驱动器、伺服电机和 ServoStudio 软件。
- 带 EtherCAT 通信模块的 Beckhoff 控制器，以及 TwinCAT 软件。

## 4.1 CDHD2 硬件与软件设置

请参见“现场总线接线与设置”章节。

确保所有硬件设置均符合以下小节的说明：

- 现场总线接线
- 节点地址
- 终端电阻开关
- 命令接口模式
- CAN 总线位速率
- 插补时间

在激活 TwinCAT System Manager 之前，请确保正确的 `*.xml` 文件（与固件版本对应）位于 `C:\TwinCAT\Io\EtherCAT`。

## 4.2 控制器与 PC 之间的通信

使用 TwinCAT 软件，通过以下步骤建立控制器与 PC 之间的通信。

注意：

- Beckhoff 控制器指 TwinCAT NC PTP（点到点轴定位软件）。
- TwinCAT NC PTP 包含轴定位软件（设定值生成、位置控制）、带 NC 接口的集成软件 PLC、用于调试的操作程序，以及通过各种现场总线连接到轴的 I/O。TwinCAT NC PTP 可替代传统定位模块和 NC 控制器。由 PC 模拟的控制器会通过现场总线与驱动器和测量系统周期性交换数据。
- Beckhoff 控制器按照 IEC 61131-3 编程标准进行编程。

操作步骤：

1. 启动 TwinCAT 软件。
2. 在导航窗格中选择 `SYSTEM - Configuration`。然后在 `Version (Local)` 选项卡中单击 `Choose Target`。  
   图 4-1。
3. 单击 `Search (Ethernet)`，在网络中搜索控制器。  
   图 4-2。
4. 启用 `IP Address` 选项，并单击 `Broadcast Search`。等待控制器名称出现，格式为 `CX-xxx`。  
   图 4-3。
5. 控制器出现后，会显示 `Add Route` 选项。单击 `Add Route`。
6. 在 `Logon` 对话框中输入：  
   User Name：`Administrator`  
   Password：`1`  
   然后单击 `OK`。  
   图 4-4。
7. 在 `Add Route` 对话框中，确认控制器名称旁边出现 `X`。这表示控制器已正确连接到 PC。关闭该对话框。  
   图 4-5。
8. 在 `Choose Target System` 对话框中单击控制器，然后单击 `OK`。  
   图 4-6。
9. 打开 TwinCAT System Manager，并确认其处于 `Config Mode`。  
   图 4-7。

## 4.3 控制器与驱动器之间的通信

使用 TwinCAT 软件，通过以下步骤建立控制器与驱动器之间的通信。

1. 在导航窗格中展开 `I/O-Configuration`，然后右键单击 `I/O Devices`。
2. 选择 `Scan Devices`。出现提示时，单击 `OK`。  
   图 4-8。
3. 扫描完成后，将显示检测到的设备。CDHD2 被识别为 `Device 1 (EtherCAT)`。  
   图 4-9。
4. 启用 `Device 1 (EtherCAT)` 选项，然后单击 `OK`。
5. 当提示是否扫描 boxes（从站）时，单击 `Yes`。  
   图 4-10。
6. 当提示是否将链接轴追加到 NC 配置时，单击 `Yes`。  
   图 4-11。
7. 当提示是否激活 FreeRun 时，单击 `No`。  
   图 4-12。
8. 此过程结束后，`Device 1 (EtherCAT)` 会显示在导航窗格中，并列出所有组件（TPDO 和 RPDO），同时自动链接到 `NC-Configuration > Axis 1`。  
   图 4-13。

## 4.4 产生运动

### 4.4.1 运动设置

1. 打开 TwinCAT System Manager，并确认其处于 `Config Mode`。  
   图 4-14。
2. 在导航窗格中展开 `SYSTEM-Configuration`，并选择 `Real Time Settings`。  
   在 `Settings` 选项卡中，选择 `Base Time = 1 ms`。  
   图 4-15。  
   在 `Priorities` 选项卡中，启用 `Automatic Priority Management`。  
   图 4-16。
3. 展开 `SYSTEM-Configuration`，并选择 `Real Time Settings > I/O Idle Task`。在 `Task` 选项卡中，选择 `Cycle ticks = 1 ms`。  
   图 4-17。
4. 在导航窗格中展开 `NC-Configuration`，并选择 `NC-Task1SAF`。在 `Task` 选项卡中，选择 `Cycle ticks = 1 ms`。  
   图 4-18。
5. 展开 `NCT-Task1SAF`，并选择 `NC-Task1SVB`。在 `Task` 选项卡中，选择 `Cycle ticks = 1 ms`。确认 `NC-Task1 SVB` 的优先级值高于 `NC-Task1 SAF` 的优先级值。  
   图 4-19。
6. 展开 `NC-Configuration > Axes > Axis 1 > Axis 1_Enc`。在 `Parameter` 选项卡中执行以下操作：  
   `Encoder Evaluation > Scaling Factor = 1`，然后单击 `Download`。  
   图 4-20。  
   `Encoder Evaluation > Modulo Factor = PNUM value`，然后单击 `Download`。  
   图 4-21。
7. 展开 `NC-Configuration > Axes > Axis 1 > Axis 1_Ctrl`。在 `Parameter` 选项卡中设置：  
   `Monitoring > Position Lag Monitoring = FALSE`。  
   图 4-22。
8. 展开 `IO-Configuration > I/O Devices > Device (EtherCAT)`，并选择由红色图标指示的驱动器。  
   在 `DC` 选项卡中，选择 `Operation Mode = DC-Synchronous`。  
   图 4-23。
9. 按工具栏中的 `Run Mode` 按钮。  
   图 4-24。  
   此时会出现额外的选项卡。
10. 转到 `CoE Online` 选项卡。  
    `CoE Online` 选项卡仅显示驱动器管理的 SDO 对象（CDHD2 EtherCAT 参数）。确认对象 `6060h` 和 `60C2h` 的值如下：  
    `Object 6060h = 8`。驱动器通过协议对象 `6060h` 设置为循环同步位置模式，即 `OPMODE 8`。  
    图 4-25。  
    `Object 60C2h`：子索引 01（`60C2:01`）= `1`；子索引 02（`60C2:02`）= `-3`。循环同步工作模式的插补时间通过对象 `60C2h`（子索引 01 和子索引 02）设置。  
    图 4-26。  
    注意：插补时间必须配置为与 `I/O Idle Task`、`NC-Task 1 SAF` 和 `NC-Task 1 SVB` 中配置的 cycle ticks 相同的值。
11. 现在通过按工具栏中的以下两个按钮激活 `Run Mode`：  
    `Generate Mappings`  
    `Check Configuration`  
    图 4-27。  
    在 Run 模式下，可以产生运动。NC PTP 与驱动器通信，并接收每个 PDO 对象中包含的所有变量值（这些对象已由控制器自动映射）。  
    图 4-28。
12. 在 `NC-Online` 选项卡中测试与驱动器的通信：握住电机轴并手动转动，检查位置反馈值是否变化。参见图 4-29 中显示的各项功能。

### 4.4.2 在循环同步位置模式下产生运动

以下步骤演示如何在循环同步位置模式下产生运动。在 `NC-Online` 选项卡中，将向驱动器发送目标位置和速度。控制器会执行运动曲线。

1. 使能驱动器：  
   a. `NC-Online Screen > Enabling > Set`  
   b. 启用 `Controller`、`Feed Fw` 和 `Feed Bw` 选项，或选择 `All`  
   c. 单击 `OK`  
   图 4-30。  
   注意：要禁用驱动器，请进入 `NC-Online Screen > Enabling`，清除 `Controller` 选项，然后单击 `OK`。
2. 使用运动按钮 `F1`、`F2`、`F3` 和 `F4` 产生以下运动曲线。按图 4-31 所示，在控制器中通过 `NC-Configuration > NC-Task1 SAF > Axes > Axis1 > Parameters > Manual Velocity (Slow and Fast)` 配置速度。
   - `F1`：以快速速度发送负方向（逆时针，CCW）的点动命令。
   - `F2`：以慢速速度发送负方向（逆时针，CCW）的点动命令。
   - `F3`：以慢速速度发送正方向（顺时针，CW）的点动命令。
   - `F4`：以快速速度发送正方向（顺时针，CW）的点动命令。
3. 按图 4-32 所示设置 `Target Position` 和 `Target Velocity` 的值。
4. 按 `F5`（绿色按钮）在同步位置模式下启动运动曲线。  
   按 `F6`（红色按钮）停止运动。  
   按 `F8`（蓝色按钮）清除任何故障。  
   图 4-33 中的曲线反映所执行的运动：
   - 棕色线 = 位置反馈 - `PFB`
   - 绿色线 = 点到点发生器速度命令 - `PTPVCMD`
   - 蓝色线 = 位置误差 - `PE`
   - X 轴 = 毫秒，Y 轴 = 计数

### 4.4.3 产生绝对运动和相对运动

要在 Position Profile 模式下产生绝对或相对运动，请参见图 4-34 和图 4-35，并执行以下操作：

1. 转到 `Functions` 选项卡。
2. 配置运动的目标位置、目标速度、加速度、减速度和加加速度（jerk）。

### 4.4.4 产生阶跃运动

要在 Velocity profile 中产生阶跃序列，请参见图 4-36 和图 4-37，并执行以下操作：

1. 转到 `Functions` 选项卡。
2. 配置目标速度，以及该阶跃的时间（持续时间）。

图 4-37 中的曲线反映所执行的运动：

- 棕色线 = 位置反馈 - `PFB`
- 深绿色线 = 点到点发生器速度命令 - `PTPVCMD`
- 浅绿色线 = 速度 - `V`
- X 轴 = 毫秒，Y 轴 = 计数

# 5 为 CDHD2 CANopen 配置 Horner 控制器

本章说明如何配置 CDHD2 CAN 伺服驱动器，使其能够在 CAN 网络上与 Horner 控制器进行通信和运行。

应用系统由以下部分组成：

- CDHD2 CAN 伺服驱动器、伺服电机和 ServoStudio 软件。
- 带 CAN 通信端口的 Horner 控制器，以及 Horner Cscape 软件。

## 5.1 CDHD2 硬件与软件设置

请参见“现场总线接线与设置”章节。

确保所有硬件设置均符合以下小节的说明：

- 现场总线接线
- 节点地址
- 终端电阻开关
- 命令接口模式
- CAN 总线位速率
- 插补时间

确保正确的 `*.eds` 文件已安装在控制器中。

## 5.2 控制器与 PC 之间的通信

1. 启动 Cscape。  
   当 Cscape 软件启动后，必须建立控制器与 PC 之间的通信。
2. 使用 `Connection Wizard` 定义通信方式。  
   注意：Horner 控制器具有一个 CAN 端口，可用于 CsCAN 或 CANopen 模式。CsCAN 是 Horner 开发的标准，可为其他单元或 SCADA 系统提供网络，并为编程、监控和故障排除提供一个网络连接点。CANopen 是业界认可的标准，可支持与第三方设备（例如驱动器和 I/O 模块）的连接。  
   Horner Cscape 可编程逻辑控制器软件结合了逻辑、消息和网络功能。它支持图形化梯形图编程（基于 IEC-1131），并支持操作界面开发。  
   本配置说明假设 Horner 控制器和 CDHD2 CAN 驱动器正在按照 CANopen 协议运行并通信。  
   选择 `Serial`。  
   图 5-1：Cscape Connection Wizard。
3. 单击 `New File` 按钮，开始新的应用程序。  
   图 5-2：New File 按钮。
4. 选择用于开发应用程序的编辑器类型。选择 `Advanced Ladder Editor`。  
   图 5-3：Editor Type 选项。

## 5.3 控制器与驱动器之间的通信

1. 启动 CANopen Network Configurator：  
   在 `Project Navigator` 窗格中，选择 `Networking > Network Configuration`。等待 CANopen Network Configurator 启动。  
   图 5-4：Project Navigator。
2. 选择要为 CANopen 控制器创建的节点类型。由于控制器将作为主站，因此选择 `Add As Master`。  
   图 5-5：Node Selector。
3. 配置 CANopen 主站的通信设置。使用图 5-6 中显示的设置。
4. 配置 CANopen 从站（驱动器）的设置。使用图 5-7 中显示的设置。  
   注意：请确保 `Slave Node ID` 与 CDHD2 的物理地址一致。
5. 在 CANopen Configurator 画面中，选择 `CANopen Network > Master x > Special Function Objects`，并配置以下设置：
   - 启用 `Generate SYNC Message` 选项。
   - 设置对象 `1006h - Communication Cycle Period` 的值。对于本应用，将其设置为 `1000 us` 或 `1 ms`。
   - 设置对象 `1007h - Synchronous Window Length` 的值。对于本应用，将其设置为 `5000 us` 或 `5 ms`。
   图 5-8。
6. 重复步骤 5，为 `Slave x > Special Function Objects` 配置相同设置。

## 5.4 PDO 对象映射

在开始用 Cscape 编写应用程序之前，EDS 文件中的所有 PDO 对象都必须映射到控制器。

完成以下过程后，Cscape 会自动映射 PDO 对象。

1. 启动 Cscape。
2. 从菜单栏选择 `Program > Motion Configuration`。  
   图 5-9。
3. 在 `Network status register` 字段中输入 `%R0100`，然后按 `Add`。  
   图 5-10。
4. 配置第一个内部控制器存储寄存器，以完成 PDO 映射。  
   图 5-11。
5. 确保 `Network Baudrate` 设置为 `500 Kbps`。
6. 按 `Configure Drive` 按钮。EDS 文件中的所有 PDO 对象将通过 Horner-ServoStudio 应用桥导出到控制器。
7. 立即关闭 Horner-ServoStudio 应用桥。等待 Cscape 从驱动器接收 PDO 对象。
8. 该过程完成后，可按 `View Configured PDO` 按钮查看变量映射。  
   图 5-12。
9. PDO 映射过程完成后，即可开始开发应用程序。

注意：使用 Cscape 软件时，可通过相应的 CANopen 对象，使用 SDO Read/Write 功能块设置 CDHD2 参数 `PNUM`、`PDEN`、`FBGDS`、`FBGMS`、`FBITPRD` 和 `FBITIDX`。图 5-13 显示 ServoStudio 与 Cscape 中的参数设置。

# 6 为 CDHD2 EtherCAT 配置 Keba 控制器

要配置 Keba 运动控制器以配合 CDHD2 EtherCAT 驱动器使用，需要在 PC 上安装一组定制文件。

要获取这些文件，以及获得安装和配置帮助，请联系 Servotronix 技术支持。

- `CustomDrivesIO`  
  将所有文件解压到以下文件夹：  
  `C:\Kemro\KeStudioV2.3\Targets\KeMotion_CP24xCP25x_02.60\io\CustomDrives\Flexy2.0_EtherCatDrive`
- `McCustomDriveLibrary`  
  将该文件解压到库文件夹，并覆盖现有文件：  
  `C:\Kemro\KeStudio V2.3\Targets\KeMotion_CP24xCP25x_02.60\lib`

注意：根据软件安装情况，文件夹 `KeMotion_CP24xCP25x_02.60` 的名称可能不同。

这些文件放置到位后，即可执行 PLC 配置。当提示选择驱动器类型时，请选择 `CDHD2`。

# 7 CANopen 操作

## 7.1 设备通信

CDHD2 通信接口符合以下标准：

- CiA 301：CANopen 应用层和通信配置文件
- IEC 61800-7-1：接口定义（此前为 CiA 402-1：通用定义）
- IEC 61800-7-201：Profile Type 1（CiA 402）（此前为 CiA 402-2：运行模式和应用数据）
- IEC 61800-7-301：Profile Type 1 的映射（此前为 CiA 402-3：PDO 映射）

图 7-1 所示为通信架构。设备控制、驱动器启停以及多个模式相关命令由状态机执行；运行模式定义驱动器行为。标准对象位于 `0x1000`、`0x6000` 范围，制造商特定对象位于 `0x2000` 范围。

## 7.2 通信对象

通信对象用于交换过程数据和服务数据、进行过程或系统时间同步、监督错误状态，以及控制和监视节点状态。这些对象由结构、传输类型和 CAN 标识符定义。

### 7.2.1 服务数据通信

服务数据对象（SDO）用于直接访问 CANopen 设备对象字典中的对象条目。由于这些对象条目可包含任意大小和任意数据类型的数据，SDO 可用于在客户端与服务器之间传输多个数据集，每个数据集可包含任意大的数据块。客户端通过多路复用信息（对象字典的索引和子索引）控制要传输的数据集。数据集内容在对象字典中定义。

通常，SDO 以一系列段的形式传输。在传输这些段之前，会有一个初始化阶段，客户端和服务器在该阶段准备进行段传输。对于 SDO，也可以在初始化阶段传输最多 4 字节的数据集。该机制称为 SDO expedited transfer（SDO 加速传输）。

无论哪种传输类型，SDO 传输始终由客户端发起。被访问对象字典的所有者是该 SDO 的服务器。客户端或服务器均可主动中止 SDO 传输。

通过 SDO，可在两个 CANopen 设备之间建立点对点通信通道。一个 CANopen 设备可支持多个 SDO。默认情况下支持一个 Server-SDO（Default SDO）。

### 7.2.2 过程数据通信

过程数据对象（PDO）用于实时数据传输。PDO 传输没有协议开销。

PDO 对应对象字典中的对象，并提供到应用对象的接口。应用对象到 PDO 的数据类型和映射由对象字典中相应的默认 PDO 映射结构决定。CDHD2 支持可变 PDO 映射；因此，在配置过程中，可通过对对象字典中相应对象应用 SDO 服务，将 PDO 数量以及应用对象到 PDO 的映射传输到 CANopen 设备。

PDO 同时用于数据发送和数据接收，分别称为 Transmit-PDO（TPDO）和 Receive-PDO（RPDO）。支持 TPDO 的 CANopen 设备是 PDO 生产者，支持 RPDO 的 CANopen 设备是 PDO 消费者。CDHD2 两者均支持。PDO 通信参数描述 PDO 的通信能力；PDO 映射参数包含 PDO 内容信息。

每个 PDO 都必须有一对通信参数和映射参数。

CDHD2 对 TPDO 和 RPDO 数量有上限。默认实现 4 个 TPDO 和 4 个 RPDO：

| 默认 PDO | 内容 |
|---|---|
| TPDO1 | Statusword (`6041h`) 16 bit；Modes of operation display (`6061h`)；Torque actual value (`6077h`) 16 bit |
| TPDO2 | Position actual value (`6064h`) 32 bit |
| TPDO3 | Torque demand command (`6074h`) 16 bit；Analog input 1 (`20F2h`) 16 bit |
| TPDO4 | Digital inputs (`60FDh`) 32 bit；Position external command (`20B6h`) 32 bit；Following error actual value (`60F4h`) 32 bit |
| RPDO1 | Controlword (`6040h`) 16 bit；Mode of operation (`6060h`) 8 bit |
| RPDO2 | Target position (`607Ah`) 32 bit；Profile velocity (`6081h`) 32 bit |
| RPDO3 | Target velocity (`60FFh`) 32 bit |
| RPDO4 | Target torque (`6071h`) 16 bit；Digital outputs (`60FEh`) 32 bit；Torque offset (`60B2h`) 16 bit |

## 7.3 设备控制与状态机

功率驱动系统有限状态自动机（PDS FSA）是定义功率驱动系统行为的数学模型。由于即使通信网络未正常工作，功率驱动系统也必须能提供本地控制，因此通信 FSA 与 PDS FSA 只是松耦合。图 7-2 显示功率驱动系统如何通过网络远程运行，或在本地运行。

功率驱动系统由控制设备通过网络发送的 `Controlword` 操作。功率驱动系统状态由驱动设备产生的 `Statusword` 报告。FSA 也受错误检测信号控制。

PDS FSA 定义功率驱动系统状态以及可能的控制序列。单个状态表示一种特定的内部或外部行为。功率驱动系统状态也决定哪些命令会被接受。例如，只有当驱动器处于 `Operation Enabled` 状态时，才可以启动点到点运动。

## 7.4 指示运行状态

上电后，以及启动某个运行模式时，功率驱动系统会经过多个运行状态。这些运行状态由内部监控并受到监控功能影响。

图 7-3 说明 PDS FSA 行为，并根据用户命令和内部驱动器故障考虑功率电子部分的控制。

| 状态 | 含义 |
|---|---|
| Not Ready to Switch On | 从控制器收到“未准备好运行”。 |
| Switch On Disabled | 已准备好运行。可以读写参数。不能执行运动功能。 |
| Ready to Switch On | 已准备好运行。可以读写参数。不能执行运动功能。必须接通母线电压。 |
| Operation Enabled | 驱动器功率级已使能。无故障。可以执行运动功能。 |
| Quick Stop Active | 驱动器已通过受控停止方式停止。功率级已使能。不能执行运动功能。 |
| Fault Reaction Active | 已发生故障。驱动器正在降速到 0 速度（Active Disable 过程）。 |
| Fault | 已发生故障。功率级已禁用。 |

`Statusword` 参数的 bit 0、1、2、3、5 和 6 提供运行状态信息。

| 运行状态 | bit 6 Switch On Disabled | bit 5 Quick Stop | bit 3 Fault | bit 2 Operation Enabled | bit 1 Switch On | bit 0 Ready to Switch On |
|---|---:|---:|---:|---:|---:|---:|
| 2 Not Ready To Switch On | 0 | X | 0 | 0 | 0 | 0 |
| 3 Switch On Disabled | 1 | X | 0 | 0 | 0 | 0 |
| 4 Ready To Switch On | 0 | 1 | 0 | 0 | 0 | 1 |
| 5 Switched On | 0 | 1 | 0 | 0 | 1 | 1 |
| 6 Operation Enabled | 0 | 1 | 0 | 1 | 1 | 1 |
| 7 Quick Stop Active | 0 | 0 | 0 | 1 | 1 | 1 |
| 8 Fault Reaction Active | 0 | X | 1 | 1 | 1 | 1 |
| 9 Fault | 0 | X | 1 | 0 | 0 | 0 |

`Statusword` 位分配：

- bit 0-3：状态位
- bit 4：Voltage enabled
- bit 5-6：状态位
- bit 7：Warning
- bit 8：保留
- bit 9：Remote
- bit 10：Target reached
- bit 11：Internal limit is active
- bit 12-13：运行模式相关
- bit 14-15：制造商特定

说明：

- bit 4 = 1 表示 DC 母线电压正确。如果电压缺失或过低，设备不会从状态 3 转换到状态 4。
- bit 7（warning）= 1 表示存在警告条件。警告不是错误或故障（例如超过温度限制、任务被拒绝）。PDS FSA 状态不变。警告原因可能在故障代码参数对象 `603Fh` 中给出。
- bit 9 置位时，设备通过现场总线执行命令。bit 9 复位时，设备由其他接口控制。在这种情况下，仍可通过现场总线读写参数。
- bit 10 与 bit 12 用于监视当前运行模式。
- bit 13 仅在需要先解决错误才能继续处理时变为 1。

## 7.5 更改运行状态

可使用 `Controlword` 参数在运行状态之间切换。

`Controlword` 位分配：

- bit 0：Switch On
- bit 1：Enable Voltage
- bit 2：Quick Stop
- bit 3：Enable Operation
- bit 4-6：运行模式相关
- bit 7：Fault Reset
- bit 8：Halt
- bit 9：保留
- bit 10-15：保留，必须为 0

更改后的设置立即生效。`Controlword` 为 `Unsigned16`。

`Controlword` 的 bit 0、1、2、3 和 7 可用于切换运行状态：

| 现场总线命令 | 状态转换 | 转换到 | bit 7 Fault Reset | bit 3 Enable Operate | bit 2 Quick Stop | bit 1 Enable Voltage | bit 0 Switch On |
|---|---|---|---|---|---|---|---|
| Shutdown | T2, T6, T8 | 4 Ready To Switch On | X | X | 1 | 1 | 0 |
| Switch On | T3 | 5 Switched On | X | X | 1 | 1 | 1 |
| Disable Voltage | T7, T9, T10, T12 | 3 Switch On Disabled | X | X | X | 0 | X |
| Quick Stop | T7, T10/T11 | 3 Switch On Disabled / 7 Quick Stop Active | X | X | 0 | 1 | X |
| Disable Operation | T5 | 5 Switched On | X | 0 | 1 | 1 | 1 |
| Enable Operation | T4, T16 | 6 Operation Enabled | X | 1 | 1 | 1 | 1 |
| Fault Reset | T15 | 3 Switch On Disabled | 0 -> 1 | X | X | X | X |

说明：

- bit 4-6 用于运行模式相关设置。
- bit 8 = 1 可触发 Halt。
- bit 9-15 保留。

## 7.6 启动和更改运行模式

`Mode of Operation` 参数（`6060h`）用于设置所需运行模式。

| 值 | 运行模式 |
|---:|---|
| 1 | Profile Position |
| 3 | Profile Velocity |
| 4 | Profile Torque |
| 6 | Homing |
| 7 | Interpolated Position |
| 8 | Cyclic Synchronous Position |
| 9 | Cyclic Synchronous Velocity |
| 10 | Cyclic Synchronous Torque |

写入后，设置立即生效。数据类型为 `Integer8`，访问权限为读/写。

`Mode of Operation Display`（`6061h`）用于读取当前运行模式，模式值同上。

## 7.7 Profile Position 模式

说明：在 Profile Position 运行模式下，电机根据主站控制器发送的目标位置、加速度和速度值执行运动。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Profile Position 模式（`1`）。
- 将 `Target position (607Ah)` 设置为目标位置，单位为 pulse。
- 将 `Profile velocity (6081h)` 设置为轮廓速度，单位为 pulse/s。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 查询 `Position actual value (6064h)` 获取电机实际位置。
- 查询 `Statusword (6041h)` 获取 following error、set-point acknowledge 和 target reached 的当前状态。

可选信息：

- 查询 `Position demand value (6062h)` 获取内部参考值，单位为 pulse。
- 查询 `Position actual value (6063h)` 获取实际位置值，单位为 increments。
- 设置 `Following error window (6065h)` 为允许的跟随误差，单位为 pulse。
- 查询 `Following error actual value (60F4h)` 获取当前跟随误差，单位为 pulse。
- 设置 `Position window (6067h)` 和 `Position window time (6068h)`。当目标位置与当前电机位置之间的差值在指定时间内保持在位置窗口内时，认为已到达目标位置。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`6062h`、`6063h`、`6064h`、`6065h`、`6067h`、`6068h`、`6081h`、`6091h`、`6092h`、`60F2h`、`60F4h`、`60FCh`。

`Controlword (6040h)` 中 bit 4-6 和 bit 8 用于启动运动：

- bit 4：New Target Value。`0 -> 1` 启动到目标位置的运动。
- bit 5：Change Set Point Immediately。决定运动中传输的目标值是否立即生效，以及是否在当前目标位置停止。
- bit 6：Absolute / Relative。`0` 为绝对运动，`1` 为相对运动。
- bit 8：Halt。使用 Halt 停止运动。

`Statusword (6041h)` 中 bit 10 和 bit 12-15 提供当前运动信息：

- bit 10：Target reached。`0` 未到达目标位置，`1` 已到达目标位置。
- bit 12：Target value acknowledge。`0` 可接受新位置，`1` 新目标位置已接受。
- bit 13：Following error bit。`0` 无跟随误差，`1` 有跟随误差。
- bit 14-15：制造商特定。

示例报文见英文提取稿的第 65-66 页；十六进制 COB-ID/Data 建议按原文核对使用。

## 7.8 Homing 模式

说明：在 Homing 运行模式下，电机执行运动，直到到达 home position，也称为参考点或零点。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Homing 模式（`6`）。
- 设置 `Home offset (607Ch)`。
- 设置 `Home method (6098h)`；取值范围为 1 到 35，用于指定不同回零方法。
- 将 `Home speeds (6099h sub-index 1)` 设置为搜索限位开关的速度。
- 将 `Home speeds (6099h sub-index 2)` 设置为搜索 index pulse 的速度。
- 将 `Home acceleration (609Ah)` 设置为加速度斜坡值。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 启动 Homing。
- 查询 `Statusword (6041h)` 获取设备状态。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`607Ch`、`6098h`、`6099h`、`609Ah`。

`Controlword (6040h)`：bit 4 启动回零，bit 8 终止运动。

- bit 4：Homing operation start，启动 Homing。
- bit 8：Halt，使用 Halt 停止运动。

`Statusword`：

- bit 10：Target reached。`0` 表示 Homing 未完成。
- bit 12：Homing attained。`1` 表示 Homing 成功完成。
- bit 13：Homing error。`1` 表示 Homing 错误。
- bit 14-15：制造商特定。

## 7.9 Profile Velocity 模式

说明：在 Profile Velocity 运行模式下，驱动器根据目标速度运行。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Profile Velocity 模式（`3`）。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 设置 `Target velocity (60FFh)` 为目标速度。如果功率级已使能，新目标速度会立即生效并开始运动。
- 查询 `Statusword (6041h)` 获取设备状态。

可选信息：

- 查询 `Velocity demand value (606Bh)` 获取参考速度。
- 查询 `Velocity actual value (60C3h)` 获取实际速度。
- 设置 `Velocity window (606Dh)`。
- 设置 `Velocity window time (606Eh)`，用于定义速度保持在窗口内并判定为已达到目标速度所需的持续时间。
- 查询或设置速度阈值相关对象以定义静止窗口。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`606Bh`、`606Ch/60C3h`、`606Dh`、`606Eh`、`60FFh` 等。

`Controlword`：bit 8 用于 Halt 停止运动；bit 4、5、6、9 对此模式无关。

`Statusword`：

- bit 10：Target reached。`0` 表示目标速度未达到。
- bit 12：Velocity。用于速度状态监视。
- bit 14-15：制造商特定。

## 7.10 Profile Torque 模式

说明：在 Profile Torque 运行模式下，驱动器按目标转矩运行。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Profile Torque 模式（`4`）。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 根据电机规格设置 `Motor rated current (6075h)`，单位为 mA。
- 设置 `Target torque (6071h)` 为目标转矩，单位为额定转矩的 0.1%。

可选信息：

- 查询 `Motor rated current (6075h)` 获取由电机和驱动器决定的额定电流。
- 查询 `Current actual value (6078h)` 获取实际电流，单位为额定电流的 0.1% 增量。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`6071h`、`6074h`、`6075h`、`6078h`、`6087h` 等。

`Controlword`：bit 8 用于 Halt 停止运动；bit 4、5、6、9 对此模式无关。

`Statusword`：bit 10 表示目标转矩是否达到。

## 7.11 Interpolated Position 模式

说明：在 Interpolated Position 运行模式下，主站向驱动器发送插补位置数据，驱动器按插补位置执行运动。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Interpolated Position 模式（`7`）。
- 将 `Target position (60C1h)` 设置为目标位置，单位为 pulse。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 查询 `Position actual value (6064h)` 获取电机实际位置。
- 查询 `Statusword (6041h)` 获取 following error、set-point acknowledge 和 target reached 的当前状态。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`6062h`、`6063h`、`6064h`、`6065h`、`60C1h`、`60F4h`。

`Controlword`：bit 4 用于启动运动。

`Statusword`：

- bit 10：Target reached。`0` 未到达目标位置。
- bit 12：Target value acknowledge。`0` 表示可接受新位置，`1` 表示新目标位置已接受。
- bit 13：Following error bit。`0` 无跟随误差，`1` 有跟随误差。
- bit 14-15：制造商特定。

## 7.12 Cyclic Synchronous Position 模式

说明：在 Cyclic Synchronous Position 运行模式下，主站在每个 EtherCAT/CAN 周期发送目标位置，驱动器执行位置控制。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Cyclic Synchronous Position 模式（`8`）。
- 将 `Target position (607Ah)` 设置为目标位置，单位为 pulse。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 查询 `Position actual value (6064h)` 获取电机实际位置。
- 查询 `Statusword (6041h)` 获取 following error、set-point acknowledge 和 target reached 的当前状态。

可选信息包括读取 `Position demand value (6062h)`、`Position actual value (6063h)`、设置 `Following error window (6065h)`，以及读取 `Following error actual value (60F4h)`。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`6062h`、`6063h`、`6064h`、`6065h`、`607Ah`、`60F4h`。

`Controlword`：bit 8 用于 Halt 停止运动；bit 4、5、6、9 对此模式无关。`Statusword` 按 CANopen 状态机变化。

## 7.13 Cyclic Synchronous Velocity 模式

说明：在 Cyclic Synchronous Velocity 运行模式下，主站在每个 EtherCAT/CAN 周期发送目标速度，驱动器执行速度控制。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Cyclic Synchronous Velocity 模式（`9`）。
- 设置 `Target velocity (60FFh)` 为目标速度。如果功率级已使能，新目标速度会立即生效并开始运动。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 查询 `Statusword (6041h)` 获取当前状态。

可选信息：

- 查询 `Velocity demand value (606Bh)` 获取参考速度。
- 查询 `Velocity actual value (60C3h)` 获取实际速度。
- 设置 `Velocity window (606Dh)`。
- 设置 `Velocity window time (606Eh)`。
- 查询速度阈值相关对象以设置静止窗口。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`606Bh`、`606Dh`、`606Eh`、`60FFh` 等。

`Controlword`：bit 8 用于 Halt 停止运动；bit 4、5、6、9 对此模式无关。`Statusword` 按 CANopen 状态机变化。

## 7.14 Cyclic Synchronous Torque 模式

说明：在 Cyclic Synchronous Torque 运行模式下，主站在每个 EtherCAT/CAN 周期发送目标转矩，驱动器执行转矩控制。

步骤：

- 将 `Mode of operation (6060h)` 设置为 Cyclic Synchronous Torque 模式（`10`）。
- 设置 `Target torque (6071h)` 为目标转矩。如果功率级已使能，新目标转矩会立即生效并开始运动。
- 设置 `Controlword (6040h)` 以激活运行模式并使能运动。
- 查询 `Statusword (6041h)` 获取当前状态。

可选信息：

- 查询 `Motor rated current (6075h)` 获取由电机和驱动器决定的额定电流。
- 查询 `Current actual value (6078h)` 获取实际电流，单位为额定电流 0.1% 的增量。

相关对象包括：`6040h`、`6041h`、`6060h`、`6061h`、`6071h`、`6074h`、`6075h`、`6087h`。

`Controlword`：bit 8 用于 Halt 停止运动；bit 4、5、6、9 对此模式无关。`Statusword` 按 CANopen 状态机变化。

## 7.15 数字输出操作

以下过程说明如何控制 CDHD2 数字输出。

1. 使能数字输出以允许手动控制：将对象 `60FEh` 子索引 2 设置为 `FFFFFFFFh`。这会授予对所有数字输出的写入权限。
2. 将特定输出的模式定义为空闲（idle），以便由用户手动控制该输出，而不是由驱动器逻辑控制。例如，将数字输出 3 定义为空闲：
   - 将对象 `209Ch` 子索引 1 设置为值 `3`。
   - 将对象 `209Ch` 子索引 2 设置为值 `0`。
3. 通过写入对象来设置输出状态。数字输入/输出 3 在对象 `60FE` 中由 bit 18 表示，因此可将对象 `60FE` 子索引 1 设置为 `40000h`（`2^18 = 262144`）。

# 8 单位

## 8.1 单位概述

CiA 和 ETG 标准提供两个对象用于设置齿轮比和进给常数转换因子，每个对象都有两个子索引。

这些对象有四个等效的 VarCom 驱动器参数：

| CAN 对象 | VarCom / ServoStudio | 说明 |
|---|---|---|
| `6092h` 子索引 1 | `PNUM`：Feed Constant（单位转换）分子 | 用户自定义单位的转换因子。根据电机类型，用于乘以电机转数（旋转电机）或电机极距（直线电机）。 |
| `6092h` 子索引 2 | `PDEN`：Feed Constant（单位转换）分母 | 同上 |
| `6091h` 子索引 1 | `FBGMS`：Fieldbus Gear Ratio - Motor Shaft Scaling | 现场总线设备电机轴转数的转换因子。 |
| `6091h` 子索引 2 | `FBGDS`：Fieldbus Gear Ratio - Drive Shaft Scaling | 现场总线设备驱动轴转数的转换因子。 |

可通过直接写入对象修改这些值。也可以使用 ServoStudio Motion Units 画面中的 CANopen Units 窗格。

## 8.2 位置单位

位置单位由以下公式表示：

```text
(0x6091 sub-index 1 / 0x6091 sub-index 2) x
(0x6092 sub-index 1 / 0x6092 sub-index 2)
= 1 motor revolution
```

示例：

```text
6091h sub-index 1 = 1048576
6091h sub-index 2 = 1
6092h sub-index 1 = 1
6092h sub-index 2 = 1

1048576 / 1 x 1 / 1 = 1048576
```

即：`1048576` 个位置单位 = 1 个电机转数。

### 8.2.1 位置分辨率 - 示例

位置分辨率应尽可能高，并且不得低于编码器分辨率。

当驱动器在 Synchronous Position 模式下运行时，控制器每个周期向驱动器发送一个位置命令。

低分辨率示例：

| CAN 对象 | 参数 | 值 |
|---|---|---:|
| `6092h` 子索引 1 | `PNUM` - Feed Constant 分子 | 360 |
| `6092h` 子索引 2 | `PDEN` - Feed Constant 分母 | 1 |

假设控制器希望电机以 60 rpm 的低速运动，即每秒 1 转，或每秒 360 度。典型 EtherCAT 周期为 1 ms，因此控制器将 360 度除以 1000，并每 1 ms 发送一次命令。由于 EtherCAT 仅支持整数，而 `0.36`（`360/1000`）不是整数，命令平均约每三个周期才更新一次。因此，电机会在一个周期内移动若干编码器计数，并在接下来两个周期停止，从而产生明显噪声。速度越低，噪声越严重。

高分辨率示例：

| CAN 对象 | 参数 | 值 |
|---|---|---:|
| `6092h` 子索引 1 | `PNUM` - Feed Constant 分子 | 1 |
| `6092h` 子索引 2 | `PDEN` - Feed Constant 分母 | 1 |

假设控制器希望电机以 60 rpm 低速运动，即每秒 1 转，或每秒 360000 counts。典型 EtherCAT 周期为 1 ms，因此控制器将 360000 counts 除以 1000，并每 1 ms 发送一次命令。由于 `360000/1000 = 360` 是整数，命令会在每个周期稳定更新。速度保持恒定，不会产生声学噪声。

通过 EtherCAT 发送的位置命令具有高精度优势，可改善系统性能。

## 8.3 速度单位

速度单位由以下公式表示：

```text
(0x6091 sub-index 1 / 0x6091 sub-index 2) x
(0x6092 sub-index 1 / 0x6092 sub-index 2)
= 1 rps
```

例如当 `6091h:01 = 1048576`、`6091h:02 = 1`、`6092h:01 = 1`、`6092h:02 = 1` 时，`1048576` 个速度单位 = `1 rps`。

## 8.4 加速度/减速度单位

加速度/减速度单位由以下公式表示：

```text
(0x6091 sub-index 1 / 0x6091 sub-index 2) x
(0x6092 sub-index 1 / 0x6092 sub-index 2)
= 1 rps/s
```

例如当 `6091h:01 = 1048576`、`6091h:02 = 1`、`6092h:01 = 1`、`6092h:02 = 1` 时，`1048576` 个加/减速度单位 = `1 rps/s`。

## 8.5 电流单位

电流单位来源于对象 `6075h`（Motor Rated Current），该对象以 mA 定义。

设置 `6075h` 的值后，所有其他电流相关对象的值必须按 `6075h` 的 `1/1000` 定义。

示例：假设 `6075h = 20000 mA`，要将对象 `6073h`（Max Current）设置为 `40000 mA`，应向 `6073h` 写入 `2000`。

计算如下：

```text
(2000 / 1000) x 20000 = 40000 mA
```

## 8.6 转矩单位

转矩单位来源于对象 `6076h`（Motor Rated Torque），该对象以 mNm 定义。

设置 `6076h` 的值后，所有其他转矩相关对象的值必须按 `6076h` 的 `1/1000` 定义。

示例：假设 `6076h = 500 mNm`，要将对象 `6074h`（Torque Demand）设置为 `100 mNm`，应向 `6074h` 写入 `200`。

计算如下：

```text
(200 / 1000) x 500 = 100 mNm
```

## 8.7 旋转电机单位 - 示例

### 将单位设置为转数

```text
Position = rev
Velocity = rev/sec
Acceleration = rev/sec^2
```

| CAN 对象 | 参数 | 值 |
|---|---|---:|
| `6092h` 子索引 1 | `PNUM` | 1 |
| `6092h` 子索引 2 | `PDEN` | 1 |
| `6091h` 子索引 1 | `FBGMS` | 1 |
| `6091h` 子索引 2 | `FBGDS` | 1 |

Profile Position：设置 `6060h = 1`，设置 `607Ah`（单位为转数）。如果 `607Ah = 1`，电机轴旋转 1 圈。设置 `6081h`（单位为 rev/s）。如果 `6081h = 1`，电机轴速度为 `1 rev/s`。设置 `6040h` 启动运动。

Profile Velocity：设置 `6060h = 3`，设置 `6040h` 启动运行模式，然后设置 `60FFh`。如果功率级已使能，新目标速度会立即生效并开始运动。当运行模式改变、功率级禁用或触发 quick stop 时，该值复位为 0。

### 将单位设置为度

```text
Position = deg
Velocity = deg/sec
Acceleration = deg/sec^2
```

| CAN 对象 | 参数 | 值 |
|---|---|---:|
| `6092h` 子索引 1 | `PNUM` | 360 |
| `6092h` 子索引 2 | `PDEN` | 1 |
| `6091h` 子索引 1 | `FBGMS` | 1 |
| `6091h` 子索引 2 | `FBGDS` | 1 |

Profile Position：如果 `607Ah = 360`，电机轴旋转 1 圈。如果 `6081h = 360`，电机轴速度为 `1 rev/s`。

Profile Velocity：如果 `6081h = 360`，电机轴速度为 `360 deg/s`，即每秒 1 圈。

### 将单位设置为反馈计数

```text
Position = counts
Velocity = counts/sec
Acceleration = counts/sec^2
```

| CAN 对象 | 参数 | 值 |
|---|---|---|
| `6092h` 子索引 1 | `PNUM` | `Motor_Resolution` |
| `6092h` 子索引 2 | `PDEN` | `1` |
| `6091h` 子索引 1 | `FBGMS` | `1` |
| `6091h` 子索引 2 | `FBGDS` | `1` |

该示例假设反馈设备（即编码器）每 1 个电机转数产生 10000 counts。

`Motor_Resolution` 参数（`MENCRES`）定义电机编码器分辨率：对于旋转电机，为每转线数；对于直线电机，为每极距线数。使用增量编码器时，每转或每极距的编码器计数数等于 `Motor_Resolution x 4`。

获取 `Motor_Resolution` 的值，乘以 4，然后将所得数值输入为对象 `6092h` 子索引 1 的值。

Profile Position：如果 `607Ah = 10000`，电机轴旋转 10000 counts，即 1 圈。如果 `6081h = 10000`，电机轴速度为 `10000 counts/s`，即每秒 1 圈。

Profile Velocity：如果 `6081h = 10000`，电机轴速度为 `10000 counts/s`，即每秒 1 圈。

## 8.8 直线电机单位 - 示例

直线电机的基本参数是电机极距，即电机两个连续磁极之间的距离。极距数据以毫米表示。

要读取极距距离，请查询对象 `207Dh` 子索引 0。

在直线电机中，反馈分辨率定义为每个电机极距距离对应的编码器计数数。

### 将单位设置为电机极距

```text
Position = pitch
Velocity = pitch/sec
Acceleration = pitch/sec^2
```

| CAN 对象 | 参数 | 值 |
|---|---|---:|
| `6092h` 子索引 1 | `PNUM` | 1 |
| `6092h` 子索引 2 | `PDEN` | 1 |
| `6091h` 子索引 1 | `FBGMS` | 1 |
| `6091h` 子索引 2 | `FBGDS` | 1 |

Profile Position：如果 `607Ah = 1`，电机移动 1 个 pitch 距离。如果 `6081h = 1`，电机速度为 `1 pitch/s`。

Profile Velocity：如果 `6081h = 1`，电机速度为 `1 pitch/s`。若功率级已使能，新目标速度立即生效并开始运动。

### 将单位设置为毫米

```text
Position = mm
Velocity = mm/sec
Acceleration = mm/sec^2
```

| CAN 对象 | 参数 | 值 |
|---|---|---|
| `6092h` 子索引 1 | `PNUM` | Motor Pitch Distance [mm] |
| `6092h` 子索引 2 | `PDEN` | `1` |
| `6091h` 子索引 1 | `FBGMS` | `1` |
| `6091h` 子索引 2 | `FBGDS` | `1` |

该示例假设 pitch 值为 32。

Profile Position：如果 `607Ah = 32`，电机移动 1 mm。如果 `6081h = 32`，电机速度为 `1 mm/s`。

Profile Velocity：如果 `6081h = 32`，电机速度为 `1 mm/s`。

### 将单位设置为反馈计数

```text
Position = counts
Velocity = counts/sec
Acceleration = counts/sec^2
```

| CAN 对象 | 参数 | 值 |
|---|---|---|
| `6092h` 子索引 1 | `PNUM` | `Motor_Resolution` |
| `6092h` 子索引 2 | `PDEN` | `1` |
| `6091h` 子索引 1 | `FBGMS` | `1` |
| `6091h` 子索引 2 | `FBGDS` | `1` |

`Motor_Resolution` 参数（`MENCRES`）定义编码器分辨率：对于旋转电机，为每转线数；对于直线电机，为每极距线数。使用增量编码器时，每个电机极距距离对应的编码器计数数等于 `Motor_Resolution x 4`。

Profile Position：设置 `6060h = 1`，设置 `607Ah`（单位为 counts）。如果 `607Ah = 1`，电机移动 1 count 的距离。设置 `6081h`（单位为 counts/s）。如果 `6081h = 1`，电机速度为 `1 count/s`。设置 `6040h` 启动运动。

Profile Velocity：设置 `6060h = 3`，设置 `6040h` 启动运行模式，设置 `60FFh`。如果 `6081h = 1`，电机速度为 `1 count/s`。若功率级已使能，新目标速度会立即生效并开始运动；当运行模式改变、功率级禁用或触发 quick stop 时，该值复位为 0。

## 9 Communication Segment（通信段）

以下通信配置文件对象已在 CDHD2 伺服驱动器中实现。

更多信息请参阅相应的 CAN 文档。

### `1000h`: Device Type（设备类型）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1000` |
| Description | 包含设备类型和功能相关信息。该对象由一个 16 bit 字段和第二个 16 bit 字段组成：前者描述所使用的设备配置文件，后者给出设备可选功能的附加信息。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Constant |
| PDO Mapping | No |
| Default Value | `0x00420192` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1001h`: Error Register（错误寄存器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1001` |
| Description | 错误寄存器是一个 8 bit 字段，每一位对应一种错误类型。发生错误时，相应 bit 会被置位。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

各 bit 含义如下：

| bit | 含义 |
|---:|---|
| bit 0 | 通用错误 |
| bit 1 | 电流 |
| bit 2 | 电压 |
| bit 3 | 温度 |
| bit 4 | 通信错误（溢出、错误状态） |
| bit 5 | 设备配置文件特定 |
| bit 6 | 保留 |
| bit 7 | 制造商特定 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

### `1002h`: Manufacturer Status Register（制造商状态寄存器，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1002` |
| Description | 用于制造商特定用途的公共状态寄存器。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1003h`: Predefined Error Field（预定义错误字段，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1003` |
| Description | 保存设备中发生且已通过 Emergency 对象发出的错误。该对象为错误历史记录。向子索引 0 写入 `0` 会删除完整错误历史记录。 |
| Object Code | Array |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Errors（错误数量） |
| Entry Category | Mandatory |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFE` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` – `002` – `003` – `004` – `005` – `006` – `007` – `008` – `009` – `010` |
| Description | Standard Error Field（标准错误字段） |
| Entry Category | Mandatory |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1005h`: COB-ID SYNC（CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1005` |
| Description | 定义同步对象（SYNC）的 COB-ID。若 bit 30 置为高电平，设备会生成一条供驱动器使用的 SYNC 报文。其他 bit 的含义与其他通信对象相同。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000080` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1006h`: Communication Cycle Period（通信周期，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1006` |
| Description | 定义通信周期。不使用时为 `0`。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | µs |

### `1007h`: Synchronous Window Length（同步窗口长度）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1007` |
| Description | 定义同步报文的时间窗口长度。不使用时该值为 `0`。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | µs |

### `1008h`: Manufacturer Device Name（制造商设备名称，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1008` |
| Description | 制造商分配的设备名称。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Constant |
| PDO Mapping | No |
| Default Value | Hardware-dependent |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `1009h`: Manufacturer Hardware Version（制造商硬件版本，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1009` |
| Description | 制造商分配的设备版本。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Constant |
| PDO Mapping | No |
| Default Value | Hardware-dependent |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `100Ah`: Manufacturer Software Version（制造商软件版本，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `100A` |
| Description | 制造商软件的版本号。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Constant |
| PDO Mapping | No |
| Default Value | Hardware-dependent |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `100Ch`: Guard Time（防护时间，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `100C` |
| Description | 防护时间，单位为毫秒。不使用时该值为 `0`。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | ms |

### `100Dh`: Life Time Factor（寿命时间因子，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `100D` |
| Description | 寿命时间因子与防护时间相乘，得到设备的寿命时间。不使用时该值为 `0`。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

### `1010h`: Store Parameter Field（参数保存字段）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1010` |
| Description | `VarCom - SAVE`。控制将参数保存到非易失性存储器。向子索引写入 `65766173h`（`"save"` 的 ASCII 值）会保存参数。该对象区分多个参数组。子索引 1 表示所有参数。 |
| Object Code | Array |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Save All Parameters（保存所有参数） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1011h`: Restore Default Parameters（恢复默认参数，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1011` |
| Description | `VarCom - LOAD`。加载参数默认值。向子索引写入 `64616F6Ch`（`"load"` 的 ASCII 值）会恢复参数。该对象区分多个参数组。 |
| Object Code | Array |
| Data Type | `UNSIGNED32` |

参数组如下：

| 子索引 | 参数组 |
|---|---|
| Sub-index 1 | All parameters（所有参数） |
| Sub-index 2 | Communication parameters（通信参数） |
| Sub-index 3 | Application parameters（应用参数） |
| Sub-index 4-127 | Manufacturer defined parameters（制造商定义参数） |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0x7F` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Restore All Default Parameters（恢复所有默认参数） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1014h`: COB-ID EMCY（EMCY 的 COB-ID，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1014` |
| Description | 定义紧急对象（EMCY）的 COB-ID。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000080` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1015h`: Inhibit Time Emergency（紧急报文抑制时间，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1015` |
| Description | 用于紧急报文（Emergency Server）的抑制时间。按 `100 ms` 的倍数定义。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | ms |

### `1016h`: Heartbeat Consumer Entries（心跳消费者条目，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1016` |
| Description | 心跳消费者时间定义期望的心跳周期时间，因此必须大于产生该心跳的设备上所配置的对应生产者心跳时间。各子索引的 bit 31 - 24 必须为 `0`；bit 23 - 16 包含节点 ID；bit 15 - 0 包含心跳时间。 |
| Object Code | Array |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x01` |
| Upper Limit | `0x7F` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Consumer Heartbeat Time 1（消费者心跳时间 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x02FFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Consumer Heartbeat Time 2（消费者心跳时间 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x02FFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Consumer Heartbeat Time 3（消费者心跳时间 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x02FFFFFF` |
| Unit | - |

### `1017h`: Producer Heartbeat Time（心跳生产者时间，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1017` |
| Description | 定义心跳的周期时间，该时间必须为 `1 ms` 的整数倍。不使用时其值为 `0`。按 `1 ms` 的倍数定义。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | ms |

### `1018h`: Identity Object（标识对象）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1018` |
| Description | 包含设备的一般信息。子索引 1 包含由各制造商分配的唯一值。子索引 2 标识制造商特定的产品代码（设备版本）。子索引 3 包含修订号：bit 31-16 为主修订号，bit 15-0 为次修订号。子索引 4 标识制造商特定的序列号。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x04` |
| Lower Limit | `0x01` |
| Upper Limit | `0x04` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Vendor ID（厂商 ID） |
| Entry Category | Mandatory |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x000002E1` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Product Code（产品代码） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x000002AF` = drive model AF；`0x000002EC` = drive model EC；`0x000002EB` = drive model EB |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Revision Number（修订号） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Serial Number（序列号） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1019h`: Synchronous Counter Overflow Value（同步计数器溢出值，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1019` |
| Description | 定义是否将计数器映射到 SYNC 报文中，以及该计数器的最大可能值。`0` = 长度为 `0` 的 SYNC 报文；`1` = 保留；`2..240` = 长度为 `1` 的 SYNC 报文，第一个数据字节包含计数器值；`241..255` = 保留。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xF0` |
| Unit | - |

### `1029h`: Error Behavior（错误行为，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1029` |
| Description | 子索引 `000` 包含错误类别数量。子索引 `001` 包含通信错误的错误类别。子索引 `001` 到 `254` 包含设备轮廓或制造商特定错误类别。错误类别可取值：`0` = Pre-operational；`1` = No state change；`2` = Stopped；`3 .. 127` = 保留；`128` = 忽略 CAN 接口 bus-off 状态。 |
| Object Code | Array |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x01` |
| Upper Limit | `0xFE` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Communication Error（通信错误） |
| Entry Category | Mandatory |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x7F` |
| Unit | - |

### `1200h`: Server SDO Parameter 1（服务器 SDO 参数 1，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1200` |
| Description | 包含设备作为服务器的 SDO 参数。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x02` |
| Upper Limit | `0x02` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID Client -> Server（客户端 -> 服务器 COB-ID） |
| Entry Category | Mandatory |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000600` |
| Lower Limit | `0x00000600` |
| Upper Limit | `0xBFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | COB-ID Server -> Client（服务器 -> 客户端 COB-ID） |
| Entry Category | Mandatory |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000580` |
| Lower Limit | `0x00000580` |
| Upper Limit | `0xBFFFFFFF` |
| Unit | - |

### `1201h`: Server SDO Parameter 2（服务器 SDO 参数 2，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1201` |
| Description | 包含设备作为服务器的 SDO 参数。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x02` |
| Upper Limit | `0x03` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID Client -> Server（客户端 -> 服务器 COB-ID） |
| Entry Category | Mandatory |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x80000000` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | COB-ID Server -> Client（服务器 -> 客户端 COB-ID） |
| Entry Category | Mandatory |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x80000000` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Node ID of the SDO Client（SDO 客户端节点 ID） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x7F` |
| Unit | - |

### `1400h`: Receive PDO Communication Parameter 1（接收 PDO 通信参数 1，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1400` |
| Description | 包含设备当前能够接收的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 定义 COB ID；若 bit 31 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间，单位为 `100 µs`。子索引 `4` 为异步 PDO 定义事件时间。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x2` |
| Upper Limit | `0x5` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000200` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0xFF` |
| Lower Limit | `0x0` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |
 
### `1600h`: Receive PDO Mapping Parameter 1（接收 PDO 映射参数 1）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1600` |
| Description | 包含设备能够接收的 PDO 的映射。子索引 `0` 定义映射记录中有效条目的数量。该条目数量同时也是对应 PDO 所接收的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息。这些条目通过其索引（16 bit）、子索引（8 bit）和长度（8 bit）描述 PDO 内容。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60400010` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60600008` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1601h`: Receive PDO Mapping Parameter 2（接收 PDO 映射参数 2）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1601` |
| Description | 包含设备能够接收的 PDO 的映射。子索引 `0` 定义映射记录中有效条目的数量。该条目数量同时也是对应 PDO 所接收的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息。这些条目通过其索引（16 bit）、子索引（8 bit）和长度（8 bit）描述 PDO 内容。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60400010` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60600008` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1602h`: Receive PDO Mapping Parameter 3（接收 PDO 映射参数 3）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1602` |
| Description | 包含设备能够接收的 PDO 的映射。子索引 `0` 定义映射记录中有效条目的数量。该条目数量同时也是对应 PDO 所接收的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息。这些条目通过其索引（16 bit）、子索引（8 bit）和长度（8 bit）描述 PDO 内容。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x607A0020` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60810020` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1603h`: Receive PDO Mapping Parameter 4（接收 PDO 映射参数 4）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1603` |
| Description | 包含设备能够接收的 PDO 的映射。子索引 `0` 定义映射记录中有效条目的数量。该条目数量同时也是对应 PDO 所接收的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息。这些条目通过其索引（16 bit）、子索引（8 bit）和长度（8 bit）描述 PDO 内容。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60710010` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60FE0120` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1401h`: Receive PDO Communication Parameter 2（接收 PDO 通信参数 2，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1401` |
| Description | 包含设备当前能够接收的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 定义 COB ID；若 bit 31 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间，单位为 `100 µs`。子索引 `4` 为异步 PDO 定义事件时间。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x02` |
| Upper Limit | `0x05` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000300` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |

### `1402h`: Receive PDO Communication Parameter 3（接收 PDO 通信参数 3，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1402` |
| Description | 包含设备当前能够接收的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 定义 COB ID；若 bit 31 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间，单位为 `100 µs`。子索引 `4` 为异步 PDO 定义事件时间。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x02` |
| Upper Limit | `0x05` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000400` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |

### `1403h`: Receive PDO Communication Parameter 4（接收 PDO 通信参数 4，CAN only）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1403` |
| Description | 包含设备当前能够接收的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 定义 COB ID；若 bit 31 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间，单位为 `100 µs`。子索引 `4` 为异步 PDO 定义事件时间。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x02` |
| Upper Limit | `0x05` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000500` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |

### `1800h`: Transmit PDO Communication Parameter 1（发送 PDO 通信参数 1）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1800` |
| Description | 包含设备当前能够发送的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 描述 COB-ID；若 bit `31` 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间。子索引 `4` 为保留项。子索引 `5` 定义事件定时器。子索引 `6` 定义 SYNC 起始值。起始值 `0` 表示 SYNC 报文不含数据内容；起始值 `1` 到 `240` 表示 SYNC 报文含有 `1 byte` 数据，该数据字节被视为计数器值。计数器值等于 SYNC 起始值的 SYNC 报文被视为接收到的第一条 SYNC 报文。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x05` |
| Lower Limit | `0x02` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000180` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Compatibility Entry（兼容性条目） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Event Timer（事件定时器） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `ms` |

### `1801h`: Transmit PDO Communication Parameter 2（发送 PDO 通信参数 2）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1801` |
| Description | 包含设备当前能够发送的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 描述 COB-ID；若 bit `31` 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间。子索引 `4` 为保留项。子索引 `5` 定义事件定时器。子索引 `6` 定义 SYNC 起始值。起始值 `0` 表示 SYNC 报文不含数据内容；起始值 `1` 到 `240` 表示 SYNC 报文含有 `1 byte` 数据，该数据字节被视为计数器值。计数器值等于 SYNC 起始值的 SYNC 报文被视为接收到的第一条 SYNC 报文。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x05` |
| Lower Limit | `0x02` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000280` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Compatibility Entry（兼容性条目） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Event Timer（事件定时器） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `ms` |

### `1802h`: Transmit PDO Communication Parameter 3（发送 PDO 通信参数 3）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1802` |
| Description | 包含设备当前能够发送的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 描述 COB-ID；若 bit `31` 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间。子索引 `4` 为保留项。子索引 `5` 定义事件定时器。子索引 `6` 定义 SYNC 起始值。起始值 `0` 表示 SYNC 报文不含数据内容；起始值 `1` 到 `240` 表示 SYNC 报文含有 `1 byte` 数据，该数据字节被视为计数器值。计数器值等于 SYNC 起始值的 SYNC 报文被视为接收到的第一条 SYNC 报文。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x05` |
| Lower Limit | `0x02` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000380` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Compatibility Entry（兼容性条目） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Event Timer（事件定时器） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `ms` |

### `1803h`: Transmit PDO Communication Parameter 4（发送 PDO 通信参数 4）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1803` |
| Description | 包含设备当前能够发送的 PDO 的通信参数。子索引 `0` 定义已实现的 PDO 参数数量。子索引 `1` 描述 COB-ID；若 bit `31` 置位，则该 PDO 被禁用。子索引 `2` 定义传输类型。子索引 `3` 定义禁止时间。子索引 `4` 为保留项。子索引 `5` 定义事件定时器。子索引 `6` 定义 SYNC 起始值。起始值 `0` 表示 SYNC 报文不含数据内容；起始值 `1` 到 `240` 表示 SYNC 报文含有 `1 byte` 数据，该数据字节被视为计数器值。计数器值等于 SYNC 起始值的 SYNC 报文被视为接收到的第一条 SYNC 报文。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x05` |
| Lower Limit | `0x02` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | COB-ID |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000480` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Transmission Type（传输类型） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Inhibit Time（禁止时间） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `100 µs` |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Compatibility Entry（兼容性条目） |
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Event Timer（事件定时器） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `ms` |

### `1A00h`: Transmit PDO Mapping Parameter 1（发送 PDO 映射参数 1）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1A00` |
| Description | 包含设备能够发送的 PDO 的映射。PDO 映射参数的类型位于索引 `21h`。子索引 `0` 定义映射记录中有效条目的数量；该条目数量同时也是通过相应 PDO 传输的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息；这些条目通过索引、子索引和长度描述 PDO 内容。该参数可用于校验总映射长度，并且为必需项。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60410010` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60610008` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60770010` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1A01h`: Transmit PDO Mapping Parameter 2（发送 PDO 映射参数 2）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1A01` |
| Description | 包含设备能够发送的 PDO 的映射。PDO 映射参数的类型位于索引 `21h`。子索引 `0` 定义映射记录中有效条目的数量；该条目数量同时也是通过相应 PDO 传输的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息；这些条目通过索引、子索引和长度描述 PDO 内容。该参数可用于校验总映射长度，并且为必需项。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60640020` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x606C0020` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x0` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x0` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1A02h`: Transmit PDO Mapping Parameter 3（发送 PDO 映射参数 3）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1A02` |
| Description | 包含设备能够发送的 PDO 的映射。PDO 映射参数的类型位于索引 `21h`。子索引 `0` 定义映射记录中有效条目的数量；该条目数量同时也是通过相应 PDO 传输的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息；这些条目通过索引、子索引和长度描述 PDO 内容。该参数可用于校验总映射长度，并且为必需项。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60740010` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x20F20010` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFF` |
| Unit | - |

### `1A03h`: Transmit PDO Mapping Parameter 4（发送 PDO 映射参数 4）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1A03` |
| Description | 包含设备能够发送的 PDO 的映射。PDO 映射参数的类型位于索引 `21h`。子索引 `0` 定义映射记录中有效条目的数量；该条目数量同时也是通过相应 PDO 传输的应用变量数量。子索引 `1` 到 `[number of entries]` 包含已映射应用变量的信息；这些条目通过索引、子索引和长度描述 PDO 内容。该参数可用于校验总映射长度，并且为必需项。 |
| Object Code | Record |
| Data Type | Manufacturer-specific, varies by sub-index. |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Mandatory |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x03` |
| Lower Limit | `0x00` |
| Upper Limit | `0x06` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Mapping Entry 1（映射条目 1） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60FD0020` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Mapping Entry 2（映射条目 2） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x20B60020` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Mapping Entry 3（映射条目 3） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x60F40020` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Mapping Entry 4（映射条目 4） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `005` |
| Description | Mapping Entry 5（映射条目 5） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `006` |
| Description | Mapping Entry 6（映射条目 6） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `1C00h`: Sync Manager Communication Type (ECT only)（Sync Manager 通信类型，仅 ECT）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1C00` |
| Description | 最多可描述 32 种 Sync Manager 类型。前四种 Sync Manager 类型是固定的，其余类型可配置为四种类型之一。默认配置如下：`1` - Mailbox receive（邮箱接收）；`2` - Mailbox send（邮箱发送）；`3` - Process data output（过程数据输出）；`4` - Process data input（过程数据输入）。 |
| Object Code | Array |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Access | Read Only |
| PDO Mapping | no |
| Default Value | `0x04` |
| Lower Limit | `0x00` |
| Upper Limit | `0x20` |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Sub-Index 1（子索引 1） |
| Data Type | `UNSIGNED8` |
| Access | Read Only |
| PDO Mapping | no |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0x04` |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Sub-Index 2（子索引 2） |
| Data Type | `UNSIGNED8` |
| Access | Read Only |
| PDO Mapping | no |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0x04` |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Sub-Index 3（子索引 3） |
| Data Type | `UNSIGNED8` |
| Access | Read Only/Read Only/Read Only |
| PDO Mapping | no |
| Default Value | `0x03` |
| Lower Limit | `0x00` |
| Upper Limit | `0x04` |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Sub-Index 4（子索引 4） |
| Data Type | `UNSIGNED8` |
| Access | Read Only |
| PDO Mapping | no |
| Default Value | `0x04` |
| Lower Limit | `0x00` |
| Upper Limit | `0x04` |

### `1C10h`: Sync Manager 0 PDO Assignment (ECT only)（Sync Manager 0 PDO 分配，仅 ECT）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1C10` |
| Description | 用于从 Sync Manager 2 开始向 Sync Manager 分配 PDO。 |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | no |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0000` |

### `1C11h`: Sync Manager 1 PDO Assignment (ECT only)（Sync Manager 1 PDO 分配，仅 ECT）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1C11` |
| Description | Sync Manager 1 PDO Assignment（Sync Manager 1 PDO 分配） |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | no |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0000` |

### `1C12h`: Sync Manager 2 PDO Assignment (ECT only)（Sync Manager 2 PDO 分配，仅 ECT）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1C12` |
| Description | Sync Manager 2 PDO Assignment（Sync Manager 2 PDO 分配） |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Assigned RxPDO（已分配 RxPDO 数量） |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x0004` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0004` |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Sub-Index 1（子索引 1） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x1600` |
| Lower Limit | `0x1600` |
| Upper Limit | `0x17FF` |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Sub-Index 2（子索引 2） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x1601` |
| Lower Limit | `0x1600` |
| Upper Limit | `0x17FF` |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Sub-Index 3（子索引 3） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x1602` |
| Lower Limit | `0x1600` |
| Upper Limit | `0x17FF` |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Sub-Index 4（子索引 4） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x1603` |
| Lower Limit | `0x1600` |
| Upper Limit | `0x17FF` |

### `1C13h`: Sync Manager 3 PDO Assignment (ECT only)（Sync Manager 3 PDO 分配，仅 ECT）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `1C13` |
| Description | Sync Manager 3 PDO Assignment（Sync Manager 3 PDO 分配） |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Assigned TxPDOs（已分配 TxPDO 数量） |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x0004` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x00FF` |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Sub-Index 1（子索引 1） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write/Read/Write/Read/Write |
| PDO Mapping | no |
| Default Value | `0x1A00` |
| Lower Limit | `0x1A00` |
| Upper Limit | `0x1BFF` |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Sub-Index 2（子索引 2） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x1A01` |
| Lower Limit | `0x1A00` |
| Upper Limit | `0x1BFF` |

| 项目 | 值 |
|---|---|
| Sub-Index | `003` |
| Description | Sub-Index 3（子索引 3） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x1A02` |
| Lower Limit | `0x1A00` |
| Upper Limit | `0x1BFF` |

| 项目 | 值 |
|---|---|
| Sub-Index | `004` |
| Description | Sub-Index 4（子索引 4） |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | no |
| Default Value | `0x1A03` |
| Lower Limit | `0x1A00` |
| Upper Limit | `0x1BFF` |

## 10 Manufacturer-Specific Object（制造商特定对象）

### `2002h`: Configuration Command（配置命令）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | VarCom - `CONFIG` |
| Description | 根据驱动器内部参数执行驱动器配置序列。写入 `01` 可启动配置命令。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

### `2003h`: Current BEMF Compensation Gain（电流 BEMF 补偿增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2003` |
| Description | VarCom - `KCBEMF`。用于电流控制的前馈 BEMF 补偿比例。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `2.0` |
| Unit | - |

### `2006h`: Current KI Gain（电流 KI 增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2006` |
| Description | VarCom - `KCI`。电流控制器积分器（KI）增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `100.0` |
| Unit | - |

### `2007h`: Current KP Gain（电流 KP 增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2007` |
| Description | VarCom - `KCP`。电流控制器比例（KP）增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `100.0` |
| Unit | - |

### `200Ah`: HD Anti-Vibration 2 Filter - Gain（HD 防振 2 滤波器 - 增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `200A` |
| Description | VarCom - `NLANTIVIBGAIN2`。HD 位置控制环防振模块 3 滤波器的增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `1000.0` |
| Unit | - |

### `200Bh`: HD Anti-Vibration 1 Filter - Sharpness（HD 防振 1 滤波器 - 锐度）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `200B` |
| Description | VarCom - `NLANTIVIBSHARP`。HD 位置控制环防振模块 1 滤波器的锐度。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.5` |
| Lower Limit | `0.00999999977648` |
| Upper Limit | `10.0` |
| Unit | - |

### `200Ch`: HD Anti-Vibration 1 Filter - Gain（HD 防振 1 滤波器 - 增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `200C` |
| Description | VarCom - `NLANTIVIBGAIN`。HD 位置控制环防振模块 1 滤波器的增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `10000.0` |
| Unit | `Rad*10-3/N` |

### `200Eh`: Automatic Homing Mode（自动回零模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `200E` |
| Description | VarCom - `AUTOHOME`。上电时要执行的自动回零类型。可能值：`0` = No Homing（不回零）；`1` = Attempt once at power up. Fail once.（上电时尝试一次；失败一次）。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `200Fh`: Fieldbus Unit Scaling（现场总线单位缩放）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `200F` |
| Description | VarCom - `FBSCALE`。内部计数的现场总线单位缩放。定义 32-bit 位置中相当于若干转的位数。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x000C` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0014` |
| Unit | - |

### `2010h`: Velocity Loop Bandwidth for Pole Placement（极点配置速度环带宽）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2010` |
| Description | VarCom - `BW`。极点配置控制器的速度控制环带宽。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x001E` |
| Lower Limit | `0x000A` |
| Upper Limit | `0x0258` |
| Unit | `Hz` |

### `2011h`: Warning Bits（警告位）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2011` |
| Description | 按 bit 列出警告。警告为 64 bit，分为两个 32-bit 段。请参见用户手册中的 Warning Messages（警告消息）章节。 |
| Object Code | Array |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x02` |
| Upper Limit | `0x02` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Low Bits（低位） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | High Bits（高位） |
| Entry Category | Optional |
| Data Type | `UNSIGNED32` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | - |

### `2013h`: Voltage Command D Component（电压命令 D 分量）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2013` |
| Description | VarCom - `CLVD`。显示电流控制器的 D 输出。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | - |

### `2014h`: Voltage Command Q Component（电压命令 Q 分量）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2014` |
| Description | VarCom - `CLVQ`。显示电流控制器的 Q 输出。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | - |

### `2015h`: Drive Name (CAN only)（驱动器名称，仅 CAN）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2015` |
| Description | VarCom - `DRIVENAME`。分配给驱动单元的名称。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `2016h`: Electrical Position（电角度位置）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2016` |
| Description | VarCom - `ELECTANGLE`。16-bit 分辨率的电角度位置。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `65536/(elect cycle)` |

### `2017h`: HD Derivative Gain（HD 微分增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2017` |
| Description | VarCom - `KNLD`。HD 控制中等效于 PID D 的参数。用于 HD 控制环以降低速度误差。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `2000.0` |
| Unit | `Hz` |

### `2018h`: HD Integral Gain（HD 积分增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2018` |
| Description | VarCom - `KNLI`。HD 控制中等效于 PID I 的参数。用于 HD 控制环以降低静止误差。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `200.0` |
| Unit | `Hz` |

### `2019h`: HD Derivative-Integral Gain（HD 微分-积分增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2019` |
| Description | VarCom - `KNLIV`。HD 控制中等效于 PID D 和 I 的参数。用于 HD 控制环以同时降低误差和稳态误差，并提高控制刚度。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `400.0` |
| Unit | `Hz` |

### `201Ah`: HD Proportional Gain（HD 比例增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `201A` |
| Description | VarCom - `KNLP`。HD 控制中等效于 PID P 的参数。用于 HD 控制环以降低位置误差。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `400.0` |
| Unit | `Hz` |

### `201Bh`: HD Global Gain（HD 全局增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `201B` |
| Description | VarCom - `KNLUSERGAIN`。HD 自适应增益缩放系数。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.5` |
| Lower Limit | `0.1` |
| Upper Limit | `3.0` |
| Unit | - |

### `201Ch`: Position Acceleration Feedforward to Current（位置加速度到电流的前馈）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `201C` |
| Description | VarCom - `KPAFRC`。位置加速度到电流环的前馈。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `-1000.0` |
| Upper Limit | `1000.0` |
| Unit | - |

### `201Dh`: Position Acceleration Feedforward（位置加速度前馈）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `201D` |
| Description | VarCom - `KPAFRV`。线性位置控制器的加速度前馈。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `-1000.0` |
| Upper Limit | `1000.0` |
| Unit | - |

### `201Eh`: Position Derivative Gain（位置微分增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `201E` |
| Description | VarCom - `KPD`。位置控制器微分（KD）增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `1000.0` |
| Unit | - |

### `201Fh`: Position Proportional Adaptive Gain（位置比例自适应增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `201F` |
| Description | VarCom - `KPE`。位置比例自适应增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `4.0` |
| Unit | - |

### `2020h`: Position Integral Gain（位置积分增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2020` |
| Description | VarCom - `KPI`。位置控制器积分增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `1000.0` |
| Unit | `Hz` |

### `2021h`: Position Integral Saturation Output（位置积分饱和输出）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2021` |
| Description | VarCom - `KPISATOUT`。位置积分输出饱和。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | `CAN user velocity units` |

### `2022h`: Position Proportional Gain（位置比例增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2022` |
| Description | VarCom - `KPP`。线性位置控制器的比例增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `1200.0` |
| Unit | - |

### `2023h`: Position Velocity Feedforward（位置速度前馈）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2023` |
| Description | VarCom - `KPVFR`。位置控制速度前馈。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `-1000.0` |
| Upper Limit | `1000.0` |
| Unit | - |

### `2024h`: Motor Type（电机类型）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2024` |
| Description | VarCom - `MOTORTYPE`。电机类型。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x2` |
| Unit | - |

### `2025h`: Velocity Feedforward Ratio（速度前馈比例）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2025` |
| Description | VarCom - `KVFR`。速度前馈比例。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `1.0` |
| Unit | - |

### `2026h`: Velocity Integral Gain（速度积分增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2026` |
| Description | VarCom - `KVI`。速度积分增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `200000.0` |
| Unit | `Hz` |

### `2027h`: Velocity Proportional Gain（速度比例增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2027` |
| Description | VarCom - `KVP`。速度比例增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `1000000.0` |
| Unit | - |

### `2028h`: Mechanical Angle（机械角度）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2028` |
| Description | VarCom - `MECHANGLE`。电机在一转内的实际位置。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | `65536/Cycle` |

### `2029h`: Motor Encoder Type（电机编码器类型）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2029` |
| Description | VarCom - `MENCTYPE`。电机编码器类型。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x000B` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x000B` |
| Unit | - |

### `202Ah`: Motor Encoder Index Position（电机编码器索引位置）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `202A` |
| Description | VarCom - `MENCZPOS`。编码器索引位置。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0078` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0167` |
| Unit | `electrical degree` |

### `202Bh`: Motor and Feedback Direction（电机与反馈方向）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `202B` |
| Description | VarCom - `MFBDIR`。电机和反馈的方向与极性。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x07` |
| Unit | - |

### `202Ch`: Position Command Move Low Pass Filter（位置命令运动低通滤波器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `202C` |
| Description | VarCom - `MOVESMOOTHLPFHZ`。位置命令运动的低通滤波器。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x1388` |
| Lower Limit | `0x000A` |
| Upper Limit | `0x1388` |
| Unit | - |

### `202Dh`: Motor Feedback Mode（电机反馈模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `202D` |
| Description | VarCom - `MFBMODE`。启用/禁用增量编码器的分辨率增强机制。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x01` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

### `202Eh`: Motor Foldback Status（电机折返状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `202E` |
| Description | VarCom - `MFOLD`。指示电机折返限制是否已降至应用电流限制以下。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | - |

### `202Fh`: Motor Foldback Delay Time（电机折返延迟时间）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `202F` |
| Description | VarCom - `MFOLDD`。电机折返延迟时间。该时间表示驱动器进入电机折返状态之前，系统电流可超过 Motor Continuous Current (`6075h`) 的持续时间。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `5.0` |
| Lower Limit | `1.0` |
| Upper Limit | `2400.0` |
| Unit | `second` |

### `2030h`: Motor Foldback Disable（电机折返禁用）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2030` |
| Description | VarCom - `MFOLDDIS`。启用/禁用电机折返保护。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `2031h`: Motor Foldback Recovery Time（电机折返恢复时间）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2031` |
| Description | VarCom - `MFOLDR`。电机折返的恢复时间。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `70.0` |
| Lower Limit | `5.0` |
| Upper Limit | `3600.0` |
| Unit | `second` |

### `2032h`: Motor Foldback Time Constant（电机折返时间常数）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2032` |
| Description | VarCom - `MFOLDT`。电机折返的时间常数。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `5.0` |
| Lower Limit | `1.0` |
| Upper Limit | `1200.0` |
| Unit | `second` |

### `2033h`: Motor Foldback Current（电机折返电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2033` |
| Description | VarCom - `MIFOLD`。由电机折返机制得出的电流限制。当 Motor Foldback Current (`2033h`) 低于 User Current Limit (`6072h`) 时，发生折返条件。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | `mA` |

### `206Ch`: Gravity Compensation（重力补偿）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `206C` |
| Description | VarCom - `IGRAV`。加到电流环命令中的值，用于补偿重力或类似的恒定干扰。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `mA` |

### `206Fh`: Encoder Index Position Feedback（编码器索引位置反馈）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `206F` |
| Description | VarCom - `INDEXPFB`。上电后首次检测到编码器索引时捕获的位置反馈。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user position units` |

### `2070h`: Input Inversion（输入反相）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2070` |
| Description | VarCom - `ININV`。每个数字输入的反相状态。先写入索引。向输入子索引写入值以执行输入反相。读取该值表示输入的反相状态。 |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Index（索引） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0001` |
| Lower Limit | `0x0001` |
| Upper Limit | `0x000B` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Value（值） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `2071h`: Dynanic Brake Current（动态制动电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2071` |
| Description | VarCom - `ISTOP`。动态制动过程中允许的最大电流。受 Drive Peak Current (`207Bh`) 限制。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x249F0` |
| Unit | `mA` |

### `2072h`: Phase U Actual Current（U 相实际电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2072` |
| Description | VarCom - `IU`。U 相（UVW 中）的实际电流。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `mA` |

### `2073h`: Phase U Current Offset（U 相电流偏移）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2073` |
| Description | VarCom - `IUOFFSET`。U 相（UVW 中）的电流偏移。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `mA` |

### `2074h`: Phase V Actual Current（V 相实际电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2074` |
| Description | VarCom - `IV`。V 相（UVW 中）的实际电流。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `mA` |

### `2075h`: Phase V Current Offset（V 相电流偏移）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2075` |
| Description | VarCom - `IVOFFSET`。V 相（UVW 中）的电流偏移。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `mA` |

### `2076h`: Zero Procedure Current（ZERO 过程电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2076` |
| Description | VarCom - `IZERO`。ZERO (`20DFh`) 过程使用的电流。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `DIPEAK` |
| Unit | `mA` |

### `2077h`: Position Integral Saturation Input（位置积分饱和输入）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2077` |
| Description | VarCom - `KPISATIN`。位置积分输入饱和。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `10000.0` |
| Unit | - |

### `2078h`: Limit Switch Negative Status（负向限位开关状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2078` |
| Description | VarCom - `LIMSWITCHNEG`。负方向硬件限位开关的状态，由输入定义。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `2079h`: Limit Switch Positive Status（正向限位开关状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2079` |
| Description | VarCom - `LIMSWITCHPOS`。正方向硬件限位开关的状态，由输入定义。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `207Ah`: Load to Motor Inertia Ratio（负载与电机惯量比）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `207A` |
| Description | VarCom - `LMJR`。负载惯量与电机惯量之比。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `600.0` |
| Unit | - |

### `207Bh`: Drive Peak Current（驱动器峰值电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `207B` |
| Description | VarCom - `DIPEAK`。驱动器额定峰值电流（正弦峰值）。由硬件定义。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | Hardware-dependent |
| Lower Limit | Hardware-dependent |
| Upper Limit | Hardware-dependent |
| Unit | `mA` |

### `207Ch`: Drive Continuous Current（驱动器连续电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `207C` |
| Description | VarCom - `DICONT`。驱动器连续额定电流（正弦峰值）。由硬件定义。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | Hardware-dependent |
| Lower Limit | Hardware-dependent |
| Upper Limit | Hardware-dependent |
| Unit | `mA` |

### `207Dh`: Motor Pitch（电机节距）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `207D` |
| Description | VarCom - `MPITCH`。直线电机的节距。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000020` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0x000186A0` |
| Unit | `mm` |

### `207Eh`: Motor Poles（电机极数）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `207E` |
| Description | VarCom - `MPOLES`。电机中单个磁极（不是极对）的数量。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0002` |
| Lower Limit | `0x0002` |
| Upper Limit | `0x0050` |
| Unit | `poles` |

### `207Fh`: Motor Resistance（电机电阻）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `207F` |
| Description | VarCom - `MR`。电机电阻。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `10.0` |
| Unit | `ohm` |

### `2080h`: Motor Resolver Poles（电机旋变极数）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2080` |
| Description | VarCom - `MRESPOLES`。旋变反馈设备中的单个极数。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0002` |
| Lower Limit | `0x0002` |
| Upper Limit | `0x0050` |
| Unit | `poles` |

### `2081h`: Motor Rated Torque（电机额定转矩）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2081` |
| Description | 电机额定转矩。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x000007D0` |
| Lower Limit | `0x00000001` |
| Upper Limit | `0xFFFFFFFF` |
| Unit | `mN·m` |

### `2082h`: Current KFF Gain（电流 KFF 增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2082` |
| Description | VarCom - `KCFF`。电流控制器前馈增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `100.0` |
| Unit | - |

### `2083h`: Torque Commutation Angle Advance at Motor Continuous Current（电机连续电流下的转矩换相角提前）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2083` |
| Description | Varcom - `MTANGLC`。电机连续电流额定值下，与转矩相关的换相角提前值。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x002D` |
| Unit | `degree` |

### `2084h`: Torque Commutation Angle Advance at Motor Peak Current（电机峰值电流下的转矩换相角提前）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2084` |
| Description | Varcom - `MTANGLP`。电机峰值电流下，与转矩相关的换相角提前值。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x002D` |
| Unit | `degree` |

### `2085h`: Velocity Commutation Angle Advance at Motor Maximum Speed（电机最高速度下的速度换相角提前）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2085` |
| Description | Varcom - `MVANGLF`。电机以最高速度运行时要使用的、与速度相关的换相角提前值。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x005A` |
| Unit | `degree` |

### `2086h`: Velocity Commutation Angle Advance at Motor Maximum Speed/2（电机最高速度/2 下的速度换相角提前）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2086` |
| Description | Varcom - `MVANGLH`。电机以最高速度/2 运行时要使用的、与速度相关的换相角提前值。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x005A` |
| Unit | `degree` |

### `2087h`: HD Spring Filter（HD 弹簧滤波器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2087` |
| Description | VarCom - `NLAFFLPFHZ`。与 HD Flexibility Compensation (`208Fh`) 配合使用，用于降低加速度突变（jerk）对负载引起的振动，并降低跟踪误差；也可用于最小化超调和稳定时间。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x1B58` |
| Lower Limit | `0x000A` |
| Upper Limit | `0x1B58` |
| Unit | `Hz` |

### `2088h`: Position Backup（位置备份）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2088` |
| Description | VarCom - `PFBBACKUP`。读取由 Position Backup 过程保存到非易失性存储器中的位置值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user position units` |

### `2089h`: Position Backup Mode（位置备份模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2089` |
| Description | VarCom - `PFBBACKUPMODE`。启用和禁用位置备份过程。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `208Ah`: HD Maximum Adaptive Gain（HD 最大自适应增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `208A` |
| Description | VarCom - `NLMAXGAIN`。自动整定会根据编码器分辨率自动设置该增益。这是推荐值。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.6` |
| Lower Limit | `1.0` |
| Upper Limit | `5.0` |
| Unit | - |

### `208Bh`: HD Current Filter - Second Notch Filter Bandwidth（HD 电流滤波器 - 第二陷波滤波器带宽）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `208B` |
| Description | VarCom - `NLNOTCH2BW`。在 HD 控制环中使用，用于定义引起系统振动的高频的宽度（锐度）。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x01F4` |
| Unit | `Hz` |

### `208Ch`: HD Current Filter - Second Notch Filter Center（HD 电流滤波器 - 第二陷波滤波器中心）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `208C` |
| Description | VarCom - `NLNOTCH2CENTER`。在 HD 控制环中使用，用于阻断另一个引起系统振动的高频。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0064` |
| Lower Limit | `0x0064` |
| Upper Limit | `0x2710` |
| Unit | `Hz` |

### `208Dh`: Emergency or Controlled Stop Current Limit（急停或受控停止电流限制）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `208D` |
| Description | VarCom - `ESTOPILIM`。急停或受控停止期间的电流限制。表示为 User Current Limit (`6073h`) 的系数。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0010000000475` |
| Upper Limit | `1.0` |
| Unit | - |

### `208Eh`: Position Command（位置命令）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `208E` |
| Description | VarCom - `PCMD`。位置命令的值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user position units` |

### `208Fh`: HD Flexibility Compensation（HD 柔性补偿）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `208F` |
| Description | VarCom - `NLPEAFF`。与 HD Spring Filter (`2087h`) 配合使用，用于降低加速度突变（jerk）对负载引起的振动，并降低跟踪误差；也可用于最小化超调和稳定时间。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `200000.0` |
| Unit | `Hz` |

### `2090h`: Homing Status（回零状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2090` |
| Description | VarCom - `HOMESTATE`。指示回零过程的状态。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

### `2091h`: HD Acceleration/Deceleration Spring Filter Gain（HD 加速/减速弹簧滤波器增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2091` |
| Description | VarCom - `NLPEDFFRATIO`。确定加速/减速弹簧滤波器增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `1.99899995327` |
| Unit | - |

### `2095h`: Position Offset（位置偏移）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2095` |
| Description | VarCom - `PBFOFFSET`。加到内部累计位置计数器上的反馈偏移，用于给出位置 (`6064h`) 的实际值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

### `2096h`: HD Anti-Vibration 1 Filter - Center Frequency（HD 防振 1 滤波器 - 中心频率）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2096` |
| Description | VarCom - `NLANTIVIBHZ`。HD 位置控制环防振模块 1 滤波器中心频率。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `400.000030518` |
| Lower Limit | `5.0` |
| Upper Limit | `400.0` |
| Unit | `Hz` |

### `2097h`: HD Anti-Vibration 2 Filter - Center Frequency（HD 防振 2 滤波器 - 中心频率）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2097` |
| Description | VarCom - `NLANTIVIBHZ2`。HD 位置控制环防振模块 2 滤波器中心频率。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `400.000030518` |
| Lower Limit | `5.0` |
| Upper Limit | `400.0` |
| Unit | `Hz` |

### `2099h`: Current Level 1 for Digital Output Definition（数字输出定义的电流等级 1）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2099` |
| Description | VarCom - `OUTILVL1`。用于控制数字输出的条件中的第一个电流等级。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x000249F0` |
| Unit | `mA` |

### `209Ah`: Current Level 2 for Digital Output Definition（数字输出定义的电流等级 2）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `209A` |
| Description | VarCom - `OUTILVL2`。用于控制数字输出的条件中的第二个电流等级。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x000249F0` |
| Unit | `mA` |

### `209Bh`: Output Inversion（输出反相）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `209B` |
| Description | VarCom - `OUTINV`。每个数字输出的反相状态。先写入索引。然后向输出索引写入值以执行输出反相。读取该值表示数字输出的反相状态。 |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x02` |
| Upper Limit | `0x02` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Index（索引） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0001` |
| Lower Limit | `0x0001` |
| Upper Limit | `0x0007` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Value（值） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `209Ch`: Output Mode（输出模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `209C` |
| Description | VarCom - `OUTMODE`。定义将激活指定数字输出的条件。先写入输出索引，然后向对应输出索引写入功能。功能码：`0` = Idle（空闲）；`1` = Active (enabled)（激活/使能）；`2` = Brake release signal（制动释放信号）；`3` = Alarm for any fault（任意故障报警）；`4` = In position indication matching INPOS（与 INPOS 匹配的到位指示）；`5` = Stopped indication (matching STOPPED=2)（停止指示，与 STOPPED=2 匹配）；`6` = Foldback indication (motor or drive) (fault or FOLD)（电机或驱动器折返指示，故障或 FOLD）；`7` = Average current exceeds OUTILVL1（平均电流超过 OUTILVL1）；`8` = Average current is above OUTILVL1 and below OUTILVL2（平均电流高于 OUTILVL1 且低于 OUTILVL2）；`9` = Velocity exceeds OUTVLVL1（速度超过 OUTVLVL1；当速度超过 OUTVLVL1 设定等级时输出激活）；`10` = Velocity is above OUTVLVL1 and below OUTVLVL2（速度高于 OUTVLVL1 且低于 OUTVLVL2；当速度高于 OUTVLVL1 设定等级且低于 OUTVLVL2 设定等级时输出激活）；`11` = Position (PFB) is above OUTPLVL1（位置 PFB 高于 OUTPLVL1；当位置超过 OUTPLVL1 设定等级时输出激活）；`12` = Position (PFB) is above OUTPLVL1 and below OUTPLVL2（位置 PFB 高于 OUTPLVL1 且低于 OUTPLVL2；当位置高于 OUTPLVL1 设定等级且低于 OUTPLVL2 设定等级时输出激活）；`13` = Encoder battery low voltage fault（编码器电池低电压故障）；`14` = Warning on（警告开启）；`15` = Faults or disabled（故障或已禁用）；`16` = Encoder battery low voltage warning（编码器电池低电压警告）；`17` = Phase find succeeded（相位查找成功）；`18` = Over-current fault exists（存在过流故障）；`19` = Over-voltage fault exists（存在过压故障）；`20` = Under-voltage fault exists（存在欠压故障）；`21` = Phase find required（需要相位查找）；`22` = Alarm for any fault except phase find failure（除相位查找失败以外的任意故障报警）；`23` = Homing complete（回零完成）；`24` = Encoder simulation index（编码器仿真索引）；`25` = Zero position after homing（回零后零位）；`27` = PCOM module 1 output（PCOM 模块 1 输出）；`28` = PCOM module 2 output（PCOM 模块 2 输出）。 |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Sub-Index | `000` |
| Description | Number of Entries（条目数量） |
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0002` |
| Lower Limit | `0x0002` |
| Upper Limit | `0x0002` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `001` |
| Description | Output Index（输出索引） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0001` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

| 项目 | 值 |
|---|---|
| Sub-Index | `002` |
| Description | Function Code（功能码） |
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

### `209Dh`: Position Level 1 for Digital Output Definition（数字输出定义的位置等级 1）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `209D` |
| Description | VarCom - `OUTPLVL1`。用于控制数字输出的条件中的第一个位置值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user position units` |

### `209Eh`: Position Level 2 for Digital Output Definition（数字输出定义的位置等级 2）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `209E` |
| Description | VarCom - `OUTPLVL2`。用于控制数字输出的条件中的第二个位置值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user position units` |

### `209Fh`: Velocity Level 1 for Digital Output Definition（数字输出定义的速度等级 1）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `209F` |
| Description | VarCom - `OUTVLVL1`。用于控制数字输出的条件中的第一个速度值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user velocity units` |

### `20A0h`: Velocity Level 2 for Digital Output Definition（数字输出定义的速度等级 2）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A0` |
| Description | VarCom - `OUTVLVL2`。用于控制数字输出的条件中的第二个速度值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user velocity units` |

### `20A1h`: Over-Voltage Threshold（过压阈值）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A1` |
| Description | VarCom - `OVTHRESH`。检测母线过压的阈值等级。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `V` |

### `20A2h`: Software Enable Status（软件使能状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A2` |
| Description | VarCom - `SWEN`。指示软件使能的状态。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

### `20A3h`: Position Loop Position Error（位置环位置误差）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A3` |
| Description | VarCom - `PELOOP`。位置环使用的位置误差值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `CAN user position units` |

### `20A4h`: Phase Find Command（相位查找命令）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A4` |
| Description | VarCom - `PHASEFIND`。启动一个用于初始化增量编码器系统换相的过程。写入 `1` 可启动相位查找命令。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

### `20A5h`: Forced Electrical Position（强制电角度位置）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A5` |
| Description | VarCom - `PHASEFINDANGLE`。一转内的位置。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | `65536/electrical cycle` |

### `20A6h`: Phase Find Gain（相位查找增益）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A6` |
| Description | VarCom - `PHASEFINDGAIN`。调整相位查找机制的增益。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `10.0` |
| Unit | - |

### `20A7h`: Phase Find Current（相位查找电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A7` |
| Description | VarCom - `PHASEFINDI`。调整相位查找机制的电流。受 Maximum Current (`6073h`) 限制。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `IMAX` |
| Unit | `mA` |

## 原 PDF 第 257 页

### `20A8h`: Phase Find Mode（相位查找模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A8` |
| Description | VarCom - `PHASEFINDMODE`。定义相位查找的换相方式。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `2` | 软启动。默认值。也称为 Wake-No-Shake 例程。 |
| `4` | 平滑启动。将换相角设置为 180 度，并逐步增大电流，直到检测到 1 个电角度的运动。 |
| `5` | 高转矩启动。将换相角设置为 180 度，并逐步增大电流，直到检测到 1 个电角度的运动。 |
| `11` | 手动换相。换相偏移由 Forced Electrical Position (`20A5h`) 的值定义。 |
| `12` | 回零。应用 `ZERO` 命令并使用得到的 `MPHASE`。支持带 Z 轴的系统。 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0002` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x000B` |
| Unit | - |

## 原 PDF 第 258 页

### `20A9h`: Phase Find Status（相位查找状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20A9` |
| Description | VarCom - `PHASEFINDST`。指示增量编码器换相相位查找过程的状态。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 未启动 |
| `1` | 正在运行 |
| `2` | 成功 |
| `3` | 失败 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

### `20AAh`: Phase Find Duration（相位查找持续时间）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20AA` |
| Description | VarCom - `PHASEFINDTIME`。限制软启动模式下相位查找 (`20A8h`) 的持续时间。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0064` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x2710` |
| Unit | `ms` |

## 原 PDF 第 259 页

### `20ABh`: Position Loop Controller Mode（位置环控制器模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20AB` |
| Description | VarCom - `POSCONTROLMODE`。定义位置环控制器的类型。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 线性控制环 |
| `1` | HD 控制环；仅用于向后兼容 |
| `2` | 采样率为 250 s 的 HD 控制环 |
| `5` | 采样率为 125 s 的 HD 控制环；建议所有新应用使用 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `20ACh`: Position Limiting Mode（位置限制模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20AC` |
| Description | VarCom - `POSLIMMODE`。启用/禁用软件位置限位。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

## 原 PDF 第 260 页

### `20ADh`: PRB Generator Frequency（PRB 发生器频率）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20AD` |
| Description | VarCom - `PRBFRQ`。定义 PRB 激励的频率。对于伪二进制噪声（`208Fh` 子索引 `1` = `0`、`1`），该对象不起作用。对于正弦波和方波发生器（`208Fh` 子索引 `1` = `2` 或 `208Fh` 子索引 `1` = `3`），该对象分别定义正弦波和方波发生器的频率。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `100.0` |
| Lower Limit | `0.0` |
| Upper Limit | `5000.0` |
| Unit | `Hz` |

## 原 PDF 第 261 页

### `20AEh`: PRB Generator Mode（PRB 发生器模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20AE` |
| Description | VarCom - `PRBMODE`。定义是否以及如何激活 PRB 信号发生器。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | PRB 发生器未激活 |
| `1` | PRB 发生器仅在记录期间激活 |
| `2` | PRB 发生器连续激活 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0002` |
| Unit | - |

## 原 PDF 第 262 页

### `20AFh`: PRB Generator Configuration（PRB 发生器配置）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20AF` |
| Description | VarCom - `PRBPARAM`。PRB 发生器配置。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

信号类型：

| 值 | 说明 |
|---|---|
| `0` | 8 bit 随机噪声 |
| `1` | 10 bit 随机噪声 |
| `2` | 正弦波 |
| `3` | 方波 |

Current Amplitude 受 Max Current (`6073h`) 限制。Velocity Amplitude 受 Max Profile Velocity (`607Fh`) 限制。Counter Period 相对于电流环更新率。

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x5` |
| Lower Limit | `0x5` |
| Upper Limit | `0x5` |
| Unit | - |

**子索引 `001`：Signal Type（信号类型）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0003` |
| Unit | - |

## 原 PDF 第 263 页

**子索引 `002`：Current Amplitude（电流幅值）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | CAN user current units |

**子索引 `003`：Velocity Amplitude（速度幅值）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | CAN user velocity units |

**子索引 `004`：Counter Period（计数器周期）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 264 页

**子索引 `005`：Config（配置）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `20B0h`: Position Command Generator Target Error（位置命令发生器目标误差）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B0` |
| Description | VarCom - `PTPTE`。运动轮廓期间的目标误差，即点到点运动中距目标位置的剩余距离。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | CAN user position units |

## 原 PDF 第 265 页

### `20B1h`: Position Command Generator Velocity（位置命令发生器速度）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B1` |
| Description | VarCom - `PTPVCMD`。位置命令轮廓的一阶导数，以速度单位表示。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | CAN user velocity units |

### `20B2h`: PWM Frequency（PWM 频率）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B2` |
| Description | VarCom - `PWMFRQ`。PWM 信号的频率。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `16.0` |
| Lower Limit | `0.0` |
| Upper Limit | `0.0` |
| Unit | `kHz` |

## 原 PDF 第 266 页

### `20B3h`: Gearing Mode（电子齿轮模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B3` |
| Description | VarCom - `GEARMODE`。电子齿轮源和方法。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x04` |
| Unit | - |

### `20B4h`: PWM Saturation Ratio（PWM 饱和比）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B4` |
| Description | 电流在一个换相周期内处于饱和状态的持续时间。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.5` |
| Lower Limit | `0.5` |
| Upper Limit | `1.5` |
| Unit | - |

## 原 PDF 第 267 页

### `20B5h`: In Position Indication（到位指示）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B5` |
| Description | VarCom - `INPOS`。指示位置误差是否在允许容差范围内。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 未到位 |
| `1` | 已到位 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `20B6h`: Hardware Position External (DSP)（外部硬件位置 (DSP)）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B6` |
| Description | VarCom - `HWPEXTMACHN`。由外部反馈设备 (DSP) 测得的位置；来自机器接口连接器的脉冲与方向输入的 32 bit 计数器。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | CAN: Yes；ECT: TxPDO |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 268 页

### `20B8h`: Fault Relay Status（故障继电器状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B8` |
| Description | VarCom - `RELAY`。故障继电器的状态。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 继电器断开 |
| `1` | 继电器闭合 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

### `20B9h`: Fault Relay Mode（故障继电器模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20B9` |
| Description | VarCom - `RELAYMODE`。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 发生故障时继电器断开 |
| `1` | 禁用时继电器断开 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

## 原 PDF 第 269 页

### `20BAh`: Remote Hardware Enable Status（远程硬件使能状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20BA` |
| Description | VarCom - `REMOTE`。外部硬件使能输入的状态。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | Remote enable 输入关闭。 |
| `1` | Remote enable 输入打开。 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

### `20BBh`: Resolver Amplitude Range（旋变幅值范围）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20BB` |
| Description | VarCom - `RESAMPLRANGE`。旋变正弦/余弦信号偏差的可接受范围，以百分比表示。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0023` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0064` |
| Unit | percentage |

## 原 PDF 第 270 页

### `20BCh`: Resolver Conversion Bandwidth（旋变转换带宽）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20BC` |
| Description | VarCom - `RESBW`。旋变转换带宽。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x012C` |
| Lower Limit | `0x00C8` |
| Upper Limit | `0x0320` |
| Unit | `Hz` |

### `20BDh`: Save/Load Status（保存/加载状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20BD` |
| Description | 保存/加载状态。将所有系统配置变量从工作 RAM 复制到非易失性存储器。写入 `01` 可启动该命令。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 271 页

### `20BEh`: Sine/Cosine Calibration Command（正弦/余弦校准命令）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20BE` |
| Description | VarCom - `SININIT`。激活用于校准正弦编码器或旋变正弦和余弦信号的过程。该校准用于降低正弦编码器或旋变读数中的谐波误差。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `20BFh`: Sine/Cosine Calibration Mode（正弦/余弦校准模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20BF` |
| Description | VarCom - `SININITMODE`。启用/禁用上电时对正弦编码器或旋变正弦和余弦信号的自动校准。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 272 页

### `20C0h`: Sine/Cosine Calibration Status（正弦/余弦校准状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C0` |
| Description | VarCom - `SININITST`。正弦编码器或旋变校准过程的状态。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

### `20C1h`: Sine/Cosine Calibration Parameters (CAN only)（正弦/余弦校准参数（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C1` |
| Description | VarCom - `SINPARAM`。返回旋变正弦和余弦信号校准参数。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 273 页

### `20C2h`: Synchronization Mode（同步模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C2` |
| Description | VarCom - `SYNCSOURCE`。设置用于将驱动器时钟同步到外部同步信号的方法。当驱动器检测到来自 EtherCAT 或 CANopen 的 `SYNC` 信号时，会分别自动将 `SYNCSOURCE` 设置为 `5` 或 `6`。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 禁用；无同步 |
| `1` | 基于快速数字输入 5，将驱动器时钟同步到控制器 |
| `2` | 基于快速数字输入 6，将驱动器时钟同步到控制器 |
| `3` | 基于脉冲差分输入（Pulse & Direction）同步驱动器时钟 |
| `4` | 同步信号源为来自 Machine I/F 的脉冲输入 |
| `5` | 在 EtherCAT 驱动器（EC 和 EB 型号）中自动设置。只读。 |
| `6` | 在 CAN 驱动器（AF 型号）中自动设置。只读。 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0005` |
| Unit | - |

## 原 PDF 第 274 页

### `20C3h`: Tracking Factor（跟踪因子）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C3` |
| Description | VarCom - `TF`。使用 PDFF 速度控制器进行跟踪时的微分因子。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0064` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x00C8` |
| Unit | percentage |

### `20C4h`: Motor Over-Temperature（电机过温）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C4` |
| Description | VarCom - `THERM`。电机温控器输入的状态，用于指示过温条件。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 温控器输入闭合（正常），或当 Motor Over-Temperature Mode (`20C6h`) = `3` 时被忽略。 |
| `1` | 温控器输入断开，表示过热。 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 275 页

### `20C5h`: Motor Over-Temperature Clear Fault Level（电机过温故障清除等级）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C5` |
| Description | VarCom - `THERMCLEARLEVEL`。清除电机过温故障的等级。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000064` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x000F4240` |
| Unit | ohm |

### `20C6h`: Motor Over-Temperature Mode（电机过温模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C6` |
| Description | VarCom - `THERMODE`。定义驱动器对过温故障的响应方式。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 立即禁用驱动器 |
| `3` | 忽略温控器输入 |
| `4` | 仅发出警告 |
| `5` | 发出警告。如果该条件在 Motor Over-Temperature Time (`20C8h`) 后仍持续，则发出故障 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0005` |
| Unit | - |

## 原 PDF 第 276 页

### `20C7h`: Motor Temperature（电机温度）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C7` |
| Description | VarCom - `THERMREADOUT`。电机温度。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | ohm |

### `20C8h`: Motor Over-Temperature Time（电机过温时间）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C8` |
| Description | VarCom - `THERMTIME`。检测到电机过温后，到驱动器断开故障继电器之前的秒数。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x001E` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x012C` |
| Unit | second |

## 原 PDF 第 277 页

### `20C9h`: Motor Over-Temperature Fault Level（电机过温故障等级）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20C9` |
| Description | VarCom - `THERMTRIPLEVEL`。电机过温故障等级。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000096` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x000F4240` |
| Unit | ohm |

### `20CAh`: Motor Over-Temperature Type（电机过温类型）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20CA` |
| Description | VarCom - `THERMTYPE`。电机温度传感器的类型。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 正温度系数 (PTC) |
| `1` | 负温度系数 (NTC) |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |


## 原 PDF 第 278 页

### `20CBh`: Tamagawa Multi-Turn Reset（Tamagawa 多圈复位）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20CB` |
| Description | VarCom - `TMTURNRESET`。复位 Tamagawa 多圈编码器的计数器。写入 `01` 可启动该命令。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

### `20CCh`: Run Time (CAN only)（运行时间（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20CC` |
| Description | VarCom - `TRUN`。驱动器自生产以来累计经过的总运行时间。不能复位。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 279 页

### `20CDh`: Under-Voltage Mode（欠压模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20CD` |
| Description | VarCom - `UVMODE`。定义驱动器对欠压故障的响应方式。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 无论驱动器处于禁用还是使能状态，立即锁存故障。 |
| `1` | 如果驱动器已使能，则发出警告；如果驱动器已禁用，则忽略。 |
| `2` | 如果驱动器已使能，则发出警告，然后等待 Under-Voltage Time (`20D0h`) 后锁存故障；如果驱动器已禁用，则忽略。 |
| `3` | 如果驱动器已禁用，则发出警告；如果驱动器已使能，则立即锁存故障。 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0003` |
| Unit | - |

## 原 PDF 第 280 页

### `20CEh`: Under-Voltage Recovery Mode（欠压恢复模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20CE` |
| Description | VarCom - `UVRECOVER`。定义驱动器从欠压故障恢复的方式。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 欠压条件清除后，通过将驱动器从禁用切换到使能状态来恢复。 |
| `1` | 欠压条件清除后自动恢复。 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `20CFh`: Under-Voltage Threshold 64（欠压阈值 64）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20CF` |
| Description | VarCom - `UVTHRESH`。用于检测欠压条件的等级。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | Hardware-dependent |
| Lower Limit | `0x0014` |
| Upper Limit | `0x0190` |
| Unit | `V` |

## 原 PDF 第 281 页

### `20D0h`: Under-Voltage Time（欠压时间）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D0` |
| Description | VarCom - `UVTIME`。在 Under-Voltage Mode (`20CDh`) = `2` 时，欠压警告显示后到被锁存为故障之前的时间。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x001E` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x012C` |
| Unit | second |

### `20D1h`: Bus Voltage (DC)（母线电压 (DC)）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D1` |
| Description | VarCom - `VBUS`。用于电流控制器设计的驱动器母线电压。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0140` |
| Lower Limit | `0x000A` |
| Upper Limit | `0x0352` |
| Unit | `V` |

## 原 PDF 第 282 页

### `20D3h`: Velocity Error（速度误差）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D3` |
| Description | VarCom - `VE`。速度环的速度误差。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | CAN user velocity units |

### `20D4h`: Velocity Loop Controller（速度环控制器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D4` |
| Description | VarCom - `VELCONTROLMODE`。定义速度环控制器的类型。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | PI 控制器（使用 `2026h`、`2027h`） |
| `1` | PDFF 控制器（使用 `2025h`、`2026h`、`2027h`） |
| `2` | 标准极点配置控制器（使用 `2037h`、`2039h`、`2010h`、`207Ah`、`20C3h`） |
| `7` | 带积分器的 HD 速度环（使用 `2017h`、`201Ah`） |
| `3,4,5,6` | 不供用户使用 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x07` |
| Unit | - |

## 原 PDF 第 283 页

### `20D5h`: Velocity Design Conversion (CAN only)（速度设计转换（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D5` |
| Description | VarCom - `VELDESIGN`。速度设计结构。返回内部速度控制器的转换结果；该内部速度控制器由标准速度控制模式之一设置，并转换为通用扩展多项式控制器结构。仅适用于线性位置控制器。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `20D6h`: Velocity Filter Mode（速度滤波器模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D6` |
| Description | VarCom - `VELFILTMODE`。定义从位置反馈中提取速度信号的滤波器类型。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 无滤波器 |
| `1` | 一阶滤波器 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0001` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0003` |
| Unit | - |

## 原 PDF 第 284 页

### `20D7h`: Drive Version (CAN only)（驱动器版本（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D7` |
| Description | VarCom - `VER`。驱动器固件版本。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `20D8h`: Velocity Loop Output Filter（速度环输出滤波器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D8` |
| Description | VarCom - `VF`。用户定义的速度环输出滤波器。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x08` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 285 页

**子索引 `001`：Polynom_Term_1**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `002`：Polynom_Term_2**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `003`：Polynom_Term_3**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 286 页

**子索引 `004`：Polynom_Term_4**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `005`：Polynom_Term_5**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `006`：Polynom_Term_6**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 287 页

**子索引 `007`：Polynom_Term_7**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `008`：Term_Execute**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

## 原 PDF 第 288 页

### `20D9h`: Velocity Loop Input Filter（速度环输入滤波器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20D9` |
| Description | VarCom - `VFI`。用户定义的速度环输入滤波器。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x08` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

**子索引 `001`：Polynom_Term_1**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |


## 原 PDF 第 289 页

**子索引 `002`：Polynom_Term_2**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `003`：Polynom_Term_3**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `004`：Polynom_Term_4**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 290 页

**子索引 `005`：Polynom_Term_5**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `006`：Polynom_Term_6**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `007`：Polynom_Term_7**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 291 页

**子索引 `008`：Term_Execute**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x1` |
| Unit | - |

### `20DAh`: Advanced Pole Placement H Polynomial（高级极点配置 H 多项式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20DA` |
| Description | VarCom - `VH`。扩展速度控制器 H-polynomial。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0D` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 292 页

**子索引 `001`：manu_spec_Vh_Polynom_ Term_1**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `002`：manu_spec_Vh_Polynom_ Term_2**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `003`：manu_spec_Vh_Polynom_ Term_3**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 293 页

**子索引 `004`：manu_spec_Vh_Polynom_ Term_4**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `005`：manu_spec_Vh_Polynom_ Term_5**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `006`：manu_spec_Vh_Polynom_ Term_6**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 294 页

**子索引 `007`：manu_spec_Vh_Polynom_ Term_7**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `008`：manu_spec_Vh_Polynom_ Term_8**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `009`：manu_spec_Vh_Polynom_ Term_9**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 295 页

**子索引 `010`：manu_spec_Vh_Polynom_ Term_10**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `011`：manu_spec_Vh_Polynom_ Term_11**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `012`：manu_spec_Vh_Polynom_ Term_12**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 296 页

**子索引 `013`：manu_spec_Vh_Polynom_ Term_Execute**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

### `20DBh`: Advanced Pole Placement R Polynomial（高级极点配置 R 多项式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20DB` |
| Description | VarCom - `VR`。扩展速度控制器 R-polynomial。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0B` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 297 页

**子索引 `001`：Polynom_Term_1**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `002`：Polynom_Term_2**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `003`：Polynom_Term_3**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 298 页

**子索引 `004`：Polynom_Term_4**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `005`：Polynom_Term_5**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `006`：Polynom_Term_6**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 299 页

**子索引 `007`：Polynom_Term_7**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `008`：Polynom_Term_8**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `009`：Polynom_Term_9**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 300 页

**子索引 `010`：Polynom_Term_10**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

**子索引 `011`：Term_Execute**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

### `20DCh`: Wake No Shake Status (CAN only)（Wake No Shake 状态（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20DC` |
| Description | VarCom - `WNSERR`。Wake No Shake 状态。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 301 页

### `20DDh`: Display Warnings (CAN only)（显示警告（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20DD` |
| Description | VarCom - `WRN`。列出自上次清除缓冲区以来发生的警告。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `20DEh`: External Encoder Resolution（外部编码器分辨率）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20DE` |
| Description | VarCom - `XENCRES`。外部编码器的分辨率。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000800` |
| Lower Limit | `0x00000064` |
| Upper Limit | `0x00989680` |
| Unit | - |

## 原 PDF 第 302 页

### `20DFh`: Zeroing Command（调零命令）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20DF` |
| Description | VarCom - `ZERO`。激活 Zeroing 模式，通过在两相中施加固定电流来锁定转子位置。这有助于确定带旋变或绝对值编码器的电机上的换相偏移。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 303 页

### `20E0h`: Input Mode（输入模式）

## 原 PDF 第 304 页

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E0` |
| Description | VarCom - `INMODE`。定义每个数字输入的功能。先写入输入索引，然后写入要分配给相应输入索引的功能值。 |
| Object Code | Array |
| Data Type | `UNSIGNED16` |

可能值：

| 值 | 说明 |
|---|---|
| `0` | 空闲 |
| `1` | Remote enable |
| `2` | 清除故障 |
| `3` | Phase lock loop (`PLL`) 同步 |
| `4` | 急停，激活 Active Disable |
| `5` | 正向限位开关 |
| `6` | 负向限位开关 |
| `7` | 保留 |
| `8` | 原点开关 |
| `9` | 脚本触发 |
| `10` | 脚本 bit 0 |
| `11` | 脚本 bit 1 |
| `12` | 脚本 bit 2 |
| `13` | 脚本 bit 3 |
| `14` | 脚本 bit 4 |
| `15` | 保留 |
| `16` | 保留 |
| `17` | Gearing pulse signal，仅用于数字输入 5 |
| `18` | Gearing direction signal，仅用于数字输入 6 |
| `19` 至 `25` | 保留 |
| `26` | 回零命令 |
| `27` | Touch probe 1 |
| `28` | 保留 |
| `29` | 保留 |
| `30` | 保持并恢复运动 |
| `31` | 保留 |
| `32` | 驱动器使能时切换运行模式 |
| `33` | 显式设置 `OPMODE` 4 和 `ENCFOLLOWER` 1 |
| `34` | 显式设置 `OPMODE` 4 和 `ENCFOLLOWER` 2 |
| `35` | 显式设置 `OPMODE` 4 和 `ENCFOLLOWER` 3 |
| `36` | 显式设置 `OPMODE` 4 和 `ENCFOLLOWER` 4 |
| `37` | 显式设置 `OPMODE` 4 和 `ENCFOLLOWER` 5 |
| `38` | 以速度 `JOGSPD1` 将电机 JOG 到正方向 |
| `39` | 以速度 `-JOGSPD1` 将电机 JOG 到负方向 |
| `40` | 以速度 `JOGSPD2` 将电机 JOG 到正方向 |
| `41` | 以速度 `-JOGSPD2` 将电机 JOG 到负方向 |

## 原 PDF 第 305 页

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x02` |
| Upper Limit | `0x02` |
| Unit | - |

**子索引 `001`：Input Index（输入索引）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0001` |
| Lower Limit | `0x0001` |
| Upper Limit | `0x000B` |
| Unit | - |

**子索引 `002`：Function Code（功能代码）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0001` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0029` |
| Unit | - |

## 原 PDF 第 306 页

### `20E1h`: Rotary Address Switch（旋转地址开关）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E1` |
| Description | VarCom - `ADDR`。定义驱动器通信地址的旋转开关位置。 |
| Object Code | Variable |
| Data Type | `VISIBLE_STRING` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `20E2h`: Test Digital Display（测试数码显示）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E2` |
| Description | VarCom - `DISPLAYTEST`。测试驱动器前面板上的数码显示。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

## 原 PDF 第 307 页

### `20E3h`: Encoder Simulation Mode（编码器仿真模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E3` |
| Description | VarCom - `ENCOUTMODE`。指示编码器仿真的状态。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0x0001` |
| Unit | - |

### `20E4h`: Encoder Simulation Line Resolution（编码器仿真线数分辨率）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E4` |
| Description | VarCom - `ENCOUTRES`。编码器仿真输出的分辨率，以线数表示。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000800` |
| Lower Limit | `0xFF676980` |
| Upper Limit | `0x00989680` |
| Unit | Number of lines |

## 原 PDF 第 308 页

### `20E5h`: Encoder Simulation Index Position（编码器仿真索引位置）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E5` |
| Description | VarCom - `ENCOUTZPOS`。编码器仿真输出的索引偏移值。 |
| Object Code | Variable |
| Data Type | `UNSIGNED32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x02625A00` |
| Unit | counts |

### `20E6h`: Recording Done（记录完成）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E6` |
| Description | VarCom - `RECDONE`。指示记录是否完成且数据是否可用。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0x01` |
| Unit | - |

## 原 PDF 第 309 页

### `20E7h`: Get Recorded Data (CAN only)（获取记录数据（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E7` |
| Description | VarCom - `GET`。获取使用记录机制捕获的记录数据。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x06` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

**子索引 `001`：Packet Select（数据包选择）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 310 页

**子索引 `002`：Domain**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `DOMAIN` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

**子索引 `003`：Data Length（数据长度）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `INTEGER16` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | - |

**子索引 `004`：Data Status（数据状态）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 311 页

**子索引 `005`：RT Data Ack**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

**子索引 `006`：NumOfChn**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 312 页

### `20E8h`: Trigger Recording (CAN only)（触发记录（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E8` |
| Description | VarCom - `RECTRIG`。触发记录。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x05` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

**子索引 `001`：Var**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `VISIBLE_STRING` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 313 页

**子索引 `002`：ThrsLvl**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `REAL32` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0` |
| Upper Limit | `0` |
| Unit | - |

**子索引 `003`：PreTrg**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

**子索引 `004`：EdgePlr**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 314 页

**子索引 `005`：Activate**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

### `20E9h`: Stop Recording (CAN only)（停止记录（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20E9` |
| Description | VarCom - `RECOFF`。停止活动记录。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 315 页

### `20EAh`: Record Command (CAN only)（记录命令（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20EA` |
| Description | VarCom - `RECORD`。记录实时值的命令。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x09` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

**子索引 `001`：Sample Time（采样时间）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 316 页

**子索引 `002`：Num Points（点数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0001` |
| Lower Limit | `0x0001` |
| Upper Limit | `0xFFFF` |
| Unit | - |

**子索引 `003`：Var1**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `VISIBLE_STRING` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

**子索引 `004`：Var2**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `VISIBLE_STRING` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 317 页

**子索引 `005`：Var3**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `VISIBLE_STRING` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

**子索引 `006`：Var4**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `VISIBLE_STRING` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

**子索引 `007`：Var5**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `VISIBLE_STRING` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 318 页

**子索引 `008`：Var6**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `VISIBLE_STRING` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

**子索引 `009`：Activate**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

### `20EBh`: Recording Status（记录状态）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20EB` |
| Description | VarCom - `RECING`。指示数据记录是否正在进行。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 319 页

### `20ECh`: Ready to Record（准备记录）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20EC` |
| Description | VarCom - `RECRDY`。指示记录机制的就绪状态。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | - |

### `20EEh`: Maximum Velocity for Drive and Motor（驱动器和电机最大速度）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20EE` |
| Description | VarCom - `VMAX`。驱动器和电机组合的最大速度。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | - |

## 原 PDF 第 320 页

### `20EFh`: Dead Time Compensation Minimal Level（死区补偿最小等级）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20EF` |
| Description | VarCom - `KCD`。开始补偿死区效应所需的最小电流水平。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `1.0` |
| Lower Limit | `0.0` |
| Upper Limit | `10.0` |
| Unit | - |

### `20F0h`: Maximum Current for Drive and Motor（驱动器和电机最大电流）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F0` |
| Description | VarCom - `IMAX`。驱动器和电机组合的最大电流限制。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x00000000` |
| Upper Limit | `0x000249F0` |
| Unit | `mA` |

## 原 PDF 第 321 页

### `20F2h`: Analog Input 1（模拟输入 1）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F2` |
| Description | VarCom - `ANIN1`。模拟输入 1 的值。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | CAN: Yes；ECT: TxPDO |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | `V` |

### `20F3h`: Analog Input 1 Deadband（模拟输入 1 死区）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F3` |
| Description | VarCom - `ANIN1DB`。模拟输入 1 的死区范围。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | `V` |

## 原 PDF 第 322 页

### `20F4h`: Analog Input 1 Current Scaling（模拟输入 1 电流缩放）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F4` |
| Description | VarCom - `ANIN1ISCALE`。来自输入 1 的模拟电流命令缩放值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `V` |

### `20F5h`: Analog Input 1 Low Pass Filter（模拟输入 1 低通滤波器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F5` |
| Description | VarCom - `ANIN1LPFHZ`。施加到模拟输入 1 的一阶滤波器的拐角频率。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x03E8` |
| Lower Limit | `0x000A` |
| Upper Limit | `0x2710` |
| Unit | `Hz` |

## 原 PDF 第 323 页

### `20F6h`: Analog Input 1 Offset（模拟输入 1 偏置）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F6` |
| Description | VarCom - `ANIN1OFFSET`。模拟输入 1 的偏置电压。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | `V` |

### `20F7h`: Analog Input 1 Velocity Scaling（模拟输入 1 速度缩放）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F7` |
| Description | VarCom - `ANIN1VSCALE`。来自输入 1 的模拟速度命令缩放值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00000000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `V` |

## 原 PDF 第 324 页

### `20F8h`: Analog Input 1 Zeroing（模拟输入 1 清零）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F8` |
| Description | VarCom - `ANIN1ZERO`。通过修改模拟偏置值将模拟输入 1 的值清零。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

### `20F9h`: Analog Input 2（模拟输入 2）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20F9` |
| Description | VarCom - `ANIN2`。模拟输入 2 的值。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read Only |
| PDO Mapping | CAN: Yes；ECT: TxPDO |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | `V` |

## 原 PDF 第 325 页

### `20FAh`: Analog Input 2 Deadband（模拟输入 2 死区）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20FA` |
| Description | VarCom - `ANIN2DB`。模拟输入 2 的死区范围。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | `V` |

### `20FBh`: Analog Input 2 Current Scaling（模拟输入 2 电流缩放）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20FB` |
| Description | VarCom - `ANIN2ISCALE`。来自输入 2 的模拟电流命令缩放值。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x80000000` |
| Upper Limit | `0x7FFFFFFF` |
| Unit | `V` |

## 原 PDF 第 326 页

### `20FCh`: Analog Input 2 Low Pass Filter（模拟输入 2 低通滤波器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20FC` |
| Description | VarCom - `ANIN2LPFHZ`。施加到模拟输入 2 的一阶滤波器的拐角频率。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x03E8` |
| Lower Limit | `0x000A` |
| Upper Limit | `0x2710` |
| Unit | `Hz` |


### `20FDh`: Analog Input 2 Offset（模拟输入 2 偏置）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20FD` |
| Description | VarCom - `ANIN2OFFSET`。模拟输入 2 的偏置电压。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | `V` |

## 原 PDF 第 327 页

### `20FFh`: Analog Input 2 Zeroing（模拟输入 2 清零）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `20FF` |
| Description | VarCom - `ANIN2ZERO`。通过修改模拟偏置值将模拟输入 2 的值清零。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |

## 原 PDF 第 328 页

### `2100h`: Analog Input 2 Mode（模拟输入 2 模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2100` |
| Description | VarCom - `ANIN2MODE`。定义模拟输入 2 的功能。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

可能值：

| 值 | 说明 |
|---|---|
| `-1` | 硬件定义双增益。`ANIN2` 未激活，`ANIN1` 具有 16 bit 分辨率，`ANIN2MODE` 为只读。 |
| `0` | 空闲。`ANIN2` 输入电压为只读。 |
| `1` | 双增益。需要在模拟输入之间连接外部跳线。 |
| `2` | 电流限制模式。第二个模拟输入限制电流命令。 |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0xFFFF` |
| Upper Limit | `0x0002` |
| Unit | - |

## 原 PDF 第 329 页

### `2103h`: Homing Command（回零命令）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2103` |
| Description | VarCom - `HOMECMD`。启动回零过程。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

### `2104h`: Current Level for Homing on Hard Stop（硬限位回零电流等级）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2104` |
| Description | VarCom - `HOMEIHARDSTOP`。检测到硬限位时的电流等级。当回零过程使用硬限位（而不是限位开关）进行方向反转时使用。 |
| Object Code | Variable |
| Data Type | `INTEGER32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 330 页

### `2106h`: Current Loop Compatibility Mode（电流环兼容模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2106` |
| Description | VarCom - `KCMODE`。电流控制环的类型。允许使用新固件版本，同时保持现有电流控制设置。 |
| Object Code | Variable |
| Data Type | `INTEGER16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x8000` |
| Upper Limit | `0x7FFF` |
| Unit | - |

### `2108h`: Position Command Moving Average Filter（位置命令移动平均滤波器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2108` |
| Description | VarCom - `MOVESMOOTHAVG`。移动平均滤波器。可应用于位置或速度参考命令，以平滑命令并将其整形成 S 曲线轮廓。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 331 页

### `2109h`: Position Command Smoothing Mode（位置命令平滑模式）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2109` |
| Description | VarCom - `MOVESMOOTHMODE`。定义位置命令的平滑方法。 |
| Object Code | Variable |
| Data Type | `UNSIGNED16` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `210Bh`: HD Anti-Vibration - Load to Motor Inertia Ratio（HD 防振 - 负载与电机惯量比）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `210B` |
| Description | VarCom - `NLANTIVIBLMJR`。HD 位置控制环防振滤波器的负载与电机惯量比。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `0.0` |
| Unit | - |

## 原 PDF 第 332 页

### `210Ch`: HD Anti-Vibration Filter - Divider（HD 防振滤波器 - 分频器）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `210C` |
| Description | VarCom - `NLANTIVIBN`。HD 位置控制环防振滤波器 - 分频器。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.00999999977648` |
| Lower Limit | `0.00999999977648` |
| Upper Limit | `100.0` |
| Unit | - |

### `210Dh`: HD Current Filter Low Pass Filter Rise Time（HD 电流滤波器低通滤波器上升时间）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `210D` |
| Description | VarCom - `NLFILTT1`。在 HD 控制环中用于定义截止频率的倒数。 |
| Object Code | Variable |
| Data Type | `REAL32` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0.0` |
| Lower Limit | `0.0` |
| Upper Limit | `0.0` |
| Unit | - |

## 原 PDF 第 333 页

### `2113h`: Drive Ready（驱动器就绪）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2113` |
| Description | VarCom - `READY`。指示驱动器是否已准备好激活，仅仍需要外部 remote enable 开关。 |
| Object Code | Variable |
| Data Type | `UNSIGNED8` |

**条目说明**

| 项目 | 值 |
|---|---|
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

### `2114h`: Drive Status (CAN only)（驱动器状态（仅 CAN））

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2114` |
| Description | VarCom - `ST`。返回详细的驱动器状态消息。 |
| Object Code | Record |
| Data Type | `NLTUNE DOMAIN` |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x02` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

## 原 PDF 第 334 页

**子索引 `001`：Status Select（状态选择）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED8` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x00` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

**子索引 `002`：Domain**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `DOMAIN` |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x0` |
| Lower Limit | - |
| Upper Limit | - |
| Unit | - |

## 原 PDF 第 335 页

### `2115h`: Step Command（阶跃命令）

**对象说明**

| 项目 | 值 |
|---|---|
| Index | `2115` |
| Description | VarCom - `STEP`。生成阶跃或方波速度命令。子索引 1 - Duration1；子索引 2 - Velocity1；子索引 3 - Duration2；子索引 4 - Velocity2；子索引 5 - Activate。 |
| Object Code | Record |
| Data Type | Manufacturer-specific，随子索引而变化。 |

**子索引 `000`：Number of Entries（条目数）**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Access | Read Only |
| PDO Mapping | No |
| Default Value | `0x06` |
| Lower Limit | `0x00` |
| Upper Limit | `0xFF` |
| Unit | - |

**子索引 `001`：Duration1**

| 项目 | 值 |
|---|---|
| Entry Category | Optional |
| Data Type | `UNSIGNED16` |
| Access | Read/Write |
| PDO Mapping | No |
| Default Value | `0x0000` |
| Lower Limit | `0x0000` |
| Upper Limit | `0xFFFF` |
| Unit | - |
