# 中文导读开始
# 中文说明：本脚本用于演示“interviewquestiongenerator”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：interview question generator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 27: Interview Question Generator

topics = {
    "power": ["Explain load flow", "What is power factor?"],
    "circuit": ["Explain Ohm’s law", "What is Kirchhoff’s law?"]
}

topic = input("Enter topic (power/circuit): ")

for q in topics.get(topic, []):
    print("-", q)
