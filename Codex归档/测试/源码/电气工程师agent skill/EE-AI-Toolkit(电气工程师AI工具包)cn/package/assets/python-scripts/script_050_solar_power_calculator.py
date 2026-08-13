# 中文导读开始
# 中文说明：本脚本用于演示“光伏功率计算器”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：solar power calculator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 50: Solar Power

area = float(input("Panel Area (m^2): "))
irradiance = float(input("Irradiance (W/m^2): "))
efficiency = float(input("Efficiency (0–1): "))

power = area * irradiance * efficiency

print(f"Solar Power Output = {power:.2f} W")
