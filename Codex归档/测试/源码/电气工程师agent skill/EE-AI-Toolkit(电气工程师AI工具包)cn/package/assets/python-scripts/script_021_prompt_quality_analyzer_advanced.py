# 中文导读开始
# 中文说明：本脚本用于演示“提示词qualityanalyzeradvanced”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：prompt quality analyzer advanced
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 21: Prompt Quality Analyzer

def analyze_prompt(prompt):
    score = 0

    if "calculate" in prompt.lower():
        score += 1
    if "step-by-step" in prompt.lower():
        score += 1
    if "with equations" in prompt.lower():
        score += 1
    if "example" in prompt.lower():
        score += 1

    return score

prompt = input("Enter prompt: ")

score = analyze_prompt(prompt)
print(f"Prompt Quality Score: {score}/4")
