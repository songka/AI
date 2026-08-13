IO 表检查实操案例

使用目的：
这套文件用于课堂演示“错误用法”和“正确用法”的区别。
学员不需要写代码，也可以按步骤完成。

建议课堂顺序：
1. 打开 input/sample-io-table.csv，先让学员肉眼看 1 分钟。
2. 打开 prompts/wrong-prompt.txt，演示错误问法为什么不稳定。
3. 打开 skill/SKILL.md，说明技能（Skill）如何把经验写成流程。
4. 运行工具脚本，得到 tool-output/check-result.csv。
5. 打开 prompts/correct-prompt.txt，让 AI 把工具结果转成工程评审表。
6. 打开 expected-output/engineering-review.csv，对照预期输出。
7. 打开 concept-map.txt，分析每一部分分别属于什么概念。

推荐命令：
python outputs/skill-examples/io-table-review/scripts/check_io_table.py outputs/ai-practice-cases/io-table-demo/input/sample-io-table.csv
