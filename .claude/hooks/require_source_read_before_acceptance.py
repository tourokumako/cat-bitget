#!/usr/bin/env python3
"""require_source_read_before_acceptance.py — 受け入れ条件を書く瞬間の必読ゲート（本体）

なぜ要るか（2026-08-19・41回目・まこさん指示「必読hookを作れ」）
  CC は受け入れ条件（.claude/state/acceptance.md）を、正本を開かずに書いた。
  ・直す対象 gen_materials.py は読んだが、それが作る materials.md を読んでいなかった
  ・照合の相手（entry_exit_matrix.md ほか4本）を1本も読んでいなかった
  ・そのうえ「読んだもの」の表に、開いていないファイルを1本 書いた（虚偽）
  根っこ＝どの正本を読むかを CC が決め、読んだかどうかも CC が申告していた。
  だから、両方をプログラムに渡す。

何を見るか（3つ）
  A: TARGET に書いた対象のファイルを Read tool で開いたか
  B: TARGET が自動で作る文書（その .py の GENERATES の欄）を開いたか
  C: 受け入れ条件の本文で「読んだ」「開いた」と書いた行に出てくるファイルを、本当に開いたか

★2026-08-27（68回目・まこさん承認「進めて良い」・設計書 iter=new-file-target-gate-20260827）
  新しく作るファイルを TARGET に書けるようにした（next_step.md §6 の86番＝2026-08-23 から放置）。

  なぜ要ったか
    A は「TARGET のパスを開いたか」だけを見て、そのファイルが実在するかを見ていなかった。
    新しく作るファイルは存在しない＝開けない＝必ず止まる。
    ＝新しいファイルを作る受け入れ条件が、1本も書けなかった（56回目と68回目の2回 当たった）。

  何を足したか（2行）
    NEW_FILE: … 新しく作るファイルのパス（カンマ区切りで複数可）
    MODEL:    … 手本にしたファイルのパス（カンマ区切り・1本以上）
    ★TARGET の行の書き方は1文字も変えていない。
      理由＝TARGET の行を読む仕組みが5本 在り、そのうち require_acceptance_before_impl.sh は
      行の中身をそのままファイル名として使う（同 87行）＝印を足すとファイル名が壊れる。

  判定（TARGET 1件ごと）
    ① NEW_FILE に書いていない                   → 今までどおり（開いていなければ ❌）
    ② NEW_FILE に書いた ＋ 実在しない ＋ MODEL を全部 開いた → 通す（★新しく通るのはここだけ）
    ③ NEW_FILE に書いた ＋ 実在する             → ❌（宣言が嘘）
    ④ NEW_FILE に書いた ＋ MODEL の行が無い     → ❌
    ⑤ NEW_FILE に書いた ＋ MODEL を開いていない → ❌
    ★②のとき、そのパスは C の検査からも外す（新しいファイルは開けないため）。

  取らなかった直し方
    「ファイルが無ければ A を飛ばす」は取らない。
    ファイル名を打ち間違えただけでも「無い」と判定され、何も開かずに書けてしまうため（86番に記載）。

判定の材料
  .claude/state/read_log.txt … record_read.sh（PostToolUse on Read）が Read tool の実績を
  絶対パスで1行ずつ書く。SessionStart の reset_read_log.sh が毎セッション消す。

限界（正直に書く）
  ・Read tool の offset/limit（一部だけ読む）を区別できない。1行でも開けば「読んだ」になる。
  ・本文に書かないファイルは C の対象外＝「書かなければ通る」。A と B は書かなくても効く。
  ・手本（MODEL）に何を挙げるかは CC が決める＝関係の薄いファイルを挙げても通る。
  ・新規と宣言せずに、既に在る別のファイルを TARGET にして回る道は残る（68回目に CC がやった）。
  ・囲み（```）の中に書いた見本の行も、TARGET・MODEL の宣言として読む（next_step.md §6 の113番）。
    避け方＝見本の行の頭に空白を入れる。
  ・受け入れ条件の中身が正しいかは見ない。まこさんの目と併用する。
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys
import tempfile

_REPO = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
_SDK = _REPO / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
_READ_LOG = _REPO / ".claude" / "state" / "read_log.txt"
_ACCEPTANCE_NAMES = ("acceptance.md",)

# 本文で「読んだ」と名乗っている行を拾う語
_CLAIM_WORDS = ("読んだ", "読みました", "開いた", "開いて読ん", "読了")
# ファイルらしい文字の並び
_FILE_RE = re.compile(r"[A-Za-z0-9_./\-]+\.(?:md|py|json)")
# 本文の中でファイル名を囲っている記号を外す
_STRIP = "`*「」（）()［］[]、。 \t"


def read_log_paths() -> list[str]:
    if not _READ_LOG.exists():
        return []
    return [ln.strip() for ln in _READ_LOG.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _opened(token: str, log: list[str]) -> bool:
    """token（パスの断片でもよい）が read_log に在るか。末尾一致と basename 一致の両方で見る。"""
    t = token.strip(_STRIP)
    if not t:
        return True
    base = t.rsplit("/", 1)[-1]
    for p in log:
        if p.endswith("/" + t) or p.endswith(t) or p.rsplit("/", 1)[-1] == base:
            return True
    return False


def generates_of(py_path: pathlib.Path) -> list[str]:
    """その .py が『自分が作る文書』として名乗っているものを取り出す（GENERATES の欄）。"""
    if not py_path.exists() or py_path.suffix != ".py":
        return []
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    out: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "GENERATES" not in names:
            continue
        try:
            val = ast.literal_eval(node.value)
        except Exception:
            continue
        for item in val or []:
            if isinstance(item, (list, tuple)) and item:
                out.append(str(item[0]))
            elif isinstance(item, str):
                out.append(item)
    return out


def _line_values(text: str, prefix: str) -> list[str]:
    """行の頭が prefix の行から、カンマ区切りのパスを集める（重複は残す）。"""
    out: list[str] = []
    for ln in text.splitlines():
        if not ln.startswith(prefix):
            continue
        for part in ln[len(prefix):].split(","):
            p = part.strip()
            if p:
                out.append(p)
    return out


def targets_in(text: str) -> list[str]:
    return _line_values(text, "TARGET:")


def new_files_in(text: str) -> list[str]:
    """NEW_FILE: の行＝これから新しく作るファイル（2026-08-27・86番の直し）。"""
    return _line_values(text, "NEW_FILE:")


def models_in(text: str) -> list[str]:
    """MODEL: の行＝手本にしたファイル（新しく作るときに、A の代わりに読了を確かめる相手）。"""
    return _line_values(text, "MODEL:")


def _exists_anywhere(rel: str) -> bool:
    """そのパスが実在するか。リポジトリの直下と bitget-python-sdk-api の直下の2か所を見る。

    ★2か所を見る理由＝受け入れ条件の TARGET は、両方の書き方で書かれてきたため
      （例＝.claude/hooks/… はリポジトリ直下／scripts/priority_rebuild/… は sdk 直下）。
    """
    r = rel.strip(_STRIP)
    if not r:
        return False
    return (_REPO / r).exists() or (_SDK / r).exists()


def claimed_files(text: str) -> list[str]:
    """本文で『読んだ』と名乗っている所に出てくるファイル名を集める。

    ★行だけを見ると取りこぼす（2026-08-19 に実測）。
      CC は見出しの文に「実際に開いて読んだものだけを書きます」と書き、
      その下の表の行にはファイル名だけを書いた＝行に「読んだ」の語が無い。
    だから「名乗りの文が出てから、次の見出しか区切り線までの間」をまとめて見る。
    """
    out: list[str] = []
    in_claim = False
    for ln in text.splitlines():
        s = ln.strip()
        # 見出し・区切り線で名乗りの範囲を閉じる
        if s.startswith("#") or s.startswith("---"):
            in_claim = any(w in ln for w in _CLAIM_WORDS)
            if in_claim:
                for m in _FILE_RE.finditer(ln):
                    out.append(m.group(0))
            continue
        if any(w in ln for w in _CLAIM_WORDS):
            in_claim = True
        if in_claim:
            for m in _FILE_RE.finditer(ln):
                out.append(m.group(0))
    # 重複を消す（順番は保つ）
    return list(dict.fromkeys(out))


def check(text: str, log: list[str]) -> list[str]:
    """足りないものの一覧を返す（空なら通す）。"""
    ng: list[str] = []
    news = {n.strip(_STRIP) for n in new_files_in(text)}
    models = models_in(text)
    declared_new: set[str] = set()          # ②が成り立った＝C の検査からも外すもの
    for tgt in targets_in(text):
        cand = _SDK / tgt
        t = tgt.strip(_STRIP)
        if t in news:
            # ③ 新規と書いたのに実在する＝宣言が嘘
            if _exists_anywhere(t):
                ng.append(f"A 新規（NEW_FILE:）と書いたのに実在する: {tgt}"
                          "（新規の宣言を外して、そのファイルを開く）")
                continue
            # ④ 手本の行が無い
            if not models:
                ng.append(f"A 新規（NEW_FILE:）なのに手本（MODEL:）の行が無い: {tgt}"
                          "（手本にしたファイルを1本以上 書く）")
                continue
            # ⑤ 手本を開いていない
            miss = [m for m in models if not _opened(m, log)]
            if miss:
                for m in miss:
                    ng.append(f"A 手本（MODEL:）を開いていない: {m}")
                continue
            # ② 通す（B は実在しないので元から飛ぶ）
            declared_new.add(t)
            continue
        if not _opened(tgt, log):
            if not _exists_anywhere(t):
                ng.append(f"A 直す対象が実在しない: {tgt}"
                          "（新しく作るなら NEW_FILE: と MODEL: の2行を足す）")
            else:
                ng.append(f"A 直す対象を開いていない: {tgt}")
        for gen in generates_of(cand):
            if not _opened(gen, log):
                ng.append(f"B その対象が作る文書を開いていない: {gen}")
    for f in claimed_files(text):
        if f.strip(_STRIP) in declared_new:  # 新しく作るファイルは開けない＝C の対象外
            continue
        if not _opened(f, log):
            ng.append(f"C 『読んだ』と書いたのに開いていない: {f}")
    return list(dict.fromkeys(ng))


def _payload_text(d: dict) -> str:
    """検査に掛ける文章を組み立てる。

    ★まるごと書き換えるとき（Write＝`content` が在る）は、いま在るファイルを読まない
      （2026-08-27・まこさん承認「どちらもOK」）。
      なぜ直したか＝設計書は毎回 `acceptance.md` へ**上書き**する決まり（恒久の決まり §0-2 の1番）。
      直す前は、いま在るファイルの中身も一緒に読んで対象を拾っていたので、**対象が変わるたびに
      「前の設計書の対象」と、その対象が作る文書を開けと要求していた**（2026-08-26 に実際に起きた
      ＝前の設計の `gen_materials.py` と関連文書4本を、関係が無いのに開かされた）。
    ★一部だけ書き換えるとき（Edit／MultiEdit）は、いまのまま読む。書き込む中身に `TARGET:` の
      行が入らないので、いま在るファイルから拾わないと A と B の検査が効かなくなるため。
    ★この直しで新しい穴は開かない＝まるごと書き換えでも、書き込む中身に `TARGET:` が在れば
      A と B は今までどおり効く（下の T11〜T13 で実測）。
    """
    ti = d.get("tool_input", {}) or {}
    parts: list[str] = []
    full_overwrite = isinstance(ti.get("content"), str)     # Write＝まるごと書き換え
    for k in ("content", "new_string"):
        v = ti.get(k)
        if isinstance(v, str):
            parts.append(v)
    for e in ti.get("edits", []) or []:
        v = (e or {}).get("new_string")
        if isinstance(v, str):
            parts.append(v)
    fp = ti.get("file_path") or ""
    p = pathlib.Path(fp) if fp else None
    if p is not None and p.exists() and not full_overwrite:
        try:
            parts.append(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return "\n".join(parts)


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    fp = (d.get("tool_input", {}) or {}).get("file_path") or ""
    if pathlib.Path(fp).name not in _ACCEPTANCE_NAMES:
        return 0
    text = _payload_text(d)
    if not targets_in(text) and not claimed_files(text):
        return 0
    ng = check(text, read_log_paths())
    if not ng:
        return 0
    print("🔒 [必読ゲート・受け入れ条件] 正本を開かずに受け入れ条件を書こうとしています。",
          file=sys.stderr)
    print("   まこさん指示 2026-08-19「必読hookを作れ」。"
          "根っこ＝どの正本を読むかを CC が決め、読んだかも CC が申告していた。", file=sys.stderr)
    print("", file=sys.stderr)
    for x in ng:
        print(f"   ❌ {x}", file=sys.stderr)
    print("", file=sys.stderr)
    print("   対処＝上のファイルを Read tool で実際に開いてから、書き直してください。", file=sys.stderr)
    print("   A＝直す対象そのもの ／ B＝その対象が作る文書（GENERATES の欄）"
          " ／ C＝本文で『読んだ』と書いたファイル", file=sys.stderr)
    print("   （解除の合言葉はありません＝2026-08-16 に全部 廃止）", file=sys.stderr)
    return 2


# ── わざと壊して止まるか試すテスト ──────────────────────────────────────────
def selftest() -> int:
    ng: list[str] = []
    real = _SDK / "scripts" / "priority_rebuild" / "gen_materials.py"
    # ★「全部 開いた」の見本は手書きしない＝実物の GENERATES から作る（2026-08-27）。
    #   直す前は materials.md と materials.json の2本を手で書いていた。65回目（2026-08-26）に
    #   gen_materials.py が やることリスト2本も作るようになり、見本が古くなって T3 と T5 が
    #   落ちたまま気づかれなかった（＝手書きの一覧は腐る。印の一覧を機械で集めるのと同じ理由）。
    log_ok = (["/x/scripts/priority_rebuild/gen_materials.py"]
              + [f"/x/{g}" for g in generates_of(real)]
              + ["/x/.claude/memory/regime_detection_kb.md"])
    tgt = "TARGET: scripts/priority_rebuild/gen_materials.py\n"

    # T1 何も開いていない → A で止まる
    if not any(x.startswith("A ") for x in check(tgt, [])):
        ng.append("T1: 対象を開いていないのに通った")
    # T2 対象だけ開いた → B（作る文書）で止まる
    only_py = ["/x/scripts/priority_rebuild/gen_materials.py"]
    if not any(x.startswith("B ") for x in check(tgt, only_py)):
        ng.append("T2: 作る文書を開いていないのに通った")
    # T3 対象と作る文書を開いた → 通る
    if check(tgt, log_ok):
        ng.append("T3: 全部 開いているのに止まった")
    # T4 『読んだ』と書いたのに開いていない → C で止まる
    lie = tgt + "\n| `.claude/memory/nonexistent_kb.md` | 読んだ |\n"
    if not any(x.startswith("C ") for x in check(lie, log_ok)):
        ng.append("T4: 開いていないファイルを『読んだ』と書いたのに通った")
    # T5 『読んだ』と書いたものを本当に開いている → 通る
    honest = tgt + "\n| `.claude/memory/regime_detection_kb.md` | 読んだ |\n"
    if check(honest, log_ok):
        ng.append("T5: 正しく開いているのに止まった")
    # T6 TARGET が無い文書は対象外（空を返す）
    if check("ただの文章です。\n", []):
        ng.append("T6: TARGET も『読んだ』も無いのに止まった")
    # T7 GENERATES の取り出しが実物で動く
    gens = generates_of(real)
    if not any(g.endswith("materials.md") for g in gens):
        ng.append(f"T7: 実物から GENERATES を取り出せない（取れたもの＝{gens}）")
    # T8 末尾一致の取り違えが無い（別の materials.md を開いても、別の道のものは通す）
    if _opened("scripts/priority_rebuild/gen_materials.py", ["/x/y/gen_other.py"]):
        ng.append("T8: 関係の無いファイルで通ってしまう")
    # T9 ★見出しの文で名乗り、表の行にはファイル名だけ、の形でも拾う（2026-08-19 の実測で追加）
    sec = (tgt + "\n#### ④ ベースアップ\n\n実際に開いて読んだものだけを書きます。\n\n"
           "| 読んだもの | 何が書いてあったか |\n|---|---|\n"
           "| `.claude/memory/nonexistent_kb.md` | レジーム判定の手法 |\n")
    if not any(x.startswith("C ") for x in check(sec, log_ok)):
        ng.append("T9: 見出しで名乗り表に並べた形を拾えない（2026-08-19 に実際に取りこぼした形）")
    # T10 名乗りの範囲は次の見出しで閉じる（関係の無い節のファイル名を巻き込まない）
    sec2 = (tgt + "\n## 読んだもの\n\n| `.claude/ratchet/materials.md` | 読んだ |\n"
            "\n## 触るファイル\n\n`.claude/memory/nonexistent_kb.md` を将来 使うかもしれない\n")
    if any("nonexistent_kb" in x for x in check(sec2, log_ok)):
        ng.append("T10: 別の節のファイル名まで『読んだ』として巻き込んでいる")

    # ── T11〜T13 まるごと書き換えのとき、いま在るファイルを読まない（2026-08-27・まこさん承認）──
    #   ★直す前は、前の設計書の対象を開けと要求していた（2026-08-26 に実際に起きた）。
    with tempfile.TemporaryDirectory() as _td:
        _old = pathlib.Path(_td) / "acceptance.md"
        _old.write_text("TARGET: scripts/priority_rebuild/gen_materials.py\n"
                        "\n読んだもの＝`.claude/ratchet/materials.md`\n", encoding="utf-8")
        _new_tgt = "TARGET: scripts/priority_rebuild/engine_tuner_gen.py\n"
        # T11 まるごと書き換え（Write）＝新しい対象だけを見る（前の対象を持ち込まない）
        _w = _payload_text({"tool_input": {"file_path": str(_old), "content": _new_tgt}})
        if "gen_materials.py" in _w:
            ng.append("T11: まるごと書き換えなのに、前の設計書の対象を持ち込んでいる")
        if "engine_tuner_gen.py" not in _w:
            ng.append("T11: 書き込む中身の対象が拾えていない")
        # T12 一部だけ書き換え（Edit）＝いまのまま、いま在るファイルから対象を拾う
        _e = _payload_text({"tool_input": {"file_path": str(_old), "new_string": "1行だけ足す\n"}})
        if "gen_materials.py" not in _e:
            ng.append("T12: 一部だけの書き換えで、いま在るファイルの対象を拾えていない（穴が開く）")
        # T13 メタ確認＝まるごと書き換えでも、その対象を開いていなければ やはり止まる
        if not any(x.startswith("A ") for x in check(_w, [])):
            ng.append("T13 メタ確認: まるごと書き換えで、対象を開いていないのに通ってしまう")

    # ── N1〜N6 新しく作るファイルを TARGET に書ける（2026-08-27・86番・まこさん承認「進めて良い」）──
    _new = "scripts/dashboard/nonexistent_new_file_for_selftest.py"
    _exist = "scripts/priority_rebuild/gen_materials.py"
    _m1 = "scripts/dashboard/build_regime_gate_rg.py"
    _m2 = "scripts/priority_rebuild/regime_r9_diag.py"
    _log_models = [f"/x/{_m1}", f"/x/{_m2}"]
    if _exists_anywhere(_new):
        ng.append(f"N0: 見本に使う『実在しないパス』が実在する（見本を変える）: {_new}")
    if not _exists_anywhere(_exist):
        ng.append(f"N0: 見本に使う『実在するパス』が実在しない（見本を変える）: {_exist}")
    # N1 新規＋実在しない＋手本を全部 開いた → 通る（★この設計で新しく通る唯一の形）
    n1 = f"TARGET: {_new}\nNEW_FILE: {_new}\nMODEL: {_m1}, {_m2}\n"
    if check(n1, _log_models):
        ng.append(f"N1: 新規＋手本を開いているのに止まった（{check(n1, _log_models)}）")
    # N2 新規と書いたのに実在する → 止まる
    n2 = f"TARGET: {_exist}\nNEW_FILE: {_exist}\nMODEL: {_m1}\n"
    if not any("実在する" in x for x in check(n2, _log_models)):
        ng.append("N2: 新規と書いたのに実在するのに通った")
    # N3 新規なのに手本の行が無い → 止まる
    n3 = f"TARGET: {_new}\nNEW_FILE: {_new}\n"
    if not any("手本（MODEL:）の行が無い" in x for x in check(n3, _log_models)):
        ng.append("N3: 手本の行が無いのに通った")
    # N4 新規＋手本を1本も開いていない → 止まる
    if not any("手本（MODEL:）を開いていない" in x for x in check(n1, [])):
        ng.append("N4: 手本を開いていないのに通った")
    # N5 新規と宣言していない＋実在しない → 止まる（画面の文が「実在しない」に変わる）
    n5 = f"TARGET: {_new}\n"
    if not any("直す対象が実在しない" in x for x in check(n5, [])):
        ng.append("N5: 新規と宣言していない実在しない対象で通った、または文が変わっていない")
    # N6 新規＋手本2本のうち1本だけ開いた → 止まる
    if not any("手本（MODEL:）を開いていない" in x for x in check(n1, [f"/x/{_m1}"])):
        ng.append("N6: 手本を1本しか開いていないのに通った")

    for x in ng:
        print(f"❌ {x}")
    print(f"{'❌' if ng else '✅'} わざと壊して止まるか試すテスト {19 - len(ng)}/19 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
