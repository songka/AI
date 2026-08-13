# 中文导读开始
# 中文说明：本脚本用于演示“功率triangle计算器”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：power triangle calculator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 32: Power Triangle

import math

P = float(input("Real Power (kW): "))
PF = float(input("Power Factor: "))

S = P / PF
Q = math.sqrt(S**2 - P**2)

print(f"Apparent Power = {S:.2f} kVA")
print(f"Reactive Power = {Q:.2f} kVAR")
