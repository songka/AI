# 中文导读开始
# 中文说明：本脚本用于演示“jobapplicationtracker”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：job application tracker
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 78: Job Tracker

jobs = []

while True:
    company = input("Company (or 'exit'): ")

    if company == "exit":
        break

    status = input("Status (applied/interview/offer): ")
    jobs.append((company, status))

print("\nApplications:")
for j in jobs:
    print(j[0], "-", j[1])
