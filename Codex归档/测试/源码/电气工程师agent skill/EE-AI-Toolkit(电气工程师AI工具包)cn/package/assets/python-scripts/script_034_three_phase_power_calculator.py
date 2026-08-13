# 中文导读开始
# 中文说明：本脚本用于演示“三相相功率计算器”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：three phase power calculator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 34: Three-Phase Power

import math

V = float(input("Line Voltage (V): "))
I = float(input("Current (A): "))
PF = float(input("Power Factor: "))

P = math.sqrt(3) * V * I * PF

print(f"Three-phase Power = {P/1000:.2f} kW")
