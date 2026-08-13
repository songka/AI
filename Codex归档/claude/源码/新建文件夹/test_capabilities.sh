#!/usr/bin/env bash
# 測試各模型的 識圖 / 上下文 / 推理 能力
set -u
cd "D:\claude\新建文件夹" || exit 1

MODELS=(
  "deepseek-v4-pro"
  "deepseek-v4-flash"
  "gpt-5.6-sol"
  "gpt-5.6-luna"
  "gpt-5.6-terra"
  "gpt-5.5"
)
OUT="cap_test_results"
mkdir -p "$OUT"
TIMEOUT=150

# context 測試輸入：填充內容(marker在結尾) + 問題
cat context_filler.txt context_prompt.txt > context_full_prompt.txt

echo "==== START $(date '+%H:%M:%S') ===="

for m in "${MODELS[@]}"; do
  echo ""
  echo "######## MODEL: $m ########"

  # ---------- 1) VISION ----------
  echo "--- [$m] vision ---"
  timeout "$TIMEOUT" claude -p --input-format stream-json --output-format stream-json --verbose --model "$m" < vision_input.json > "$OUT/$m.vision.raw" 2> "$OUT/$m.vision.err"
  powershell -NoProfile -ExecutionPolicy Bypass -File parse_output.ps1 "$OUT/$m.vision.raw" > "$OUT/$m.vision.summary" 2>/dev/null
  if grep -q '^NOTJSON_TAIL' "$OUT/$m.vision.summary"; then
    echo "  !! 模型載入失敗: $(grep '^NOTJSON_TAIL' "$OUT/$m.vision.summary" | cut -c1-200)"
  else
    cw=$(sed -n 's/^CONTEXT: //p' "$OUT/$m.vision.summary")
    echo "  官方 contextWindow: ${cw:-?}"
    sed -n 's/^RESULT: /  識圖答案: /p' "$OUT/$m.vision.summary" | cut -c1-200
    grep -q '^ERROR:' "$OUT/$m.vision.summary" && sed -n 's/^ERROR: /  識圖錯誤: /p' "$OUT/$m.vision.summary"
  fi

  # ---------- 2) REASONING ----------
  echo "--- [$m] reasoning ---"
  timeout "$TIMEOUT" claude -p --model "$m" < reasoning_prompt.txt > "$OUT/$m.reasoning.out" 2> "$OUT/$m.reasoning.err"
  if [ -s "$OUT/$m.reasoning.out" ]; then
    cat "$OUT/$m.reasoning.out"
  else
    echo "  (無輸出) stderr: $(head -1 "$OUT/$m.reasoning.err")"
  fi

  # ---------- 3) CONTEXT empirical (~60k tokens) ----------
  echo "--- [$m] context 60k ---"
  timeout "$TIMEOUT" claude -p --model "$m" < context_full_prompt.txt > "$OUT/$m.context.out" 2> "$OUT/$m.context.err"
  if [ -s "$OUT/$m.context.out" ]; then
    echo "  60k 召回: $(head -1 "$OUT/$m.context.out" | cut -c1-120)"
  else
    echo "  (無輸出) stderr: $(head -1 "$OUT/$m.context.err")"
  fi
done

echo ""
echo "==== DONE $(date '+%H:%M:%S') ===="
