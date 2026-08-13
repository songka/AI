# 中文导读开始
# 中文说明：本脚本用于演示“smartmeter数据aggregator”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：smart meter data aggregator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 48: Smart Meter Aggregator

import pandas as pd

data = {
    "Hour": range(1, 6),
    "Load": [100, 120, 110, 130, 140]
}

df = pd.DataFrame(data)

total = df["Load"].sum()
average = df["Load"].mean()

print("Total Load =", total)
print("Average Load =", average)
