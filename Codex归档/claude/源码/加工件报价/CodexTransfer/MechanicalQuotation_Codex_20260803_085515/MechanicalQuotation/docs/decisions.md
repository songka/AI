# Architecture Decisions — 機構2D自動報價系統

## ADR-001: Python 版本選擇

**日期**: 2026-07-31
**決策**: Python 3.11+
**理由**: ezdxf 和 pydantic v2 最低要求；3.14 當前運行環境兼容。

---

## ADR-002: 構建系統選擇

**日期**: 2026-07-31
**決策**: setuptools + pyproject.toml (PEP 621)
**理由**: Python 生態標準；click 用於 CLI 入口點定義。

---

## ADR-003: DXF 庫選擇

**日期**: 2026-07-31
**決策**: ezdxf
**理由**: 最成熟的 Python DXF 庫，支持 R12-R2018 格式，活躍維護。

---

## ADR-004: 分層架構

**日期**: 2026-07-31
**決策**: 四層架構 (Domain / Application / Infrastructure / Rules)
**理由**: 憲章 §3 定義；Domain 層隔離業務邏輯與外部依賴。

---

## ADR-005: AI 禁用為默認

**日期**: 2026-07-31
**決策**: `ai_enabled: False` 為默認值
**理由**: 憲章 §8 要求系統必須支持 AI 關閉模式；Phase 1-7 不依賴 AI。

---

## ADR-006: 價格來源編碼

**日期**: 2026-07-31
**決策**: 使用 C/H/E/AI/M/U 六級編碼
**理由**: 憲章 §6 定義；確保每個價格可追溯至規則或來源。
