IO 表检查中文实操案例

使用目的：
这套文件用于课堂演示“错误用法”和“正确用法”的区别。
所有示例内容尽量使用中文，只有少量行业常用缩写保留，例如 DI、DO、PLC、CSV。

建议课堂顺序：
1. 打开 input/IO表样例.csv，让学员先肉眼找问题。
2. 打开 prompts/错误提示词.txt，演示为什么一句“帮我看看”不稳定。
3. 打开 skill/SKILL.md，说明技能（Skill）如何把岗位经验写成流程。
4. 运行 tools/检查IO表.py，得到 tool-output/工具检查结果.csv。
5. 打开 prompts/正确提示词.txt，让 AI 把工具结果转成工程预审表。
6. 打开 expected-output/工程预审结果.csv，对照预期输出。
7. 打开 concept-map.txt，分析每一部分分别属于什么概念。

推荐命令：
python outputs/ai-practice-cases/io-table-demo-cn/tools/检查IO表.py outputs/ai-practice-cases/io-table-demo-cn/input/IO表样例.csv
