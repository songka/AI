# 中文导读开始
# 中文说明：本脚本用于演示“提示词versiontracker”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：prompt version tracker
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 68: Prompt Version Tracker

history = []

while True:
    p = input("Enter prompt (or 'exit'): ")

    if p == "exit":
        break

    history.append(p)

print("\nPrompt Versions:")
for i, h in enumerate(history):
    print(f"Version {i+1}: {h}")
