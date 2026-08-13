# 中文导读开始
# 中文说明：本脚本用于演示“capacitorplacementoptimizer”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：capacitor placement optimizer
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 93: Capacitor Placement

buses = [1, 2, 3, 4]
voltages = [0.95, 0.92, 0.97, 0.90]

min_voltage = min(voltages)
index = voltages.index(min_voltage)

print(f"Place capacitor at Bus {buses[index]} (Lowest Voltage)")
