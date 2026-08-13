# 中文导读开始
# 中文说明：本脚本用于演示“提示词logger”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：prompt logger
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 17: Prompt Logger

prompt = input("Enter prompt: ")

with open("prompts.txt", "a") as f:
    f.write(prompt + "\n")

print("Prompt saved.")
