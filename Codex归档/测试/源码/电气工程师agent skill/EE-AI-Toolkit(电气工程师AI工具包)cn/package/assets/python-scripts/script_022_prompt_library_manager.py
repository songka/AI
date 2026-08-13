# 中文导读开始
# 中文说明：本脚本用于演示“提示词librarymanager”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：prompt library manager
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 22: Prompt Library Manager

import json

prompts = {}

while True:
    choice = input("Add/View/Exit: ").lower()

    if choice == "add":
        key = input("Enter category: ")
        value = input("Enter prompt: ")
        prompts.setdefault(key, []).append(value)

    elif choice == "view":
        print(json.dumps(prompts, indent=2))

    elif choice == "exit":
        break
