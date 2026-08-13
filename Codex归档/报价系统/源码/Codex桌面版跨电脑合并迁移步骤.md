# Codex 桌面版跨电脑合并迁移步骤

适用场景：

- 旧电脑项目根目录：`C:\Users\lfaf-test\Documents`
- 新电脑项目根目录：`D:\codex`
- 新电脑已经存在自己的项目和 Codex 对话，需要合并，不能覆盖。
- 操作系统：Windows。

## 一、下载迁移工具

推荐使用开源工具 **Codex Migrate**：

- 项目主页：<https://github.com/ChenglongLi777/codex-migrate>
- Windows 下载页面：<https://github.com/ChenglongLi777/codex-migrate/releases>

在 Releases 页面下载 Windows ZIP，解压后运行：

```text
Codex Migrate.exe
```

说明：这是第三方社区工具，不是 OpenAI 官方产品。Windows SmartScreen 可能提示风险。请确认下载地址来自上述 GitHub 仓库，并按照 Release 页面提供的信息校验文件 checksum。

## 二、需要使用的路径映射

在 Codex Migrate 中设置下面这条父目录映射：

```text
C:\Users\lfaf-test\Documents=D:\codex
```

例如：

```text
C:\Users\lfaf-test\Documents\报价系统
→ D:\codex\报价系统
```

项目下面的相对目录结构应保持不变。

## 三、旧电脑：准备项目文件

Codex Migrate 主要迁移 Codex 对话、索引和项目关联，不会自动复制实际项目文件。

先通过以下任一方式将项目转移到新电脑：

1. 已经提交到 GitHub/GitLab 的项目，在新电脑重新克隆到 `D:\codex`。
2. 没有上传到 Git 的项目，通过移动硬盘、局域网或可信存储复制。

目标结构示例：

```text
D:\codex\报价系统
D:\codex\项目B
D:\codex\项目C
```

不要遗漏未提交的代码、未跟踪文件、配置文件和项目使用的本地资料。

## 四、旧电脑：导出 Codex 数据

1. 保存正在进行的工作。
2. 完全退出 Codex Desktop。
3. 如果打开了 Codex CLI、VS Code Codex 扩展或其他 Codex 进程，也将其关闭。
4. 打开 `Codex Migrate.exe`。
5. 选择旧电脑的 Codex 数据目录：

```text
C:\Users\lfaf-test\.codex
```

6. 选择 Export/Backup，将备份保存到移动硬盘或加密目录。
7. 导出后应得到类似目录：

```text
Codex_backup\
```

8. 保留这份原始备份，不要手工修改其中的 JSONL 或 SQLite 文件。

重要：备份包含私人对话、命令、工具输出、图片、本机路径和配置。不要上传到公开 GitHub 仓库或公开网盘。工具通常不会复制根目录登录凭据 `auth.json`，新电脑应使用自己的账号正常登录。

## 五、新电脑：导入前备份

1. 确保新电脑的项目已经放到 `D:\codex`。
2. 确认新电脑原有 Codex 项目和对话目前可以正常打开。
3. 完全退出新电脑的 Codex Desktop、Codex CLI 和相关扩展。
4. 使用 Codex Migrate 先备份新电脑当前的：

```text
C:\Users\lfaf-test\.codex
```

5. 将这份“新电脑导入前备份”单独保存，不能与旧电脑备份混在一起。

切勿直接用旧电脑的整个 `.codex` 覆盖新电脑的 `.codex`，否则新电脑已有对话可能丢失。

## 六、新电脑：预览并合并导入

1. 打开 `Codex Migrate.exe`。
2. 选择旧电脑导出的 `Codex_backup`。
3. 选择需要迁移的项目和对话。
4. 设置父目录映射：

```text
C:\Users\lfaf-test\Documents=D:\codex
```

5. 如果某些实际项目还没有复制，可以暂时选择 History-only recovery（仅恢复历史）。
6. 首先执行 Preview 或 Dry Run，不要立即正式写入。
7. 在预览结果中逐项确认：

   - 旧项目路径正确转换到 `D:\codex\项目名`。
   - 新电脑原有会话显示为保留，而不是删除或覆盖。
   - 没有无法解释的 UUID divergent conflict。
   - 对应的 `D:\codex\项目名` 目录真实存在。

8. 预览无误后执行正式 Import/Merge。
9. 等待工具报告成功，不要在处理中启动 Codex。

### 可选：命令行方式

假设备份在 `E:\Codex_backup`，先预览：

```powershell
codex-migrate import "E:\Codex_backup" --dry-run `
  --map "C:\Users\lfaf-test\Documents=D:\codex"
```

确认无误后正式导入：

```powershell
codex-migrate import "E:\Codex_backup" `
  --map "C:\Users\lfaf-test\Documents=D:\codex"
```

请把 `E:\Codex_backup` 替换成实际备份路径。

## 七、导入后的验证

1. 重新启动 Codex Desktop。
2. 确认新电脑原有项目和对话仍然存在。
3. 确认旧电脑迁移过来的项目和对话已经出现。
4. 每个项目随机打开两到三条对话，检查内容是否完整。
5. 确认项目关联路径为：

```text
D:\codex\项目名
```

6. 选择一条迁移后的非关键对话，发送一条测试消息，确认可以正常继续。
7. 同时检查普通会话和已归档会话。
8. 在确认稳定使用一段时间前，不要删除两台电脑的原始备份。

## 八、发生问题时

如果出现以下情况，应停止继续操作：

- Codex 无法启动。
- 原有对话大量消失。
- 工具报告同一 UUID 内容分叉。
- 项目路径映射到不存在或错误的目录。
- SQLite、JSONL 或索引校验失败。

处理方法：

1. 完全退出 Codex。
2. 使用 Codex Migrate 的 rollback 功能恢复导入前快照。
3. 如果自动回滚不可用，保留当前异常目录的副本，再使用“新电脑导入前备份”整体恢复。
4. 不要只恢复 `state_5.sqlite` 或只复制 `sessions`；相关数据库、WAL/SHM、索引和会话文件需要保持同一备份版本。

## 九、最终检查清单

- [ ] 已下载可信来源的 Codex Migrate。
- [ ] 已备份旧电脑 `.codex`。
- [ ] 已备份新电脑导入前的 `.codex`。
- [ ] 实际项目已复制或克隆到 `D:\codex`。
- [ ] 使用映射 `C:\Users\lfaf-test\Documents=D:\codex`。
- [ ] 已先执行 Preview/Dry Run。
- [ ] 没有未处理的 UUID 分叉冲突。
- [ ] 已确认新电脑原有对话没有被覆盖。
- [ ] 已抽查迁移后的对话和项目路径。
- [ ] 原始备份仍被安全保留。

