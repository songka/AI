# 外接报价 Skill 接入说明

接口正文以 `external-quotation-skill-protocol-v1.0.yaml` 为准。系统支持两种来源：

- HTTP/HTTPS 服务：实现 `GET /v1/capabilities` 与 `POST /v1/quote`。
- 本地或 SMB 公共槽文件夹：文件夹内放置 UTF-8 `skill.json` 和清单指定的 `.exe` 执行文件。

文件夹清单可复制 `external-skill-folder-v1.0.example.json` 并改名为 `skill.json`。`entrypoint`
必须是同一文件夹内的 `.exe` 相对路径，不能跳出 Skill 文件夹。系统通过标准输入发送与 HTTP
`POST /v1/quote` 完全相同的 UTF-8 JSON；执行文件须把协议响应 JSON 写到标准输出，诊断信息写到
标准错误。返回码必须为 0，默认超时 60 秒，响应上限 5 MB。

管理员在“外接Skill设置”中可输入 HTTP 地址，或选择本地/SMB 文件夹，再点击“检测并添加/更新”。
整套报价模式只能选择一个声明支持整套报价的 Skill；分布式模式按箭头顺序执行，每一步可选内置
系统或一个支持该步骤的 Skill，也可在不同步骤使用多个 Skill。

分布式调用发生在内置图纸解析、AI 工艺判断和分项报价之后，因此请求中的 `built_in_context` 会包含
内置特征、已有费用行、警告及 AI 审核结果。Skill 可据此继续审核或生成建议。外接结果仍受正式价格
防线约束：公司正式价必须引用已发布 `company_price_id` 且单价一致；AI 估价只能作为待确认参考，
不能直接进入正式总价。

生产设置保存到 SMB 公共槽 `data/external-skill-routing.json`，并同步本地缓存。测试应构造
`sync_enabled=False` 的设置服务，只写测试缓存，禁止写真实 SMB。
