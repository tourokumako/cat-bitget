#!/bin/bash
# approve_impl.sh — まこさんが受け入れ条件リスト(.claude/state/acceptance.md)を承認する。
#
# 目的（まこさん命令 2026-06-15「指示→受け入れ条件リスト→合意→実装→照合 を標準にし、
#   リスト＋OK が無いと実装に入れない物理強制」）:
#   会話の指示も含め、実装の前に「やること(受け入れ条件)」を文字に起こしてまこさんが承認する。
#   承認＝その時点のリストの内容指紋(sha256)を記録。以後リストを1文字でも変えると指紋が変わり
#   再承認が必要になる（CC がリストをこっそり書き換えて別物を実装する、を防ぐ）。
#
# 使い方: まこさんが内容を確認して納得したら
#   bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LIST="$STATE/acceptance.md"

if [ ! -f "$LIST" ]; then
  echo "❌ 受け入れ条件リストがありません: $LIST" >&2
  echo "   先に CC がリストを書き、チャットで内容を提示するのを待ってください。" >&2
  exit 1
fi

# ★2026-09-02（まこさん承認 iter="impl-lock-20260902"）＝承認の前に、前に承認した控えとの差分を出す。
#   なぜ要るか＝CC が設計書を書き換えて実装に合わせる道（抜け道3）を、まこさんが見える形にする。
#   実測＝2026-09-02 に CC が TARGET の行を書き換えて再承認を頼んだ。そのときは CC が手で差分を出した。
#   ここに置けば、CC が黙って書き換えても、承認の瞬間に必ず画面へ出る。
ARC_DIR_PRE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive"
ITER_PRE=$(grep -oE 'iter="[^"]*"' "$LIST" | head -1 | sed 's/iter="//;s/"$//')
if [ -n "$ITER_PRE" ]; then
  SAFE_PRE=$(printf '%s' "$ITER_PRE" | tr ' /' '__')
  PREV="$ARC_DIR_PRE/${SAFE_PRE}.md"
  if [ -f "$PREV" ]; then
    echo "── 前に承認した控えとの差分（この iter は承認済み＝書き換えられています）──"
    if diff "$PREV" "$LIST" > /dev/null 2>&1; then
      echo "   差分なし（1文字も変わっていません）"
    else
      diff "$PREV" "$LIST" | head -40
      echo "   （差分の行数: $(diff "$PREV" "$LIST" | grep -c '^[<>]')）"
    fi
    echo "───────────────────────────────────────────────"
  fi
fi

SHA=$(shasum -a 256 "$LIST" | awk '{print $1}')
echo "$SHA" > "$STATE/acceptance.approved"
echo "✅ 承認しました（内容指紋を記録）。"
echo "   指紋: $SHA"
grep -E '^(TARGET|STATUS):' "$LIST" 2>/dev/null

# ★2026-09-02＝設計書の spec_lists を設定ファイルへ機械で書き出す（設計書 §3.1 の段2）。
#   なぜ要るか＝一覧を設計書と実装の2か所に書くと、片方だけ減らせる（2026-09-02 の食い違いの型）。
#   実装は この設定ファイルを読む＝一覧をコードに焼かない。書き出すのは機械＝CC は2か所に書かない。
SPEC_OUT="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/spec_lists.json"
python3 - "$LIST" "$SPEC_OUT" <<'PY'
import json, re, sys, pathlib
md = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])
blocks = re.findall(r"```json\s*(\{.*?\})\s*```", md, re.S)
lists = {}
for b in blocks:
    try:
        d = json.loads(b)
    except Exception:
        continue
    if isinstance(d.get("spec_lists"), dict):
        lists.update(d["spec_lists"])
if lists:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"_これは何か": "設計書の spec_lists を承認のときに機械で書き出したもの。実装はここを読む（コードに一覧を焼かない）。",
         "_作り方": "approve_impl.sh が承認の瞬間に acceptance.md から書き出す。手で書き換えない。",
         "_出どころ": sys.argv[1], **lists}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"   📋 spec_lists: {len(lists)} 件を書き出しました → {out.name}（実装はここを読む）")
PY

# 承認した acceptance を git 管理 archive へ凍結保存（2026-06-27 まこさん指示・改善アーク自動生成の源）。
#   acceptance.md は state/ で gitignore＋上書き＝永続しない。承認の瞬間に .claude/ratchet/（git 追跡）へコピー＝
#   各 iter の承認版が git に永続（指紋＋git の二重で改ざん検出）。gen_improvement_arc.py が今後 iter の
#   狙い/内容/方法 を ここの ARC マーカーから読む（acceptance archive 優先・無ければ ledger）。
ARC_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive"
mkdir -p "$ARC_DIR"
ITER=$(grep -oE 'iter="[^"]*"' "$LIST" | head -1 | sed 's/iter="//;s/"$//')
if [ -n "$ITER" ]; then
  SAFE=$(printf '%s' "$ITER" | tr ' /' '__')
  cp "$LIST" "$ARC_DIR/${SAFE}.md"
  echo "   📦 archive: acceptance_archive/${SAFE}.md（承認版を git 管理へ凍結＝改善アーク自動生成の源）"
else
  cp "$LIST" "$ARC_DIR/${SHA:0:12}.md"
  echo "   ⚠️ acceptance に ARC マーカー(<!-- ARC iter=\"...\" ... -->)が無いため指紋名で保存: ${SHA:0:12}.md"
  echo "      （次回からは acceptance に ARC マーカーを入れると改善アークが自動生成される＝acceptance_checklist 参照）"
fi
# ★2026-09-02（まこさん承認 iter="impl-lock-20260902"）＝照合の道具のハッシュ値を、承認の瞬間に記録する。
#   なぜ要るか＝CC が照合の道具（verify_design_contract.py）を書き換えれば、どんな実装でも通せる（抜け道5）。
#   承認のときにだけ印が更新される＝まこさんの承認なしに道具を書き換えると、次の照合が止まる。
#   ★限界（正直に）＝CC が この印のファイルを手で書き換えれば通る（H2・G2 と同じ限界・明示の違反）。
VERIFY_TOOL="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py"
if [ -f "$VERIFY_TOOL" ]; then
  VSHA=$(shasum -a 256 "$VERIFY_TOOL" | awk '{print $1}')
  printf '%s\n' "$VSHA" > "$STATE/verify_tool.approved"
  echo "   🔧 照合の道具の指紋を記録: ${VSHA:0:16}…（この道具を書き換えると、次の照合が止まります）"
fi

echo "   以後このリストを変更したら再承認が必要です。"
