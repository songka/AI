# Architecture — 機構2D自動報價系統

版本：V2.0（多人企業部署架構）
日期：2026-08-01

---

## 一、部署架構

```
                    ┌──────────────────────────────────┐
                    │       SMB 共享盤 (網路磁碟)        │
                    │                                  │
                    │  /data/       用戶+權限+角色       │
                    │  /rules/      規則 (draft/pub/arch)│
                    │  /prices/     價格 (draft/pub/arch)│
                    │  /history/    歷史報價庫            │
                    │  /audit/      審計日誌 (append-only)│
                    │  /change-requests/  變更請求隊列    │
                    │  /logs/       系統日誌              │
                    └────────┬─────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
     Client A            Client B           Client C
  ┌────────────┐     ┌────────────┐     ┌────────────┐
  │ 登入: 張三  │     │ 登入: 李四  │     │ 登入: 王五  │
  │ 角色: Admin │     │ 角色: Engr  │     │ 角色: Sales │
  │            │     │            │     │            │
  │ Local Cache│     │ Local Cache│     │ Local Cache│
  │ C:\ProgData│     │ C:\ProgData│     │ C:\ProgData│
  └────────────┘     └────────────┘     └────────────┘
```

---

## 二、軟件分層

```
src/quotation/
│
├── domain/                    # 數據模型（無外部依賴）
│   ├── drawing.py             # Drawing
│   ├── feature.py             # Feature
│   ├── bom.py                 # BomEntry, ParsedPart, BomSheet
│   ├── material.py            # MaterialProperties
│   ├── quote.py               # Quote, QuoteItem, PriceSource
│   ├── rule.py                # RuleSet, MaterialRule, SurfaceRule, ...
│   ├── issue.py               # Issue, IssueReport
│   ├── historical.py          # [Phase 2] HistoricalFeature
│   ├── pricing.py             # [Phase 4] MaterialPrice, ProcessPrice, ...
│   ├── user.py                # [Phase 4] User, UserRole, UserStatus
│   ├── permission.py          # [Phase 4] Permission, Role
│   └── audit.py               # [Phase 4] AuditLog
│
├── application/               # 服務層
│   ├── analyze_service.py     # 分析流程
│   ├── quote_service.py       # 報價流程
│   ├── batch_service.py       # 批量處理
│   ├── auth_service.py        # [Phase 4] 認證與權限
│   ├── sync_service.py        # [Phase 4] Cache 同步
│   └── change_request_service.py  # [Phase 5] 變更請求
│
├── infrastructure/
│   ├── dxf/                   # CAD 解析
│   │   ├── converter.py       # DWG→DXF
│   │   ├── parser.py          # DXF 解析
│   │   └── scanner.py         # 文件掃描
│   ├── excel/                 # Excel I/O
│   │   ├── bom_reader.py      # BOM Reader ✅
│   │   └── writer.py          # 報價輸出
│   ├── parser/                # BOM 解析
│   │   ├── description_parser.py  # [Phase 2.2]
│   │   ├── dimension_parser.py
│   │   └── material_normalizer.py
│   ├── database/              # 資料庫
│   │   └── repository.py      # SQLite CRUD
│   ├── notification/          # [Phase 5] 通知
│   │   └── feishu.py          # 飛書 Webhook
│   ├── smb/                   # [Phase 4] SMB
│   │   └── smb_client.py      # SMB 文件訪問
│   └── cache/                 # [Phase 4] Cache
│       └── cache_manager.py   # 本地 Cache 管理
│
├── rules/                     # 規則引擎
│   ├── loader.py
│   ├── matcher.py
│   ├── calculator.py
│   ├── validator.py
│   └── version_resolver.py   # [Phase 4] 版本選擇
│
├── cli/
│   └── main.py
│
└── utils/
    ├── config.py
    ├── logging.py
    ├── serialization.py
    ├── crypto.py              # [Phase 4] bcrypt + AES
    └── i18n.py                # [Phase 5] 國際化
```

---

## 三、依賴規則

```
CLI / GUI
  └── Application
        ├── Domain
        └── Infrastructure
              └── Domain

禁止:
  Domain → Infrastructure
  Domain → Application
  Application → CLI
```

---

## 四、數據流（兩條獨立流程）

### 流程 A：知識庫建立（離線）

```
BOM + DWG → BomReader → DescriptionParser → HistoricalFeature → SQLite
```

### 流程 B：實際報價（線上）

```
客戶 DWG/PDF → DWG→DXF → CAD Parser → Feature Extractor
    → Feature → SimilaritySearch(歷史庫) + RuleEngine(規則)
    → Quote → Snapshot → Export Excel
```

---

## 五、多人協作流程

```
工程師修改價格 → Change Request → Admin 審核 →
  ├─ 通過 → 發布到 published/ → 歸檔 → 通知所有人 → Audit Log
  └─ 退回 → 通知提交者 → Audit Log

報價時：鎖定當前規則版本 → 報價完成 → Snapshot（凍結版本號）
```

---

## 六、Phase 總覽

```
Phase 0 ✅  初始化框架
Phase 1 ✅  Domain 模型
Phase 2 🔜  歷史知識庫 (BOM→HistoricalFeature→SQLite)
Phase 3     CAD 解析 (DWG→DXF→Feature)
Phase 4     多人架構 (User/Permission/Audit/SMB/Cache/Sync)
Phase 5     協作流程 (ChangeRequest/飛書/i18n/發布)
Phase 6     報價規則引擎 + 定價管理
Phase 7     AI 輔助
Phase 8     GUI
```
