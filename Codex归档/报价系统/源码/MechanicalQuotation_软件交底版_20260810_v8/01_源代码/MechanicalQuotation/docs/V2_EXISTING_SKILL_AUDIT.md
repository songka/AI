# 现有报价 Skill 审计与 V2 迁移清单

审计日期：2026-08-10。范围为本项目源码 Skill 与本机同步缓存中的公共槽报价 Skill；没有修改公共槽线上配置。

## 发现的资源

| 资源 | 状态 | 当前是否实际执行 | V2 决策 |
|---|---|---:|---|
| `part.cost.estimator` 3.0.0 | 已注册的文件夹 Skill，声明 10 个步骤，不含 `PART_CLASSIFICATION` | 否。缓存配置版本 5 的 11 个步骤全部为 `builtin` | `DEPRECATE` 为兼容资源，先不删除；拆分后再逐路由迁移 |
| `external-quotation-skill-refactor` | 本项目给 Codex 使用的开发工具 Skill | 不参与报价运行 | `REPLACE` 为 V2 Skill/Agent 重构与训练工具 |
| 5 个内置 Agent 契约 | 备注理解、零件分类、工艺规划、待确认项估价、价格审核 | 按 AI 可用性与内部回退执行 | `KEEP/SHARE`，允许在设置页查看内容 |
| 内部规则步骤 | 特征、材料、分项计价、汇总、合理性约束、风险汇总等 | 是 | `KEEP/SHARE`，不为了凑 11 个步骤而包装成 Agent |

## `part.cost.estimator` 问题

1. 一个资源同时声明备注、特征、材料、工艺、工时、计价、未知估价、汇总、审核和人工建议，权限与失败边界过大。
2. 未声明零件分类，却含四类输入参考；不能在分类前可靠选择类别专用逻辑。
3. 未声明具体工艺范围和每步 Agent，因此无法区分铣、车、磨、焊等专业估算器。
4. 当前所有路由为内置，实际报价并未调用该 Skill；直接删除没有即时执行影响，但公共槽兼容和历史调试仍需保留版本资产。

## 建议拆分目标

| 新资源建议 | 类型 | 路由层 | 来源能力 | 迁移动作 |
|---|---|---|---|---|
| `company.drawing-notes` | 共用 Skill + Agent | 全局步骤 1 | 备注理解 | `SHARE` |
| `company.part-classifier` | 共用 Skill + Agent | 全局步骤 2 | 新补充分类型契约 | `CREATE` |
| `company.machining-plan` | Skill，可绑定规划 Agent | 加工件步骤 5 | 加工工艺规划 | `SPLIT` |
| `company.sheetmetal-plan` | Skill，可绑定规划 Agent | 钣金件步骤 5 | 钣金工艺规划 | `SPLIT` |
| `company.weldment-plan` | Skill，可绑定规划 Agent | 焊接件步骤 5 | 焊接工艺规划 | `SPLIT` |
| `company.frame-plan` | Skill，可绑定规划 Agent | 型材组装步骤 5 | 型材工艺规划 | `SPLIT` |
| `company.<process>-time` | Skill/Agent | 类别 + 具体工艺步骤 6 | 各工艺工时 | 按证据逐项 `SPLIT/CREATE` |
| `company.price-audit` | 共用 Skill + Agent | 步骤 10，必要时工艺覆盖 | 通用价格审核 | `SHARE` |
| `company.excel-quotation` | 命令型 Skill | Excel 任务，不作为推理 Agent | Excel 读写修改/导出 | `SPLIT` |

不要一次创建全部目标资源。先用代表性图纸和人工确认工时证明某个工艺的规则，再发布该工艺 Skill/Agent；无证据的能力标记 `UNKNOWN` 并继续使用内置规则。

## 安全迁移顺序

1. 保持现有公共槽配置不变。
2. 在本地创建并测试一个新资源版本。
3. 管理员检测资源，双击确认清单和内容。
4. 只迁移一个类别/工艺/步骤路由并开启调试。
5. 对照内置结果、人工标准和回退场景。
6. 验收后扩大路由；全部替代且历史查询不再依赖时，才考虑下线旧 Skill。
