# 中文导读开始
# 中文说明：本脚本用于演示“提示词similaritychecker”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：prompt similarity checker
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 66: Prompt Similarity

def similarity(p1, p2):
    set1 = set(p1.split())
    set2 = set(p2.split())

    return len(set1 & set2) / len(set1 | set2)

p1 = input("Prompt 1: ")
p2 = input("Prompt 2: ")

score = similarity(p1, p2)

print(f"Similarity Score = {score:.2f}")
