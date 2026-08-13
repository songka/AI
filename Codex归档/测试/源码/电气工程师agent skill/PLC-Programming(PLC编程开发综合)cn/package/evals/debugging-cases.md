<!-- 中文导读开始 -->

## 中文导读

本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Debugging eval cases

## Case D1: Alarm re-latch

User:
“报警复位后下一扫又来了，帮我排查。”

Should trigger:

- yes

Task type:

- debugging

Required:

- separate symptom from hypothesis
- inspect trigger, reset permissive, and re-latch path
- mention scan-cycle possibility
- avoid pretending root cause is already proven

Forbidden:

- giving a single unsupported cause as fact
- skipping reset path analysis

## Case D2: Output flashes then drops

User:
“启动条件满足但输出只亮一下就没了。”

Should trigger:

- yes

Task type:

- debugging

Required:

- suspect overwrite or ownership conflict
- provide writer-list or ownership-trace style debug approach
- keep hypotheses separate from facts

Forbidden:

- blaming hardware first without logic checks
- ignoring multi-writer risk

## Case D3: Step never advances

User:
“步骤卡在 20 不往下走。”

Should trigger:

- yes

Task type:

- debugging

Required:

- inspect transition condition, timer or counter, interlock, and state ownership
- propose a step-by-step isolation path

Forbidden:

- jumping directly to code rewrite
- ignoring current state visibility
