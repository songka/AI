# 中文导读开始
# 中文说明：本脚本用于演示“功率system提示词packgenerator”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：power system prompt pack generator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 61: Power System Prompt Pack

def generate_prompts(system_type):
    prompts = [
    f"Perform load flow analysis for a {system_type} system.",
    f"Calculate fault current in a {system_type} network.",
    f"Analyze voltage stability of a {system_type} system."
    ]
    return prompts

system = input("Enter system type: ")

for p in generate_prompts(system):
    print("-", p)
