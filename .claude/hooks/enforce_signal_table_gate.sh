#!/bin/bash
# enforce_signal_table_gate.sh — G1【Critical・safety＝fast-mode でも有効】（CP4 監査・まこさん GO 2026-08-06）
# 目的: 承認の指紋つきの型の表（signal_families.json ＋ signal_families_approved.txt の md5 一致）が
#   無いうちは、生成器のコード（engine_tuner_gen.py / engine_tuner_exec.py）を1行も書けない。
#   背景: 2026-08-01 に CC が「相場として意味のある組み合わせか」の制約ゼロの生成器を作った（欠陥 D1）。
#   型の表の先行承認を物理強制する＝表が無い・承認が無い・表が変わった、のどれでもブロック。
#   エスケープは無し（監査 G1「1行も書けない」）。解除は まこさんが gen_signal_families.py --approve を実行。
# 検収（番人）: 対象外ファイル=通す ／ 承認なしで対象ファイル=止まる ／ 承認あり=通す ／ 表が変わったら再び止まる。

#
# ★2026-08-16（まこさん決定「C」）＝比べる指紋を「ファイル全体の md5」から「中身の指紋」に変えた。
#   中身＝部品・時間足・型・区分・禁止の組・追加の部品・役割×系統の対応表・向きの決まり・系統の分類。
#   中身に入れないもの＝設定ファイル recipes/search_limits.json の写し（inventory.limits_copy）。
#   なぜ＝設定ファイルに鍵を1つ足すだけで表が古くなり、直近2回（2026-08-15・2026-08-16）とも
#   「写しの追加1行だけ」で再承認になっていた。承認が毎回 押すだけのものになると重みが薄れる。
#   ★計算は gen_signal_families.core_hash と同じ（番人が --core-hash で突き合わせる）。

SDK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
TABLE="$SDK/.claude/ratchet/signal_families.json"
APPROVED="$SDK/.claude/ratchet/signal_families_approved.txt"

# 中身の指紋を計算する（gen_signal_families.core_hash と同じ計算＝番人が突き合わせる）
core_hash() {
  python3 -c '
import json, hashlib, sys
t = json.load(open(sys.argv[1], encoding="utf-8"))
t.pop("approval", None)
inv = t.get("inventory")
if isinstance(inv, dict):
    inv.pop("limits_copy", None)
print(hashlib.md5(json.dumps(t, ensure_ascii=False, sort_keys=True, indent=1).encode("utf-8")).hexdigest())
' "$TABLE" 2>/dev/null
}

# 番人が突き合わせるための出口（標準入力を読む前に処理する）
if [ "$1" = "--core-hash" ]; then
  core_hash
  exit 0
fi

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

now=$(core_hash)                                # ★中身の指紋（2026-08-16・まこさん決定 C）
[ -n "$now" ] || fail "型の表の中身の指紋を計算できない（json が壊れている疑い）"
rec=$(head -1 "$APPROVED" | awk '{print $1}')   # 1行目だけが指紋（2行目以降は承認の逐語の記録）
[ "$now" = "$rec" ] || fail "承認の指紋（${rec:0:8}…）が今の表の中身（${now:0:8}…）と一致しない＝中身が変わった。再承認が要る（設定ファイルの写しだけの違いなら、ここは一致します）"

exit 0
