#!/bin/bash
# enforce_e37_scalp_frequency.sh — PostToolUse on Bash（2026-07-16 まこさん指示・fast-mode 専用ガード）
# 目的: E37＝スキャル（§1.2.1・ROLE_CHECK e37=scalp＝小刻みに大量・高頻度が役割）。
#   fast-mode で E37 の実験を採点/report した時、件数/日 が下限 5 を割っていたら「§1.2.1 戦略逸脱」を警告する。
#   背景(2026-07-16): net を追う反復(v21 armed DC・v26 到達+max-age)が入口を絞り、E37 の頻度が 7.6→2.3件/日 まで
#   degrade してスキャル役割を違反した。頻度を守る hook(enforce_role_criteria/e37_pdca/strategy_anchor)は
#   process hook で fast-mode 無効＝誰も止めなかった。この穴を fast-mode でも効く形で塞ぐ。
#   ★下限 5件/日=まこさん確定（要件の理想は 10件/日・§6.1.1）。相対の尻すぼみ禁止(前版より減らすな)は警告文で促す。
# 判別: fast-mode ON かつ score.py/report.py を E37 の *_score.csv に対して走らせた時だけ。警告のみ(exit 0・非ブロック)。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（OFF では process の役割 hook に任せる）

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# score.py / report.py を走らせた時だけ
printf '%s' "$CMD" | grep -qE '(score|report)\.py' || exit 0
# E37 の *_score.csv パスを抽出（e36 等は対象外＝役割が違う）
CSVPATH=$(printf '%s' "$CMD" | grep -oE '[^[:space:]]*trades_e37[A-Za-z0-9_]*_score\.csv' | head -1)
[ -z "$CSVPATH" ] && exit 0

python3 - "$CSVPATH" <<'PYEOF'
import sys, os
import pandas as pd
p = sys.argv[1]
# パス解決（as-is / bitget-python-sdk-api 配下 / repo 直下 を試す）
cands = [p,
         os.path.join("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api", p),
         os.path.join("/Users/tachiharamasako/Documents/GitHub/cat-bitget", p)]
path = next((c for c in cands if os.path.exists(c)), None)
if path is None:
    sys.exit(0)   # 見つからなければ黙る（誤発火しない）
try:
    d = pd.read_csv(path)
    if not len(d): sys.exit(0)
    d["e"] = pd.to_datetime(d["entry_time"]); d["x"] = pd.to_datetime(d["exit_time"])
    npos = d["position_id"].nunique() if "position_id" in d.columns else len(d)
    days = max(1, (d["x"].max() - d["e"].min()).days)
    freq = npos / days
except Exception:
    sys.exit(0)
if freq >= 5.0:
    sys.exit(0)   # 下限クリア → 黙る
sys.stderr.write(
    f"\n⚠️ [E37 スキャル頻度ガード・§1.2.1 戦略逸脱・fast-mode] このE37実験は 件数/日 {freq:.2f} < 下限 5。\n"
    f"  ★本来の目標＝1時間に約5件エントリー（＝1日数十件〜・まこさん 2026-07-16）。5件/日 は『これを割ったら論外』の最低ラインで、目標はその桁違い上。\n"
    f"  E37=スキャル＝小刻みに大量が役割（ROLE_CHECK e37=scalp・§6.1.1）。低頻度で net を作る＝尻すぼみ＝§1.2.1 違反＝却下。\n"
    f"  ⛔ この結果を『改善/前進』として採用・記録しない。入口を作り直して頻度を桁で上げる（1時間5件へ近づける）のが最優先。\n"
    f"  ★併せて『前の版より件数/日を減らさない(尻すぼみ禁止・台帳ルール)』も守る。net はスキャル頻度を保ったまま出口/場面の質で解く。\n")
sys.exit(0)
PYEOF
exit 0
