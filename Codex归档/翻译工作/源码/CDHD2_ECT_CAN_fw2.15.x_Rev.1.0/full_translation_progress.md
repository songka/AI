# CDHD2 手册全文翻译进度

## 任务目标

将 `CDHD2_ECT_CAN_fw2.15.x_Rev.1.0.pdf` 全文翻译为专业简体中文，面向伺服驱动、运动控制、EtherCAT/CANopen 和 CiA 402 使用场景。

## 文件

- 源 PDF：`CDHD2_ECT_CAN_fw2.15.x_Rev.1.0.pdf`
- 英文提取稿：`CDHD2_ECT_CAN_fw2.15.x_Rev.1.0_extracted_en.md`
- 中文主译稿：`CDHD2_ECT_CAN_fw2.15.x_Rev.1.0_zh.md`
- 当前 PDF/Word 阶段性输出：`CDHD2_ECT_CAN_fw2.15.x_Rev.1.0_zh_translation.pdf`、`CDHD2_ECT_CAN_fw2.15.x_Rev.1.0_zh_translation.docx`

## 已完成

- 封面、修订历史、版权声明、免责声明、商标、联系信息、技术支持
- 第 1 章 Introduction
- 第 2 章 Fieldbus Wiring and Setup
- 第 3 章 Configuring softMC Controller for CDHD2 EtherCAT
- 第 4 章 Configuring Beckhoff Controller for CDHD2 EtherCAT
- 第 5 章 Configuring Horner Controller for CDHD2 CANopen
- 第 6 章 Configuring Keba Controller for CDHD2 EtherCAT
- 第 7 章 CANopen Operation
- 第 8 章 Units
- 第 9 章 Communication Segment：已完成 PDF 第 95–165 页，对象 `1000h`、`1001h`、`1002h`、`1003h`、`1005h`、`1006h`、`1007h`、`1008h`、`1009h`、`100Ah`、`100Ch`、`100Dh`、`1010h`、`1011h`、`1014h`、`1015h`、`1016h`、`1017h`、`1018h`、`1019h`、`1029h`、`1200h`、`1201h`、`1400h`、`1401h`、`1402h`、`1403h`、`1600h`、`1601h`、`1602h`、`1603h`、`1800h`、`1801h`、`1802h`、`1803h`、`1A00h`、`1A01h`、`1A02h`、`1A03h`、`1C00h`、`1C10h`、`1C11h`、`1C12h`、`1C13h`
- 第 10 章 Manufacturer-Specific Object：已完成 PDF 第 166–335 页，对象 `2002h`–`2115h`（其中 `2115h` 已完成至子索引 `001`；中间按英文提取稿对象顺序连续完成，含 `20E8h`、`20E9h`、`20EAh`、`20EBh`、`20ECh`、`20EEh`、`20EFh`、`20F0h`、`20F2h`–`20FDh`、`20FFh`、`2100h`、`2103h`、`2104h`、`2106h`、`2108h`、`2109h`、`210Bh`、`210Ch`、`210Dh`、`2113h`、`2114h`、`2115h`）

## 待完成

- 第 10 章 Manufacturer-Specific Object，PDF 第 336 页开始
- 第 11 章 Standard Servo Drive Objects
- 附录/尾页，如英文提取稿中仍有内容

## 下一次继续位置

从英文提取稿 `## Page 336` 开始，继续翻译第 10 章 `Manufacturer-Specific Object` 的 `2115h: Step Command` 子索引 `002`，随后连续处理 `2116h` 及后续制造商特定对象。

## 专业翻译规则

- 保留对象号、子索引、bit 编号、十六进制值、COB-ID/Data、命令、路径、单位、公式、参数名和变量名。
- `Controlword` 译为“控制字”，`Statusword` 译为“状态字”，`object dictionary` 译为“对象字典”，`fieldbus` 译为“现场总线”。
- `Profile Position/Velocity/Torque Mode` 译为“轮廓位置/速度/转矩模式”。
- `Cyclic Synchronous Position/Velocity/Torque Mode` 译为“循环同步位置/速度/转矩模式”。
- 对象字典条目应尽量保留原结构：对象标题、说明、索引、对象代码、数据类型、访问权限、PDO 映射、默认值、上下限、单位、子索引表、备注。
- 报文示例只翻译步骤说明，十六进制数据保持原样。
- 不要写本地翻译 API 脚本；由 Codex 自动化分批直接更新译稿。

