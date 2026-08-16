#!/bin/bash
[ -f "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode" ] && exit 0  # [fast-mode] process hook を一時無効化（touch/rm pdca_fast_mode で切替・safety hook には入れない・2026-07-16）
# require_direct_csv_for_analysis.sh — PreToolUse on Bash（2026-06-24 まこさん指示で新設）
# 目的: report.py / analyze.py の【分析対象（第1引数）が archive/ 配下】ならブロック。
#   ＝「archive の CSV を分析している＝最新実験が archive に押し出された＝実験→分析の順序ミス」を物理検出。
#
# 背景（2026-06-24 事案）: 実験 rvB を --tag で走らせた後、恒等チェックのため rvoff を2本目の --tag で走らせ、
#   archive_prior_experiments が rvB を archive へ自動退避→その archive の rvB を入力に report/analyze を回し、
#   出力（report_/analysis_）が archive に出た（§3.1 違反＝直下=現役+最新実験の出力であるべき）。
#   正しい手順＝実験は1回走らせ、その直後に【直下で】precheck→score→report→analyze を済ませる。
#   2本目の --tag 実験を走らせると1本目が archive へ退避される＝その前に分析する。
#
# 正直な限界: cwd を archive にして basename で実行するとパスに archive が出ず検出漏れする（別経路）。
#   本 hook はフルパス/相対パスに /archive/ が出る今回の症状を止める。解除は 2026-08-16 に廃止（過去の再分析は CSV を archive の外へコピーしてから）。

INPUT=$(cat)

VERDICT=$(printf '%s' "$INPUT" | python3 -c "
import sys, json, re
try:
    cmd = (json.load(sys.stdin).get('tool_input', {}) or {}).get('command', '')
except Exception:
    print('OK'); sys.exit(0)
# ★解除（ANALYZE_ARCHIVE_OK=1）は 2026-08-16 に廃止（まこさん指示）＝通す道は無い。
# report.py / analyze.py の直後の最初の非フラグトークン（=分析対象 CSV）を見る
for m in re.finditer(r'(report|analyze)\.py\s+(\S+)', cmd):
    arg = m.group(2)
    if arg.startswith('-'):        # 対象でなくフラグなら判定しない（稀）
        continue
    if '/archive/' in arg or arg.startswith('archive/'):
        print('BLOCK:' + arg); sys.exit(0)
print('OK')
" 2>/dev/null)

case "$VERDICT" in
  BLOCK:*)
    tgt="${VERDICT#BLOCK:}"
    echo "🔒 [分析は直下で・archive 分析ブロック] report/analyze の分析対象が archive 配下です: $tgt" >&2
    echo "" >&2
    echo "＝最新実験が archive に押し出された兆候（実験→分析の順序ミス・2026-06-24 事案）。" >&2
    echo "正しい手順: 実験は1回 --tag で走らせ、その直後に【ratchet 直下】で precheck→score→report→analyze を済ませる。" >&2
    echo "  ・2本目の --tag 実験を走らせると1本目が archive へ自動退避される＝その前に分析を終える。" >&2
    echo "  ・直下の最新実験 CSV を分析対象にせよ（archive の CSV を入力にしない）。" >&2
    echo "  ・解除は 2026-08-16 に廃止。過去実験を再分析するなら CSV を archive の外へコピーしてから。" >&2
    exit 2 ;;
  *) exit 0 ;;
esac
