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
FROZEN_OUT="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/impl_functions_frozen.json"
python3 - "$LIST" "$SPEC_OUT" "$FROZEN_OUT" <<'PY'
import json, re, sys, pathlib
sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/"
                   "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
from verify_design_contract import resolve_spec_list      # noqa: E402
md = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])
frozen_out = pathlib.Path(sys.argv[3])
blocks = re.findall(r"```json\s*(\{.*?\})\s*```", md, re.S)
lists = {}
obj = {}
for b in blocks:
    try:
        d = json.loads(b)
    except Exception:
        continue
    if isinstance(d.get("spec_lists"), dict):
        lists.update(d["spec_lists"])
    if "impl_file" in d:
        obj = d
# ★2026-09-03（監査 cp14 の B-2・Critical）＝{"from","kind"} を、ここで配列へ展開してから書く。
#   直す前＝辞書をそのまま写していた。照合D は「2件以上の配列」を求めるので、必ず落ちた。
#   ＝承認が書く形と、照合が求める形が食い違っていた（どちらの道でも照合D が成立しない）。
resolved = {}
bad = []
for _k, _v in lists.items():
    if not isinstance(_v, dict):
        bad.append(f"{_k}: 正本を指す形（from/kind）ではありません")
        continue
    _items, _why = resolve_spec_list(_v)
    if not _items:
        bad.append(f"{_k}: 正本から一覧を作れません（{_why}）")
        continue
    resolved[_k] = _items
    print(f"   📖 spec_lists {_k}: {len(_items)} 件へ展開しました（出どころ＝{_why}）")
if bad:
    print("❌ 承認を中止します（監査 cp14 の B-2＝辞書のまま書き出さない）:", file=sys.stderr)
    for _b in bad:
        print(f"   ・{_b}", file=sys.stderr)
    sys.exit(3)
lists = resolved
# ★2026-09-02（監査 cp13 の A-1・抜け道16）＝一覧が空でも必ず書き出す。
#   直す前＝`if lists:` だった。だから設計書に一覧が無いと、このファイルが作られず、
#   前に承認した一覧がそのまま残った（監査の抜け道16）。実測＝承認を打っても作られなかった。
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(
    {"_これは何か": "設計書の spec_lists を承認のときに機械で書き出したもの。実装はここを読む（コードに一覧を焼かない）。",
     "_作り方": "approve_impl.sh が承認の瞬間に acceptance.md から書き出す。手で書き換えない。",
     "_出どころ": sys.argv[1], **lists}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"   📋 spec_lists: {len(lists)} 件を書き出しました → {out.name}（実装はここを読む）")

# ★2026-09-03（監査 cp14 の B-1・Critical）＝impl_functions を凍結保存する。
#   監査の逐語＝「承認の瞬間に impl_functions を一覧のファイルと同じ場所へ凍結保存し、
#   照合A・B は凍結された版と比べる。承認後に impl_functions が変わったら止める」。
_fz = obj.get("impl_functions") or {}
frozen_out.parent.mkdir(parents=True, exist_ok=True)
frozen_out.write_text(json.dumps(
    {"_これは何か": "承認の瞬間に凍結した impl_functions。照合A・B はここと比べる（実装から作り直せない）。",
     "_作り方": "approve_impl.sh が承認の瞬間に acceptance.md から書き出す。手で書き換えない。",
     "_出どころ": sys.argv[1], **_fz}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"   🧊 impl_functions: {sum(len(v) for v in _fz.values() if isinstance(v, list))} 件を凍結しました"
      f" → {frozen_out.name}（以後この版と比べます）")

# ★方針③（監査 §6-A の3・2026-09-02）＝機械で照らせる件数と、照らせない件数を、2行だけ出す。
#   ★これは「数字の確認」ではない。監査の逐語＝「合っているかを確かめるものではなく、
#     『照らせないものが何件 残っているか』の報告である。まこさんは、その件数が増えたときだけ
#     理由を聞けばよい」。
mu_from = obj.get("must_use_from") or {}
mu_hand = obj.get("must_use") or {}
n_fn = sum(len(v) for v in (obj.get("impl_functions") or {}).values() if isinstance(v, list))
orig_lists = obj.get("spec_lists") or {}
n_probe = sum(1 for v in orig_lists.values() if isinstance(v, dict) and v.get("probe"))
n_sh = len([x for t in re.findall(r"^TARGET:\s*(.+)$", md, re.M)
            for x in t.split(",") if x.strip().endswith(".sh")])
n_reason = 1 if obj.get("no_spec_lists_reason") else 0
# ★2026-09-03（監査 cp15 の C-4・Critical）＝自由記述の判定をやめ、実物と機械で比べる。
#   監査の逐語＝「凍結の中身を承認のたびに gen_impl_functions.py の出力と比べ、完全一致なら
#   『実装から作った』として方針③の『機械で照らせない』に必ず数える
#   （いまの generated_from の自由記述の判定を廃止する）」。
#   直す前＝設計書の generated_from に何と書くかで件数が決まった＝CC の自己申告に戻っていた。
#   実測（監査 cp15）＝凍結ファイルと実物から作った一覧は identical: True なのに、件数は 0件 と出た。
#   ★この件数は「毎回 0 になるのが良い」ものではない。**設計の段階では書けないので、
#     実装の後に確定させる形にした（C-4 の対）。だから 照合A・B は常にここへ入るのが正しい姿。**
# ★2026-09-03（監査 cp16 の E-2・Critical・まこさん指定・承認 36051934db6eede3）
#   ＝比べる相手を「git の差分」から「ファイルの中の全関数」に変えた。
#   まこさんの逐語＝「比べる相手を『gitの差分』から『ファイルの中の全関数』に変える。
#     目的は ⚠️ を消すことではなく、commit してもしなくても常に ⚠️ が出るようにすること。
#     ⚠️ が出続けるのが正しい状態。件数を良く見せる操作をしない。」
#   直す前の実測（監査 cp16 の Q3）＝比べる相手が touched_functions（git の差分）だったので、
#     実装を commit しただけで差分が空になり、⚠️ が消えて「📐 設計書の側が出どころ」に
#     反転し、『機械で照らせる』が 0件 → 3件 に増えた。設計書は1バイトも変えていないのに。
#   直した後＝git を一切 見ない。ファイルを読んで、その中の全関数を並べて比べる。
from verify_design_contract import functions_ast            # noqa: E402
_SDK = ("/Users/tachiharamasako/Documents/GitHub/cat-bitget/"
        "v3-bitget-api-sdk/bitget-python-sdk-api")
_ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"


def _abs_of(rel: str) -> str:
    return (str(pathlib.Path(_SDK) / rel) if rel.startswith("scripts/priority_rebuild/")
            else str(pathlib.Path(_ROOT) / rel))


def all_functions(path: str) -> list:
    """そのファイルの中の全関数の名前を並べて返す（git を見ない・監査 cp16 の E-2）。

    ★touched_functions（git の差分）と違い、commit してもしなくても同じ答えを返す。
    ★読めなかったときは None を返す＝「判定できない」として、呼ぶ側が
      『設計書の側が出どころ』とは言わない（監査の逐語）。
    """
    try:
        return sorted(functions_ast(open(path, encoding="utf-8").read()))
    except Exception:                                        # noqa: BLE001
        return None


_fz_design = obj.get("impl_functions") or {}
_from_impl, _unknown = {}, []
for _rel in _fz_design:
    _got = all_functions(_abs_of(_rel))
    if _got is None:
        _unknown.append(_rel)
    else:
        _from_impl[_rel] = _got
_same = (bool(_fz_design) and not _unknown
         and all(sorted(_fz_design.get(k) or []) == _from_impl.get(k) for k in _fz_design))
n_self_gen = sum(len(v) for v in _fz_design.values() if isinstance(v, list)) if _same else 0
if _same:
    print("   ⚠️ impl_functions は、実物のファイルの中の全関数と完全に同じです"
          "（＝実装から作った期待値＝循環）。下の『機械で照らせない』に数えます。")
    print("      ★これは commit してもしなくても同じ答えです（監査 cp16 の E-2）。")
elif _unknown:
    print("   ❓ impl_functions の出どころを判定できません"
          f"（読めなかったファイル: {', '.join(_unknown)}）。")
    print("      ★「設計書の側が出どころ」とは言いません（監査 cp16 の E-2）。")
elif _fz_design:
    print("   📐 impl_functions は、実物のファイルの中の全関数とは違います"
          "（＝設計書の側が出どころ）。")
# ★2026-09-03（監査 cp15 の C-8①）＝「部品だけで確かめた完成の条件」の数え方を直す。
#   監査の逐語＝「完成の条件の表の『経路』の欄が 部品 の行だけを数える（実物 137行の全文検索をやめる）」。
#   直す前＝文書全体の | 行から「部品」を含む行を数えていた＝説明の文まで拾い、実測で 3件 と出た
#   （本当の該当は 0行）。まこさんの画面に、その数字が出ていた。
_m_at2 = re.search(r"^<!--\s*ACCEPT_TABLE_START\s*-->\s*$(.*?)^<!--\s*ACCEPT_TABLE_END\s*-->\s*$",
                   md, re.S | re.M)
n_part = 0
if _m_at2:
    _rows2 = []
    for _ln in _m_at2.group(1).splitlines():
        _s = _ln.strip()
        if not _s.startswith("|"):
            continue
        _cells = [c.strip() for c in _s.strip("|").split("|")]
        if set("".join(_cells)) <= set("-: "):
            continue
        _rows2.append(_cells)
    if _rows2:
        _hd = _rows2[0]
        _ir = next((i for i, c in enumerate(_hd) if "経路" in c), -1)
        if _ir >= 0:
            n_part = len([r for r in _rows2[1:] if _ir < len(r) and "部品" in r[_ir]])
# ★C-4＝実装から作った一覧は「照らせる」に数えない（二重に数えないため）
n_fn_ok = 0 if _same else n_fn
print(f"   機械で照らせる: {len(mu_from) + n_probe + n_fn_ok}件"
      f"（正本から作った名前 {len(mu_from)}件／振る舞いで測る一覧 {n_probe}件／関数の一致 {n_fn_ok}件）")
print(f"   機械で照らせない: {len(mu_hand) + n_sh + n_reason + n_self_gen}件"
      f"（手で書いた名前 {len(mu_hand)}件／bash の判定 {n_sh}件／設計書に書いた理由 {n_reason}件"
      f"／実装から作ったもの {n_self_gen}件）")
# ★2026-09-03（監査 cp14 の B-5）＝逃げ道が使われたら、件数として必ず画面に出す。
print(f"   逃げ道の件数: 空＋理由で通した一覧 {n_reason}件"
      f"／部品だけで確かめた完成の条件 {n_part}件")
PY
# ★2026-09-03（監査 cp14 の B-2）＝一覧を展開できなければ、承認そのものを取り消す。
#   黙って辞書のまま書き出すと、照合D が必ず落ちる形が固定されるため。
if [ $? -ne 0 ]; then
  rm -f "$STATE/acceptance.approved"
  echo "❌ 承認を取り消しました（上の理由）。設計書を直してから、もう一度 承認してください。" >&2
  exit 1
fi

# 承認した acceptance を git 管理 archive へ凍結保存（2026-06-27 まこさん指示・改善アーク自動生成の源）。
#   acceptance.md は state/ で gitignore＋上書き＝永続しない。承認の瞬間に .claude/ratchet/（git 追跡）へコピー＝
#   各 iter の承認版が git に永続（指紋＋git の二重で改ざん検出）。gen_improvement_arc.py が今後 iter の
#   狙い/内容/方法 を ここの ARC マーカーから読む（acceptance archive 優先・無ければ ledger）。
ARC_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive"
mkdir -p "$ARC_DIR"
ITER=$(grep -oE 'iter="[^"]*"' "$LIST" | head -1 | sed 's/iter="//;s/"$//')
# ★2026-09-03（監査 cp15 の C-8②・P-9）＝上書きする前に、前の版を連番で残して git に登録する。
#   監査の逐語＝「approve_impl.sh が承認のたびに ①前の版の控え（連番つき）②その版の指紋
#   ③差分の全文 を acceptance_archive/ へ保存し、git に登録する。保存が失敗したら承認を取り消す」。
#   直す前＝同じ名前の控えを毎回 上書きしていた＝「設計書を1文字も変えていない」を後から確かめられなかった。
if [ -n "$ITER" ]; then
  SAFE_P=$(printf '%s' "$ITER" | tr ' /' '__')
  PREV_MD="$ARC_DIR/${SAFE_P}.md"
  if [ -f "$PREV_MD" ]; then
    SEQ=1
    while [ -f "$ARC_DIR/${SAFE_P}.$(printf '%02d' $SEQ).md" ]; do SEQ=$((SEQ+1)); done
    KEEP="$ARC_DIR/${SAFE_P}.$(printf '%02d' $SEQ).md"
    cp "$PREV_MD" "$KEEP" || { echo "❌ 前の版を保存できませんでした。承認を取り消します。" >&2; rm -f "$STATE/acceptance.approved"; exit 1; }
    diff "$PREV_MD" "$LIST" > "${KEEP%.md}.diff.txt" 2>/dev/null
    shasum -a 256 "$PREV_MD" | awk '{print $1}' > "${KEEP%.md}.sha.txt"
    ( cd "/Users/tachiharamasako/Documents/GitHub/cat-bitget" && git add "$KEEP" "${KEEP%.md}.diff.txt" "${KEEP%.md}.sha.txt" ) \
      || { echo "❌ 前の版を git に登録できませんでした。承認を取り消します。" >&2; rm -f "$STATE/acceptance.approved"; exit 1; }
    echo "   🗂 前の版を残しました: $(basename "$KEEP")（指紋と差分の全文つき・git に登録）"
  fi
fi
if [ -n "$ITER" ]; then
  SAFE=$(printf '%s' "$ITER" | tr ' /' '__')
  cp "$LIST" "$ARC_DIR/${SAFE}.md"
  # ★2026-09-03（監査 cp15 の C-5）＝控えごとに、その承認時の凍結も一緒に残す。
  cp "$FROZEN_OUT" "$ARC_DIR/${SAFE}.frozen.json" 2>/dev/null \
    && echo "   🧊 控えの凍結も残しました: ${SAFE}.frozen.json（この控えを照合するときは これと比べます）"
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

# ★2026-09-03（監査 cp15 の C-3・Critical）＝承認の記録を1本にする。
#   監査の逐語＝「approve_impl.sh が design_approved.json も同時に更新する
#   （または approve_design.sh を approve_impl.sh から呼ぶ）」。
#   何が起きていたか（実測）＝12:07 に設計書を承認 → 12:20 に設計書を書き換え → 12:22 に
#   approve_impl.sh だけ打ち直した。design_approved.json は 12:07 のまま置き去りで、
#   上流の実行ゲートが閉じたまま監査依頼書が書かれた（監査 S-1）。
#   ★同じ処理を2か所に書き写さない＝もう一方の承認スクリプトを、ここから呼ぶ。
echo "── もう一方の承認の記録（design_approved.json）も同時に更新します（監査 cp15 の C-3）──"
bash "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_design.sh" "$LIST"
if [ $? -ne 0 ]; then
  echo "❌ もう一方の承認の記録を更新できませんでした。承認を取り消します。" >&2
  rm -f "$STATE/acceptance.approved"
  exit 1
fi

# ★2026-09-03（監査 cp15 の P-8）＝承認の直後に「いま強制が通るか」を自分で確かめる。
#   監査の逐語＝「approve_impl.sh の末尾で verify_design_contract.py --check-approval <設計書> を
#   実行し、通らなければ承認を取り消す」。
#   何が起きていたか＝承認したのにゲートが閉じたまま、監査依頼書が書かれた（監査 S-1）。
echo "── 承認の直後に、いま強制が通るかを自分で確かめます（監査 cp15 の P-8）──"
VERIFY_TOOL_PY="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py"
CHK=$(python3 "$VERIFY_TOOL_PY" --check-approval "$LIST" 2>&1)
if [ $? -ne 0 ]; then
  echo "❌ 承認を取り消します。承認したのに、強制が通らない状態です（監査 cp15 の P-8）。" >&2
  echo "$CHK" >&2
  rm -f "$STATE/acceptance.approved"
  exit 1
fi
echo "   ✅ $CHK"

# ★2026-09-03（監査 cp16 の E-12・まこさん指名・承認 36051934db6eede3）
#   ＝壊し方を機械が実行し、終了コードを控えに保存する。
#   監査の逐語＝「完成の条件の各行の壊し方をコマンドの文字列にし、承認スクリプトが実際に
#     走らせて acceptance_archive/<iter>.breaks.json に終了コードを保存する。
#     ✅ 済 は終了コードが0でないときだけ書ける」。
#   ★順番＝①壊すプログラムを凍結する ②走らせる ③書けなかったら承認を取り消す。
#     凍結を先にするのは、走らせるプログラムが「凍結と違えば止まる」作りだから。
#   ★まこさん指示 2026-09-03＝「.claude/breaks/*.sh は、承認の時点で凍結する。
#     承認前は自由に書ける。承認後に1文字でも変わったら、run_breaks.py が rc=2 で止まる。」
RUNB="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/run_breaks.py"
if [ -f "$RUNB" ]; then
  echo "── 壊し方を機械が走らせます（監査 cp16 の E-12）──"
  python3 "$RUNB" --freeze
  if [ $? -ne 0 ]; then
    echo "❌ 壊すプログラムを凍結できませんでした。承認を取り消します（監査 cp16 の E-12）。" >&2
    rm -f "$STATE/acceptance.approved"
    exit 1
  fi
  python3 "$RUNB" --design "$LIST" --iter "$ITER"
  if [ $? -ne 0 ]; then
    echo "❌ 壊し方の記録を作れませんでした。承認を取り消します（監査 cp16 の E-12・P-9 と同じ扱い）。" >&2
    rm -f "$STATE/acceptance.approved"
    exit 1
  fi
else
  echo "   ⚠️ 走らせるプログラムがまだありません（$RUNB）＝壊し方の記録は作られません。" >&2
fi

echo "   以後このリストを変更したら再承認が必要です。"
