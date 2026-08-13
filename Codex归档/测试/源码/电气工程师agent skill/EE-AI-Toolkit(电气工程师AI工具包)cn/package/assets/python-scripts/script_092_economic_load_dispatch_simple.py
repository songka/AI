# 中文导读开始
# 中文说明：本脚本用于演示“economic负载dispatch基础”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：economic load dispatch simple
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 92: Economic Load Dispatch

cost_A = 10 # $/MW
cost_B = 15

demand = float(input("Total Demand (MW): "))

# Use cheaper generator first
gen_A = min(demand, 100)
gen_B = demand - gen_A

cost = gen_A * cost_A + gen_B * cost_B

print(f"Generator A: {gen_A} MW")
print(f"Generator B: {gen_B} MW")
print(f"Total Cost = ${cost:.2f}")
