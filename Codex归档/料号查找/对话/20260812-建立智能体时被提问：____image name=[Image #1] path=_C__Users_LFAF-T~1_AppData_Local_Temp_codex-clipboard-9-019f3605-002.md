ts`
- `reason` 或 `note` 保持简短，只写可核查判断依据，不写长篇说明
- 若无法确认品牌，相关字段必须与证据强度一致，不得过度确认

### JSONL output

若用户要求 JSONL，则每行输出一个对象，字段与 CSV 对应，保持一致命名。

## Quality Bar

- 先求正确，再求覆盖。
- 宁可把结果标记为 `suspected` 或 `unknown`，也不要把不充分线索写成 `confirmed`。
- 不要因为型号部分匹配、图片大致相似、或供应商口径单一，就直接确认品牌。
- 若一个候选只在图片、另一个候选只在文字上匹配，要明确保留冲突，不要强行定论。

## Handling Uploaded Files

- 当用户上传清单文件时，优先把它当成待研究的输入清单。
- 逐条处理，不要改写原文件内容，也不要把任务理解成文件清洗。
- 如果输入信息严重不足，仍应尽量输出结构化结果，但把对应行标为 `unknown` 或 `suspected`，并在 `notes` 或 `reason` 中简短写明缺失点。

## Web Research

需要时使用 Web search 查找公开网页信息、品牌官网、产品页、PDF 和图片证据。

检索时优先组合这些线索：

- 料号 / 型号
- 名称或品类词
- 规格词
- 供应商或品牌词
- 中英文别名

## Safety

- 不要伪造证据 URL。
- 不要把猜测包装成事实。
- 不要省略结论等级。
- 不要输出与证据无关的品牌断言。
- 当无法确认时，明确输出 `unknown` 或 `suspected`。
[64] user: 工作分阶段不是用2个skill吗？为什么你的提示词里面没有了
[65] user: 请同时把2个skills也生成好，打包发给我
[81] user: 我已经更新智能体，如何测试
[83] user: 流程2有问题，需要优先找中文网站，没有可以淘宝查找。图片需要多角度多张图片
[103] user: 
# Files mentioned by the user:

## asset_result_uc3_sample_5.csv: //tsclient/D/Codex项目/料号检测系统/查询/asset_result_uc3_sample_5.csv

## asset_pending_uc3_sample_5.csv: //tsclient/D/Codex项目/料号检测系统/查询/asset_pending_uc3_sample_5.csv

## My request for Codex:
这是我的输入输出，请检测
[154] user: 
# Files mentioned by the user:

## asset_result_uc3_sample_11.csv: //tsclient/D/Codex项目/料号检测系统/查询/asset_result_uc3_sample_11.csv

## asset_pending_uc3_sample_11.csv: //tsclient/D/Codex项目/料号检测系统/查询/asset_pending_uc3_sample_11.csv

## My request for Codex:
查找AS228T-A的料官网应该是https://www.delta-china.com.cn/zh-CN/products/PLC-Programmable-Logic-Controllers/4259/，bing就直接能找到.我之前让你用淘宝查找，你确认下是否可行，因为我测试是需要先登录的，看看有哪里适合抓图的
[177] user: 
# Files mentioned by the user:

## fnd_gfm.tsv: C:/Users/lfaf-test/Documents/料号查找/fnd_gfm.tsv

## My request for Codex:
好的我改完了，我们来跑整个流程吧
[217] user: 
# Files mentioned by the user:

## 系统物料20260701.tsv: //tsclient/D/Codex项目/料号检测系统/查询/系统物料20260701.tsv

## My request for Codex:
这个是最新数据
[218] user: 能不能把我与codex的也做成技能，每次有下一步说明
[235] tool apply_patch result: Exit code: 1
Wall time: 0.4 seconds
Output:
Failed to delete file C:\Users\lfaf-test\Documents\料号查找\.codex\skills\external-part-pipeline-manager\SKILL.md
[236] assistant: 删除旧模板时被 Windows 文件属性拦了一下，不影响。我换成直接覆盖更新文件内容，并补齐目录。
[237] tool shell_command call: {"command":"Get-Item -Force -LiteralPath '.codex\\skills\\external-part-pipeline-manager\\SKILL.md' | Select-Object FullName,Attributes,IsReadOnly,Length","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[238] tool shell_command result: Exit code: 0
Wall time: 1 seconds
Output:

FullName                                                                                Attributes IsReadOnly Length
--------                                                                                ---------- ---------- ------
C:\Users\lfaf-test\Documents\料号查找\.codex\skills\external-part-pipeline-manager\SKILL.md    Archive      False   4073
[239] assistant: 我先看一下模板开头，用 update hunk 来整体替换，避免 Windows 删除句柄的问题。
[240] tool shell_command call: {"command":"Get-Content -LiteralPath '.codex\\skills\\external-part-pipeline-manager\\SKILL.md' -TotalCount 80","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[241] tool shell_command result: Exit code: 0
Wall time: 1 seconds
Output:
---
name: external-part-pipeline-manager
description: [TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it.]
---

# External Part Pipeline Manager

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" -> "Reading" -> "Creating" -> "Editing"
- Structure: ## Overview -> ## Workflow Decision Tree -> ## Step 1 -> ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" -> "Merge PDFs" -> "Split PDFs" -> "Extract Text"
- Structure: ## Overview -> ## Quick Start -> ## Task Category 1 -> ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" -> "Colors" -> "Typography" -> "Features"
- Structure: ## Overview -> ## Guidelines -> ## Specifications -> ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" -> numbered capability list
- Structure: ## Overview -> ## Core Capabilities -> ### 1. Feature -> ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources (optional)

Create only the resource directories this skill actually needs. Delete this section if no resources are required.

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Codex for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Codex's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Codex should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Codex produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)
[242] assistant: 接下来是一次比较大的替换：把初始化模板替换成正式流程说明。然后我会加 `openai.yaml` 和 handoff 参考文档。
[243] tool apply_patch call: *** Begin Patch
*** Update File: .codex/skills/external-part-pipeline-manager/SKILL.md
@@
 ---
 name: external-part-pipeline-manager
-description: [TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it.]
+description: Manage the local Codex side of the external purchased-part research pipeline for fnd_gfm/system material TSV files. Use when working on this project to index TSV data, export ChatGPT Web handoff CSV batches, import brand and asset result CSVs, validate outputs, update assets manifests, and always report the current stage plus the exact next step.
 ---
 
 # External Part Pipeline Manager
 
-## Overview
-
-[TODO: 1-2 sentences explaining what this skill enables]
-
-## Structuring This Skill
-
-[TODO: Choose the structure that best fits this skill's purpose. Common patterns:
-
-**1. Workflow-Based** (best for sequential processes)
-- Works well when there are clear step-by-step procedures
-- Example: DOCX skill with "Workflow Decision Tree" -> "Reading" -> "Creating" -> "Editing"
-- Structure: ## Overview -> ## Workflow Decision Tree -> ## Step 1 -> ## Step 2...
-
-**2. Task-Based** (best for tool collections)
-- Works well when the skill offers different operations/capabilities
-- Example: PDF skill with "Quick Start" -> "Merge PDFs" -> "Split PDFs" -> "Extract Text"
-- Structure: ## Overview -> ## Quick Start -> ## Task Category 1 -> ## Task Category 2...
-
-**3. Reference/Guidelines** (best for standards or specifications)
-- Works well for brand guidelines, coding standards, or requirements
-- Example: Brand styling with "Brand Guidelines" -> "Colors" -> "Typography" -> "Features"
-- Structure: ## Overview -> ## Guidelines -> ## Specifications -> ## Usage...
-
-**4. Capabilities-Based** (best for integrated systems)
-- Works well when the skill provides multiple interrelated features
-- Example: Product Managem<truncated omitted_approx_tokens="2184" />dd File: .codex/skills/external-part-pipeline-manager/references/web-agent-handoff.md
+# Web Agent Handoff
+
+Use these instructions when preparing files for ChatGPT Web.
+
+## Brand Batch Prompt
+
+```text
+请使用 external-part-brand-id 处理附件：
+
+{brand_pending_file}
+
+只做品牌识别，不要查官网图片。
+
+输出文件名必须是：{brand_result_file}
+输出 CSV，不要输出 Markdown 表格。
+CSV 字段必须严格为：
+part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note
+
+正式批次规则：
+- 原始 brand_raw 可作为重要线索，但如果要写 confirmed，必须给真实证据 URL。
+- 如果只有原始表品牌、还没有联网证据，应写 suspected，并在 note 说明“原始表有品牌，待官网核验”。
+- 型号可能有 0/O、1/I/l、缺少连接符、型号不全等问题，必须保留 original_model 和 normalized_model。
+- 不允许留空 evidence_url。
+- 不允许无证据确认品牌。
+```
+
+## Asset Batch Prompt
+
+```text
+请使用 external-part-official-image-finder 处理附件：
+
+{asset_pending_file}
+
+只做官网产品页和图片 URL 查找，不要重新做品牌识别。
+
+输出文件名必须是：{asset_result_file}
+输出 CSV，不要输出 Markdown 表格。
+CSV 字段必须严格为：
+part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note
+
+规则：
+- 优先中文官网、中国官网、台湾官网、香港官网、中文 PDF。
+- 中文资料不足时再查中文工业品平台和国际分销商。
+- 淘宝/天猫只作为人工补图参考，不作为自动抓图来源。
+- 每个料号尽量输出 3-6 张多角度图片，每张图片一行。
+- image_url 优先使用可直接下载的 .jpg/.jpeg/.png/.webp。
+- 产品页 URL 放 official_url，不要重复当作 image_url。
+```
*** End Patch
[244] tool apply_patch result: Exit code: 0
Wall time: 0 seconds
Output:
Success. Updated the following files:
A .codex/skills/external-part-pipeline-manager/agents/openai.yaml
A .codex/skills/external-part-pipeline-manager/references/web-agent-handoff.md
M .codex/skills/external-part-pipeline-manager/SKILL.md
[245] assistant: Skill 已经写好了。我现在跑基础校验，再打一个压缩包，方便你以后迁移到别的项目或重新安装。
[246] tool shell_command call: {"command":"python 'C:\\Users\\lfaf-test\\.codex\\skills\\.system\\skill-creator\\scripts\\quick_validate.py' '.codex\\skills\\external-part-pipeline-manager'","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[247] tool shell_command call: {"command":"Get-ChildItem -Recurse -File -LiteralPath '.codex\\skills\\external-part-pipeline-manager' | Select-Object FullName,Length,LastWriteTime | Sort-Object FullName","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[248] tool shell_command result: Exit code: 1
Wall time: 1.2 seconds
Output:
Traceback (most recent call last):
  File "C:\Users\lfaf-test\.codex\skills\.system\skill-creator\scripts\quick_validate.py", line 10, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
[249] tool shell_command result: Exit code: 0
Wall time: 1.3 seconds
Output:

FullName                                                                                                       Length L
                                                                                                                      a
                                                                                                                      s
                                                                                                                      t
                                                                                                                      W
                                                                                                                      r
                                                                                                                      i
                                                                                                                      t
                                                                                                                      e
                                                                                                                      T
                                                                                                                      i
                                                                                                                      m
                                                                                                                      e
--------                                                                                                       ------ -
C:\Users\lfaf-test\Documents\料号查找\.codex\skills\external-part-pipeline-manager\agents\openai.yaml                 296 2
C:\Users\lfaf-test\Documents\料号查找\.codex\skills\external-part-pipeline-manager\references\web-agent-handoff.md   1831 2
C:\Users\lfaf-test\Documents\料号查找\.codex\skills\external-part-pipeline-manager\SKILL.md                          6530 2
[250] assistant: 校验脚本本身需要 `PyYAML`，系统 Python 没装这个库；我不会为了这个去装依赖。我改用 Codex 自带运行时再试一次，如果也没有就做手动校验。
[251] tool load_workspace_dependencies call: {}
[252] tool load_workspace_dependencies result: Workspace dependencies are available for this local desktop thread.

### Workspace Dependencies
Use these bundled paths for sheets, slides, documents, PDFs, images, or browser automation:
- Bundle version: `26.630.12135`
- Git executable: `C:\Users\lfaf-test\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe`
- Node.js executable: `C:\Users\lfaf-test\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`
- Node.js packages: `C:\Users\lfaf-test\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules`
- pnpm executable: `C:\Users\lfaf-test\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd`
- Python executable: `C:\Users\lfaf-test\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- Python packages: `C:\Users\lfaf-test\.cache\codex-runtimes\codex-primary-runtime\dependencies\python`
- Native binaries: `C:\Users\lfaf-test\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin`
[253] assistant: 我拿到 Codex 自带 Python 路径了，用它来跑校验；这个环境通常带齐插件依赖。
[254] tool shell_command call: {"command":"& 'C:\\Users\\lfaf-test\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' 'C:\\Users\\lfaf-test\\.codex\\skills\\.system\\skill-creator\\scripts\\quick_validate.py' '.codex\\skills\\external-part-pipeline-manager'","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[255] tool shell_command result: Exit code: 1
Wall time: 1.3 seconds
Output:
Traceback (most recent call last):
  File "C:\Users\lfaf-test\.codex\skills\.system\skill-creator\scripts\quick_validate.py", line 10, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
[256] assistant: 两个 Python 环境都没有 `PyYAML`，所以自动校验跑不了。我做手动校验时发现 `short_description` 可能还是偏短，我顺手拉长一点，避免 UI 元数据再次被拒。
[257] tool apply_patch call: *** Begin Patch
*** Update File: .codex/skills/external-part-pipeline-manager/agents/openai.yaml
@@
 interface:
   display_name: "外购件流程管家"
-  short_description: "管理料号资料流水线并持续给出下一步"
+  short_description: "管理外购件资料流水线状态并持续给出下一步"
   default_prompt: "Use $external-part-pipeline-manager to inspect the current pipeline state and tell me the exact next step."
*** End Patch
[258] tool apply_patch result: Exit code: 0
Wall time: 0 seconds
Output:
Success. Updated the following files:
M .codex/skills/external-part-pipeline-manager/agents/openai.yaml
[259] assistant: 现在我打包这个 Codex skill，并做一个轻量检查：确认前置信息、openai.yaml、引用文档都在包里。
[260] tool shell_command call: {"command":"$zip='external_part_pipeline_manager_skill.zip'; if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }; Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory((Resolve-Path '.codex\\skills\\external-part-pipeline-manager'), (Join-Path (Get-Location) $zip)); Get-Item -LiteralPath $zip | Select-Object FullName,Length,LastWriteTime","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[261] tool shell_command result: Exit code: 0
Wall time: 1.5 seconds
Output:

FullName                                                                   Length LastWriteTime    
--------                                                                   ------ -------------    
C:\Users\lfaf-test\Documents\料号查找\external_part_pipeline_manager_skill.zip   4219 2026/7/6 15:26:02
[262] tool shell_command call: {"command":"Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::OpenRead((Resolve-Path 'external_part_pipeline_manager_skill.zip')).Entries | Select-Object FullName,Length | Sort-Object FullName","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[263] tool shell_command call: {"command":"Get-Content -LiteralPath '.codex\\skills\\external-part-pipeline-manager\\SKILL.md' -TotalCount 20","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[264] tool shell_command call: {"command":"Get-Content -LiteralPath '.codex\\skills\\external-part-pipeline-manager\\agents\\openai.yaml'","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[265] tool shell_command result: Exit code: 0
Wall time: 1.5 seconds
Output:

FullName                        Length
--------                        ------
agents\openai.yaml                 305
references\web-agent-handoff.md   1831
SKILL.md                          6530
[266] tool shell_command result: Exit code: 0
Wall time: 1.3 seconds
Output:
---
name: external-part-pipeline-manager
description: Manage the local Codex side of the external purchased-part research pipeline for fnd_gfm/system material TSV files. Use when working on this project to index TSV data, export ChatGPT Web handoff CSV batches, import brand and asset result CSVs, validate outputs, update assets manifests, and always report the current stage plus the exact next step.
---

# External Part Pipeline Manager

Use this skill for the `鏂欏彿鏌ユ壘` workflow whenever the user asks to continue, test, run, resume, import, export, check, or plan the external purchased-part pipeline.

The workflow has two agents:

- Codex desktop: local files, deterministic scripts, indexing, CSV handoff, result import, validation, image download, `assets.json`.
- ChatGPT Web agent: web research through `external-part-brand-id` and `external-part-official-image-finder`.

Do not use Codex quota for broad web research unless the user explicitly asks. Prefer producing clean handoff files for ChatGPT Web.

## Mandatory Response Pattern

Every time this skill is used, finish with a short "涓嬩竴姝? block containing:
[267] tool shell_command result: Exit code: 0
Wall time: 1.3 seconds
Output:
interface:
  display_name: "澶栬喘浠舵祦绋嬬瀹?
  short_description: "绠＄悊澶栬喘浠惰祫鏂欐祦姘寸嚎鐘舵€佸苟鎸佺画缁欏嚭涓嬩竴姝?
  default_prompt: "Use $external-part-pipeline-manager to inspect the current pipeline state and tell me the exact next step."

policy:
  allow_implicit_invocation: true
[268] assistant: PowerShell 控制台又把中文显示成乱码，这不一定代表文件坏了。不过我需要确认 YAML 字符串没有因为编码显示问题丢引号；我用 Python 以 UTF-8 读原文检查。
[269] tool shell_command call: {"command":"python -c \"from pathlib import Path; p=Path('.codex/skills/external-part-pipeline-manager/agents/openai.yaml'); print(repr(p.read_text(encoding='utf-8')))\"","workdir":"C:\\Users\\lfaf-test\\Documents\\料号查找","timeout_ms":10000}
[270] tool shell_command result: Exit code: 0
Wall time: 1 seconds
Output:
'interface:\n  display_name: "外购件流程管家"\n  short_description: "管理外购件资料流水线状态并持续给出下一步"\n  default_prompt: "Use $external-part-pipeline-manager to inspect the current pipeline state and tell me the exact next step."\n\npolicy:\n  allow_implicit_invocation: true\n'
[271] assistant: 可以，已经做好了 Codex 侧的流程技能：

- Skill 目录：[external-part-pipeline-manager](</C:/Users/lfaf-test/Documents/料号查找/.codex/skills/external-part-pipeline-manager/SKILL.md>)
- Web 交接提示模板：[web-agent-handoff.md](</C:/Users/lfaf-test/Documents/料号查找/.codex/skills/external-part-pipeline-manager/references/web-agent-handoff.md>)
- 备份压缩包：[external_part_pipeline_manager_skill.zip](</C:/Users/lfaf-test/Documents/料号查找/external_part_pipeline_manager_skill.zip>)

这个 skill 规定了每次 Codex 接手时都要判断当前阶段，并在结尾输出：

```text
下一步
执行人:
输入:
动作:
输出:
```

它覆盖这些场景：

- 索引最新 TSV
- 导出 `brand_pending_*.csv`
- 等 ChatGPT Web 返回 `brand_result_*.csv`
- 导入品牌结果
- 导出 `asset_pending_*.csv`
- 等 ChatGPT Web 返回 `asset_result_*.csv`
- 导入图片结果
- 后续下载图片、更新 `assets.json`

以后你可以直接说：

```text
使用 $external-part-pipeline-manager，检查当前流程状态，告诉我下一步。
```

我尝试跑官方 quick validate，但本机两个 Python 环境都缺 `PyYAML`，校验脚本跑不起来；我已做了手动结构检查，包里包含 `SKILL.md`、`agents/openai.yaml`、`references/web-agent-handoff.md`。

**下一步**
执行人: Codex  
输入: `系统物料20260701.tsv` 或当前 `fnd_gfm.tsv`  
动作: 把索引脚本升级为支持 `--source`，然后用最新 TSV 重跑索引  
输出: 新的 `data/indexed_parts.jsonl`、`data/target_parts.jsonl`、`reports/index_report.md`
[272] user: 数据量过大会不会在哪个步骤卡死，是否需要做计划任务，比如在技能里面直接判断，如果需要的就在下一步的提示词里面加入计划任务，并让完成后自动销毁
[273] user: 数据量过大会不会在哪个步骤卡死，是否需要做计划任务，比如在技能里面直接判断，如果需要的就在下一步的提示词里面加入计划任务，并让完成后自动销毁
[274] assistant: 会，尤其会卡在两个地方：网页端联网研究和图片抓取/下载。我的建议不是全程计划任务，而是让 Codex skill 按批量阈值自动判断：小批直接跑，大批生成“计划任务提示词”，让 ChatGPT Web 分批执行，完成后再提醒你删除/停用任务。先检查一下当前能不能直接接入自动化工具，同时我会把这个判断规则写进流程管家 skill。
[275] assistant: 我会把判断规则写得很具体：品牌识别超过 50 条、图片查找超过 10-20 条、下载图片超过 100 张，就建议拆批或计划任务；并且计划任务只能处理“当前批次/待处理目录”，完成后必须输出“可删除/停用任务”的指令，避免一直跑。
[276] tool apply_patch call: *** Begin Patch
*** Update File: .codex/skills/external-part-pipeline-manager/SKILL.md
@@
 ## Mandatory Response Pattern
 
 Every time this skill is used, finish with a short "下一步" block containing:
 
 - `执行人`: Codex / ChatGPT Web / 人工
 - `输入`: exact file path or file name
 - `动作`: one sentence
 - `输出`: expected file path or file name
+- `是否建议计划任务`: yes/no, with a short reason
 
 If work was performed, also state:
 
 - what changed
 - which files were created or updated
 - whether validation passed
@@
 ## Pipeline Stages
+
+## Batch and Schedule Policy
+
+Large batches can stall in web research and image collection. Decide whether to run directly or schedule by these thresholds:
+
+- Local TSV indexing: run directly unless the file is unusually large (>100k rows).
+- Brand identification handoff: run directly for <=50 rows; suggest a ChatGPT Web scheduled task for >50 rows.
+- Official page and image lookup: run directly for <=10 rows; suggest a ChatGPT Web scheduled task for >10 rows, because image search is slower.
+- Image download/update: run directly for <=100 direct image URLs; suggest a Codex automation or split batches for >100 URLs.
+
+When a schedule is suggested, include it in the "下一步" block and generate a schedule prompt that:
+
+1. Processes only one explicit pending file or one explicit pending folder.
+2. Writes the expected result file name.
+3. Stops when the expected result file is produced or when no pending rows remain.
+4. Does not start the next stage automatically unless the user explicitly asked for that.
+5. Says "本计划任务可删除/停用" after completion.
+
+Do not create an actual automation unless the user explicitly asks to create it. If the user asks to create a Codex automation, use the automation tool rather than writing raw schedule directives.
@@
 ## ChatGPT Web Rules
 
 Brand identification must use `external-part-brand-id`.
 
 Official image lookup mus<truncated omitted_approx_tokens="376" />pg/.jpeg/.png/.webp。
 - 产品页 URL 放 official_url，不要重复当作 image_url。
 ```
+
+## Brand Schedule Prompt
+
+Use this for ChatGPT Web scheduled tasks when the brand batch is larger than 50 rows.
+
+```text
+请按计划任务方式处理本批次，只处理这个附件：
+
+{brand_pending_file}
+
+使用 external-part-brand-id。
+输出文件名必须是：{brand_result_file}
+输出 CSV，不要输出 Markdown 表格。
+不要查官网图片，不要进入下一阶段。
+
+如果已生成 {brand_result_file} 或发现没有待处理行，请停止任务，并在最后回复：
+本计划任务可删除/停用。
+```
+
+## Asset Schedule Prompt
+
+Use this for ChatGPT Web scheduled tasks when the asset batch is larger than 10 rows.
+
+```text
+请按计划任务方式处理本批次，只处理这个附件：
+
+{asset_pending_file}
+
+使用 external-part-official-image-finder。
+输出文件名必须是：{asset_result_file}
+输出 CSV，不要输出 Markdown 表格。
+不要重新做品牌识别，不要下载图片，不要生成 assets.json。
+每个料号尽量输出 3-6 张多角度图片 URL。
+
+如果已生成 {asset_result_file} 或发现没有待处理行，请停止任务，并在最后回复：
+本计划任务可删除/停用。
+```
*** Update File: docs/local_pipeline_runbook.md
@@
 ## 当前状态
@@
 等待：
 
 - ChatGPT 网页智能体返回 `brand_result_uc3_0001.csv`
+
+## 批量与计划任务建议
+
+- 品牌识别：每批 50 条以内可手动跑；超过 50 条建议使用 ChatGPT Web 计划任务。
+- 官网图片查找：每批 10 条以内可手动跑；超过 10 条建议使用 ChatGPT Web 计划任务。
+- 图片下载：100 张以内可直接让 Codex 下载；超过 100 张建议拆批或使用 Codex 自动化。
+
+计划任务必须只处理一个明确输入文件，生成一个明确输出文件。完成后要求回复：
+
+`本计划任务可删除/停用。`
*** End Patch
>>> TRANSCRIPT END
Reviewed Codex session id: 019f2c13-71df-7160-b449-4e71cced4ad5
Some conversation entries were omitted.
The Codex agent has requested the following action:
>>> APPROVAL REQUEST START
Assess the exact planned action below. Use read-only tool checks when local state matters.
Planned action JSON:
{
  "cwd": "C:\\Users\\lfaf-test\\Documents\\料号查找",
  "files": [
    "C:\\Users\\lfaf-test\\Documents\\料号查找\\.codex\\skills\\external-part-pipeline-manager\\references\\web-agent-handoff.md",
    "C:\\Users\\lfaf-test\\Documents\\料号查找\\.codex\\skills\\external-part-pipeline-manager\\SKILL.md",
    "C:\\Users\\lfaf-test\\Documents\\料号查找\\docs\\local_pipeline_runbook.md"
  ],
  "patch": "*** Begin Patch\n*** Update File: .codex/skills/external-part-pipeline-manager/SKILL.md\n@@\n ## Mandatory Response Pattern\n \n Every time this skill is used, finish with a short \"下一步\" block containing:\n \n - `执行人`: Codex / ChatGPT Web / 人工\n - `输入`: exact file path or file name\n - `动作`: one sentence\n - `输出`: expected file path or file name\n+- `是否建议计划任务`: yes/no, with a short reason\n \n If work was performed, also state:\n \n - what changed\n - which files were created or updated\n - whether validation passed\n@@\n ## Pipeline Stages\n+\n+## Batch and Schedule Policy\n+\n+Large batches can stall in web research and image collection. Decide whether to run directly or schedule by these thresholds:\n+\n+- Local TSV indexing: run directly unless the file is unusually large (>100k rows).\n+- Brand identification handoff: run directly for <=50 rows; suggest a ChatGPT Web scheduled task for >50 rows.\n+- Official page and image lookup: run directly for <=10 rows; suggest a ChatGPT Web scheduled task for >10 rows, because image search is slower.\n+- Image download/update: run directly for <=100 direct image URLs; suggest a Codex automation or split batches for >100 URLs.\n+\n+When a schedule is suggested, include it in the \"下一步\" block and generate a schedule prompt that:\n+\n+1. Processes only one explicit pending file or one explicit pending folder.\n+2. Writes the expected result file name.\n+3. Stops when the expected result file is produced or when no pending rows remain.\n+4. Does not start the next stage automatically unless the user explicitly asked for that.\n+5. Says \"本计划任务可删除/停用\" after completion.\n+\n+Do not create an actual automation unless the user explicitly asks to create it. If the user asks to create a Codex automation, use the automation tool rather than writing raw schedule directives.\n@@\n ## ChatGPT Web Rules\n \n Brand identification must use `external-part-brand-id`.\n \n Official image lookup must use `external-part-official-image-finder`.\n@@\n Taobao/Tmall policy:\n@@\n - Never use as the only source for `product_url_confidence=confirmed`.\n+\n+## Schedule Prompt Templates\n+\n+Use these when a batch is large enough to schedule.\n+\n+Brand schedule prompt:\n+\n+```text\n+请按计划任务方式处理本批次，只处理这个附件：\n+\n+{brand_pending_file}\n+\n+使用 external-part-brand-id。\n+输出文件名必须是：{brand_result_file}\n+不要查官网图片，不要进入下一阶段。\n+如果已生成 {brand_result_file} 或发现没有待处理行，请停止任务，并在最后回复：本计划任务可删除/停用。\n+```\n+\n+Asset schedule prompt:\n+\n+```text\n+请按计划任务方式处理本批次，只处理这个附件：\n+\n+{asset_pending_file}\n+\n+使用 external-part-official-image-finder。\n+输出文件名必须是：{asset_result_file}\n+不要重新做品牌识别，不要下载图片，不要生成 assets.json。\n+每个料号尽量输出 3-6 张多角度图片 URL。\n+如果已生成 {asset_result_file} 或发现没有待处理行，请停止任务，并在最后回复：本计划任务可删除/停用。\n+```\n@@\n 5. Report the next action with exact command or handoff instruction.\n+6. If the pending batch exceeds the thresholds in \"Batch and Schedule Policy\", include the matching schedule prompt in the next-step instructions.\n*** Update File: .codex/skills/external-part-pipeline-manager/references/web-agent-handoff.md\n@@\n ## Asset Batch Prompt\n@@\n - image_url 优先使用可直接下载的 .jpg/.jpeg/.png/.webp。\n - 产品页 URL 放 official_url，不要重复当作 image_url。\n ```\n+\n+## Brand Schedule Prompt\n+\n+Use this for ChatGPT Web scheduled tasks when the brand batch is larger than 50 rows.\n+\n+```text\n+请按计划任务方式处理本批次，只处理这个附件：\n+\n+{brand_pending_file}\n+\n+使用 external-part-brand-id。\n+输出文件名必须是：{brand_result_file}\n+输出 CSV，不要输出 Markdown 表格。\n+不要查官网图片，不要进入下一阶段。\n+\n+如果已生成 {brand_result_file} 或发现没有待处理行，请停止任务，并在最后回复：\n+本计划任务可删除/停用。\n+```\n+\n+## Asset Schedule Prompt\n+\n+Use this for ChatGPT Web scheduled tasks when the asset batch is larger than 10 rows.\n+\n+```text\n+请按计划任务方式处理本批次，只处理这个附件：\n+\n+{asset_pending_file}\n+\n+使用 external-part-official-image-finder。\n+输出文件名必须是：{asset_result_file}\n+输出 CSV，不要输出 Markdown 表格。\n+不要重新做品牌识别，不要下载图片，不要生成 assets.json。\n+每个料号尽量输出 3-6 张多角度图片 URL。\n+\n+如果已生成 {asset_result_file} 或发现没有待处理行，请停止任务，并在最后回复：\n+本计划任务可删除/停用。\n+```\n*** Update File: docs/local_pipeline_runbook.md\n@@\n ## 当前状态\n@@\n 等待：\n \n - ChatGPT 网页智能体返回 `brand_result_uc3_0001.csv`\n+\n+## 批量与计划任务建议\n+\n+- 品牌识别：每批 50 条以内可手动跑；超过 50 条建议使用 ChatGPT Web 计划任务。\n+- 官网图片查找：每批 10 条以内可手动跑；超过 10 条建议使用 ChatGPT Web 计划任务。\n+- 图片下载：100 张以内可直接让 Codex 下载；超过 100 张建议拆批或使用 Codex 自动化。\n+\n+计划任务必须只处理一个明确输入文件，生成一个明确输出文件。完成后要求回复：\n+\n+`本计划任务可删除/停用。`\n*** End Patch",
  "tool": "apply_patch"
}
>>> APPROVAL REQUEST END
