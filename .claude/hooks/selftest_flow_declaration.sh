#!/bin/bash
# selftest_flow_declaration.sh — enforce_flow_declaration.sh の番人（2026-08-19 新設・まこさん決定「直す」）
#
# 目的: 「走らせずに名前を数えるだけ」のコマンドは通り、「本当に実行する」コマンドは止まることを、
#   実際に hook へ入力を渡して確かめる（わざと壊して落ちるかのメタ確認・cat_requirements §2.9③）。
#
# 経緯: 2026-08-18 に、grep でファイルの名前を数えただけで2回 止まった（worklog §11.6）。
#   原因＝「コマンドのどこかに python が在り、どこかに対象の名前が在る」で判定していた。
#   直したあと＝区切り（; & | 改行）で分けた断片ごとに「python がその対象を実行しようとしているか」を見る。
#
# 使い方: bash .claude/hooks/selftest_flow_declaration.sh
# ★注意: 「本当に実行するなら止まる」は、いまの宣言ファイルの状態に依存する（宣言が新しく、対象が
#   書かれていて、貼った印も在れば通る）。その場合はその旨を表示して pass 扱いにしない＝人が見て判断する。

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/enforce_flow_declaration.sh"
ng=0

run() {  # $1=名前 $2=期待（pass / block） $3=コマンド
  local js
  js=$(printf '%s' "$3" | python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.stdin.read()}}))')
  # ★local と代入を同じ行に書くと、$? が local の終了コード（いつも0）で上書きされる（bash の落とし穴）
  local rc
  local got
  printf '%s' "$js" | bash "$HOOK" >/dev/null 2>&1
  rc=$?
  got="pass"
  [ "$rc" != "0" ] && got="block"
  if [ "$got" = "$2" ]; then
    echo "  ✅ $1"
  else
    echo "  ❌ $1（期待 $2 ／ 実際 $got）"
    ng=$((ng + 1))
  fi
}

echo "=== enforce_flow_declaration.sh の番人 ==="
run "grep で名前を数えるだけなら通る" pass 'grep -c regime scripts/priority_rebuild/engine_tuner_gen.py'
run "grep と python が同じコマンドに在っても、python が対象を実行していなければ通る" pass 'grep -c regime engine_tuner_gen.py ; python3 - '
run "自己検査は通る" pass 'python3 scripts/priority_rebuild/engine_tuner.py --selftest'
run "対象外のスクリプトは通る" pass 'python3 scripts/priority_rebuild/gen_materials.py --verify'
run "本当に実行するなら止まる（宣言が無い・古い・貼っていない のいずれかのとき）" block 'python3 scripts/priority_rebuild/engine_tuner.py --purpose search'


# ★数え方の一致の検査（2026-08-19 まこさん決定「2」・新設）
#   宣言ファイルを一時的に差し替えて、食い違いで止まるかを実測する。**終わったら必ず元に戻す**（trap）。
DECL="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/flow_declaration.md"
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/flow_declaration_posted"
BACK_D="$(mktemp)"
BACK_M="$(mktemp)"
cp "$DECL" "$BACK_D" 2>/dev/null
cp "$MARK" "$BACK_M" 2>/dev/null
restore() { cp "$BACK_D" "$DECL" 2>/dev/null; cp "$BACK_M" "$MARK" 2>/dev/null; rm -f "$BACK_D" "$BACK_M"; }
trap restore EXIT

write_decl() {  # $1 = 数え方の行（空文字なら書かない）
  {
    echo "【フロー宣言】"
    echo "段: テスト（この検査そのもの）"
    echo "工程: わざと壊して止まるかを試す"
    echo "実行: engine_tuner.py --logic S2"
    echo "目的: 数え方と --purpose の一致の検査が働くかを実測する"
    [ -n "$1" ] && echo "$1"
  } > "$DECL"
  shasum -a 256 "$DECL" | awk '{print $1}' > "$MARK"
}

echo ""
echo "=== 数え方（宣言）と --purpose（コマンド）の一致 ==="
write_decl "数え方: 確認する（check・累積に数えない）"
run "宣言=確認する × --purpose check なら通る" pass 'python3 scripts/priority_rebuild/engine_tuner.py --logic S2 --purpose check'
run "★宣言=確認する × --purpose search は止まる（2026-08-19 の違反の形）" block 'python3 scripts/priority_rebuild/engine_tuner.py --logic S2 --purpose search'
write_decl "数え方: 値を選ぶ（search・累積に数える）"
run "宣言=値を選ぶ × --purpose search なら通る" pass 'python3 scripts/priority_rebuild/engine_tuner.py --logic S2 --purpose search'
run "★宣言=値を選ぶ × --purpose check は止まる（逆向きも見る）" block 'python3 scripts/priority_rebuild/engine_tuner.py --logic S2 --purpose check'
write_decl ""
run "数え方の行が無い × --purpose を使うと止まる" block 'python3 scripts/priority_rebuild/engine_tuner.py --logic S2 --purpose check'
write_decl "数え方: 値を選ぶ／確認する（両方 書いてしまった）"
run "数え方に両方 書いてあると止まる" block 'python3 scripts/priority_rebuild/engine_tuner.py --logic S2 --purpose search'

restore
trap - EXIT

echo ""
echo "番人: $((11 - ng))/11 pass"
[ "$ng" -gt 0 ] && exit 1
exit 0
