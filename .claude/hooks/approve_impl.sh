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

# ★2026-09-06（まこさん指示「だから、強制でミスを繰り返さないようにしろよ」・設計書 iter="pre-audit-check-20260906"）
#   ＝承認の前に、設計書ゲートの全判定をここでも走らせ、不足を全部 出す。
#   なぜ要るか（実測）＝2026-09-06 に CC は同じ設計書で承認を7回 求めた。毎回 違う判定に当たり、
#   出た分だけ直して残りを確かめずに出していた。承認の瞬間に全部 出せば、その往復が消える。
#   ★CC が --check-design を打ち忘れても、ここで止まる（これが強制の本体）。
#   ★2026-09-06 に直した＝直す前は require_acceptance_before_impl.sh を --check で呼んでいたが、
#     hook 側の口は --check-md なので分岐に入らず、標準入力も渡していなかったので file_path が空になり、
#     対象外として何も見ずに通っていた（＝この強制は空振りしていた）。
#     いまは pre_audit_check.py --check-design を呼ぶ＝設計書ゲートを2群とも走らせる
#     （群1＝実装ファイルを書く瞬間の判定を TARGET 全部に対して ／ 群2＝設計書そのものを書く瞬間の判定）。
_PRE_CHECK=$(python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-design "$LIST" 2>&1)
if [ $? -ne 0 ]; then
  echo "❌ 承認を中止します（設計書に不足が在ります・2026-09-06 の強制）:" >&2
  printf '%s\n' "$_PRE_CHECK" | sed 's/^/   /' >&2
  echo "   ★上の不足を全部 直してから、もう一度 承認してください。" >&2
  exit 1
fi

# ★2026-10-04（154回目・まこさん指示・逐語「承認するまえに確認するフローに修正して」
#   「私が承認する前にCCが設計書の内容を確認して修正箇所を見つけられるように、フローを修正すべき」）
#   ＝承認の前に、CC が設計書のいまの版を全部の項目について見直し終えているかを見る（見直し表＝gen_review.py --check）。
#   なぜ要るか（実測）＝154回目に CC は、道具が作った設計書を全部 読む前に承認のコマンドを出した。CC の側の検査
#   （require_read_used・require_design_check_before_approval）はターンの終わりに走るので、返信は先に画面へ出て、
#   まこさんは承認を打たれた。CC は承認の後に読んで抜け（完成の条件に RCI の行が無い）を見つけた。
#   ★ここで止めれば、CC が見直しを飛ばしても・抜けを見つけたままでも、承認そのものが通らない（これが強制の本体）。
#   止まる条件＝見直し表が無い／設計書のいまの版について書いたものではない／埋まっていない項目が在る／
#   判定が「抜け」の項目が残っている。限界＝見直しの判断が正しいかは見ない。
_RV_CHECK=$(python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/gen_review.py" --check "$LIST" 2>&1)
if [ $? -ne 0 ]; then
  echo "❌ 承認を中止します（CC が設計書の見直しを終えていません・2026-10-04 の強制）:" >&2
  printf '%s\n' "$_RV_CHECK" | sed 's/^/   /' >&2
  echo "   ★CC に「設計書を全部 読んで見直し表を埋め、抜けを直してから、もう一度 承認をお願いして」と伝えてください。" >&2
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
from verify_design_contract import resolve_spec_list, contract_for_freeze      # noqa: E402
md = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])
frozen_out = pathlib.Path(sys.argv[3])
# ★2026-09-05（監査 cp20 の C1・C2・Critical・まこさん承認 iter="freeze-fail-closed-cp20-20260905"）
#   ＝囲みを自前の regex で選ぶのをやめ、照合の道具と同じ関数（contract_for_freeze → extract_block）で
#     契約を1つ取る＝囲みの選択規則を1つにする（C2）。
#   直す前＝「最後の impl_file の囲み」を取り、impl_functions が無ければ黙って {} を凍結した
#     （2026-09-04 に3回・空が凍結されたのは2本）。spec_lists も「どの囲みでも在れば集める」だった。
#   直した後＝契約が読めない／impl_functions が無い／空で理由なし、のどれかなら
#     凍結を書く前に承認を中止する（C1・fail-closed）。理由の在る空（cp19 の形）は通す。
obj, why = contract_for_freeze(md)
if obj is None:
    print("❌ 承認を中止します（監査 cp20 の C1＝空の凍結を書かない）:", file=sys.stderr)
    print(f"   ・{why}", file=sys.stderr)
    sys.exit(3)
lists = dict(obj.get("spec_lists") or {})
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
# ★2026-09-05（監査 cp20 の C1）＝ここに来る obj は contract_for_freeze を通っている
#   ＝impl_functions は辞書で、空なら no_impl_functions_reason が在る。空で理由なしは上で止めた。
_fz = obj.get("impl_functions") or {}
frozen_out.parent.mkdir(parents=True, exist_ok=True)
frozen_out.write_text(json.dumps(
    {"_これは何か": "承認の瞬間に凍結した impl_functions。照合A・B はここと比べる（実装から作り直せない）。",
     "_作り方": "approve_impl.sh が承認の瞬間に acceptance.md から書き出す。手で書き換えない。",
     "_出どころ": sys.argv[1], **_fz}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"   🧊 impl_functions: {sum(len(v) for v in _fz.values() if isinstance(v, list))} 件を凍結しました"
      f" → {frozen_out.name}（以後この版と比べます）")

# ★2026-09-07（next_step §6 の138番・設計書 iter="approval-audit-plumbing-20260907"）
#   ＝承認の時点で「もう汚れていた .py」の一覧を凍結する。
#   何が困っていたか（実測）＝照合A(双方向)（verify_design_contract.py の 1044-1051行）は
#     git status に出る .py を全部 見て、設計書の impl_functions に無ければ落とす。
#     その .py が中で何を呼ぶかは見ない＝**並走している別のセッションが .py を編集中なら、
#     どの設計書でも同じように落ちる**（2026-09-06 に実測＝FAIL の10本は、その時点で
#     未コミットだった10本と1本も違わなかった）。
#   直した後＝承認の瞬間の「もう汚れていた .py」を基準として残し、照合A(双方向) はそれを数えない。
#     ＝この工事で触った .py だけが照合の相手になる。
#   ★限界（正直に）＝承認の前にわざと .py を汚しておけば、その1本は照合の外に出る。
#     ただし scripts/priority_rebuild/*.py と .claude/tools/*.py は承認の前に書けない
#     （承認ゲート）ので、この道が使えるのは hook の .py だけ（設計書 §7 の Q5 の5）。
import subprocess as _sp
_dirty_out = frozen_out.parent / "acceptance_archive" / (
    (re.search(r'iter="([^"]+)"', md).group(1).replace(" ", "_").replace("/", "_")
     if re.search(r'iter="([^"]+)"', md) else "noiter") + ".dirty.json")
_watch = ("scripts/priority_rebuild/", ".claude/hooks/", ".claude/tools/")
try:
    _root = _sp.run(["git", "rev-parse", "--show-toplevel"],
                    capture_output=True, text=True, timeout=30).stdout.strip()
    _st = _sp.run(["git", "-C", _root, "status", "--porcelain"],
                  capture_output=True, text=True, timeout=30).stdout if _root else ""
except Exception:                                          # noqa: BLE001
    _st = ""
_dirty = sorted({_l[3:].strip().split(" -> ")[-1] for _l in _st.splitlines()
                 if _l[3:].strip().endswith(".py")
                 and any(_w in _l for _w in _watch)})
_dirty_out.parent.mkdir(parents=True, exist_ok=True)
_dirty_out.write_text(json.dumps(
    {"_これは何か": "承認の瞬間に、もう汚れていた .py の一覧。照合A(双方向) はここに在るものを数えない。",
     "_なぜ": "並走している別のセッションが編集中の .py で、どの設計書でも落ちるのを止めるため（138番）。",
     "_作り方": "approve_impl.sh が承認の瞬間に git status から書き出す。手で書き換えない。",
     "files": _dirty}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"   🧊 承認の時点で汚れていた .py: {len(_dirty)} 本を基準として凍結しました"
      f" → {_dirty_out.name}（照合A(双方向) はこれを数えません）")

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
  # ★2026-09-29（まこさん指示「以下で修正すること」＝承認の後は、設計書の控えと一緒に archive へ移す）
  #   ＝設計の元となる逐語のファイル（.claude/state/verbatim/<iter>/）を acceptance_archive/verbatim/<iter>/ へ移して git に登録する。
  #   逐語の道具（gen_verbatim.py）は、名前の解決で この archive も探すので、移した後も設計書の照らしは通る。
  VB_SRC="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/verbatim/${ITER}"
  if [ -d "$VB_SRC" ]; then
    mkdir -p "$ARC_DIR/verbatim"
    VB_DST="$ARC_DIR/verbatim/${SAFE}"
    if [ -d "$VB_DST" ]; then
      SEQ=1
      while [ -d "$ARC_DIR/verbatim/${SAFE}.$(printf '%02d' $SEQ)" ]; do SEQ=$((SEQ+1)); done
      VB_DST="$ARC_DIR/verbatim/${SAFE}.$(printf '%02d' $SEQ)"
    fi
    mv "$VB_SRC" "$VB_DST" \
      && ( cd "/Users/tachiharamasako/Documents/GitHub/cat-bitget" && git add "$VB_DST" ) \
      || { echo "❌ 設計の元となる逐語のファイルを archive へ移せませんでした。承認を取り消します。" >&2; rm -f "$STATE/acceptance.approved"; exit 1; }
    echo "   📚 設計の元となる逐語のファイルも移しました: acceptance_archive/verbatim/$(basename "$VB_DST")/（git に登録）"
  fi
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
  # ★2026-09-17（仕組み1の後半・設計書 iter="breaks-target-count-20260917"・L-605・まこさん決定「載っているものだけにします」）
  #   ＝凍結の前に、壊すプログラムが探す文字を いまのコードで数える。
  #   この設計書の完成の条件に載っている壊すプログラムが、探す文字を ちょうど1か所 見つけられなければ承認を取り消す
  #   （0か所＝何も壊せない・2か所以上＝どこを壊すか定まらない）。載っていないものは画面に出すだけ。
  #   なぜ＝コードの行を直したのに壊すプログラムの探す文字を直さないと、承認で何も壊せず rc=0 になった（103回目の b95）。
  echo "── 壊すプログラムが探す文字を、いまのコードで数えます（L-605）──"
  CNT=$(python3 "$RUNB" --count-targets --design "$LIST" 2>&1); CNT_RC=$?
  printf '%s\n' "$CNT" | grep -v -e '^✅ 1か所' -e '^      相手=.*文字 1 か所' -e '^      相手=.*形 1 か所' -e '^— 数えない' -e '数えない理由＝'
  if [ "$CNT_RC" -ne 0 ]; then
    echo "❌ この設計書の壊すプログラムが、壊す相手の文字を ちょうど1か所 見つけられません。承認を取り消します（L-605）。" >&2
    echo "   ＝壊すプログラムの探す文字を、いまのコードの行に合わせてから、もう一度 承認してください。" >&2
    rm -f "$STATE/acceptance.approved"
    exit 1
  fi
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

  # ★2026-09-06（まこさん指示「承認3回は多い」→「できるならやれよ」）
  #   ＝走らせた終了コードを、設計書の「いまの状態」の欄へ**機械が**書き込む。
  #   直す前＝CC が手で「✅済」に書き換え、そのために**もう1回 承認**が要った。
  #     実測（同日）＝1つの工事で承認 5回（X-5・X-9）と 3回（X-7）＝合計8回。
  #   ★書き込むのは機械が測った終了コードだけ（CC の文章は1文字も入らない）。
  #   ★「未着手」の行だけを書き換える＝CC が既に説明を書いた行はそのまま。
  #   ★書き換えたら指紋を取り直す＝まこさんが打った1回で、承認と設計書が食い違わない。
  BJ="$ARC_DIR_PRE/$ITER.breaks.json"
  if [ -f "$BJ" ]; then
    python3 - "$LIST" "$BJ" <<'PYEOF'
import json
import re
import shlex
import subprocess
import sys
md_p, bj_p = sys.argv[1], sys.argv[2]
rows = (json.loads(open(bj_p, encoding='utf-8').read()) or {}).get('rows') or []
code = {str(r.get('no')): r.get('code') for r in rows}
# ★2026-09-08（next_step §6 の159番・監査 cp29 の §5-5）＝「済」の材料を、
#   「終了コードが 0 以外」から「宣言した期待値と一致したか（match）」に変える。
#   なぜ＝b51 は向きが裏返っている（土台ゲートが通った＝守りが消えた が「正しい成功」）。
#     0 以外なら何でも合格だと、中で異常が起きた終了コード（lib.sh の 99＝控えから
#     戻せなかった）まで「止まった」に数えた＝b51 の 1 と見分けが付かなかった。
#   ★古い記録には match が無い。そのときは今までどおり「0 以外」で判定する（後方互換）。
match = {str(r.get('no')): r.get('match') for r in rows if 'match' in r}
src = open(md_p, encoding='utf-8').read()

# ★2026-09-07（監査 cp25 の §5-1・Critical・まこさん承認 iter="cp25-done-mark-and-extra-tests-20260907"）
#   ＝「済」を書く条件を2つにした。
#   直す前＝壊すプログラムの終了コードが 0 以外なら、それだけで「済」を書いていた。
#     ＝壊すプログラムは2本しか無いのに、完成の条件11件とも「済」になった（監査 cp25 の実測）。
#     b33 は MMI にも 出口の枝の順番にも T33-e の行にも触れないのに、その3行まで済になった。
#     さらに #4 は「いま 0本」と書いてあるセルに済が付いた＝条件を満たしていない行が済になった。
#   直した後＝次の2つが**両方**そろったときだけ「済」を書く。
#     ①壊すプログラムの終了コードが 0 以外（＝その検査は本物）
#     ②その行の「その数字を出したコマンド」を実際に走らせ、終了コードが 0（＝条件が満たされている）
#   ★どちらか一方でも欠ければ「未着手」のまま残す。走らせた結果は画面に出す。
#   ★壊すプログラムの欄が空の行は済にしない（①が測れないため）。
#   限界（正直に）＝そのコマンドが条件を測っているかは見ない（終了コードだけ）。
#     時間のかかる行は打ち切りで未着手のまま残る。
SDK = ("/Users/tachiharamasako/Documents/GitHub/cat-bitget/"
       "v3-bitget-api-sdk/bitget-python-sdk-api")
# ★2026-09-12＝120 から 600 へ。
#   何が起きていたか（実測）＝完成の条件の「その数字を出したコマンド」には
#     `engine_tuner_gen.py --selftest` が多く、これは **7分4秒** かかる（2026-09-11 に実測）。
#     120秒では必ず打ち切られ、rc が None になり、その行は永久に「済」にならなかった。
#   ★走らせる道具（run_breaks.py）の打ち切りも、同じ理由で 600 に直した（同日）。
#     そちらは壊すプログラムを走らせるので、打ち切りのとき束ごと やさしく止める形にした。
#     こちらは条件のコマンドを走らせるだけ（何も壊さない）ので、秒数だけを直す。
TIMEOUT_SEC = 600


def _cmd_of(cell):
    """セルから、走らせるコマンドを取り出す（`…` で囲まれた最初のもの）。無ければ None。"""
    m = re.search(r'`([^`]+)`', cell or '')
    if not m:
        return None
    c = m.group(1).strip()
    return c if c.startswith('python3 ') or c.startswith('bash ') else None


def _run(cmd):
    """そのコマンドを走らせて終了コードを返す。走らせられなければ None。"""
    try:
        r = subprocess.run(shlex.split(cmd), cwd=SDK, capture_output=True,
                           text=True, timeout=TIMEOUT_SEC)
        return r.returncode
    except Exception:                                        # noqa: BLE001
        return None


# ★2026-09-17（仕組み3・まこさん指示 2026-09-16「この３つのミスを繰り返さない仕組みを作れ」・L-603・まこさん OK「１　OK」）
#   ＝機械が前に書いた「済」の行も、承認のたびに見直す。
#   直す前＝「未着手」の行しか見なかった。壊すプログラムを直して走らせ直しても、済の行の説明
#     （壊したときの rc と意味）は古いまま残った（103回目の #6＝古い壊すプログラムで付いた済と説明が残った）。
#   直した後＝機械の書いた済の行（「承認のときに機械が2つとも測った」の文字が在る行）も、未着手の行と
#     同じ2つの条件で測り直す。
#     ・2つとも通った → 説明を、いま測った rc と いまの壊すプログラムの意味（# MEANS:）で書き直す
#     ・どちらかが通らない → 「未着手」に戻し、理由を画面に出す
#   ★CC が手で書いた済の行（機械の文字が無い行）は触らない（いままでどおり）。
#   ★限界（正直に）＝済の行の条件のコマンドも走らせ直すので、承認の時間が延びる（1行あたり最大 TIMEOUT_SEC）。
MACHINE_DONE_RE = re.compile(r'\*\*✅済\*\*＝壊すと rc=[^|]*?（承認のときに機械が2つとも測った）(?:／壊した意味＝[^|]*)?')
n, out = 0, []
for ln in src.splitlines(True):
    t = ln.strip()
    _done_m = MACHINE_DONE_RE.search(ln) if t.startswith('|') else None
    if t.startswith('|') and ('**未着手**' in t or _done_m):
        cells = [c.strip() for c in t.strip('|').split('|')]
        no = cells[0] if cells else ''
        c = code.get(no)
        # 壊すプログラムの欄（見出しの並び＝# / 完成の条件 / コマンド / 経路 / 壊し方 / 壊すプログラム / …）
        brk = cells[5] if len(cells) > 5 else ''
        cmd = _cmd_of(cells[2] if len(cells) > 2 else '')
        ok_brk = match[no] if no in match else (c not in (0, None))
        _why = None
        if not ok_brk:
            _why = ("期待した終了コードと違う" if no in match
                    else "壊すプログラムが落ちていない") + f"（rc={c}）"
        elif not brk or brk in ('—', '-', ''):
            _why = "壊すプログラムの欄が空"
        elif cmd is None:
            _why = "走らせるコマンドを読み取れない"
        else:
            rc2 = _run(cmd)
            if rc2 != 0:
                _why = f"条件のコマンドが rc={rc2}（0 でない）"
        if _why is None:
            _mn = next((r.get('means') for r in rows if str(r.get('no')) == no), '')
            _sfx = f'／壊した意味＝{_mn}' if _mn else ''
            _new = (f'**✅済**＝壊すと rc={c}（宣言どおり）／条件のコマンドも rc=0'
                    f'（承認のときに機械が2つとも測った）{_sfx}')
            if _done_m:
                if _done_m.group(0) != _new:
                    ln = ln.replace(_done_m.group(0), _new, 1)
                    n += 1
                    print(f"   🔁 #{no} 済のまま＝測り直して説明を書き直した（壊すと rc={c}／条件のコマンド rc=0）")
                else:
                    print(f"   ✅ #{no} 済のまま＝測り直した結果も説明も前と同じ")
            else:
                ln = ln.replace('**未着手**', _new)
                n += 1
                print(f"   ✅ #{no} 済＝壊すと rc={c}（宣言どおり）／条件のコマンド rc=0")
            if _mn:
                print(f"        意味＝{_mn}")
        elif _done_m:
            ln = ln.replace(_done_m.group(0), '**未着手**', 1)
            n += 1
            print(f"   ⏪ #{no} を「未着手」に戻した＝測り直すと {_why}")
        else:
            print(f"   ⏸ #{no} は「未着手」のまま＝{_why}")
    out.append(ln)
if n:
    open(md_p, 'w', encoding='utf-8').write(''.join(out))
    print(f"   ✍️ 完成の条件 {n} 行の状態を書き替えました（済にした行・済の説明を書き直した行・未着手に戻した行の合計＝上の ✅／🔁／⏪）")
PYEOF
    NEW_H=$(shasum -a 256 "$LIST" | awk '{print $1}')
    OLD_H=$(cat "$STATE/acceptance.approved" 2>/dev/null)
    if [ "$NEW_H" != "$OLD_H" ]; then
      printf '%s' "$NEW_H" > "$STATE/acceptance.approved"
      python3 - "$LIST" "$NEW_H" "$STATE/design_approved.json" <<'PYEOF'
import json
import sys
md, h, p = sys.argv[1], sys.argv[2], sys.argv[3]
with open(p, 'w', encoding='utf-8') as f:
    json.dump({md: h}, f, ensure_ascii=False, indent=1)
    f.write('\n')
PYEOF
      echo "   🔏 承認の指紋を取り直しました: $(printf '%s' "$NEW_H" | cut -c1-16)…"
      echo "   ＝この1回で「済」まで確定します（承認をもう一度 打つ必要はありません）"
      # ★2026-09-08（監査 cp29 の §5-6・next_step §6 の160番）＝控えを取り直す。
      #   何が起きていたか＝控えは 322行 あたりで取るが、それは「済」を書き込む前の版だった。
      #     ＝控えだけを読むと、最後に「済」になった行が永久に未着手に見えた（実測＝12行目）。
      #   照合はどこも落ちていなかった（印は書き込んだ後の版を指すため）が、
      #   控えは「後から中身が分かる」ために残すもの（恒久の決まり §0-2）。
      #   ★上書きするのは <iter>.md（いちばん新しい承認版）だけ。連番の控え（.01〜）は触らない
      #     ＝あれは「前の版」の記録なので、書き替えると経緯が消える。
      if [ -n "$ITER" ]; then
        _SAFE_A=$(printf '%s' "$ITER" | tr ' /' '__')
        cp "$LIST" "$ARC_DIR/${_SAFE_A}.md" \
          && echo "   📦 控えを取り直しました: ${_SAFE_A}.md（「済」を書き込んだ後の版・160番）"
      fi
    fi
  fi
else
  echo "   ⚠️ 走らせるプログラムがまだありません（$RUNB）＝壊し方の記録は作られません。" >&2
fi

echo "   以後このリストを変更したら再承認が必要です。"
