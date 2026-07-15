#!/bin/bash
# warn_usd_absolute_in_e37.sh — PreToolUse on Write|Edit（2026-07-16 まこさん指示・H6 価格非依存の警告のみ・非ブロック）
# 目的: e37_range_scalp.py に新しい数値閾値を書く瞬間、USD 絶対値っぽい値（価格への絶対$オフセット／_USD 定数／
#   _usd 変数の数値比較）を警告する。H6＝価格非依存(%/比率/BTC 単位)。USD 絶対値の閾値は学習期($30-60k)と
#   本番($100k+)で意味が変わる＝重大インシデント級(false_positive §0-1 / 類型H・phase_compliance §-1)。
# ★警告のみ(exit 0)＝ブロックしない。%/比率なら無視、USD 絶対値なら %/比率へ直す（まこさん指示「警告だけ」）。
# 安全系＝fast-mode でも常時オン（マーカー判定を入れない）。対象は e37 の編集だけ（他ファイルは黙る）。
# 注: V9 継承の既存 USD ゲートは対象外にできない（新しく書く行だけ見る）＝誤検知あり得る＝だから警告のみ。
INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FP=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
printf '%s' "$FP" | grep -qE 'e37_range_scalp\.py$' || exit 0

# 新しく書く内容（Edit=new_string / Write=content）
NEW=$(printf '%s' "$INPUT" | python3 -c "import sys,json
d=json.load(sys.stdin).get('tool_input',{}) or {}
print(d.get('new_string', d.get('content','')))" 2>/dev/null)

# USD 絶対値っぽい行を抽出（%/pct/_PCT/比率/index 系の行は除外＝価格相対や整数indexは対象外）
HITS=$(printf '%s' "$NEW" \
  | grep -nE '(_USD[[:space:]]*=|_usd\b[[:space:]]*[<>]=?[[:space:]]*[0-9]|(avg|entry|mark|lp|lim|price)[]"_a-z0-9]*[[:space:]]*[-+][[:space:]]*\(?[0-9]{2,})' \
  | grep -vE '%|pct|_PCT|SCALP_FLOOR|ratio|比率|_idx|first_idx|last_fill' \
  | head -8)
[ -z "$HITS" ] && exit 0

cat >&2 <<EOF
⚠️ [H6 価格非依存チェック・警告のみ・非ブロック] e37 に USD 絶対値っぽい数値閾値を書いています。確認してください:
$HITS
H6＝価格非依存(%/比率/BTC単位)。USD 絶対値の閾値は学習期(\$30-60k)と本番(\$100k+)で意味が変わる（重大インシデント級・false_positive §0-1/類型H）。
→ これが USD 絶対値なら %/比率(例 lot["avg"]*(1-0.15/100)) に直す。既に %/比率、または既存 V9 継承ゲートなら無視してよい。
EOF
exit 0
