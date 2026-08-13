# 中文导读开始
# 中文说明：本脚本用于演示“负载预测线性回归”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：load forecasting linear regression
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 2: Load Forecasting

import numpy as np
from sklearn.linear_model import LinearRegression

# Sample data
days = np.array([1, 2, 3, 4, 5]).reshape(-1, 1)
load = np.array([400, 420, 450, 470, 500])

model = LinearRegression()
model.fit(days, load)

prediction = model.predict([[6]])

print(f"Predicted Load for Day 6: {prediction[0]:.2f} MW")
