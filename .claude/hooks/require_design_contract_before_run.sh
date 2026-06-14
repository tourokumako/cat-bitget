#!/bin/bash
# require_design_contract_before_run.sh — PreToolUse on Bash
# 戦略スクリプト（設計書に DESIGN_CONTRACT を持つ実装）を python で実行する前に、
# 設計書 ↔ 実装 の機械照合（verify_design_contract.py）を走らせ、FAIL なら exit 2 でブロック。
#
# 目的（まこさん命令 2026-06-15「hookで物理強制して設計書通りに実装をするようにして」）:
#   CC は設計に時間をかけても、まこさんが確認できない工程で設計の核心成分を実装から抜く
#   虚偽（false_positive 類型G・例: E35 設計 §5.2 の RANGE_OK に Jump Model を含むのに実装に無い）
#   を繰り返した。net は score.py が偽れないが「設計通り作った」という工程報告だけは物理チェックが
#   無かった。本 hook はその唯一の穴を塞ぐ＝設計と乖離した実装は trades CSV すら作れない（採点に進めない）。
#
# 仕組み:
#   実行コマンドから .py を抽出 → .claude/ratchet/*.md の DESIGN_CONTRACT を走査し
#   impl_file の basename が一致する設計書を探す → 一致すれば verify_design_contract.py を実行
#   → FAIL（成分欠落）なら exit 2（実行を止める）。一致する contract が無い .py は素通り（exit 0）。

BASE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET="$BASE/.claude/ratchet"
VERIFY="$BASE/scripts/priority_rebuild/verify_design_contract.py"
ACC="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md"   # 受け入れ条件リストの contract も照合対象に

INPUT=$(cat)

# 実行コマンドから走らせる .py の basename 一覧を取得
PYS=$(printf '%s' "$INPUT" | python3 -c "
import sys, json, re, os
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cmd = (d.get('tool_input', {}) or {}).get('command', '') or ''
# python で「実行」する .py だけを対象にする（git add / ls / grep 等のパス言及には反応しない）
for m in re.finditer(r'python[0-9.]*\s+(?:-[A-Za-z]\S*\s+)*([^\s|&;><]+\.py)', cmd):
    print(os.path.basename(m.group(1)))
" 2>/dev/null)

[ -z "$PYS" ] && exit 0

# 各設計書 contract の impl_file basename → 設計書パス の対応を作り、実行 .py と突き合わせる
HIT_MD=$(printf '%s' "$PYS" | python3 -c "
import sys, os, re, json, glob
run = set(x.strip() for x in sys.stdin if x.strip())
ratchet = '$RATCHET'
mds = glob.glob(os.path.join(ratchet, '*.md')) + ['$ACC']
for md in mds:
    if not os.path.exists(md):
        continue
    try:
        t = open(md, encoding='utf-8').read()
    except Exception:
        continue
    i = t.find('DESIGN_CONTRACT')
    if i < 0:
        continue
    m = re.search(r'\`\`\`(?:json)?\s*(\{.*?\})\s*\`\`\`', t[i:], re.S)
    if not m:
        continue
    try:
        c = json.loads(m.group(1))
    except Exception:
        continue
    impl = os.path.basename(c.get('impl_file', ''))
    if impl and impl in run:
        print(md)
" 2>/dev/null)

[ -z "$HIT_MD" ] && exit 0

FAILED=0
MSG=""
while IFS= read -r MD; do
    [ -z "$MD" ] && continue
    OUT=$(python3 "$VERIFY" "$MD" 2>&1)
    if [ $? -ne 0 ]; then
        FAILED=1
        MSG="$MSG
$OUT"
    fi
done <<< "$HIT_MD"

if [ "$FAILED" -ne 0 ]; then
    echo "🔒 [設計↔実装ゲート] 設計書通りに実装されていません（まこさん命令 2026-06-15・類型G 物理検出）。" >&2
    echo "設計が要求した成分が実装のシグナル定義に連結されていません。実装を設計書 DESIGN_CONTRACT 通りに直してから再実行してください。" >&2
    echo "$MSG" >&2
    exit 2
fi
exit 0
