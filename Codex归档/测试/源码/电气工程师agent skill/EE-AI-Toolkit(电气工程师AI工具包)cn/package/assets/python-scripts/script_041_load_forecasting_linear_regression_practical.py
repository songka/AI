# 中文导读开始
# 中文说明：本脚本用于演示“负载预测线性回归practical”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：load forecasting linear regression practical
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 41: Load Forecasting

import numpy as np
from sklearn.linear_model import LinearRegression

# Example historical data
hours = np.array(range(1, 11)).reshape(-1, 1)
load = np.array([100, 120, 130, 150, 170, 160, 180, 200, 210, 220])

model = LinearRegression()
model.fit(hours, load)

future_hour = int(input("Enter next hour to predict: "))
prediction = model.predict([[future_hour]])

print(f"Predicted Load = {prediction[0]:.2f} MW")
