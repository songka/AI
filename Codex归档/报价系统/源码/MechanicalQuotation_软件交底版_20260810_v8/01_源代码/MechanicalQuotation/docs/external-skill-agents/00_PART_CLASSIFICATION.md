# 零件类别分类 Skill 对接说明

步骤代码：`PART_CLASSIFICATION`

这是类别路由前置步骤。输入为图纸原文和内置几何/制造特征，输出只能是 `MACHINING`、
`SHEET_METAL`、`WELDMENT` 或 `FRAME_ASSEMBLY`。不得使用图号、文件名或历史价格猜测类别。

返回字段：`part_category`、`confidence`、`evidence`、`alternatives`。分类可信度低于 0.6、
类别越界或结果无效时，主程序必须回退内置几何规则，并在 Skill 调试中显示回退原因。

分类完成后，主程序才根据类别选择后续十步 Skill 路由。
