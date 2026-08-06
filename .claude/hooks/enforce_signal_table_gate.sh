#!/bin/bash
# enforce_signal_table_gate.sh — G1【Critical・safety＝fast-mode でも有効】（CP4 監査・まこさん GO 2026-08-06）
# 目的: 承認の指紋つきの型の表（signal_families.json ＋ signal_families_approved.txt の md5 一致）が
#   無いうちは、生成器のコード（engine_tuner_gen.py / engine_tuner_exec.py）を1行も書けない。
#   背景: 2026-08-01 に CC が「相場として意味のある組み合わせか」の制約ゼロの生成器を作った（欠陥 D1）。
#   型の表の先行承認を物理強制する＝表が無い・承認が無い・表が変わった、のどれでもブロック。
#   エスケープは無し（監査 G1「1行も書けない」）。解除は まこさんが gen_signal_families.py --approve を実行。
# 検収（番人）: 対象外ファイル=通す ／ 承認なしで対象ファイル=止まる ／ 承認あり=通す ／ 表が変わったら再び止まる。

SDK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
TABLE="$SDK/.claude/ratchet/signal_families.json"
APPROVED="$SDK/.claude/ratchet/signal_families_approved.txt"

input=$(cat)

fp=$(printf '%s' "$input" | python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get('tool_input',{}).get('file_path',''))
except Exception:
    print('')" 2>/dev/null)

case "$(basename "$fp")" in
  engine_tuner_gen.py|engine_tuner_exec.py) ;;
  *) exit 0 ;;
esac

fail() {
  echo "🔒 [G1 型の表の先行承認・safety hook] $1" >&2
  echo "   生成器のコード（engine_tuner_gen.py / engine_tuner_exec.py）は、承認の指紋つきの型の表が" >&2
  echo "   有効になるまで1行も書けません（CP4 監査 G1・まこさん GO 2026-08-06）。" >&2
  echo "   解除＝まこさんが scripts/priority_rebuild/gen_signal_families.py --approve を実行する。" >&2
  echo "   状態の確認＝python3 gen_signal_families.py --status" >&2
  exit 2
}

[ -f "$TABLE" ] || fail "型の表（signal_families.json）が存在しない"
[ -f "$APPROVED" ] || fail "承認の指紋（signal_families_approved.txt）が存在しない＝表は未承認"

now=$(md5 -q "$TABLE" 2>/dev/null || md5sum "$TABLE" | awk '{print $1}')
rec=$(head -1 "$APPROVED" | awk '{print $1}')   # 1行目だけが指紋（2行目以降は承認の逐語の記録）
[ "$now" = "$rec" ] || fail "承認の指紋（${rec:0:8}…）が今の表（${now:0:8}…）と一致しない＝表が変わった。再承認が要る"

exit 0
