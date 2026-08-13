# 中文导读开始
# 中文说明：本脚本用于演示“电阻network求解”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：resistance network solver
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 37: Series & Parallel Resistance

import math

choice = input("Series or Parallel (s/p): ").lower()

values = list(map(float, input("Enter resistances (space separated): ").split()))

if choice == "s":
    result = sum(values)
elif choice == "p":
    result = 1 / sum(1/r for r in values)

print(f"Equivalent Resistance = {result:.2f} Ohm")
