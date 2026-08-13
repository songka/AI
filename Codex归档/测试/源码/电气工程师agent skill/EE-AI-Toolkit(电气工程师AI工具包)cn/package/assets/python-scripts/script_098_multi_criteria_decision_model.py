# 中文导读开始
# 中文说明：本脚本用于演示“multicriteriadecisionmodel”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：multi criteria decision model
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 98: Multi-Criteria Decision

options = {
    "Option A": [0.8, 0.7, 0.9],
    "Option B": [0.9, 0.6, 0.8]
}

weights = [0.4, 0.3, 0.3]

scores = {}

for k, v in options.items():
    scores[k] = sum(w*x for w, x in zip(weights, v))

best = max(scores, key=scores.get)

print("Best Option:", best)
print("Score:", scores[best])
