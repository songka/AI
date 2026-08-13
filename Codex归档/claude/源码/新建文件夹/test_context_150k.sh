#!/usr/bin/env bash
# 高階上下文測試：~160k token
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
mkdir -p cap_test_results
TIMEOUT=240

awk 'BEGIN{for(i=1;i<=8000;i++) printf "FILLER-%05d The quick brown fox jumps over the lazy dog 0123456789 repeat filler line.\n", i}' > context_filler_150k.txt
printf '\nMARKER-LINE: LAST-TOKEN-7K3QZ-END\n' >> context_filler_150k.txt
cat context_filler_150k.txt context_prompt.txt > context_full_150k.txt
echo "filler bytes: $(wc -c < context_full_150k.txt)"

echo "==== 150k START $(date '+%H:%M:%S') ===="
for m in "${MODELS[@]}"; do
  echo ""
  echo "--- [$m] context ~160k ---"
  timeout "$TIMEOUT" claude -p --model "$m" < context_full_150k.txt > "cap_test_results/$m.context150k.out" 2> "cap_test_results/$m.context150k.err"
  rc=$?
  if [ -s "cap_test_results/$m.context150k.out" ]; then
    echo "  [$m] 150k 召回: $(head -1 "cap_test_results/$m.context150k.out" | cut -c1-120)"
  else
    echo "  [$m] (無輸出, rc=$rc) stderr: $(head -1 "cap_test_results/$m.context150k.err")"
  fi
done
echo "==== 150k DONE $(date '+%H:%M:%S') ===="
