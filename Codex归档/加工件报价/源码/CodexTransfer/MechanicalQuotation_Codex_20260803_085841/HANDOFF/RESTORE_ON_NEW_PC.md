# 在另一台電腦還原 MechanicalQuotation

## 1. 解壓

解壓後直接使用：

```text
<轉移包>\MechanicalQuotation
```

包內已包含完整Git歷史、程式、規則、價格快照、測試、現有樣本、runtime資料，以及DeepSeek key。

## 2. Key位置

```text
MechanicalQuotation\runtime\secrets\deepseek_api_key.txt
```

這是報價軟體使用的DeepSeek key，不是Codex登入憑證。Codex仍需在另一台電腦用自己的ChatGPT/Codex帳號登入。

確認Key不會進Git：

```powershell
cd "<轉移包>\MechanicalQuotation"
git check-ignore runtime/secrets/deepseek_api_key.txt
```

不得執行：

```text
git add -f runtime/secrets/deepseek_api_key.txt
```

## 3. 重建虛擬環境

不要搬舊電腦的`.venv`。

```powershell
cd "<轉移包>\MechanicalQuotation"
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

若`pyproject.toml`未完整聲明開發依賴，再參考：

```text
..\HANDOFF\requirements-transfer.txt
```

## 4. 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ -q --tb=line
```

目前基準約為：

```text
656 passed, 2 skipped
```

以`docs\CURRENT_HANDOFF.md`與最新commit為準。

## 5. 啟動UI

```powershell
.\.venv\Scripts\python.exe -m quotation.ui.demo_app
```

## 6. 啟動API

```powershell
.\.venv\Scripts\python.exe -m uvicorn quotation.api.main:app --host 127.0.0.1 --port 8000
```

Swagger：

```text
http://127.0.0.1:8000/docs
```

## 7. DeepSeek

```text
Base URL: http://10.97.144.27:3000/v1
Model: deepseek-v4-flash
Key: runtime/secrets/deepseek_api_key.txt
```

另一台電腦必須能連到同一內網。自動測試必須使用Mock，不能因內網不通而失敗。

## 8. 在Codex打開

Codex選擇本機資料夾：

```text
<轉移包>\MechanicalQuotation
```

第一條訊息：

```text
請先閱讀 docs/CURRENT_HANDOFF.md、HANDOFF/TRANSFER_INFO.md、HANDOFF/CODEX_MASTER_PROMPT.md，檢查git status與最新commit，恢復測試/UI/API基準後，按主提示詞接管整個專案。
```

## 9. Git恢復備份

包內還有：

```text
HANDOFF\MechanicalQuotation.bundle
```

Repository損壞時可重新克隆：

```powershell
git clone "..\HANDOFF\MechanicalQuotation.bundle" MechanicalQuotation-Recovered
```
