# CURRENT HANDOFF — 2026-08-06（Codex 接管中）

## 2026-08-06 Milestone 34：打包版管理员登录与 FastAPI 启动说明修复

- 确认打包版“管理员登录”无弹窗的根因不是登录密码：便携构建漏复制认证服务必须读取的
  `config/roles.yaml` 与 `config/permissions.yaml`。GUI EXE 没有控制台，原异常未显示，因而表现为
  点击后没有反应。
- 便携构建现已强制包含两份 RBAC 配置；管理员登录表单统一挂到实际顶层窗口、等待可见后再抓取焦点，
  并延长前置显示时间。认证组件若仍因文件、SMB 或配置异常而无法建立，会显示中文错误和原始原因，
  不再静默失败。
- 启动说明已明确：桌面报价、导出和本地管理查询不需要启动 FastAPI，直接运行
  `MechanicalQuotation.exe` 即可；只有外部系统调用 REST API 或使用 Swagger 调试时才运行
  `start_api.bat`。
- 验证结果：界面/认证/打包专项实际执行项 `33 passed`；另一个用例首次运行因 pytest 默认临时目录
  ACL 拒绝访问而未建立夹具，改用正常 Windows 权限后全量为 `827 passed, 1 skipped`。跳过项仍为
  环境可选 UI 测试，无业务测试失败。
- 打包运行时已直接实例化 `AuthService` 并成功读取包内 RBAC 配置；便携自检和报价 Smoke 均返回
  退出码 0。桌面 EXE 在未另行启动 FastAPI 的情况下持续运行 5 秒；目录内旧 `api.pid` 指向已不存在
  的进程且修改时间早于本次启动，确认不是桌面程序启动 API。
- 新交付包 `MechanicalQuotation_交付版_20260806_v5.zip`，大小 `222000050` bytes，SHA256
  `5FE9E1FB982E1A8EEA7E36008D895837404B5F3ECE959B9ADCCC7CBEF30F3EAE`。包内 DeepSeek Key
  非空但不进入 manifest；Key 内容未输出、未加入 Git。旧 v4 及更早交付物未覆盖。

## 2026-08-06 Milestone 33：v4 Windows 交付包与最终验证

- 从 Milestone 32 提交 `45e8776` 重建 `dist/MechanicalQuotation`。交付目录包含签名 Python
  运行时桌面 EXE/控制台、FastAPI 启停脚本、已授权内部使用的
  `third_party/ODAFileConverter-27.1`、非空 DeepSeek 侧车、外接 Skill 协议/十份 Agent 文档、
  v3 十步流程图和 SMB 设置缓存结构；Key 内容未显示、未进入 manifest、未加入 Git。
- 包内自检与报价冒烟完成并生成 JSON/HTML 报告；可携结构测试 `4 passed`。桌面 EXE 隐藏启动
  8 秒持续存活，随后按精确 PID 关闭；FastAPI 从最终目录启动，`/api/v1/health=ok`，OpenAPI
  可读取，随后按精确 PID 关闭。
- DeepSeek 健康检查从开发目录确认 `configured=true / reachable=true / model_found=true`，延迟约
  876 ms。没有把本地图纸内容发送到真实模型；结构化报价 AI、超时熔断、工艺候选成本选择与
  AI 估价计入由 Mock 自动化回归验证。
- 最终全量回归收集 827 项：`826 passed, 1 skipped`；跳过项为当前环境可选测试，无失败。
  Ruff F/E9、协议 YAML 解析、`git diff --check` 均通过。
- 新交付 ZIP：`MechanicalQuotation_交付版_20260806_v4.zip`，221,931,691 bytes；SHA-256
  `FD18DE1093E7157C300B4485ED471DF779733A02BDECE078FBBCB9AA6AA1C3F4`。旧 ZIP 保留未覆盖，
  本次交付以 v4 与该哈希为准。
- 没有写真实 SMB、没有使用 UC/图号/文件名查价、没有推送远端、没有提交 DeepSeek Key。

## 2026-08-06 Milestone 32：AI 计入报价、四类十步路由、成本工艺与 Skill 调试

- 有效 AI 估价不再只放参考字段：费用行改为 `source=AI` 并计入本次未税小计、税额和含税总价；
  UI、历史、单笔/批量 Excel 均显示“AI估算已计入，待人工确认”，任务状态强制为
  `REVIEW_REQUIRED`。AI 价不能冒充公司核准价；整件图纸特征模型 E 参考价仍不计入。
- 生产 Resolver 不匹配历史整件正式价格；公司核准价只按已发布材料、工艺、表面处理等分项记录。
  外接 Skill 协议、训练规范、生成提示词和逐 Agent 文档已同步相同边界。
- 外接 Skill 设置升级为 schema 1.1：加工件、钣金件、焊接件、型材组装件可分别继承全局默认，
  或覆盖整套/分布式 10 步路由。生产仍由管理员发布到 SMB；测试使用 `sync_enabled=False`，
  不写真实公共槽。
- 新增管理员可控调试模式。报价后可在“查看 Skill 调试”逐步检查 10 步实际输入 JSON、实际输出
  JSON、执行者、耗时、失败回退和自动验收；自动检查必填字段、授权步骤、request ID、协议版本、
  C 价来源及 AI 待审标记。调试内容不包含 DeepSeek Key、认证头或密码。
- 工艺 Agent 输入新增可用工艺小时费率；CNC 与普通铣床都可完成时，AI 分别估算工时，系统按
  `工时 × 工价` 确定性比较，在满足质量/精度要求的候选中选择最低成本路线。0.8 小时 CNC ×
  80 元与 1.0 小时铣床 × 40 元的回归案例正确选择铣床 40 元，并保留人工审核警告。
- 修复 AI 报价看似永久卡住：后台工作线程捕获异常并恢复 UI；备注理解/工艺判断并行；DeepSeek
  默认超时缩短为 20 秒，首次连接失败后开启 30 秒快速熔断；界面显示当前 AI 处理步骤。
- 新增纠正版 `current-quotation-flow-with-skill-ai-v3.png`：完整显示四类零件、10 个 AI/Skill
  步骤、工时×工价选择、AI 估价计入、人工审核、调试模式与失败回退。旧 v2 保留作审计。
- DeepSeek 只读健康验证：`configured=true / reachable=true / model_found=true`，延迟约 876 ms；
  没有输出 Key。自动化聚焦回归 `63 passed, 2 skipped`；全量源码回归收集 827 项，重建包前为
  `826 passed, 1 failed`，唯一失败是旧 `dist` 尚未包含 v3 流程图，待本里程碑打包阶段消除。
- 不使用 UC/图号/文件名查价；没有写真实 SMB；没有输出或提交 DeepSeek Key；没有推送远端。

## 2026-08-06 Milestone 31：AI 流程图可携交付验证

- 刷新可携目录后，外接 Skill 开发清单与 `current-quotation-flow-with-skill-ai-v2.png` 均已进入
  `dist/MechanicalQuotation/docs`；包内自检与冒烟通过，可携布局 `4 passed`。
- 新交付 ZIP：`MechanicalQuotation_交付版_20260806_v3.zip`，222,163,527 bytes，SHA-256
  `FF470D92A4D1E76ACE6298F7754AECEA34846202D590B712475FF8F735E30CC3`。本次交付以 v3 为准，旧 ZIP
  保留且未覆盖。
- 本次只新增说明和图片，不改变 Milestone 29 已通过的报价、AI、FastAPI、DWG/PDF 和权限逻辑；
  不写真实 SMB、不输出或提交 DeepSeek Key、不推送远端。

## 2026-08-06 Milestone 30：外部 Skill 开发清单与 AI 流程图 v2

- `EXTERNAL_SKILL_INTEGRATION.md` 新增外部开发步骤，并区分“运行必需文件”和“完整验收交付物”。
  文件夹 Skill 运行时只需 `skill.json`、`SKILL.md` 和可选 UTF-8 参考资料；不得包含 EXE、DLL、
  脚本或 DeepSeek Key。HTTP Skill 另需服务源码、依赖锁定、启动说明及三个标准接口。
- 新增 `docs/images/current-quotation-flow-with-skill-ai-v2.png`，明确突出“程序内置 DeepSeek AI
  （统一模型）”，并分别标注文件夹 Skill 只是提示词/参考文档、HTTP Skill 可自行调用 AI；图中保留
  整套/分布式路由、正式价格保护、AI 参考价不计入合计、人工审核和失败回退。
- 可携构建脚本与布局测试已纳入该图片，后续交付包会自动包含外部开发说明及 AI 流程图。
- 不写真实 SMB、不输出或提交 DeepSeek Key、不推送远端。

## 2026-08-06 Milestone 29：逐 Agent 文件交付包与最终验证

- 以 Milestone 28 源码刷新 `dist/MechanicalQuotation`；包内包含获授权 ODA 转换器、非空 DeepSeek
  侧车、共通协议、生成指令、训练规范、提示词 YAML 以及 10 份
  `docs/external-skill-agents/*.md` 独立对接说明。Key 不在 `package_manifest.json`，没有输出内容，
  没有加入 Git。
- 从最终交付目录实测本地文件夹 Skill：程序发现 `validation.note.agent` 后调用包内 DeepSeek，针对
  “材质：3mm厚度不锈钢；表面拉丝”返回中文备注摘要、正确 request ID、
  `DOCUMENT_UNDERSTANDING` 完成步骤和 `confidence=0.95`；临时验证 Skill 已移除。
- 包内自检 `14/14`、报价/税务/Excel 冒烟 `3/3`、可携布局 `4/4`；FastAPI 从交付目录启动后
  `/api/v1/health=ok`，OpenAPI 共 32 条路由，随后按精确 PID 停止测试程序。
- 最终全量回归收集 821 项，结果 `820 passed, 1 skipped`。首次运行唯一失败为本机系统 Python
  Tcl/Tk 资源暂时无法读取；指定交付包内完整 Tcl/Tk 后该 UI 测试单独通过且全量无失败，产品包
  自身桌面资源与自检均正常。
- 最终 ZIP：`MechanicalQuotation_交付版_20260806_v2.zip`，220,614,568 bytes（约 210.4 MiB），
  SHA-256 `065EF72AF9F8AC427375A2E7083501C9CFE5FE047664F3E8DB96C750E7BBD4CD`。旧 ZIP 保留，
  本次交付以 v2 和上述哈希为准。
- 没有写真实 SMB、没有使用 UC/图号/文件名匹配价格、没有推送远端、没有提交 DeepSeek Key。

## 2026-08-06 Milestone 28：文件夹 Skill、逐 Agent 提示词与外部训练规范

- 本地或 SMB 文件夹 Skill 改为 `skill.json + SKILL.md + 可选参考文档`；主程序将 Skill 文档和
  用户选择的图纸资料交给程序内置 DeepSeek，不再执行文件夹内 EXE、脚本、DLL 或 shell 命令。
- 完整报价模式继续只允许一个整套 Skill；分布式模式按 10 个逻辑 Agent 顺序执行，每步可选内置
  能力或不同外部 Skill。即使普通界面“智能辅助”未勾选，已配置的文件夹 Skill 仍能使用内置
  DeepSeek；内置 AI 报价步骤本身仍受原开关控制。
- 新增 `EXTERNAL_SKILL_TRAINING_GUIDE.md`、`EXTERNAL_SKILL_GENERATION_PROMPT.md` 和机器可复制的
  `external-skill-prompt-templates-v1.0.yaml`，供外部团队或外部 AI 按统一协议生成与训练 Skill。
- `external-skill-agents/` 新增 10 份逐步对接说明：图纸与备注理解、特征提取、材料判断、工艺路线、
  工时估算、分项计价、待确认估价、价格审核、人工审核建议及报价汇总；每份均定义步骤代码、输入、
  提示词、返回字段与验收条件。
- 图纸备注输入保留原文、来源文件、页码/实体、来源类型和可信度；优先级为原生 DWG/DXF 向量文字、
  配套 PDF 明确文字、OCR、模型推断。冲突证据不能静默覆盖，材料/关键要求冲突必须转人工审核。
- 文件夹 Skill 指令/参考资料只允许 UTF-8 文本型文件、限制 128 KB 并阻止路径越界；正式价格、
  AI 参考价、禁止 UC/图号/文件名查价与中文输出防线保持不变。
- 静态检查、Ruff F/E9、协议 YAML 解析和 `git diff --check` 通过；核心专项回归 `35 passed`。
  测试使用本机临时目录和 `sync_enabled=False`，没有写入真实 SMB，没有输出或提交 DeepSeek Key。
- 本里程碑源码 Commit 后的可携包刷新与最终验证见 Milestone 29；旧 `20260806` ZIP 不包含本次
  逐 Agent 文件，不能作为本次功能的最终交付包。

## 2026-08-06 Milestone 27：含 AI、ODA、Skill 的异机便携交付验证

- 重建 `dist/MechanicalQuotation`，包含签名 Python 运行时、获授权的 `third_party/ODAFileConverter-27.1`、外接 Skill 协议/文件夹清单范例，以及用户明确授权随公司内部交付的非空 DeepSeek Key 侧车文件。Key 不在 `package_manifest.json`，没有加入 Git，也没有在日志输出内容。
- 包内自检 `14/14`、报价与 Excel 冒烟 `3/3`、便携结构测试 `4/4`；DeepSeek 从最终交付目录实际验证 `configured=true / reachable=true / model_found=true`，并从异机模拟副本完成一次中文结构化材料/表面处理抽取。桌面 EXE 免登录启动 8 秒持续存活，FastAPI `/api/v1/health` 返回 `ok`。
- 最终全量回归共收集 817 项，结果 `817 passed`；修改范围 Ruff F/E9 和协议 YAML 解析通过，`git diff --check` 通过。
- 新交付 ZIP：`MechanicalQuotation_交付版_20260806.zip`，210.4 MB，SHA-256 `33B95ECD115670528EDB6C4D4FA68F0B8D19C5B1AFDD3DADF58EEBB727DC0FEE`。解压目录约 531.7 MB、10,969 个文件。
- 异机模拟：从最终 ZIP 解压到与仓库分离且含中文/空格的 `C:\Users\lfaf-test\Documents\报价系统\异机 模拟 20260806-0937\MechanicalQuotation`；该副本自检通过、DeepSeek 可达，FastAPI 从新路径启动成功，健康状态 `ok`，OpenAPI 共 32 条路由，证明不依赖开发仓库绝对路径。
- 接收电脑要求 Windows 10/11 64 位、能访问公司内网 DeepSeek 与 SMB 公共槽；FastAPI 默认绑定 `127.0.0.1:8000`，在接收电脑本机使用 `start_api.bat` 和 `/docs`，默认不对局域网其它机器开放。
- 不使用 UC 料号匹配，不推送远端、不提交 DeepSeek Key；旧 `20260805` ZIP 未删除，最终交付以 `20260806` ZIP 和上述哈希为准。

## 2026-08-06 Milestone 26：免登录启动、按权限显示管理功能与报价审计

- 桌面程序始终直接进入免登录模式，不再因已启用认证或存在用户库而在启动时强制弹出登录。访客可使用新建报价、批量报价、报价记录、Excel 导出和只读价格管理。
- 左侧新增“管理员登录/退出登录”。登录后不重启即可按实际权限显示供应商管理、价格审核、用户管理、外接 Skill 设置和系统设置；退出后立即回到访客菜单。人工审核与报价删除不会向访客显示。
- 报价历史新增“删除报价”，只对具有 `quotation.delete` 权限的登录用户显示；删除时同一事务清除报价摘要、费用明细、人工调整和审核记录。FastAPI 同步新增受权限保护的 DELETE 接口。
- 每次报价保存业务报价人、Windows 登录用户名、电脑名称及 IP；未登录报价人明确记录为“免登录用户”。历史列表、结构化详情及中文导出字段均可追溯。
- 专项回归 `37 passed`。打包前全量源码回归为 `815 passed, 1 skipped`；旧交付目录造成的唯一结构失败已在 Milestone 27 重建后消除，最终全量为 `817 passed`。
- 不使用 UC 料号匹配；测试 Skill 设置使用 `sync_enabled=False`，不写真实 SMB；不推送远端、不提交 DeepSeek Key。

## 2026-08-06 Milestone 25：外接报价 Skill、分布式流程与 SMB 同步设置

- 新增机器可读协议 `docs/external-quotation-skill-protocol-v1.0.yaml`：支持整套报价或 10 个分步环节，定义中文输入输出、正式价格引用、AI 参考价、审核证据、错误和回退规则。正式 C 价必须引用请求中的已发布公司价格记录并保持单价一致，禁止 UC/图号/文件名查价。
- 管理员可选择“整套报价”或“分布式报价”。整套模式只允许一个声明支持完整报价的 Skill；分布式页面以编号卡片和箭头体现顺序，每步可选择内置系统或一个兼容 Skill，不同步骤可组合多个 Skill。
- Skill 来源支持 HTTP/HTTPS、本地文件夹或 SMB 公共槽文件夹。该里程碑最初采用文件夹 EXE 方案，
  已由 Milestone 28 正式替换为“文件夹提示词/参考文档 + 主程序内置 DeepSeek”，不得再按旧 EXE
  方式制作文件夹 Skill。
- 路由设置由管理员修改并发布到 SMB `data/external-skill-routing.json`，各电脑读取相同设置并保留本地缓存；测试模式强制只写测试缓存。分布式 Skill 可读取内置图纸解析、AI 工艺判断、多智能体审核和现有报价分项作为上下文，再返回审核或报价建议。
- 外接 Skill 失败、超时、协议错误或正式价格校验失败时记录中文警告并回退内置报价，不允许外部结果绕过公司已发布价格和人工审核防线。
- 专项回归包含协议、设置隔离、HTTP/文件夹发现、完整 Skill 报价、API 与权限，共 `37 passed`（与 Milestone 26 联合专项）。
- 不使用 UC 料号匹配，不写真实 SMB，不推送远端、不提交 DeepSeek Key。

## 2026-08-05 Milestone 24：管理员用户与逐项权限管理

- 桌面端新增“用户管理”页面：具有 `user.view` 权限才显示入口；具有 `user.manage` 权限才显示新增用户、角色与权限分配、重置密码、启用和停用按钮。管理员可选择系统角色并逐项勾选功能权限，用户资料加密结构向后兼容，旧用户继续继承角色默认权限。
- 登录后的左侧菜单改为按用户实际权限生成；页内的 Excel 导出、人工审核、供应商维护和价格审核按钮也按相应权限隐藏。权限变更后用户重新登录即可刷新桌面菜单。
- FastAPI 新增用户列表、新增用户、权限分配、密码重置和账号状态接口；每次受保护请求都会重新读取用户当前状态与实际权限，撤权或停用后旧 API 令牌不能继续使用已撤销功能。
- 安全保护：拒绝未知权限；当前管理员不能修改自己的角色/权限或停用自己；禁止停用或降级最后一名有效管理员。
- 用户权限专项回归 `57 passed, 2 skipped`；最终全量回归共收集 807 项，结果为 `806 passed, 1 skipped`；Ruff F/E9 与 `git diff --check` 通过。
- 当时的 Windows 便携包记录已由后续交付要求取代；当前最终包必须同时包含获授权的 ODA 转换器、外接 Skill 协议和用户明确授权随包交付的 DeepSeek Key，最终文件名与哈希以最新里程碑为准。
- 不使用 UC 料号匹配，不提交 DeepSeek Key，不推送远端。

## 2026-08-05 Milestone 23：Windows 干净交付包

- 已生成可交付压缩包 `MechanicalQuotation_交付版_20260805.zip`；接收方必须解压并保留整个 `MechanicalQuotation` 文件夹，不能只复制 `MechanicalQuotation.exe`。包内新增中文《交付与启动说明》，并保留自检、冒烟测试及 API 启停脚本。
- 干净构建排除了开发测试目录、缓存、重复 Python 包和本机运行资料；未包含 `quotation_history.db`、管理员本机密钥 `user_store_key.txt` 或第三方 ODA 安装程序。`deepseek_api_key.txt` 为 0 字节占位文件，不含 DeepSeek Key。
- 接收方使用 DXF/PDF 不需要额外转换器；使用 DWG 时须自行合法安装 ODA File Converter 并在系统设置中指定路径；使用 `.SLDDRW/.SLDPRT` 时须安装 SOLIDWORKS。AI 功能由每台电脑自行配置 DeepSeek Key；SMB 公共槽还需要公司网络和共享目录权限。
- 解压后包体约 460 MB，共 10,766 个文件；Milestone 24 重建后的压缩包仍为 182.3 MB、11,830 个 ZIP 条目，最新 SHA-256 见上方 Milestone 24。
- 交付包内 self-check `12/12`、smoke `3/3`、便携包结构测试 `4 passed`；最终全量回归 `800 passed, 2 skipped`。
- 不使用 UC 料号匹配，不提交 DeepSeek Key，不推送远端。

## 2026-08-05 Milestone 22：价格管理中文名称

- 价格管理列表不再显示 `SUP-*` 来源代码，改为供应商主档中的中文名称；没有供应商来源的正式费率显示“公司内部核准价”，未知供应商代码显示“供应商名称未维护”，内部 ID 仍保留供数据库追溯。
- 材料、工艺和表面处理标准代码在列表、详情与价格审核页转换为中文友好名称，例如 `A6061-T6 → 6061-T6 铝合金`、`AL_PROFILE → 铝型材`、`SUS304 → 304 不锈钢`、`CNC → 数控加工`；内部标准代码仍用于准确查价，不修改正式价格数据。
- 支持用“铝”等中文名称搜索正式价格；供应商原始报价页也优先显示中文材料名称。
- 中文化与工艺联合专项回归 `83 passed`；最终全量回归 `800 passed, 2 skipped`；Ruff F 类检查与 `git diff --check` 通过。
- 不使用 UC 料号匹配，不提交 DeepSeek Key，不推送远端。

## 2026-08-05 Milestone 21：普通铣床与 CNC 成本分流

- 根因确认：旧确定性规则只要识别到孔或螺纹就生成通用 CNC 项；虽然已发布价格同时包含铣床 `40 元/小时` 与 CNC `80 元/小时`，AI 判断出的铣床只会追加，不能撤销旧 CNC，可能造成设备等级过高或重复计价。
- AI 工艺提示现在要求选择“成本最低且足够完成”的设备：普通平面、直边、槽与常规孔优先普通铣床，孔或螺纹本身不再作为必须 CNC 的理由；明确 CNC/加工中心、复杂曲面、多轴联动或高重复定位精度才选择 CNC，且同一去除加工不得同时返回 CNC 与铣床。
- 当 AI 明确判断铣床足够、未同时判断 CNC、且图纸文字没有 CNC/数控/加工中心要求时，报价服务撤销仅因孔位自动产生的通用 CNC 项，并按公司已发布铣床小时费率生成独立分项；替换结果强制保留人工审核提示。
- 其它工艺审计同步修复：攻牙改用中文名称且因没有独立发布费率继续保持待确认；钣金切割、折弯与焊接不再漏项，缺少正式费率时生成带工程量的中文未定价分项并由 AI 提供审核参考；未知装配工时不再形成正式 0 元价，零个连接件不再生成无意义费用行。
- AI 若判断普通车床已足够、没有同时判断 CNC 且图纸无明确 CNC 要求，也可撤销仅由孔位推导的通用 CNC；磨床、放电、快丝和慢丝仍按证据作为可能的附加工序，不会擅自替代主要去除加工。
- 工艺专项回归 `80 passed`；最终全量回归 `800 passed, 2 skipped`（共收集 802 项）；修改范围 Ruff F 类检查与 `git diff --check` 通过。
- 不使用 UC 料号匹配，不提交 DeepSeek Key，不推送远端。

## 2026-08-05 Milestone 20：修复多智能体分项价格审核调用

- 修复价格审核阶段错误调用 `QuotationApplicationService._item_to_dict` 的问题；该序列化方法实际属于 `QuoteJobResult`，旧代码因此显示“多智能体价格审核失败：`QuotationApplicationService` 没有 `_item_to_dict` 属性”。
- 现在正式报价分项会正确转换为受控字典，再交给价格审核智能体；审核智能体仍只有审计权，无权修改公司发布单价，风险汇总结果继续决定是否进入人工审核。
- 新增完整回归，覆盖 DXF 报价、备注理解、工艺规划、分项价格审核与风险汇总闭环；专项回归 `30 passed`，全量回归 `794 passed`，修改范围 Ruff F 类检查与 `git diff --check` 通过。
- Windows 便携包已刷新；包内 self-check `12/12`、smoke `3/3`。
- 不使用 UC 料号匹配，不提交 DeepSeek Key，不推送远端。

## 2026-08-05 Milestone 19：明确使用用户选中的图纸

- 修复新增 SOLIDWORKS 格式后引入的主图优先级回归：新建报价明确选择 PDF/DWG/DXF/SLDDRW/SLDPRT 时，始终以用户选中的档案为主，不再被同目录同图号的其他格式替换。因此选择 DWG 不会因为旁边存在 SLD 文件而错误提示未安装 SOLIDWORKS；选择 PDF 也不会偷偷切换成旁边的几何档。
- 批量“选择档案”改为只使用已选档案分组：同一图号只选一个几何档时严格使用该档；只有用户同时选中两个或更多同名几何档时，才在已选档案内部按 `DWG → DXF → SLDDRW → SLDPRT` 选择主档。未选中的同目录档案不会参与抢占。
- “选择资料夹”没有单一明确选择时，采用相同固定格式顺序；DWG/DXF 路由与 SOLIDWORKS 原生文件路由继续完全分离。
- 专项回归 `44 passed`；全量回归 `792 passed, 1 skipped`（共收集 793 项）；修改范围 Ruff F 类检查与 `git diff --check` 通过。
- Windows 便携包已刷新；包内 self-check `12/12`、smoke `3/3`。
- 不使用 UC 料号匹配，不提交 DeepSeek Key，不推送远端。

## 2026-08-05 Milestone 18：多智能体报价审核

- 新增多智能体编排：备注理解智能体负责材料/公差/粗糙度/特殊要求及歧义，工艺规划智能体
  负责白名单工艺与工时，价格审核智能体负责遗漏、重复、单位和工时异常，风险汇总智能体负责
  汇总分歧并决定是否必须人工审核。
- 各智能体独立使用结构化 JSON；价格审核智能体无权修改公司单价，工艺智能体只可选择已发布
  费率对应白名单，风险结论为 REVIEW/BLOCK 或备注存在风险时强制进入人工审核。
- 单件界面与 Excel 特征摘要新增“多智能体审核结论/摘要”，完整结构同时保留在任务
  `ai_suggestions.agents`，供 API 和后续审计使用。
- 专项回归 `46 passed, 2 skipped`；全量回归收集 786 项并全部通过或按环境跳过；修改范围
  Ruff F 类检查与 `git diff --check` 通过。
- Windows 便携包已刷新；包内 self-check `12/12`、smoke `3/3`。

## 2026-08-05 Milestone 17：SOLIDWORKS 原生入口与 AI 工艺判断

- 扫描器、单件/批量选择框和报价服务已接入 `.SLDDRW/.SLDPRT`；新增 SOLIDWORKS COM
  转换适配器，合法安装 SOLIDWORKS 后可静默另存隔离 DXF、缓存结果并沿用正式解析管线。
- 当前电脑没有 SOLIDWORKS/COM 注册，因此只能验证缺失依赖时的明确错误，尚不能声称真实
  SLD 文件已现场转换成功；ODA 与中望 CAD 不能替代此依赖。
- DeepSeek 新增结构化工艺判断：只允许 CNC、车床、铣床、磨床、钳工、放电、快丝、慢丝
  白名单；拒绝低于 0.6 可信度、未知代码、零/负工时，并限制最大工时。
- 新建报价与批量报价默认启用 AI 工艺判断；没有配置 DeepSeek 时安全回退到可追踪规则，不会
  因缺少密钥阻断报价。
- AI 判断的工艺使用公司已发布小时费率形成独立费用行，保留中文证据与可信度，任务强制进入
  人工审核；AI 不得提供或覆盖公司单价，重复的规则工艺不会再次计费。
- 专项回归 `48 passed`；全量回归 `783 passed, 1 skipped`。
- Windows 便携包已刷新并确认包含 SOLIDWORKS 转换脚本；包内 self-check `12/12`、smoke `3/3`。

## 2026-08-05 Milestone 16：登录模式即时生效与工艺/格式边界澄清

- 系统设置中的登录开关改为“保存后立即登录”：从默认免登录切换为登录模式时，当前窗口直接
  显示首位管理员建立、用户库连接或账号登录流程，不再要求关闭并重启程序。
- 登录成功后在同一进程更新用户会话、供应商维护与价格审核服务，并按角色立即重建左侧菜单；
  用户取消登录时自动撤销本次启用并恢复免登录，避免出现“配置已启用但当前窗口未认证”。
- 登录对话框现在可以复用已经打开的主窗口作为父窗口，同时保留启动时独立登录窗口的行为。
- 已在详细报价规则中写明当前加工工艺判定：正式工艺来自图纸文字与二维几何规则；AI 只提供
  缺失字段或 U 项参考，不会自动写入正式工艺或总价。钣金完整切割/折弯模型仍未完成，焊接
  工程量不足时仍须人工确认。
- 已明确原生 `.SLDDRW/.SLDPRT` 当前不支持。本机未检测到 SOLIDWORKS，现有 ODA 只转换
  DWG/DXF，中望 CAD 2011 不能作为 SOLIDWORKS 无头转换器；可先从 SOLIDWORKS 导出
  DXF/DWG 与配套 PDF 后报价。
- 即时登录专项回归 `27 passed, 1 skipped`；全量回归 `780 passed, 1 skipped`；修改范围
  Ruff F 类检查与 `git diff --check` 通过。
- 已刷新现有 Windows 便携包且保留运行资料；包内 self-check `12/12`、smoke `3/3`，
  `MechanicalQuotation.exe` 无参数启动 7 秒仍存活。

## 2026-08-05 Milestone 15：正式报价恢复为分项，整件模型价降级为审核参考

- 修复根因：图纸特征校准命中且没有 U 项时，旧逻辑会用单一“图纸特征校准估价”覆盖
  材料、加工、表面处理等费用行，导致界面错误显示“正式价格来自图纸”。
- 当前正式报价始终保留材料、加工、表面处理、外购及其他逐项金额；正式总价仅由这些费用
  行计算。整件模型价只显示为“整件模型参考价（不计入）”，不生成正式费用行、不覆盖细项、
  不进入未税小计、税额或含税总价。
- 只有 PDF 且缺少可计算二维几何时，返回“缺少二维几何，无法生成分项报价”U 项，正式
  合计为 0；模型金额只供人工审核，不能伪装为正式价格。
- 单件界面新增“分项未税合计”和“整件模型参考价（不计入）”；单件 Excel 的特征摘要改用
  中文字段，并在报价表新增“费用类别”。批量 Excel 原有“报价明细”继续直接导出逐项数据。
- 已增加回归测试，覆盖文件改名不影响计算、模型不进入正式费用行、材料及加工细项保留、
  PDF 无几何不形成正式价格，以及中文界面字段分离。
- 专项回归 `36 passed, 1 skipped`；全量回归 `779 passed, 1 skipped`；修改范围 Ruff F 类检查
  与 `git diff --check` 均通过。
- 已刷新 `dist/MechanicalQuotation` 现有便携包而不清空用户运行资料；补齐便携包此前遗漏的
  `bcrypt` 认证依赖后，包内 self-check `12/12`、smoke `3/3`，无参数启动
  `MechanicalQuotation.exe` 后 7 秒仍存活。
- 本里程碑没有修改 SMB 正式价格资料，不使用 UC 匹配，不提交 DeepSeek Key，不推送远端。

## 2026-08-04 Milestone 11：SMB 公共槽与本地缓存同步

- 已实现 `SmbStorageClient`：固定在公共槽范围内解析路径，拒绝绝对路径及 `..` 越界；使用
  当前 Windows 身份，不保存 SMB 用户名或密码；提供只读健康检查、原子 JSON/文件写入和
  不覆盖既有文件的初始化部署。
- 已实现 `CacheSyncService`：同步 `data`、`rules/published`、`prices/published`、`templates`，
  SHA-256 增量复制、原子替换、缓存清单、启动同步、60 秒后台刷新、离线缓存和同步错误状态。
- 正式价格加载器、图纸特征模型、价格管理查询及供应商来源查询均优先读取
  `runtime/cache/smb`；无缓存时才回退包内资料，`draft` 不会进入正式 Resolver。
- 系统设置新增 SMB 公共槽、本地缓存、在线/离线状态和“立即同步公共资料”；FastAPI 新增
  `GET /api/v1/smb/health` 与 `POST /api/v1/smb/sync`。
- 实际公共槽
  `\\10.97.0.210\lfaf_Engineer\Mechanical\3-標準文檔\10-自動報價系統\data`
  原为空目录；已建立设计规定的目录，并在不覆盖模式放入 6 份当前已发布资料：规则、价格
  指针、V1.1 快照、特征模型、供应商来源包和版本文件。
- 真实同步首次 `changed_files=6 / total_files=6`，第二次增量同步为 `0/6`；公共槽在线，
  生产 Loader 确认价格版本 `R01-COMPANY-PRICE-V1.1` 来自 SMB 缓存。
- 源码 UI 集成 SMB 启动同步后实际运行 6 秒仍存活；FastAPI SMB health 返回在线、缓存可用。
- 聚焦测试：SMB/缓存、设置、API、价格 Loader、特征模型和管理查询 `33 passed`；启动同步
  回归 `23 passed`；全量回归 `738 passed, 1 skipped`。首次全量测试因真实缓存覆盖测试隔离
  出现 11 个失败，已修正为显式测试价格路径优先，相关规则隔离复验 `43 passed`。
  操作文档为 `docs/SMB_PUBLIC_SLOT.md`。
- 本里程碑不实现用户账号、价格维护 CRUD 或审批发布；这些按 Milestone 12–15 独立完成。
- 不推送远端，不提交 DeepSeek Key；共享盘只新增报价系统明确公共槽内容，未修改其他目录。

## 2026-08-03 Milestone 10：取消 UC 查价，改为图纸特征校准

- 用户明确要求：UC 报价只用于修复现有规则，后续文件不会有 UC；生产报价禁止用 UC 料号、
  图号或文件名匹配价格。
- 已删除 `GCS-HISTORICAL-PART-V1.0`、精确料号加载器和 `HISTORICAL_EXACT_PART` 路线；
  Milestone 9 的“同料号 0%”方案作废，不得作为当前能力或对老板汇报的数据。
- 新模型 `GCS-FEATURE-CALIBRATION-V1.0` 仅使用图纸内材料、整体尺寸和表面处理类别；模型
  文件明确列出 `part_number / drawing_number / file_name` 为禁止匹配字段，且不保存训练料号。
- 以 GCS BOM 的真实单位价校准 62 个有效样本，采用对数价格岭回归；留一法交叉验证：
  WAPE 15.78%、MAE 42.41 元、平均 APE 26.27%。
- 51 张真实 DWG 复测后分开记录价格口径：49 张特征参考价 WAPE 17.19%、MAE 53.36 元、
  平均 APE 25.05%，32 件误差不超过 30%、17 件超过 30%；48 张无 U 项的完整正式报价
  WAPE 22.22%、MAE 38.00 元。全部 51 张正式合计 WAPE 50.44%，因其中 3 张仍是部分合计，
  不得把该数或模型参考价混称为同一个“端到端准确度”。
- 49/51 张图成功提取非料号特征；48 张生成 E 正式估价，1 张焊接方通件保留 U 工艺项并
  展示整件特征参考价；2 张缺整体尺寸保持 U。启用 AI 时对 U 生成不计入正式总价的参考金额。
- 自动测试验证同一图纸改为两个完全不同、无 UC 的文件名后价格一致。
- 方通/方管/矩形管新增材料识别，焊接方通真实件估价从旧规则 1,269.67 元修正为
  6,209.42 元，对比 BOM 7,000.00 元，偏差 -11.29%。
- 老板报告、详细报价规则、UI/Excel 中文定价依据、便携版数据文件名均改为图纸特征模型口径。
- 13% 税率修正保留；BOM 税价口径仍标记未说明，需财务确认。
- 真实审计机器结果：
  `runtime/price-audit/after-feature-calibration-v3/gcs-price-audit.json`（运行时文件、不提交）。
- 全量回归：`730 passed, 1 skipped`；本次修改文件 Ruff 检查通过。全仓 Ruff 另有 566 个
  历史风格问题，不属于本里程碑，未做无关批量改写。
- Windows 便携包已重建：包内 self-check `12/12`、smoke `3/3`、包结构测试 `4/4`；
  `MechanicalQuotation.exe` 无参数隐藏启动 6 秒仍存活，FastAPI `/api/v1/health` 返回正常。
- 同一张真实方通 DWG 复制为 `未来零件甲.dwg`、`任意名称乙.dwg` 后在便携包实跑：两者均
  `REVIEW_REQUIRED`，正式合计 1,269.67 元、特征参考价 6,209.42 元，证明不依赖 UC/文件名。
- 便携包不存在旧 `historical-part` 数据；应用、配置、数据和规则目录无 DeepSeek Key 命中，
  `runtime/secrets/deepseek_api_key.txt` 为 0 字节。全包 3 个 `sk-...` 命中均为 Python
  `packaging/licenses/_spdx.py` 的许可证标识，不是密钥。
- 不修改共享盘源文件，不推送远端，不提交 DeepSeek Key。

## 2026-08-03 Milestone 9：已撤销的 UC 精确查价方案

- 该里程碑曾短暂实现按 UC 精确套用 BOM 整件价格，并得到训练答案命中 WAPE 0%。
- 用户随后确认 UC 仅是校准数据、未来不会存在，故该方案已在 Milestone 10 完整删除。
- `ca501bc` 仅保留为 Git 历史检查点；当前工作树、文档、测试和打包均不得使用该方案。

## 2026-08-03 Milestone 8：GCS 真实 BOM 价格审计基线

- 对用户指定的 GCS 双滑台打磨设备共享盘执行只读盘点，并将 BOM 复制到本机
  `runtime/price-audit/source/`；共享盘源文件未修改。
- BOM SHA-256：`DC60ACC9C86B65887D8E1CF55BAD71A9510380A190D878E950F5FBD2406C65E7`。
- 加工件 82 行、66 个唯一料号、发生金额 20,094.00 元；51 个料号匹配到 DWG/DXF，
  15 个没有二维几何图，重复料号价格冲突为 0。
- 使用生产 DWG 转换与报价管线逐张实测 51 件：WAPE 83.18%、MAE 251.91 元、
  仅 1 件误差不超过 10%，46 件误差超过 30%。50 件解析完整、1 件焊接结构需审核。
- 根因：标注/图框圆误计加工孔、包围盒重量误差、钣金计价未实现、焊接结构缺少可靠拆分，
  且原通用公式没有使用真实价格校准参数。
- 新增可重复审计工具 `tools/audit_gcs_pricing.py` 与基线报告
  `docs/GCS_PRICE_AUDIT_BASELINE.md`；运行时 JSON/CSV 不提交。
- 本里程碑只固化证据，不发布新价格，不修改共享盘，也不包含任何 DeepSeek Key。

## 2026-08-03 接管基準與 Milestone 1：DWG 正式支援

### 1. 目標與根因

- 已從 `HANDOFF/MechanicalQuotation.bundle` 無損恢復遺失的 `.git` metadata；來源為
  `9edc8f0`，恢復後工作樹乾淨。
- 已重建 Python 3.13.14 `.venv`。搬遷基準精確恢復為
  **656 passed, 2 skipped**；Windows sandbox 的 Temp ACL 會使 pytest fixture 出現
  `PermissionError`，測試需在正常 Windows 權限下執行，業務程式無需修改。
- 既有 `DwgConverter` 未接入報價管線，且舊實作把輸出放在離開函式即刪除的暫存目錄；
  也缺少配置優先級、健康檢查、快取、取消、UI/API/Excel trace。
- 新流程固定為：原始 DWG 隔離副本 → 可插拔外部 adapter → 持久 DXF 快取 →
  現有 `DxfReader` → 現有報價管線。沒有自行解析 DWG 二進位，也沒有下載或打包第三方工具。

### 2. 修改文件

- 新增 `src/quotation/infrastructure/dwg/__init__.py`
- 新增 `src/quotation/infrastructure/dwg/converter.py`
- 相容入口 `src/quotation/infrastructure/dxf/converter.py`
- 管線/API/UI/歷史/Excel：
  `quotation_service.py`、`api/main.py`、`ui/viewmodels.py`、`ui/widgets.py`、
  `history_service.py`、`batch_excel.py`
- 配置與文件：`config/user_settings.example.json`、`docs/DWG_SUPPORT.md`、
  `.gitignore`、`pyproject.toml`
- 新增測試：`tests/unit/infrastructure/dwg/`、
  `tests/unit/application/test_dwg_workflow.py`，並擴充 API/UI 測試。

### 3. 新增測試

- 成功、未配置、已配置但不可用、超時、執行失敗、空 DXF、取消。
- 中文與空格路徑、adapter 嘗試修改來源時原始 DWG 仍保持不變。
- SHA-256 快取命中，第二次不重跑 adapter。
- 環境變數優先於 `runtime/config/user_settings.json`，再搜尋 Windows 常見位置/PATH。
- DWG 經既有 DXF parser 完成報價；單一 DWG 失敗不阻斷整批。
- `/api/v1/dwg/health`、UI 中文狀態、Excel `DWG Conversion Trace`。
- 保留舊 `DwgConverter()`/`ImportResult` API，相容既有 CAD import 測試。

### 4. 全部測試結果

```text
672 passed, 2 skipped, 1 warning in 44.97s
```

新增 16 個通過測試；2 個 skip 是本機未安裝 ODA 時的既有可選整合測試。

### 5. 真實文件驗證

- 使用隨附真實 `samples/drawings/*.DWG` 驗證未配置情境：
  `DWG_CONVERSION_FAILED / NOT_CONFIGURED`，中文原因正確。
- 驗證前後 SHA-256 相同，原始 DWG 未被修改。
- 本機三個常見 ODA 安裝位置均不存在，因此尚不能宣稱真實 ODA 轉換成功；這是明確的
  外部依賴狀態，不以假成功掩蓋。

### 6. UI / API / Excel

- 接管基準：Tkinter UI 實際啟動成功；FastAPI health、Swagger、OpenAPI 均為 HTTP 200。
- DeepSeek health 可達，並完成一次中文 UTF-8 結構化抽取；未輸出 Key、原始回應或
  `reasoning_content`。
- DWG UI 狀態顯示「正在轉換DWG圖紙」/「DWG轉換失敗」。
- `GET /api/v1/dwg/health` 實測 HTTP 200；本機回報 configured=false、available=false。
- 批量 Excel 新增獨立 `DWG Conversion Trace` sheet，包含 adapter、配置來源、快取、耗時、
  暫存 DXF、原檔保護與中文錯誤。

### 7. Commit

- Checkpoint subject：`feat: add pluggable DWG to DXF conversion workflow`
- 本節與程式碼將在同一個本地 commit；不推送遠端。

### 8. Git 狀態

- Commit 前僅包含上述 Milestone 1 受控變更。
- `runtime/secrets/deepseek_api_key.txt` 維持 ignored 且未追蹤。
- `runtime/cache/` 已忽略；轉換結果不提交 Git。

## 2026-08-03 Milestone 2：真實外部圖紙閉環

- ODA File Converter 27.1 已從官方 MSI 取得並驗證 Authenticode；因 MSI 要求全機器管理員
  安裝，使用 Windows Installer administrative image 部署至使用者 LocalAppData。
- 使用者另安裝中望 CAD 2011（11.0.0.1125）；已偵測到程式，但因屬未簽章舊版 GUI，
  目前只作人工檢視備援，不接入無人值守批次。
- 本機 ignored 設定已指向已簽章執行檔；`/api/v1/dwg/health` 現為
  `configured=true, available=true`。第三方工具未打包、未加入 Git，商業授權仍須公司確認。
- 真實 `UC1000005854-J003` 與 `UC1000005855-J005` 的 2 DWG + 2 PDF 在隔離資料夾中
  掃描為 2 個 MATCHED bundle；DWG 均成功轉 DXF，PDF 抽取 195/94 個文字區塊。
- 兩筆正式報價均 COMPLETE；未稅/稅額/含稅分別為
  `1046.42 / 177.89 / 1224.31` 與 `323.91 / 55.06 / 378.97`，符合 17% 稅務。
- 真實 W001 配合可重現 AI stub 驗證缺失欄位建議；建議只保留供人工審核，不自動改價。
- 修正 FastAPI batch-upload：每批隔離目錄、保留安全原檔名、正確配對 DWG/PDF、拒絕
  同批重名，並在 Swagger multipart 表單暴露 `use_ai`。
- PDF 現在實際解析並回傳 `supplementary_analysis`；AI 使用受限長度的 PDF 文字，不再只有檔名。
- 實際 Uvicorn multipart 上傳回應 `total=2, complete=2, failed=0`，批量 Excel 下載成功；
  PDF-only 案例回傳中文原因「找不到可用的DWG或DXF幾何圖紙」。
- 詳細證據：`docs/MILESTONE2_EXTERNAL_VALIDATION.md`；可重跑客戶端：
  `tools/validate_external_api.py`。
- 聚焦測試：`30 passed`；全量測試：`677 passed, 1 warning in 51.17s`。
- 預定本地 Commit：`test: validate external drawing quotation workflow`；不推送遠端。

## 2026-08-03 Milestone 3A：W002 材料厚度與精度

- 移除 SPCC 一律套用 2 mm 的規則；優先使用抽取到的 `SheetMetalFeature.thickness_mm`。
- 新增 `MaterialCalculationTrace`，以 Decimal 保留面積、厚度、體積、密度與重量；材料費及
  表面費在貨幣邊界才以 `ROUND_HALF_UP` 量化為 0.01 元。
- 0.35 mm 回歸案例精確保留：面積 5000 mm²、體積 1750.00 mm³、密度 7.85、重量
  0.0137375 kg；不再變成 0 或 2 mm。
- 真實 `UC1004001529_W002.DWG` 使用抽取厚度 1.5 mm，材料證據鏈完整，材料金額 10.50 元，
  DWG 轉換成功且報價狀態為 REVIEW_REQUIRED。
- 聚焦測試：`43 passed`；全量測試：`679 passed, 1 warning in 51.17s`。
- 本地 Commit：`fix: preserve sheet metal thickness and material precision`；不推送遠端。

## 2026-08-03 Milestone 3B：W001 鋁型材規格與價格

- 新增共用 `normalize_profile_spec()`；`40*40`、`40×40`、`40X40`、`40x40` 均正規化為
  `40x40`，小數規格也不會留下無意義尾零。
- `profile_spec` 現由 Manufacturing Feature 傳到 Quotation Feature，再以
  `AL_PROFILE + specification + unit=m` 精確查詢 Published Pricebook。
- Published `AL_PROFILE / 40x40` 單價實測為 48 CNY/m；5.2 m 報價為 249.60 CNY，來源為
  `PUBLISHED_COMPANY_PRICEBOOK`，不再走 30 CNY/m 行業估價。
- 真實 W001 DWG/PDF 只含泛稱「型材」，沒有 40x40 或鋁材證據，因此不臆測規格；
  明確規格須來自 BOM、圖紙文字或後續人工審核。
- 聚焦測試：`58 passed`；全量測試：`684 passed, 1 warning in 49.92s`。
- 本地 Commit：`fix: normalize and price aluminum profiles`；不推送遠端。

## 2026-08-03 Milestone 3C：J029 無證據 CNC 費

- `resolve_machining()` 不再無條件加入 `_CNC_BASE_HOURS=0.5`；只有明確 CNC hint、孔或螺紋
  證據時才產生 CNC 項。
- 接通 Quotation Service 的 `sheet_metal` resolver 路由，並在 feature summary 顯示
  `quotation_route`。
- 薄板抽取新增不鏽鋼／鋼板／厚度關鍵字及 `N mm` 厚度解析；真實 J029 的
  「2mm厚度不鏽鋼」識別為 `SUS304 / 2.0 mm / SHEET_METAL`。
- 真實 `UC1007000773_J029.DWG` 實測 `cnc_items=[]`，40 元 CNC 費消失；材料文字無法
  完全正規化時保留 source=U、INCOMPLETE，沒有猜價。
- W001 同樣不再產生無加工證據的 CNC 項；合理的 cost completion 由 85.7% 更新為 83.3%。
- 聚焦測試：`47 passed`（另 UI 14 passed）；全量測試：
  `688 passed, 1 warning in 49.88s`。
- 本地 Commit：`fix: avoid unsupported CNC charges for sheet metal parts`；不推送遠端。

## 2026-08-03 Milestone 3D：J001 結構重量人工審核

- 以 `FRAME assembly + weld evidence` 識別無法由單張 2D 圖可靠分解的焊接結構，避免把
  整體 bounding box 當實心鋼材重量。
- 此情況建立 `UNRESOLVED_WELDMENT_STRUCTURE` 重量追蹤，重量為未知、材料成本為
  source=U，並以中文警告強制 `REVIEW_REQUIRED`，不依賴已有已知金額是否大於 0。
- 真實 `UC1003000436_J001.DWG` 實測：`status=REVIEW_REQUIRED`、`weight=-`、
  `weight_resolution=UNRESOLVED_WELDMENT_STRUCTURE`，沒有 BBOX 實心材料費。
- 中文原因：「焊接結構無法由2D圖可靠分解重量，需人工審核」。
- 聚焦測試：`36 passed`；全量測試：`690 passed, 1 warning in 49.94s`。
- 本地 Commit：`fix: require review for unresolved weldment structure weight`；不推送遠端。

### 9. 尚未完成

- Milestone 3 已完成：W002、W001、J029、J001 均已分別測試與原子提交。
- Milestone 4：價格發布資料品質。
- Milestone 5：管理與人工審核。
- Milestone 6：Windows 可攜式包。
- Milestone 7：全量驗證與最終交接。

---

## 狀態摘要

| 項目 | 狀態 |
|------|------|
| Git | master branch, clean working tree |
| Commits | `b504c43` (UI fix) + `51546f6` (batch) + `32bdf83` (API) + `74c4e49` (secrets) |
| 測試數 | **654** (50 files, +46 from baseline 608) |
| Tasks完成 | ✅ Task 0 + 0.1 + A + Phase 5.0 + 5.1 |
| 下一個任務 | W002 材料費 / W001 價格匹配 |
| DeepSeek | CONFIGURED — runtime/secrets/deepseek_api_key.txt |
| API | http://127.0.0.1:8000/docs |
| UI | .venv/Scripts/python -m quotation.ui.demo_app |
| 可攜式目錄 | dist/MechanicalQuotation/ |
| 資料庫 | runtime/data/quotation_history.db (SQLite) |

---

## ✅ Task 0: Published Company Pricebook Integration

### 正式調用鏈

```
PricingResolver.__init__()
  └─ PublishedPricebookLoader(data/current-version-pointer.json)
       ├─ validate: status=PUBLISHED, SHA256, version match, effective date
       └─ build indexes: 32 materials, 8 processes, 4 surfaces

PricingResolver.lookup(category, name)
  ├─ 1. PublishedPricebookLoader.lookup_*()
  │     └─ filters eligible_for_resolution=True (excludes Pending S)
  │     └─ returns PriceLookupResult(resolution_source=PUBLISHED_COMPANY_PRICEBOOK)
  └─ 2. Legacy YAML (DRAFT detected → LEGACY_YAML_DRAFT + fallback_warning)
```

### 修改文件 (Task 0 + 0.1)

| 檔案 | 操作 |
|------|------|
| `data/current-version-pointer.json` | NEW |
| `src/quotation/infrastructure/rules/published_pricebook_loader.py` | NEW |
| `src/quotation/infrastructure/rules/pricing_resolver.py` | REWRITTEN |
| `src/quotation/infrastructure/rules/calculators/__init__.py` | MODIFIED |
| `src/quotation/domain/quote.py` | MODIFIED (+12 trace fields) |
| `tests/unit/rules/test_pricebook_integration.py` | NEW (20 tests) |
| `tests/unit/rules/test_rule_engine.py` | REFACTORED (isolated from production pointer) |
| `tests/unit/rules/conftest.py` | NEW (test isolation) |
| `tests/unit/rules/test_rules.yaml` | NEW (test-specific prices) |
| `docs/CURRENT_HANDOFF.md` | UPDATED |

---

## J003 完整 Trace

```
=== material: S50C 材料費 ===
  amount=969.31 CNY | unit_price=10.0 CNY/kg
  source=C
  quote_price_source=C
  resolution_source=PUBLISHED_COMPANY_PRICEBOOK
  price_version_id=R01-COMPANY-PRICE-V1.0
  company_price_id=CP-ea9866e3316b
  origin_price_source=S
  origin_price_record_id=PR-B3D59928F064FF
  origin_supplier_id=None ⚠️
  price_basis=EXCLUDING_TAX

=== process: CNC 加工費 ===
  resolution_source=PUBLISHED_COMPANY_PRICEBOOK
  company_price_id=CP-38bf74b25194

=== process: TAP 加工費 (FALLBACK) ===
  resolution_source=LEGACY_YAML_DRAFT
  fallback_approval_status=DRAFT_REQUIRES_CORRECTION
  fallback_warning=True

=== surface: 表面鍍鉻 ===
  resolution_source=PUBLISHED_COMPANY_PRICEBOOK
  company_price_id=CP-75e0fa7fafca
```

---

## origin_supplier_id 結果

**S50C origin_supplier_id = `None`** ⚠️

**阻塞原因:** 這是 Published Snapshot 的**資料品質問題**，非程式碼問題。

Snapshot `company-pricebook-r01-v1.0-snapshot.json` 中的 S50C 記錄：
```json
{
  "company_price_id": "CP-ea9866e3316b",
  "origin_type": "SUPPLIER_PRICE_RECORD",
  "origin_supplier_id": null,
  "origin_price_record_id": "PR-B3D59928F064FF",
  "unit_price": 10.0
}
```

程式碼正確地：
1. 從 snapshot 讀取 `origin_supplier_id` → `null`
2. 將 `origin_type=SUPPLIER_PRICE_RECORD` 映射為 `origin_price_source=S`
3. 原樣保留 `origin_supplier_id=None` 到 `QuoteItem`

**要顯示為 Tongrui，需在 admin review 階段將 supplier_id 寫入 snapshot。** 這不在本次程式修改範圍內。

---

## Legacy Draft Fallback 警告機制

當 PricingResolver 回退到 Legacy YAML 且 YAML 狀態為 DRAFT 時：

- `resolution_source` = `LEGACY_YAML_DRAFT`（非 `LEGACY_YAML`）
- `fallback_approval_status` = YAML 中的 `status` 欄位值
- `fallback_warning` = `True`
- `fallback_reason` = 完整說明含版本號

當前生產 YAML (`rules/quotation-rules.yaml`) status = `DRAFT_REQUIRES_CORRECTION`，
因此所有 fallback 項目（如 TAP）都會被標記為 `LEGACY_YAML_DRAFT`。

---

## 測試結果

**590 passed, 2 skipped** ✓

| 類別 | 數量 |
|------|------|
| Pricebook integration tests | 20 (14 + 6 hardening) |
| Rule engine tests (isolated) | 21 |
| Cost completion tests | 7 |
| Other existing tests | 549 |
| **Total** | **597** |

---

## ✅ Task A: Quote Builder cost_completion dead code fix

### 問題
`quote_builder.py` L33-37 中的 `cost_completion` 計算位於 `return Quote(...)` 之後，永遠不執行。

### 修復
1. `Quote` 模型新增 `cost_completion: float` 欄位（`quote.py`）
2. `QuoteBuilder` 新增 `_calculate_cost_completion()` 私有純函數
3. 在 `return Quote(...)` **之前**計算並傳入 `cost_completion=...`
4. 移除 `return` 後的不可達程式碼
5. CLI 從 `quote.cost_completion` 讀取（原從 `source_summary` 讀取）

### cost_completion 計算規則
- `source=U` → 未完成
- `amount=None` → 未完成
- `amount=0` 且 `source≠U` → 合法已知價格（已完成）
- 空清單 → 0%
- 結果限制在 0.0–100.0

### J003 示例
| 指標 | 值 |
|------|-----|
| item 總數 | 4 |
| known | 4 |
| unknown | 0 |
| cost_completion | **100.0%** |
| status | COMPLETE |

### W001 示例
| 指標 | 值 |
|------|-----|
| item 總數 | 7 |
| known | 6 |
| unknown | 1 |
| cost_completion | **85.7%** |
| status | INCOMPLETE |

### 修改檔案
| 檔案 | 操作 |
|------|------|
| `src/quotation/domain/quote.py` | +cost_completion field |
| `src/quotation/infrastructure/rules/quote_builder.py` | +_calculate_cost_completion, fix dead code |
| `src/quotation/cli/main.py` | 改讀 quote.cost_completion |
| `tests/unit/rules/test_quote_builder.py` | +7 tests |

---

## 下一個原子任務

**W002 材料費 → SPCC 2mm 邏輯**

---

## 尚未處理

- W002 材料費 → SPCC 2mm 邏輯
- W001 AL_PROFILE 40x40 → frame profile 規格匹配
- J029 CNC 40 元 → `_CNC_BASE_HOURS` 對 0 holes
- J001 BBOX_ESTIMATE → REVIEW_REQUIRED 狀態
- RAL9003 V1.1 → 待發布 (DRAFT)

---

## Git Status — 已提交 (Checkpoint 2026-08-01)

### Commits
```
4311caf docs: update CURRENT_HANDOFF.md with checkpoint info
e4676df checkpoint: apply remaining Task 0/0.1 working tree modifications (5 files)
efb119e checkpoint: published pricebook integration and hardening  (root, 223 files)
```

### Working Tree: 4 files modified (Task A — pending commit)

### .gitignore 排除類別
| 類別 | 說明 |
|------|------|
| `*.xlsx`, `*.xls` | 二進制 Excel 文件 |
| `samples/drawings/*.DWG` | CAD 原始檔 (~28MB) |
| `samples/drawings/*.pdf` | PDF 圖紙 |
| `src/quotation/demo_*.dxf` | 生成的暫存 DXF |
| `data/price-review-*.json` | 價格審查中間產物 |
| `data/pricing-import-preview*.json` | 導入預覽中間產物 |
| `__pycache__/`, `*.pyc` | Python bytecode |
| `.venv/`, `.pytest_cache/`, `htmlcov/` | 虛擬環境/測試/覆蓋率 |
| `import_test.txt`, `pytest_result.txt` | 暫存測試文件 |

---

## 接管進度（2026-08-03）

### Milestone 4A：價格發布供應商來源追溯

- 根因：`tools/publish_company_prices.py` 在管理員選定來源紀錄後，將
  `origin_supplier_id` 固定寫成 `None`。
- 修正：發布流程從正式匯入包的 `pricing_source_records` 建立
  `record_id -> supplier_id` 對照，依 `Selected Origin Record ID` 保存供應商來源。
- 邊界：來源紀錄本身沒有供應商時維持 `None`，Resolver 不硬編碼或猜測供應商。
- 實際資料檢查：32 筆材料公司價中 27 筆可回溯具名供應商，5 筆來源本身無供應商。
- 獨立測試：`24 passed`（價格發布 helper + pricebook integration）。
- 預定提交：`fix: preserve supplier provenance during price publication`

### Milestone 4B：正式發布 RAL9003 公司表面處理價

- 新增正式發布工具 `tools/publish_pricebook_version.py`：只接受 `DRAFT`、阻擋錯誤為 0、
  正價、唯一鍵且 `EXCLUDING_TAX` 的公司價，發布時重建 SHA256 並原子更新版本指標。
- 已發布並啟用 `R01-COMPANY-PRICE-V1.1`：45 筆（材料 32、製程 8、表面 5）。
- RAL9003：`COATING_RAL9003 = 25 CNY/m²`、未稅、正式來源
  `PUBLISHED_COMPANY_PRICEBOOK`；描述中的 `RAL9003` 會正規化到此公司價。
- 表面計算器依發布單位選擇面積或重量；RAL9003 使用圖紙 `surface_area_mm2`，
  不再將公斤誤當平方米，缺面積時回傳未知成本要求補資料。
- v1.1 草稿仍維持 `DRAFT`，Loader 只讀 v1.1 的 `PUBLISHED` snapshot。
- 價格資料品質：發布快照重建 27/32 材料供應商追溯，並修正 RAL9003 亂碼說明。
- 獨立測試：規則與發布回歸 `140 passed`；最終發布快照重驗 `9 passed`。
- 預定提交：`feat: publish RAL9003 company surface price`

### Milestone 4C：TAP Draft 隔離

- v1.1 正式公司價不含 `TAP`。
- `TAP` 仍解析為 `LEGACY_YAML_DRAFT`，`company_price_id=None`、
  `quote_price_source=U`、`fallback_warning=True`、
  `fallback_approval_status=DRAFT_REQUIRES_CORRECTION`，報價完成度不會將其視為正式已知成本。
- UI/歷史記錄既有中文警告「舊版草稿規則，需人工確認」維持有效；未偽裝成正式公司價。

### Milestone 5：管理與人工審核

- 報價歷史：SQLite 支援圖號、文件名、狀態、日期篩選，明細包含 items、Quote 覆寫與
  完整人工審核軌跡；重存同一報價會先替換舊明細，不再累積重複行。
- 人工審核：支援材料、厚度、尺寸、表面處理、加工方式及指定 line_id 的人工價格；
  必填原因與操作者，記錄修改前後、時間、line_id、Quote 版本前後。
- 人工價：來源固定為 `M`，中文顯示「人工確認價格」，只寫當前 Quote 的 SQLite 明細，
  不修改 Published Pricebook；自動重算未稅、17% 稅額、含稅總額、完成度與狀態。
- 管理查詢：Published Pricebook 與供應商來源報價均唯讀；Pending 來源可查但不得進正式 Resolver。
- UI：原「報價記錄／價格管理／供應商管理」佔位頁已改成可搜尋表格；報價頁支援明細、
  人工審核、歷史 Excel 重匯出，價格與供應商頁提供唯讀查詢。
- FastAPI/OpenAPI：新增 `/api/v1/admin/quotes`、review queue、detail、review、history Excel、
  `/api/v1/admin/pricebook`、`/api/v1/admin/supplier-prices`。
- Excel：歷史重匯出包含「報價摘要／報價明細／人工審核軌跡」三個工作表。
- 聚焦測試：管理 UI/API/審核/Excel `29 passed`；人工價隔離重驗 `4 passed`。
- 全量測試：`707 passed`（1 個既有 Starlette deprecation warning；其餘為測試資源警告）。
- 預定提交：`feat: complete quotation management and manual review workflow`

### Milestone 6：Windows 可攜式包

- PyInstaller 6.21 `--onedir` 已建立 `dist/MechanicalQuotation/`（約 106.9 MB）。
- 包含 `MechanicalQuotation.exe`、根目錄 `config/`、`exports/`、sidecar
  `runtime/secrets/deepseek_api_key.txt`、UI/API/全部啟動與 API PID 停止批次檔。
- 新增 `--self-check` 與 `--smoke`：包內實跑皆 exit code 0；中文 HTML/JSON 報告為
  self-check `11/11`、demo smoke `3/3`，並產生 `exports/portable_smoke.xlsx`。
- 實機：封裝 UI 啟動後持續存活；封裝 FastAPI health/OpenAPI 成功，`stop_api.bat`
  依 `runtime/api.pid` 僅終止本包 API。
- Secret：交付 sidecar 為 0 bytes；以本機實際 DeepSeek Key 做精確 byte 比對，包內 0 份；
  credential-like pattern 0 筆；manifest 排除 sidecar。
- 第三方隔離：包內 ODA/ZWCAD 執行檔均為 0；根目錄 `config/user_settings.json`
  僅配置外部 converter 路徑，中望 CAD 保留人工檢圖用途。
- 指南：`docs/PORTABLE_DEMO_GUIDE.md`、`docs/PORTABLE_CHECKLIST.md`。
- 聚焦測試：`19 passed`；全量測試：`709 passed, 1 skipped`。
- PyInstaller 唯一建置警告為 ezdxf 可選 drawing add-on 未安裝 Pillow；核心 DXF Parser、
  UI、API、Excel 及包內 smoke 均已實跑通過。
- 預定提交：`feat: build portable Windows quotation demo package`

### Milestone 7：全量驗證與最終交接

- 最終測試：`711 passed, 1 warning`；warning 為 Starlette TestClient/httpx 上游棄用提示。
- 真實 Golden：20 DWG + 20 配對 PDF 全部經 ODA、PDF、正式報價與批量 Excel；
  Quote Ready 18、Review Required 2、Parse Failed 0。
- 準確度：WAPE `80.93%`、MAE `584.24 CNY`、Median absolute deviation
  `116.12 CNY`；分桶 `<=10%: 1`、`10-20%: 0`、`20-30%: 1`、`>30%: 18`。
- 準確度結論：技術管線已閉環，但尚不可宣稱價格已達自動核准門檻；歷史 BOM 缺少數量、
  有效期、工序、管理/採購成本拆分，且多數案例與現行規則差異大，必須持續供應商/工時校準。
- 價格：`R01-COMPANY-PRICE-V1.1`；Snapshot SHA256
  `15d5ada623b3a2106129c7dbbc278fc5b722da821d323a31b5809d176cd10ae3`。
- 稅務：20 案未稅 + 17% 稅額 = 含稅全部驗證；批量 Excel 6 工作表且非空。
- UI/API/AI：Tkinter 啟動成功；FastAPI health、14 個 OpenAPI paths、管理價查詢成功；
  DeepSeek configured/reachable/model_found/structured_call 全部成功，未輸出 Key/reasoning。
- 可攜包：self-check 11/11、smoke 3/3；ODA/ZWCAD 均未打包。
- Secret：以實際本機 Key 精確比對，包內 0 份；credential pattern 0；Git 提交內容不含 Key。
- 詳細逐案例報告：`docs/FINAL_VALIDATION_REPORT.md` 與 `.json`。
- 預定提交：`docs: finalize quotation system validation and handoff`

### 可攜版雙擊啟動修正（2026-08-03）

- 根因：`MechanicalQuotation.exe` 無參數時顯示 argparse help 並以 code 1 結束，雙擊表現為閃退。
- 修正：無參數預設啟動 Tkinter UI；`--ui`、`--api`、`--self-check`、`--smoke` 保持相容。
- 驗證：launcher 單元測試、重建 EXE 無參數程序存活、包內 self-check/smoke。

### Apex One 相容啟動器與 DWG/PDF 現場修正（2026-08-03）

- 第二層根因：修正無參數邏輯後，Trend Micro Apex One 仍將未簽章 PyInstaller bootloader
  隔離至 Security Agent `Suspect/Backup`；Windows Defender 無對應事件。未還原隔離檔、未修改
  企業防毒或 allow-list。
- 可攜包預設後端改為本機 PSF-signed Python runtime；`MechanicalQuotation.exe` 的
  Authenticode 為 `Valid`，Signer 為 Python Software Foundation。PyInstaller 後端保留為
  `tools/build_portable.py --backend pyinstaller`，供具代碼簽章/IT allow-list 的環境使用。
- 無參數只在 `sys.argv == [""]` 時啟動 UI；bat 改用標準
  `-m quotation.launcher --ui|--api|--self-check|--smoke`。實測 UI 窗口標題正確、程序 6 秒後
  仍存活，正常關閉後 EXE 仍存在。
- UI 使用 PSF-signed `pythonw.exe` 對應的 `MechanicalQuotation.exe`；FastAPI、自檢與 smoke
  使用同樣簽章有效的 `python.exe` 對應 `MechanicalQuotationConsole.exe`，避免 Uvicorn 在無
  console runtime 下退出。FastAPI 實測 health=`ok`、OpenAPI 14 paths、DWG health
  available=true/source=`local_appdata`，隨後依精確 PID 停止。
- 現場 DWG 失敗根因：ODA 27.1 位於使用者 LocalAppData administrative image，可攜包設定
  為空且舊 locator 只查 Program Files。現在只在受控路徑
  `%LOCALAPPDATA%/MechanicalQuotation/ODAFileConverter-*/ODAFileConverter.exe` 自動偵測；
  中望 CAD 2011 仍只作人工檢圖，不作 headless converter。
- 以畫面中的 `UC1002009711-R001`、`UC1002009712-R002` 在可攜包實跑：2 DWG 轉換均
  `SUCCESS`，2 個配對 PDF 分別抽取 111/90 個文字區塊，兩筆報價均 `COMPLETE`、無錯誤；
  證據為 `dist/MechanicalQuotation/runtime/reports/portable_external_drawings.json`。
- UI 批量表格「提示」欄失敗時改顯示第一條 error（沒有 error 才顯示 warning），且
  `UNSUPPORTED` 正確計入失敗統計。
- 包內驗證：self-check `11/11`、smoke `3/3`；實檔驗證 exit code 0；DeepSeek sidecar 空白，
  ODA/ZWCAD 均未打包。
- 測試：全量 `715 passed`；最終 launcher/portable/DWG 聚焦 `18 passed`。

### Milestone 8A：桌面工作流、中文明细与报价修正（2026-08-03）

- “新建报价”不再是示例按钮集合：可选择实际 DXF/DWG、执行单文件报价、重新计算并保存历史。
- “系统设置”已实现非敏感配置编辑、ODA 转换器选择与运行状态检查；DeepSeek 仅显示是否配置，
  不显示、复制或保存密钥。
- 报价历史、价格、供应商等详情由原始 JSON/文本弹窗改为分页表格；报价详情分为报价摘要、
  费用明细、人工调整和审核记录，并补充横向滚动与中文字段格式化。
- UI、状态、筛选、Excel 工作表及字段继续统一为简体中文；CLI `batch` 已实现扫描、报价、进度与
  中文 Excel 导出，不再保留“尚未实现”占位功能。
- 修复“材质为3mm厚度不锈钢”报价：规范为 SUS304，正确提取 3mm；重量计算不再仅对 SPCC
  使用图纸明确厚度，所有板材优先使用明确厚度。该回归现在能命中正式材料价格，并在计算证据中
  记录 `thickness_mm=3.0`。
- 未定价明细不再显示空白追踪：界面显示未定价原因、缺失信息和人工确认/智能辅助建议。
- DeepSeek 真实基准：configured/reachable/model_found/structured_call 均成功，模型
  `deepseek-v4-flash`，health latency `1058.6ms`；未输出或提交 Key。
- 阶段测试：全量单元测试首次 `665 passed, 3 failed, 1 skipped`，3 项均为中文断言同步并已修复；
  失败项与管理/设置/UI 聚焦复验 `71 passed, 1 skipped`；3mm 不锈钢及相关提取回归
  `52 passed`。

### Milestone 8B：扫描 PDF 本地 OCR（2026-08-03）

- `PdfReader` 的扫描 PDF 占位实现已替换为真实本地 OCR：PyMuPDF 逐页渲染，RapidOCR 使用
  ONNX Runtime 识别；OCR 引擎进程内复用，最多处理前 30 页，避免异常大文件无限占用资源。
- OCR 文字保存页码、位置和高度信息，导入置信度标记为低；缺少运行组件时返回中文明确错误，
  不再将空识别结果伪装成可用内容。
- 真实生成扫描 PDF 验证成功，识别结果为 `S50C PLATE 15mm`、`QTY 2 PCS`；本地单测
  `3 passed`。OCR 全程离线，不上传图纸。
- `pyproject.toml` 新增 PyMuPDF、RapidOCR、ONNX Runtime 运行依赖；系统与可携包自检新增
  “扫描 PDF 本地识别”组件检查，便携包指南补充离线数据边界。

### Milestone 8C：待确认项目的智能辅助参考估价（2026-08-03）

- 启用智能辅助时，所有来源为 `U` 的待确认费用行会单独请求 DeepSeek 给出参考单价、数量、
  计价单位、参考总额、中文理由与可信度；最多 20 行、图纸上下文最多 12000 字符。
- AI 估价保留在专用字段中，费用行仍为 `U`，不改变报价状态、不计入未税/税额/含税正式总价；
  必须经人工审核转为 `M` 后才参与正式计算。
- 新建报价表格、价格来源详情、历史 SQLite、历史详情和单笔/批量 Excel 均显示中文
  “智能辅助参考估价”，并明确标注“仅供人工参考，不计入正式总价”。
- 单文件“新建报价”和“批量报价”均提供“启用智能辅助”开关；两者使用同一外置密钥加载逻辑，
  不启用时不调用，启用后待确认费用行都会请求参考估价。
- 真实 DeepSeek 估价验证：测试费用行 `M6攻牙` 返回 `1.5元/孔 × 2 = 3.0元`、可信度 60%，
  并给出中文假设说明；未输出 Key，未写入正式价格表。
- 聚焦测试：DeepSeek 客户端、报价服务、历史、Excel、UI 与 DWG 工作流
  `45 passed, 1 skipped`。

### Milestone 8D：Windows 重建与最终全量验证（2026-08-03）

- 完整重建 `dist/MechanicalQuotation`，约 617.7 MB；包含本地 OCR 模型与 ONNX Runtime，
  不包含 ODA File Converter 或中望 CAD。
- 包内自检 `12/12`、报价/税务/Excel smoke `3/3`；包内实际扫描 PDF OCR 成功识别
  `S50C PLATE 15mm QTY 2`。FastAPI health=`ok`，OpenAPI 共 14 条路径。
- 全量测试 `726 passed, 1 skipped, 1 warning`；唯一 warning 为 Starlette TestClient 的
  上游弃用提示。
- 20 组真实 DWG + 20 组配对 PDF：19 组报价完整、1 组人工审核、0 组解析失败；
  正式报价 Excel 六个工作表均非空，未税 + 17% 税额 = 含税全部成立。
- DeepSeek 最终验证：configured/reachable/model_found/structured_call/reference_estimate_call
  全部成功，模型 `deepseek-v4-flash`，最终 health latency `538.2ms`。
- 针对内网服务偶发 HTTP 500，健康检查和结构化调用增加一次 0.5 秒重试；400 参数兼容回退
  保持不变。相关测试 `12 passed`。
- 安全扫描：本机实际 DeepSeek Key 在便携包中精确副本 `0`，文本凭证模式 `0`；第三方
  SPDX 许可证表和 `.dist-info/RECORD` 哈希索引不再作为 `sk-` 凭证误报来源。
- 准确度仍未达到自动核准水平：WAPE `81.04%`、MAE `585.05 CNY`，18/20 案偏差超过 30%；
  这反映历史价缺少数量/工序/管理成本拆分及现有供应商工时校准不足，必须保留人工审核。

### Milestone 12：用户登录、RBAC 与加密公共用户库（2026-08-04）

- 新增 `admin / engineer / sales / viewer` 四个系统角色，权限由 `config/roles.yaml` 与
  `config/permissions.yaml` 明确定义；未知权限默认拒绝。
- 登录密码采用 bcrypt 成本因子 12；至少 8 位并同时包含字母和数字；连续 5 次失败锁定 30 分钟；
  禁止停用最后一名有效管理员。
- 支持用户自行修改密码、管理员重置临时密码、最近 3 次密码复用拦截和首次登录强制改密标记。
- 用户资料以 AES-GCM 整包加密保存到 SMB `data/users.json`，同时维护
  `runtime/cache/smb/data/users.json` 加密缓存；SMB 在线优先，离线读取最近缓存。
- 用户库加密口令只从 `MECHANICAL_QUOTATION_USER_STORE_KEY` 或
  `runtime/secrets/user_store_key.txt` 读取；侧车目录已被 Git 忽略，未写入默认账号、密码或口令。
- 桌面程序新增首次管理员建立、其他电脑口令验证和用户登录窗口；登录后按角色隐藏无权限菜单；
  会话只存在内存，空闲 30 分钟锁定、绝对有效期 8 小时。
- FastAPI 新增 `/api/v1/auth/status|login|me|logout`；公共用户库建立后，报价、导出、人工审核、
  成本价格和 SMB 同步接口均执行 RBAC，未登录 401、无权限 403。
- 聚焦验证：认证核心、SMB/缓存、FastAPI RBAC 与桌面 UI `38 passed, 1 skipped`；
  API 权限联合回归 `24 passed`。运维说明见 `docs/USER_AUTH_AND_RBAC.md`。
- 全量验证：`753 passed`；其余为既有测试资源/SQLite 连接 ResourceWarning 与
  Starlette TestClient 上游弃用提示，无测试失败。
- 当前正式 SMB 尚未创建 `users.json`，因为不得代替管理员生成真实登录密码或加密口令；
  下一次启动桌面程序会由管理员本人输入并完成初始化。

### Milestone 13：供应商与原始价格维护（2026-08-04）

- 新增 SMB 供应商主档 `suppliers/suppliers.json` 和不可覆写报价目录
  `suppliers/prices/{supplier_id}/PR-*.json`；写入使用临时文件原子替换。
- 供应商支持新增、查询、搜索、编辑、停用和删除；已有历史报价时禁止删除，只能停用；
  停用或黑名单供应商禁止新增报价。
- 原始供应商报价为 S 来源，只允许追加新记录；有效价格进入 `PENDING_REVIEW`，未知价格保存为
  `null / UNKNOWN_PRICE`，禁止用 0 代替未知价格。待审核资料不会进入正式 Resolver。
- 新增中文/英文固定列 Excel 导入，逐行隔离错误并保留来源文件、工作表、单元格、报价单号和税务信息。
- FastAPI 新增供应商 CRUD、维护报价查询/新增和 Excel 导入接口；查询要求 `price.view_cost`，
  写入要求 `price.modify`；响应中的操作结果和错误使用中文。
- 桌面“供应商管理”升级为维护工作台：表格查看主档，支持新增、编辑、停用、删除、逐笔新增报价、
  导入 Excel 和表格查看历史报价；无维护权限的角色不显示写入按钮。
- `CacheSyncService` 新增 `suppliers` 资源；SMB 初始化目录新增 `suppliers/prices`。
- 正式 SMB 已执行不覆盖迁移：从现有审计包建立 6 家供应商主档，Published 价格未修改；
  同步状态 online，新增缓存 1 个文件，总缓存 7 个。
- 操作说明见 `docs/SUPPLIER_PRICE_MAINTENANCE.md`；聚焦服务/SMB `11 passed`、
  UI/API/服务 `35 passed, 1 skipped`，已登录工程师维护页面单独验证 `1 passed`。
- 全量验证：`760 passed, 1 skipped`；跳过项为环境可选测试，其余仅有既有 ResourceWarning 和
  Starlette TestClient 上游弃用提示。

### 登录首位管理员窗口可见性热修复（2026-08-05）

- 根因：认证流程隐藏 Tk 根窗口后，将管理员表单设置成该隐藏窗口的 transient 子窗口；
  Windows 会把子窗口一并隐藏或放到其他窗口后方，因此关闭首次提示后看不到输入画面。
- 修复：父窗口隐藏时不建立 transient 关系；管理员/登录表单按屏幕居中、主动显示、置顶 500ms、
  提升窗口层级并强制聚焦首个输入框。
- 新增回归：隐藏父窗口时表单必须为 `normal` 且 `winfo_viewable() == 1`；实测通过。

### Milestone 14：供应商价格审核与正式版本发布（2026-08-05）

- 新增管理员价格审核服务：待审核供应商 S 价格可批准或驳回；原始报价始终不可修改，审核决定以
  `change-requests/price-reviews/RV-PR-*.json` 追加保存。
- 批准前强制检查正数价格、明确单位、人民币币种、有效日期、来源报价单/文件，以及含税报价税率；
  含税价按明确税率换算为未税公司价，未知价格仍禁止用 0 代替。
- 批准会保留 `origin_supplier_id` 与 `origin_price_record_id`，以相同“类型+代码+规格+单位”替换
  当前默认价格，生成不可修改的新正式快照；旧版本指针进入 `prices/archive` 后再原子切换当前指针
  和 `version.txt`，随后同步本地缓存。
- 发布过程使用 5 分钟 SMB 独占锁和 `expected_current_version` 乐观版本校验，避免多管理员并发覆盖；
  批准与驳回均生成独立 `audit/AUD-PRICE-*.json` 审计记录。
- FastAPI 新增价格审核列表、批准发布和驳回三类路由；响应结果和错误均使用中文业务说明。
  桌面管理员侧栏新增“价格审核”，提供待审核/已批准/已驳回筛选、明细、批准及驳回操作；
  非管理员不显示该入口。
- 操作说明见 `docs/PRICE_APPROVAL_AND_PUBLICATION.md`。核心新增测试 `4 passed`；供应商维护、API、
  UI 联合回归 `46 passed`；全量回归 `769 passed, 1 skipped`，跳过项仍为环境可选测试。
- 正式 SMB 只读检查：公共槽在线，当前版本仍为 `R01-COMPANY-PRICE-V1.1`，供应商报价文件为 0；
  本次没有代替管理员批准真实价格，也没有修改正式价格版本。
- pytest 在沙箱权限下创建的新临时目录被 Windows 拒绝访问；改用已批准的正常 Windows 权限后
  聚焦及全量测试均通过。这是本机安全/ACL 环境现象，不是业务测试失败。

### 默认免登录与首位管理员恢复热修复（2026-08-05）

- 用户确认系统默认不需要登录。新增非敏感设置 `auth_enabled=false`：旧设置文件没有该字段时也按
  `false` 处理，桌面程序直接进入主画面；FastAPI 同样只在明确启用登录模式后执行 RBAC。
- 系统设置新增“启用账号登录与权限控制（保存后重启生效）”。免登录模式保留普通报价、批量报价、
  报价记录、已发布价格查询和系统设置，但隐藏必须记录明确操作者的“价格审核”入口。
- 修复首次建立管理员后的重复登录：账号创建成功后立即用刚输入的登录密码完成一次内部验证并建立
  会话，不再要求使用者重复输入，避免混淆“管理员登录密码”和“用户库加密口令”。
- 登录表单新增“显示密码和加密口令”开关，并进一步区分两类口令的中文标签。
- 新增受限恢复流程：仅当公共用户库恰好只有一名首位管理员、且该管理员从未成功登录时，才允许
  使用正确的用户库加密口令重设登录密码；恢复会清除失败次数和锁定状态。成功登录一次后该入口
  永久关闭，不能绕过正常管理员重置流程。
- 本机只读诊断确认用户库、缓存及加密口令均可正常读取；唯一账号 `admin` 为启用状态、未锁定，
  登录失败累计 3 次，根因不是用户库损坏。未读取或输出密码、密码哈希及加密口令内容。
- 聚焦回归：认证服务、运行接线、默认设置、登录对话框、免登录启动、桌面 UI 与 API 共
  `54 passed, 1 skipped`；全量回归 `777 passed, 1 skipped`。
- 真实启动冒烟：本机读取 `auth_enabled=false`，使用 `pythonw -m quotation.launcher --ui` 启动后
  进程持续存活 7 秒，未进入认证流程；测试结束后仅关闭本次启动的进程。
