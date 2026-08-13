# 中文导读开始
# 中文说明：本脚本用于演示“功率计算器”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：power calculator
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 1: Power Calculator

def calculate_power(voltage, current):
    return voltage * current

if __name__ == "__main__":
    V = float(input("Enter Voltage (V): "))
    I = float(input("Enter Current (A): "))

    P = calculate_power(V, I)
    print(f"Power = {P:.2f} Watts")
