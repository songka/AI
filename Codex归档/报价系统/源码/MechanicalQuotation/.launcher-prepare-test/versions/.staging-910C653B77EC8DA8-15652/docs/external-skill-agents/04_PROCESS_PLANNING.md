# 工艺路线 Skill 对接说明

步骤代码：`PROCESS_PLANNING`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.PROCESS_PLANNING` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：已确认材料、特征、尺寸、公差、粗糙度、热处理、备注、零件类别和已发布工艺小时费率；
可读取既有费用行防止重复工艺。

提示词：选择成本最低且足以完成的设备并给出工序顺序。普通平面、直边、槽、常规孔优先普通铣床；
复杂曲面、多轴、高重复定位精度或明确要求才用 CNC；车削件优先车床。同一去除加工不得同时返回
铣床和 CNC 重复计费。若两者都可行，分别估算工时并按“工时×已发布工价”比较总成本；质量、
精度或结构证据不足时不得仅因便宜采用。Skill 不得编造或修改正式单价。

返回字段：`process_route`、`equipment_choices`、`rejected_expensive_options`、`evidence`、
`confidence`。

验收：普通孔板选择铣床；有复杂三维曲面证据才选择 CNC；候选路线包含工时、工价、总成本和淘汰
理由；无证据的工艺必须删除或待确认。四类零件分别测试。
