# 中文导读开始
# 中文说明：本脚本用于演示“工程decisionsupportsystem”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：engineering decision support system
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 100: Decision Support

options = {
    "Design A": {"cost": 100, "efficiency": 90},
    "Design B": {"cost": 120, "efficiency": 95}
}

score = {}

for k, v in options.items():
    score[k] = v["efficiency"] / v["cost"]

best = max(score, key=score.get)

print("Best Design:", best)
print("Score:", score[best])
