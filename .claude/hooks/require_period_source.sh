#!/bin/bash
# require_period_source.sh — PreToolUse on Bash
# priority_rebuild の .py を python で「実行する前」に、検証期間の境界
#   (TRAIN_END / SC_START / SCORE_START / SCORE_END / SEAL_START / EMBARGO_START / EMBARGO_END)
#   を自前で定義していないか検査する。periods.py 由来でない代入があれば exit 2 でブロック。
#
# 目的（まこさん命令 2026-06-18「期間のズレが絶対に発生しない状態にしろ」）:
#   E35 が学習窓 TRAIN_END=2025-01-01・採点窓を自前ベタ書きし、地面(E31窓)と違う窓で測った。
#   審判 score.py のゲートは採点窓しか守れない（学習窓は射程外）。そこで「期間境界の数値は
#   periods.py（唯一の正本）からしか取れない」を実行段で物理強制する。日付の手打ちを禁止し、
#   全戦略が同じ正本カレンダーを参照する状態にする（single source of truth）。
#
# ルール: scripts/priority_rebuild/*.py（periods.py 自身は除く）の中で、上記の期間境界名に
#   代入していて右辺が「periods.」で始まらない（= pd.Timestamp リテラル / e34v1.TRAIN_END 等の
#   自前ソース）行があれば block。`from periods import ...`（代入でない）や
#   `SC_START = periods.SCORE_START` は通る。
# 限界: 正規表現ベース（巧妙な別名定義はすり抜けうる・L-290 同型）。審判窓ゲート(score.py)＋
#   要件定義書 periods 参照＋まこさんの目と併せて担保する。

DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"

INPUT=$(cat)
OUT=$(printf '%s' "$INPUT" | DIR="$DIR" python3 -c "
import sys, json, re, os
DIR = os.environ['DIR']
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cmd = (d.get('tool_input', {}) or {}).get('command', '') or ''
# 実行される .py を抽出（python(3) ... script.py）
m = re.search(r'python[0-9.]*[ \t]+[^|&;\n]*?([^ \t|&;\n]+\.py)', cmd)
if not m:
    sys.exit(0)
path = m.group(1); base = os.path.basename(path)
# priority_rebuild 対象のみ・periods.py は除外
if 'priority_rebuild' not in path and not os.path.exists(os.path.join(DIR, base)):
    sys.exit(0)
if base == 'periods.py':
    sys.exit(0)
cand = path if os.path.exists(path) else os.path.join(DIR, base)
if not os.path.exists(cand):
    sys.exit(0)
try:
    src = open(cand, encoding='utf-8').read()
except Exception:
    sys.exit(0)
NAMES = r'(TRAIN_END|SC_START|SCORE_START|SCORE_END|SEAL_START|EMBARGO_START|EMBARGO_END)'
bad = []
for ln in src.splitlines():
    mm = re.match(r'\s*' + NAMES + r'\s*=\s*(.+)\$', ln)
    if mm:
        rhs = mm.group(2).strip()
        if not rhs.startswith('periods.'):
            bad.append(ln.strip())
if bad:
    print(base + '\t' + ' / '.join(bad[:4]))
" 2>/dev/null)

if [ -n "$OUT" ]; then
  FILE=$(printf '%s' "$OUT" | cut -f1)
  LINES=$(printf '%s' "$OUT" | cut -f2)
  echo "🔒 [期間正本ゲート] $FILE が検証期間の境界を自前で定義しています（periods.py 由来でない）。" >&2
  echo "   該当: $LINES" >&2
  echo "   期間（学習/捨て/採点/封印）の日付は手打ち禁止。periods.py から取ってください:" >&2
  echo "     from periods import TRAIN_END, SCORE_START, SCORE_END, SEAL_START   （または SC_START = periods.SCORE_START）" >&2
  echo "   理由: 期間が複数箇所でズレる事故の根絶（まこさん 2026-06-18・ledger E0.5）。periods.py が唯一の正本。" >&2
  exit 2
fi
exit 0
