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

判定の材料
  .claude/state/read_log.txt … record_read.sh（PostToolUse on Read）が Read tool の実績を
  絶対パスで1行ずつ書く。SessionStart の reset_read_log.sh が毎セッション消す。

限界（正直に書く）
  ・Read tool の offset/limit（一部だけ読む）を区別できない。1行でも開けば「読んだ」になる。
  ・本文に書かないファイルは C の対象外＝「書かなければ通る」。A と B は書かなくても効く。
  ・受け入れ条件の中身が正しいかは見ない。まこさんの目と併用する。
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

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


def targets_in(text: str) -> list[str]:
    out: list[str] = []
    for ln in text.splitlines():
        if not ln.startswith("TARGET:"):
            continue
        for part in ln[len("TARGET:"):].split(","):
            p = part.strip()
            if p:
                out.append(p)
    return out


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
    for tgt in targets_in(text):
        cand = _SDK / tgt
        if not _opened(tgt, log):
            ng.append(f"A 直す対象を開いていない: {tgt}")
        for gen in generates_of(cand):
            if not _opened(gen, log):
                ng.append(f"B その対象が作る文書を開いていない: {gen}")
    for f in claimed_files(text):
        if not _opened(f, log):
            ng.append(f"C 『読んだ』と書いたのに開いていない: {f}")
    return list(dict.fromkeys(ng))


def _payload_text(d: dict) -> str:
    ti = d.get("tool_input", {}) or {}
    parts: list[str] = []
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
    if p is not None and p.exists():
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
    log_ok = [
        "/x/scripts/priority_rebuild/gen_materials.py",
        "/x/.claude/ratchet/materials.md",
        "/x/.claude/ratchet/materials.json",
        "/x/.claude/memory/regime_detection_kb.md",
    ]
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
    real = _SDK / "scripts" / "priority_rebuild" / "gen_materials.py"
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

    for x in ng:
        print(f"❌ {x}")
    print(f"{'❌' if ng else '✅'} わざと壊して止まるか試すテスト {10 - len(ng)}/10 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
