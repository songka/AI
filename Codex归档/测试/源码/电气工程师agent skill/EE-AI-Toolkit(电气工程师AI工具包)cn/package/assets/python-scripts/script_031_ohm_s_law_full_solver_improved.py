# 中文导读开始
# 中文说明：本脚本用于演示“欧姆s定律full求解改进版”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：ohm s law full solver improved
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 31: Ohm’s Law Solver (Improved)

def solve_ohms(V=None, I=None, R=None):
    if V is None:
        return I * R
    elif I is None:
        return V / R
    elif R is None:
        return V / I

V = float(input("Voltage (0 if unknown): "))
I = float(input("Current (0 if unknown): "))
R = float(input("Resistance (0 if unknown): "))

if V == 0:
    print("Voltage =", solve_ohms(None, I, R))
elif I == 0:
    print("Current =", solve_ohms(V, None, R))
elif R == 0:
    print("Resistance =", solve_ohms(V, I, None))
