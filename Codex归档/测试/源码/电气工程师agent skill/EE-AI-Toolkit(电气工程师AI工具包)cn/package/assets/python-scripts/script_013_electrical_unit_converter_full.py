# 中文导读开始
# 中文说明：本脚本用于演示“electrical单位转换full”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：electrical unit converter full
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 13: Unit Converter

def convert(value, from_unit, to_unit):
    units = {
    "kW": 1000,
    "MW": 1000000,
    "W": 1
    }
    return value * units[from_unit] / units[to_unit]

value = float(input("Enter value: "))
from_unit = input("From unit (W/kW/MW): ")
to_unit = input("To unit (W/kW/MW): ")

result = convert(value, from_unit, to_unit)

print(f"{result:.2f} {to_unit}")
