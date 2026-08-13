# 中文导读开始
# 中文说明：本脚本用于演示“工程报告generatoradvanced”相关的电气工程计算、数据处理或 AI 辅助分析方法。
# 原始英文主题：engineering report generator advanced
# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。
# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。
# 中文导读结束
# Script 64: Engineering Report Generator

def create_report(title, results):
    report = f"\n=== {title} ===\n"

    for key, value in results.items():
        report += f"{key}: {value}\n"

    report += "===================="
    return report

data = {
    "Voltage": "230 V",
    "Current": "10 A",
    "Power": "2300 W"
}

print(create_report("Electrical Analysis Report", data))
