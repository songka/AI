# 签核 CLI 使用说明

统一入口：

```bash
python auto-sign/qh.py sign list
python auto-sign/qh.py sign show 1
python auto-sign/qh.py sign approve 1 3
python auto-sign/qh.py sign reject 2
python auto-sign/qh.py sign fetch
python auto-sign/qh.py sign run
python auto-sign/qh.py sign --help
```

`qh sign` 当前兼容原 `cli.py` 的全部参数，签核平台请求、提交与平台复查仍由 `auto_sign.py` 负责。

## 飞书内安全指令

```text
查询
模拟自动签核
执行一次自动签核
签核 1 3
签核 1 3 发群
拒签 2
拒签 2 原因:资料不完整 不发群
全签
全拒
确认
取消
```

安全规则：

- AI 只能建议上述签核或拒签指令，不能直接执行。
- `全签`、`全拒`始终需要再次回复 `确认`。
- 本地 CLI 的 `approve-all`、`reject-all` 也必须分别输入 `确认全签`、`确认全拒`，不能跳过。
- 手动操作和动作规则相反时需要再次确认。
- 确认有效期为 10 分钟，并按申请单号快照重新核对，不按可能变化的页面编号盲目执行。
- `模拟、测试、预览、试跑`只展示匹配结果，绝不提交。
- `执行一次自动签核`是用户固定指令，只对当前账号按规则运行一轮；不会处理未匹配项目，也不会修改定时开关。AI 不能触发。

## 通知规则

通知策略独立于签核/拒签结果，优先级为：

```text
手动明确发群/不发群
> 独立通知规则
> 动作规则 group_notify
> 用户默认（默认不发群）
```

示例：

```text
加规则 拒签 描述 has_cn --name 简体拒签 --reason 描述含简体字 --notify suppress
加规则 签核 申请人 in_user_group 常用申请人 描述 starts_with_content_group 常规料号 --name 组签核
加规则 签核 描述 ends_with_content_group 允许结尾 --name 结尾组签核
加规则 拒签 描述 not_contains_content_group 允许内容 --name 排除内容拒签
加规则 通知 描述 contains 紧急 --name 紧急发群 --notify send
群通知默认 关
```

人工拒签原因可不填；未填写时依次采用拒签规则的 `reason`、规则名称、`人工拒签（未填写原因）`。

CLI 即时操作只把签核平台复查确认成功的项目写入记录；若部分项目没有被平台确认，退出码为 `2`。
