# 中文导读开始
# 中文说明：本脚本用于演示“提示词performancetracker”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：prompt performance tracker
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 30: Prompt Performance Tracker

prompts = {
    "calculate power": 4,
    "design circuit": 5,
    "load flow": 3
}

sorted_prompts = sorted(prompts.items(), key=lambda x: x[1], reverse=True)

print("Top Prompts:")
for p, score in sorted_prompts:
    print(p, "->", score)
