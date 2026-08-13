# 中文导读开始
# 中文说明：本脚本用于演示“电机startersizing”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：motor starter sizing
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 53: Motor Starter Sizing

power = float(input("Motor Power (kW): "))

current = power * 1000 / (400 * 0.8 * 1.732)

print(f"Estimated Motor Current = {current:.2f} A")

if current < 20:
    starter = "DOL Starter"
else:
    starter = "Star-Delta Starter"

print("Recommended Starter:", starter)
