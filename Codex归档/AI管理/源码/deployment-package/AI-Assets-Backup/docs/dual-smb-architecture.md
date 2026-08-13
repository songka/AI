# 双 SMB 架构

## 地址与职责

- 公共槽 `...\data\AI-Assets`：正式索引与制品分发、候选提交、用户草稿 Git 第一副本。
- 备份槽 `...\data\AI-Assets-Backup`：正式发布权威源、恢复快照、用户草稿 Git 第二副本。
- 静态看板 `...\014-AI\AI-Assets-Hub\index.html`：Chrome 直接打开。

草稿同时普通 push 到两个裸 Git 仓库；任何分叉都拒绝覆盖。正式发布先写备份权威槽，
再由 `mirror` 单向同步到公共槽。网页数据 `hub-data.js` 在 `mirror` 或
`web-export` 时重建。

两个地址位于同一 SMB 共享时并非物理隔离备份；建议文件服务器另做快照或离线备份。
