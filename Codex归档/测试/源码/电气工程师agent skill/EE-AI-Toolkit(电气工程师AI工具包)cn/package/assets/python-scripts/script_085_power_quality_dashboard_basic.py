# 中文导读开始
# 中文说明：本脚本用于演示“功率qualitydashboardbasic”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：power quality dashboard basic
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 85: Power Quality Dashboard

voltage = float(input("Voltage (V): "))
frequency = float(input("Frequency (Hz): "))
harmonics = float(input("THD (%): "))

print("\n--- Power Quality ---")
print("Voltage:", voltage)
print("Frequency:", frequency)
print("THD:", harmonics)

if voltage < 210 or voltage > 240:
    print("Voltage Out of Range!")

if frequency < 49 or frequency > 51:
    print("Frequency Out of Range!")
