#!/bin/bash
# enforce_worklog_on_experiment.sh — Stop（2026-07-16 まこさん指示・fast-mode 専用ガード）
# 目的: fast-mode は改善アーク自動生成(gen_improvement_arc)が使えない→都度ログ(session_worklog)で
#   引き継ぎの「改善内容・経緯」に誤解/ヌケモレが無い状態を保つ。実験(新 trades_*.csv)を回したのに
#   worklog に記録せずターンを終えるのをブロック＝「ヌケモレ」を物理強制。
# ★正直な限界: 「記録した(worklog が実験より新しい)」までは強制できるが、「誤解が無い(中身が正しい)」中身は
#   機械では保証できない → ブロック文にチェックリストを出す。中身の正しさはまこさんの目。
# 判別: fast-mode ON の時だけ発火。ratchet 直下の最新 trades_*.csv が 最新 session_worklog より新しければ block。
#   解除: worklog を更新する(＝新しくする)か、正当な時のみ marker worklog_ok（Bash で touch）。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（OFF では pdca_gate 等の普段の記録強制に任せる）

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
[ -f "$STATE/worklog_ok" ] && exit 0   # 明示オーバーライド（正当に記録不要な時・稀）

RATCHET="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet"
WLDIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/state"

python3 - "$RATCHET" "$WLDIR" <<'PYEOF'
import sys, os, glob
ratchet, wldir = sys.argv[1], sys.argv[2]
trades = glob.glob(os.path.join(ratchet, "trades_*.csv"))   # 直下のみ（archive は対象外）
if not trades:
    sys.exit(0)                                              # 実験なし → 通す
newest_trade = max(os.path.getmtime(p) for p in trades)
wls = glob.glob(os.path.join(wldir, "session_worklog_*.md"))
newest_wl = max((os.path.getmtime(p) for p in wls), default=0)
if newest_wl >= newest_trade:
    sys.exit(0)                                             # worklog が実験より新しい＝記録済み → 通す
sys.exit(7)                                                 # 未記録 → ブロック（7 を下で判定）
PYEOF
rc=$?
[ "$rc" -eq 0 ] && exit 0

echo "🔒 [引き継ぎ記録ゲート・fast-mode] 実験(新 trades_*.csv)を回したのに session_worklog が未更新です。" >&2
echo "" >&2
echo "fast-mode は改善アーク自動生成が使えない＝都度ログで引き継ぎの「改善内容・経緯」に誤解/ヌケモレを残さない（next_step 運転方式2・cat_requirements §8.5）。" >&2
echo "対処: session_worklog_<日付>.md に今回の実験を追記してからターンを終える。記載＝①何を変えた ②採点窓 score.py の net（学習窓を持ち込まない）③merit/demerit ④次の一手。" >&2
echo "  誤解防止チェック: 采否は採点窓 score.py の数字で書いたか／学習窓・precheck・L-320 を持ち込んでいないか／crude(疑似シミュ)の数字を采否に使っていないか。" >&2
echo "（正当に記録不要な時のみ touch .claude/state/worklog_ok）" >&2
exit 2
