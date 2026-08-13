#!/usr/bin/env bash
# 測試 Claude Code 支援的模型
# 對每個模型以 print mode (-p) 發送一個簡單問題，記錄成功/失敗與耗時
set -u

PROMPT='請用一句話回答：你目前是什麼模型？'
TIMEOUT_SEC=90
OUT_DIR="model_test_results"
mkdir -p "$OUT_DIR"

MODELS=(
  "deepseek-v4-pro"
  "deepseek-v4-flash"
  "gpt-5.6-sol"
  "gpt-5.6-luna"
  "gpt-5.6-terra"
  "gpt-5.5"
  "gpt-5.3-codex"
)

echo "開始測試 $(date '+%H:%M:%S')，共 ${#MODELS[@]} 個模型"
echo "============================================="

for m in "${MODELS[@]}"; do
  echo ""
  echo "==== 測試模型: $m ===="
  start=$(date +%s)
  timeout "$TIMEOUT_SEC" claude -p "$PROMPT" --model "$m" > "$OUT_DIR/$m.out" 2> "$OUT_DIR/$m.err"
  rc=$?
  end=$(date +%s)
  elapsed=$((end - start))

  first_line=""
  [ -s "$OUT_DIR/$m.out" ] && first_line=$(head -1 "$OUT_DIR/$m.out")
  err_head=""
  [ -s "$OUT_DIR/$m.err" ] && err_head=$(head -1 "$OUT_DIR/$m.err")

  if [ "$rc" -eq 124 ]; then
    status="TIMEOUT"
  elif [ "$rc" -eq 0 ] && [ -s "$OUT_DIR/$m.out" ]; then
    status="OK"
  else
    status="FAIL(rc=$rc)"
  fi
  printf "  狀態: %-14s 耗時: %ss\n" "$status" "$elapsed"
  if [ -n "$first_line" ]; then
    echo "  回應: $first_line"
  fi
  if [ "$status" != "OK" ] && [ -n "$err_head" ]; then
    echo "  stderr: $err_head"
  fi
done

echo ""
echo "============================================="
echo "測試完成 $(date '+%H:%M:%S')"
echo "詳細輸出保存在 $OUT_DIR/"
