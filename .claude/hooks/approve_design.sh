#!/bin/bash
# approve_design.sh — まこさんが設計書を承認する（2026-08-23・56回目・まこさん承認 67da88ef9ca8…・受け入れ条件 C-6）
#
# なぜ要るか:
#   56回目に、設計書と実物の食い違いが2件 出たとき、CC（私）が設計書の側を書き換えて0件にした。
#   これを繰り返せば、食い違いはいつでも0件にできる。
#   まこさんの逐語（2026-08-23）＝「その際、不正を働かないよう、極力自動生成で作成してほしい」。
#   ＝承認したときの設計書のハッシュ値を記録し、1文字でも変わったら、その設計書が指す .py を走らせない。
#
# 使い方: まこさんが設計書の中身を確認して納得したら
#   bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_design.sh <設計書のパス>
#
# 正直な限界:
#   ・CC がこのコマンドを勝手に実行すれば通せる（受け入れ条件の承認 approve_impl.sh と同じ）。
#     運用＝承認コマンドはまこさんが打つ。実行はやり取りの記録に残る。
#   ・記録のファイル（design_approved.json）を CC が消せば「未承認」に戻る。
#     ★ただし engine_tuner は、記録が無ければ走らない（fail-closed・hook 側）。
#   ・設計書の中身が目的に合っているかは、この仕組みでは分からない。まこさんが読む。

REPO="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
TABLE="$REPO/.claude/state/design_approved.json"

MD="$1"
if [ -z "$MD" ]; then
  echo "❌ 設計書のパスを渡してください。" >&2
  echo "   例: bash $REPO/.claude/hooks/approve_design.sh v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/contract_check_design.md" >&2
  exit 1
fi
if [ ! -f "$MD" ]; then
  echo "❌ 設計書が見つかりません: $MD" >&2
  exit 1
fi

ABS=$(cd "$(dirname "$MD")" && pwd)/$(basename "$MD")
SHA=$(shasum -a 256 "$ABS" | awk '{print $1}')

python3 - "$TABLE" "$ABS" "$SHA" <<'PYEOF'
import json, os, sys
table_path, key, sha = sys.argv[1], sys.argv[2], sys.argv[3]
table = {}
if os.path.exists(table_path):
    try:
        table = json.load(open(table_path, encoding="utf-8"))
    except Exception:
        table = {}
table[key] = sha
os.makedirs(os.path.dirname(table_path), exist_ok=True)
json.dump(table, open(table_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"✅ 設計書を承認しました（ハッシュ値を記録）。")
print(f"   設計書: {key}")
print(f"   ハッシュ値: {sha}")
print(f"   記録の場所: {table_path}（いま {len(table)} 本）")
print("   以後この設計書を1文字でも変えたら、指している .py は走りません。もう一度 承認が要ります。")
PYEOF
