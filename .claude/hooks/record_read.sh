#!/bin/bash
# record_read.sh — PostToolUse on Read
# Read tool で実際に開いたファイルパスを、セッションごとの read_log.txt（sessions/<セッション>/read_log.txt）に記録する。
# この記録を判定に使うのは require_source_read_before_acceptance（受け入れ条件の必読ゲート）。acceptance.md を書く前と、
# 承認の前の検査（approve_impl.sh → pre_audit_check.py --check-design）の中で、設計書が直す対象・読んだと書いたファイルを
# Read で開いたかを見る（require_source_read_before_acceptance.py:298-343）。
# ★2026-10-16（183回目）に直した＝直す前は「require_read_before_work.sh が判定する材料」と書いていたが、その hook は登録が無い。
#   require_read_plan_before_design は、開いたかの検査を 2026-10-01 に外し、記録の読み込みも 2026-10-17 に外した。
# ★限界＝Read の一部だけ開いた（offset と limit）か、全部 開いたかは区別しない。
# 目的: CC が SessionStart 表示を「読んだ」と扱う読んだふり（L-250）を物理的に防ぐ仕組みの一部。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"

# ★2026-10-16（183回目・まこさん「よい」）＝記録はセッションごとの置き場（sessions/<セッション>/read_log.txt）に書く。
#   直す前は全部のセッションで1つの read_log.txt を共有し、どのセッションが始まっても reset_read_log.sh が白紙にしたので、
#   2つのセッションが同時に動くと、先のセッションで開いたファイルが「開いていない」と出た（直近30日で14件）。
#   セッションの id の決め方は reset_read_log.sh と require_source_read_before_acceptance.py の _sid_of と同じ
#   （session_id、無ければ transcript_path のファイル名・使えない文字は「_」）。id が読めないときは書かない
#   （必読ゲートは止める側に倒れる）。
input=$(cat)
out=$(printf '%s' "$input" | python3 -c "import sys,json,os,re
try:
    d=json.load(sys.stdin)
except Exception:
    d={}
if not isinstance(d,dict):
    d={}
sid=d.get('session_id')
if not (isinstance(sid,str) and sid.strip()):
    tp=d.get('transcript_path')
    b=os.path.basename(tp.strip()) if isinstance(tp,str) and tp.strip() else ''
    sid=b[:-6] if b.endswith('.jsonl') else b
sid=re.sub(r'[^A-Za-z0-9._-]','_',(sid or '').strip()).lstrip('.')
if not sid or set(sid)<=set('._'):
    sid=''
print(sid)
print('' if d.get('agent_type') else (d.get('tool_input') or {}).get('file_path',''))" 2>/dev/null)
SID=$(printf '%s\n' "$out" | sed -n 1p)
fp=$(printf '%s\n' "$out" | sed -n 2p)

if [ -n "$SID" ] && [ -n "$fp" ]; then
  mkdir -p "$STATE_DIR/sessions/$SID"
  echo "$fp" >> "$STATE_DIR/sessions/$SID/read_log.txt"
fi
exit 0
