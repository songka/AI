# 中文导读开始
# 中文说明：本脚本用于演示“信号绘图改进版”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：signal plotter improved
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 12: Signal Plotter

import numpy as np
import matplotlib.pyplot as plt

t = np.linspace(0, 1, 100)
signal = 230 * np.sin(2 * np.pi * 50 * t)

plt.plot(t, signal)
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.title("AC Signal (50 Hz)")
plt.show()
