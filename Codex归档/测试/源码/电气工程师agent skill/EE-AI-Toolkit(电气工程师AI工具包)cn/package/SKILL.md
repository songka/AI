---
name: ee-ai-toolkit
description: 电气工程师 AI 工具包。用于 AI in Electrical Engineering、电气工程 AI、prompt engineering、power systems、smart grids、electrical calculations、design automation、data visualization、optimization、career toolkit、以及 100 个电气工程 Python 示例脚本相关问题。
compatibility: 需要 python3；可选使用 numpy、pandas、matplotlib、scikit-learn 运行部分附录示例。
metadata: {"openclaw":{"requires":{"bins":["python3"]}}}
---

# EE AI Toolkit（电气工程师 AI 工具包）

这个 skill 来自电气工程 AI 课程资料，面向电气工程师日常的计算、设计、分析、自动化、优化、数据可视化、提示词工程和职业发展任务。

使用这个 skill 时，要把它理解成一个“电气工程师 AI 工具箱”：

- `references/` 是资料库，用来查课程结构、知识点、提示词和脚本目录。
- `assets/python-scripts/` 是 Python 示例脚本库，用来复用或改造已有工程脚本。
- `scripts/search_ee_ai.py` 是资料检索工具，资料较大时先用它定位相关内容。

## 触发场景

当用户的问题涉及以下内容时，优先使用本 skill：

- 电气工程中的 AI 应用、提示词工程、AI 工具使用方法。
- 电力系统、智能电网、负载预测、故障分类、电能质量、优化决策。
- 电气计算，例如欧姆定律、电压降、三相功率、变压器、电缆选型、功率因数补偿。
- 数据处理和可视化，例如 CSV/Excel 数据读取、负载曲线、电压趋势、谐波图、异常检测。
- 需要复用 100 个电气工程 Python 示例脚本的任务。
- 电气工程职业工具，例如简历关键词、技能差距、面试题、项目作品集等。

## 资料读取顺序

激活本 skill 后，不要一次性读取全部资料。请根据问题类型读取最小必要资料：

- 课程结构、资料来源、主题路由：读取 `references/course-index.md`。
- 快速回答、复习或概念梳理：读取 `references/condensed-lessons.md`。
- 需要接近原文、练习、示例流程或完整上下文：读取 `references/source-digest.md`。
- 提示词、提示词改写、提示词模板：读取 `references/prompt-library.md`。
- Python 示例脚本、脚本编号、脚本用途：读取 `references/python-script-catalog.md`，再使用 `assets/python-scripts/` 中对应脚本。
- 需要核对原始 HTML 课程资料时：使用 `assets/source-html/`，或解压 `assets/source-html.tar.gz`。

资料较大时，先用检索脚本定位，再读取相关引用文件：

```bash
python3 {baseDir}/scripts/search_ee_ai.py --query "load forecasting"
```

## 输出规则

生成或修改工程答案时，必须保持以下约束：

- 明确单位、输入假设、公式、计算步骤和验证方法。
- AI 生成的设计、保护、配电、并网、优化和故障分析结果只能作为工程草案或教学示例。
- 对安全关键或合规相关电气工程问题，必须提醒用户结合适用标准、仿真工具、现场数据和有资质工程审查进行验证。
- 需要代码时，优先复用或改造 `assets/python-scripts/` 中最接近的脚本，不要从零编造。
- 用户用中文提问时，默认用中文回答；必要的英文术语、文件名、脚本名和变量名保持原样。
