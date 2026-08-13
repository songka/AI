# 中文导读开始
# 中文说明：本脚本用于演示“transmissionloss优化”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：transmission loss optimization
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 91: Loss Optimization

import numpy as np

currents = np.array([100, 90, 80, 70])
R = 0.5

losses = currents**2 * R

for i, l in zip(currents, losses):
    print(f"Current {i} A -> Loss {l:.2f} W")

best = currents[np.argmin(losses)]
print("Optimal Current for Minimum Loss:", best)
