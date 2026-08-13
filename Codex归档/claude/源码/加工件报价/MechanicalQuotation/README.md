# 機構2D圖自動報價系統
# Mechanical Quotation System for 2D Drawings

## 概述

機構2D圖自動報價系統是一套規則驅動的機械加工件自動報價引擎。
系統通過解析 DXF/DWG 圖紙，提取零件特徵，並基於公司報價規則、歷史數據和行業標準生成報價。

## 核心原則

- **規則驅動**：價格來自規則文件，非硬編碼
- **可追溯**：每筆價格標註來源 (C/H/E/AI/M/U)
- **AI 受限**：AI 僅輔助文字理解與工藝推薦，不直接定價

## 快速開始

```bash
# 安裝
pip install -e .

# 運行
quotation version

# 測試
pytest
```

## 項目結構

```
src/quotation/
├── domain/          # 數據模型層
├── application/     # 應用服務層
├── infrastructure/  # 基礎設施層 (DXF/Excel/DB/AI)
├── rules/           # 規則引擎
├── cli/             # 命令行入口
└── utils/           # 工具模塊
```

## 開發狀態

Phase 0 — 項目初始化
