# 中文导读开始
# 中文说明：本脚本用于演示“parametersweepplot”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：parameter sweep plot
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 40: Parameter Sweep

import numpy as np
import matplotlib.pyplot as plt

V = 230
I = np.linspace(1, 50, 50)

P = V * I

plt.plot(I, P)
plt.xlabel("Current (A)")
plt.ylabel("Power (W)")
plt.title("Power vs Current")
plt.show()
