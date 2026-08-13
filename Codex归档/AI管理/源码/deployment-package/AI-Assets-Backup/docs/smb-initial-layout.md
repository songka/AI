# SMB 初始目录

```text
014-AI\
├─ AI-Assets-Hub\
│  ├─ index.html
│  ├─ styles.css
│  ├─ app.js
│  └─ hub-data.js
└─ data\
   ├─ AI-Assets\
   │  ├─ registry.json
   │  ├─ artifacts\
   │  ├─ submissions\
   │  ├─ drafts\<SMB身份>\<skill|cli|agent>\<名称>.git
   │  ├─ client\
   │  ├─ scripts\
   │  ├─ skills\ai-assets-manager\
   │  └─ docs\
   └─ AI-Assets-Backup\
      ├─ registry.json
      ├─ artifacts\
      ├─ snapshots\
      ├─ drafts\<SMB身份>\<skill|cli|agent>\<名称>.git
      ├─ client\
      ├─ scripts\
      ├─ skills\ai-assets-manager\
      └─ docs\
```

网页使用 `hub-data.js` 而不是浏览器 `fetch registry.json`，因此 `file://` 和 UNC
直接打开时不受跨源读取限制。Hub 镜像或 `web-export` 更新数据后，Chrome 刷新即
显示最新内容。
