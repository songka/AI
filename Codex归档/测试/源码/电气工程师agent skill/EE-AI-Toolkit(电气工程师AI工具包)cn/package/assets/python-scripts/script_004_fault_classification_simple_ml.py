# 中文导读开始
# 中文说明：本脚本用于演示“故障分类基础机器学习”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：fault classification simple ml
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 4: Fault Classification

from sklearn.tree import DecisionTreeClassifier

# Sample data: [current, voltage]
X = [[10, 220], [50, 200], [80, 180]]
y = ["Normal", "Line Fault", "Short Circuit"]

model = DecisionTreeClassifier()
model.fit(X, y)

test = [[60, 190]]
prediction = model.predict(test)

print(f"Predicted Fault Type: {prediction[0]}")
