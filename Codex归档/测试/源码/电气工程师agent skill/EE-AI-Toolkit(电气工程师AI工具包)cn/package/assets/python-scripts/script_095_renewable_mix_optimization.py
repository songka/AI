# 中文导读开始
# 中文说明：本脚本用于演示“renewablemix优化”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：renewable mix optimization
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 95: Renewable Mix

solar = float(input("Solar Output (MW): "))
wind = float(input("Wind Output (MW): "))
cost_solar = 5
cost_wind = 7

total_cost = solar * cost_solar + wind * cost_wind

print(f"Total Cost = {total_cost}")
