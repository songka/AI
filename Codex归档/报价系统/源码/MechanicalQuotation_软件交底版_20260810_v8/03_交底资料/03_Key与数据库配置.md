# Key 与数据库配置

## DeepSeek Key

交付包默认不存在 Key 文件。进入“系统设置”，点击“从文件设置/更换”，选择只含一行 Key 的 UTF-8 文本文件。程序把内容复制到当前运行目录的 `runtime/secrets/deepseek_api_key.txt`，页面不显示 Key。

点击“删除本机 Key”只删除运行目录侧车文件；若电脑设置了环境变量 `MECHANICAL_QUOTATION_DEEPSEEK_KEY`，环境变量仍会生效。

禁止把真实 Key 放入源代码、配置模板、公共 Skill/Agent、压缩包或聊天记录。

## 数据库地址

系统只有一个“数据库地址”设置项：

| 填写示例 | 结果 |
|---|---|
| `runtime/data` | 当前程序目录下建立 `quotation_history.db` |
| `D:\MechanicalQuotationData\quotes.db` | 使用本机指定数据库文件 |
| `\\server\quotation\database` | 公共目录下建立 `quotation_history.db` |
| `\\server\quotation\database\quotes.db` | 使用公共槽指定数据库文件 |

设置步骤：进入“系统设置”→填写或选择数据库→保存→重启软件。数据库文件不存在时在首次使用时自动建立。

公共数据库目录应允许目标用户读取、建立文件、写入和重命名。程序对短时间同时写入最多等待 30 秒；不要在网络中断时反复点击保存。数据库和 `-journal` 临时文件必须位于同一共享目录，不要单独删除。

## 登录密码

“启用账号登录与权限控制”默认不勾选，因此第一次打开不要求数据库密码。只有管理员主动启用登录模式时，系统才建立用户资料加密口令。该口令与 DeepSeek Key、报价数据库地址互相独立。
