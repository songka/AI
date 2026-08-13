# 中文导读开始
# 中文说明：本脚本用于演示“singleline数据generator”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：single line data generator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 60: Single-Line Data

equipment = []

n = int(input("Number of components: "))

for i in range(n):
    name = input("Component name: ")
    rating = input("Rating: ")
    equipment.append((name, rating))

print("\nSingle-Line Data:")
for item in equipment:
    print(f"{item[0]} - {item[1]}")
