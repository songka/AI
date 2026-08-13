# 中文导读开始
# 中文说明：本脚本用于演示“功率systemresultcomparator”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：power system result comparator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 14: Result Comparator

import numpy as np

python_results = np.array([220, 225, 230])
reference_results = np.array([221, 224, 229])

error = python_results - reference_results

print("Errors:", error)
print("Mean Error:", np.mean(error))
